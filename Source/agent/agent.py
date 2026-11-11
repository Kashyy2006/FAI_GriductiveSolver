"""No-guess deduction over public snapshots and injected Encoder/SATSolver protocols."""

import logging
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass, replace

from game.contracts import CancelCheck, Encoder, PublicEngine, SATSolver
from game.models import (
    AutoSolveResult,
    Classification,
    ClassificationResult,
    ContractError,
    DeductionStep,
    EncodingResult,
    HintResult,
    KBStatus,
    PublicCharacter,
    PublicState,
    SATQuery,
    SATStatus,
    SolveOutcome,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictProof,
    VerdictResult,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Analysis:
    encoding: EncodingResult
    result: ClassificationResult


class DeductiveAgent:
    """Use SAT consequences only; keep all query state local to an invocation."""

    def __init__(self, encoder: Encoder, solver: SATSolver) -> None:
        self._encoder = encoder
        self._solver = solver
        # Context-local recording captures synchronous verifier callbacks without
        # mixing simultaneous runs or retaining results from an older game session.
        self._run_queries: ContextVar[list[SATQuery] | None] = ContextVar(
            "griductive_run_queries", default=None
        )

    @staticmethod
    def _ordered(state: PublicState) -> tuple[PublicCharacter, ...]:
        """Validate public card visibility and return deterministic board order."""
        if not isinstance(state, PublicState):
            raise ContractError("Agent requires PublicState")
        for character in state.characters:
            if (character.status is None) != (character.clue is None):
                raise ContractError("Public status and clue must be revealed together")
        if len({character.id for character in state.characters}) != len(state.characters):
            raise ContractError("Duplicate public character IDs")
        return tuple(sorted(state.characters, key=lambda character: (character.row, character.col)))

    def _ask(
        self,
        encoding: EncodingResult,
        assumptions: tuple[int, ...],
        purpose: str,
        queries: list[SATQuery],
    ) -> SATStatus:
        """Record exactly one query per completed solve; let errors propagate."""
        variables = encoding.primary_variables + encoding.auxiliary_variables
        result = self._solver.solve(deepcopy(encoding.cnf), variables, assumptions)
        if not isinstance(result.status, SATStatus):
            raise ContractError("Solver returned an invalid SAT status")
        query = SATQuery(purpose, assumptions, result.status, result.stats)
        queries.append(query)
        run_queries = self._run_queries.get()
        if run_queries is not None:
            run_queries.append(query)
        return result.status

    def _analyze(self, state: PublicState, target: str | None = None) -> _Analysis:
        """Encode a fresh public snapshot, then check consistency and consequences."""
        ordered = self._ordered(state)
        encoding = self._encoder.encode(state)
        expected_map = {c.id: c.row * state.size + c.col + 1 for c in ordered}
        if encoding.variable_map != expected_map:
            raise ContractError("Encoder variable map must use row-major primary IDs")
        if set(encoding.primary_variables) != set(expected_map.values()):
            raise ContractError("Encoder must declare every primary variable")
        queries: list[SATQuery] = []
        if self._ask(encoding, (), "CONSISTENCY", queries) == SATStatus.UNSAT:
            return _Analysis(
                encoding,
                ClassificationResult(state.token, KBStatus.INCONSISTENT, {}, tuple(queries)),
            )
        classifications: dict[str, Classification] = {}
        for character in ordered:
            if character.status is not None or (target is not None and character.id != target):
                continue
            variable = encoding.variable_map[character.id]
            innocent = self._ask(encoding, (-variable,), f"ASSUME_INNOCENT:{character.id}", queries)
            criminal = self._ask(encoding, (variable,), f"ASSUME_CRIMINAL:{character.id}", queries)
            if innocent == criminal == SATStatus.UNSAT:
                raise ContractError("Solver contradicted its consistent-KB result")
            if innocent == SATStatus.UNSAT:
                classification = Classification.CRIMINAL
            elif criminal == SATStatus.UNSAT:
                classification = Classification.INNOCENT
            else:
                classification = Classification.UNKNOWN
            classifications[character.id] = classification
        return _Analysis(
            encoding,
            ClassificationResult(state.token, KBStatus.CONSISTENT, classifications, tuple(queries)),
        )

    def classify_all(self, state: PublicState) -> ClassificationResult:
        """Classify unresolved cards, returning an empty map for an inconsistent KB."""
        return self._analyze(state).result

    def verify_verdict(self, state: PublicState, character_id: str, status: Status) -> VerdictProof:
        """Prove a proposed verdict; ACCEPTED here is not an Engine commit."""
        ordered = self._ordered(state)
        if not isinstance(status, Status):
            raise ContractError("Verdict status must be a Status enum")
        character = next((c for c in ordered if c.id == character_id), None)
        if character is None:
            raise ContractError("Unknown character ID")
        if character.status is not None:
            raise ContractError("Character is already revealed")
        result = self._analyze(state, character_id).result
        if result.kb_status == KBStatus.INCONSISTENT:
            outcome = VerdictOutcome.INCONSISTENT
        else:
            classification = result.classifications[character_id]
            if classification == Classification.UNKNOWN:
                outcome = VerdictOutcome.NOT_PROVABLE
            elif classification.value == status.value:
                outcome = VerdictOutcome.ACCEPTED
            else:
                outcome = VerdictOutcome.CONTRADICTED
        return VerdictProof(state.token, character_id, status, outcome, result.queries)

    def next_hint(self, state: PublicState) -> HintResult:
        """Choose the first forced card in row-major order without mutating state."""
        analysis = self._analyze(state)
        result = analysis.result
        for character_id, classification in result.classifications.items():
            if classification != Classification.UNKNOWN:
                return HintResult(
                    state.token,
                    result.kb_status,
                    character_id,
                    Status(classification.value),
                    analysis.encoding.active_clue_ids,
                    result.queries,
                )
        return HintResult(
            state.token,
            result.kb_status,
            None,
            None,
            analysis.encoding.active_clue_ids,
            result.queries,
        )

    @staticmethod
    def _check_accepted(
        before: PublicState, result: VerdictResult, character_id: str, status: Status
    ) -> None:
        """Reject malformed acceptance receipts rather than fabricating a trace."""
        proof = result.proof
        if (
            proof is None
            or proof.token != before.token
            or proof.character_id != character_id
            or proof.requested_status != status
            or proof.outcome != VerdictOutcome.ACCEPTED
            or result.revealed_clue is None
        ):
            raise ContractError("Accepted verdict is missing a matching proof or revealed clue")
        expected = replace(
            before,
            token=StateToken(before.token.session_id, before.token.version + 1),
            characters=tuple(
                replace(c, status=status, clue=result.revealed_clue) if c.id == character_id else c
                for c in before.characters
            ),
        )
        if result.state != expected:
            raise ContractError("Accepted verdict must reveal exactly the submitted card")

    @staticmethod
    def _merge_proof_queries(
        queries: list[SATQuery], proof: VerdictProof | None, submit_start: int
    ) -> None:
        """Reconcile this submit's receipt with its live recording, not object IDs.

        Engine may deepcopy the proof. Calls made by this Agent are already in
        the context-local recorder; a foreign verifier has no such recording.
        Compare only this invocation's ordered sequence, never globally dedup
        query values: two identical solve calls still count as two calls.
        """
        if proof is None:
            return
        recorded = tuple(queries[submit_start:])
        if recorded:
            if recorded != proof.queries:
                raise ContractError("Verifier receipt differs from its recorded SAT calls")
        else:
            queries.extend(proof.queries)

    def auto_solve(
        self, engine: PublicEngine, *, should_cancel: CancelCheck | None = None
    ) -> AutoSolveResult:
        """Submit forced verdicts; log cancellation reasons and propagate failures."""
        queries: list[SATQuery] = []
        steps: list[DeductionStep] = []
        context_token = self._run_queries.set(queries)

        def finish(outcome: SolveOutcome, state: PublicState) -> AutoSolveResult:
            return AutoSolveResult(outcome, state, tuple(steps), tuple(queries))

        def cancel(reason: str, state: PublicState) -> AutoSolveResult:
            LOGGER.warning("AUTO_SOLVE_CANCELLED reason=%s", reason)
            return finish(SolveOutcome.CANCELLED, state)

        try:
            state = engine.get_public_state()
            while True:
                current = engine.get_public_state()
                if current.token != state.token:
                    return cancel("STATE_CHANGED", current)
                if should_cancel is not None and should_cancel():
                    return cancel("USER_CANCELLED", engine.get_public_state())
                start = len(queries)
                hint = self.next_hint(state)
                current = engine.get_public_state()
                if current.token != state.token:
                    return cancel("STATE_CHANGED", current)
                if should_cancel is not None and should_cancel():
                    return cancel("USER_CANCELLED", engine.get_public_state())
                if hint.kb_status == KBStatus.INCONSISTENT:
                    return finish(SolveOutcome.INCONSISTENT, current)
                # next_hint checks consistency even when all cards are already open.
                if all(c.status is not None for c in state.characters):
                    return finish(SolveOutcome.SOLVED, current)
                if hint.character_id is None or hint.status is None:
                    return finish(SolveOutcome.STUCK, current)
                submit_start = len(queries)
                receipt = engine.submit_verdict(
                    hint.character_id, hint.status, expected_token=hint.token
                )
                self._merge_proof_queries(queries, receipt.proof, submit_start)
                if receipt.outcome in (VerdictOutcome.STALE_STATE, VerdictOutcome.ALREADY_REVEALED):
                    return cancel(receipt.outcome.value, engine.get_public_state())
                if receipt.state.token.session_id != state.token.session_id:
                    return cancel("STATE_CHANGED", engine.get_public_state())
                if (
                    receipt.outcome != VerdictOutcome.ACCEPTED
                    and receipt.state.token != state.token
                ):
                    return cancel("STATE_CHANGED", engine.get_public_state())
                if receipt.outcome == VerdictOutcome.INCONSISTENT:
                    return finish(SolveOutcome.INCONSISTENT, receipt.state)
                if receipt.outcome != VerdictOutcome.ACCEPTED:
                    return cancel(f"ENGINE_{receipt.outcome.value}", engine.get_public_state())
                self._check_accepted(state, receipt, hint.character_id, hint.status)
                steps.append(
                    DeductionStep(
                        len(steps) + 1,
                        state.token,
                        receipt.state.token,
                        hint.active_clue_ids,
                        tuple(queries[start:]),
                        hint.character_id,
                        hint.status,
                        receipt.revealed_clue,
                    )
                )
                state = receipt.state
        except Exception as error:
            LOGGER.error("AUTO_SOLVE_ERROR type=%s", type(error).__name__)
            raise
        finally:
            self._run_queries.reset(context_token)
