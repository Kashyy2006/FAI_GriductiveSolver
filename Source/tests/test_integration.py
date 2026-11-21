"""Real-stack regressions for proof ownership, SAT accounting, parity and resets."""

import json
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from agent.agent import DeductiveAgent
from agent.trace import save_trace
from game.engine import GameEngine
from game.models import (
    CNF,
    Clue,
    ClueType,
    Literal,
    PublicState,
    Puzzle,
    Region,
    RegionType,
    SATResult,
    SATStatus,
    SolveOutcome,
    SolverStats,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictProof,
    VerdictResult,
)
from game.puzzle_loader import load_puzzle, puzzle_from_dict
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver

SOURCE = Path(__file__).resolve().parents[1]


class CountingSolver:
    """Count actual calls without using the Agent's nested trace records."""

    def __init__(self, *, constant_stats: bool = False) -> None:
        self.inner = DPLLSolver()
        self.calls = 0
        self.constant_stats = constant_stats
        self.records: list[tuple[tuple[int, ...], SATStatus, SolverStats]] = []

    def solve(
        self,
        cnf: CNF,
        variables: Sequence[int],
        assumptions: Sequence[Literal] = (),
        *,
        timeout_seconds: float | None = None,
    ) -> SATResult:
        self.calls += 1
        result = self.inner.solve(cnf, variables, assumptions, timeout_seconds=timeout_seconds)
        if self.constant_stats:
            result = replace(result, stats=SolverStats(0, 0, 0, 0.0))
        self.records.append((tuple(assumptions), result.status, result.stats))
        return result


def chain_puzzle(size: int = 3) -> Puzzle:
    return load_puzzle(SOURCE / f"puzzles/{size}x{size}/example_01.json")


def common_neighbors_parity_puzzle(kind: ClueType) -> Puzzle:
    """Build a 3x3 chain whose B1 parity clue stays hidden until B1 is proved."""
    target = Status.CRIMINAL if kind == ClueType.EVEN else Status.INNOCENT
    statuses = {
        "A1": Status.INNOCENT,
        "B1": Status.CRIMINAL,
        "C1": Status.INNOCENT,
        "A2": Status.INNOCENT,
        "B2": target,
        "C2": Status.INNOCENT,
        "A3": Status.INNOCENT,
        "B3": Status.INNOCENT,
        "C3": Status.INNOCENT,
    }
    clues = {
        "A1": {"id": "clue_A1", "type": "FACT", "person": "B1", "status": "CRIMINAL"},
        "B1": {
            "id": "clue_B1",
            "type": kind.value,
            "region": {"kind": "COMMON_NEIGHBORS", "first": "A1", "second": "C1"},
        },
    }
    for cell_id in ("C1", "A2", "B2", "C2", "A3", "B3", "C3"):
        clues[cell_id] = {
            "id": f"clue_{cell_id}",
            "type": "FACT",
            "person": cell_id,
            "status": statuses[cell_id].value,
        }
    characters = []
    for row in range(3):
        for col in range(3):
            cell_id = f"{chr(65 + col)}{row + 1}"
            characters.append(
                {
                    "id": cell_id,
                    "name": f"Person {row * 3 + col + 1:02d}",
                    "profession": "Detective",
                    "row": row,
                    "col": col,
                    "hidden_status": statuses[cell_id].value,
                    "clue": clues[cell_id],
                }
            )
    return puzzle_from_dict(
        {
            "schema_version": "1.0",
            "puzzle_id": f"common_neighbors_{kind.value.lower()}",
            "size": 3,
            "characters": characters,
            "initially_revealed": ["A1"],
        }
    )


@pytest.mark.parametrize(("size", "expected_calls"), [(3, 105), (4, 301)])
@pytest.mark.parametrize("foreign_verifier", [False, True])
@pytest.mark.parametrize("constant_stats", [False, True])
def test_real_engine_copies_proof_without_double_counting_actual_calls(
    size: int, expected_calls: int, foreign_verifier: bool, constant_stats: bool
) -> None:
    solver = CountingSolver(constant_stats=constant_stats)
    encoder = CNFEncoder()
    agent = DeductiveAgent(encoder, solver)
    verifier = DeductiveAgent(encoder, solver) if foreign_verifier else agent
    engine = GameEngine(chain_puzzle(size), verifier.verify_verdict)
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.SOLVED
    assert len(result.steps) == size * size - 1
    assert len(result.queries) == solver.calls == expected_calls
    assert sum(len(step.queries) for step in result.steps) + 1 == expected_calls
    assert [step.step for step in result.steps] == list(range(1, size * size))
    assert result.queries[-1].purpose == "CONSISTENCY"
    assert (
        len([q for q in result.queries if q.purpose == "CONSISTENCY"]) == 2 * len(result.steps) + 1
    )


@pytest.mark.parametrize("kind", [ClueType.EVEN, ClueType.ODD])
def test_real_parity_clue_reveals_and_solves_without_a_fake_encoder(kind: ClueType) -> None:
    puzzle = chain_puzzle()
    # For ODD, invert both labels and FACT semantics to preserve the real chain.
    if kind == ClueType.ODD:

        def opposite(status: Status) -> Status:
            return Status.INNOCENT if status == Status.CRIMINAL else Status.CRIMINAL

        puzzle = replace(
            puzzle,
            characters=tuple(
                replace(
                    c,
                    hidden_status=opposite(c.hidden_status),
                    clue=replace(c.clue, status=opposite(c.clue.status)),
                )
                for c in puzzle.characters
            ),
        )
    first = puzzle.characters[0]
    puzzle = replace(
        puzzle,
        characters=(
            replace(
                first,
                clue=Clue(
                    "parity_initial", kind, region=Region(RegionType.EXPLICIT, cells=("B1",))
                ),
            ),
        )
        + puzzle.characters[1:],
    )
    solver = CountingSolver()
    agent = DeductiveAgent(CNFEncoder(), solver)
    engine = GameEngine(puzzle, agent.verify_verdict)
    initial = engine.get_public_state()
    hint = agent.next_hint(initial)
    assert hint.character_id == "B1"
    assert hint.status == (Status.INNOCENT if kind == ClueType.EVEN else Status.CRIMINAL)
    calls_before = solver.calls
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.SOLVED
    assert len(result.queries) == solver.calls - calls_before
    assert result.steps[0].active_clue_ids == ("parity_initial",)
    assert initial.characters[1].status is None
    assert engine.get_public_state().characters[1].status == hint.status


@pytest.mark.parametrize(
    ("kind", "target_status", "opposite_status"),
    [
        (ClueType.EVEN, Status.CRIMINAL, Status.INNOCENT),
        (ClueType.ODD, Status.INNOCENT, Status.CRIMINAL),
    ],
)
def test_hidden_common_neighbors_parity_clue_joins_kb_only_after_reveal(
    kind: ClueType, target_status: Status, opposite_status: Status
) -> None:
    puzzle = common_neighbors_parity_puzzle(kind)
    encoder = CNFEncoder()
    agent = DeductiveAgent(encoder, DPLLSolver())
    engine = GameEngine(puzzle, agent.verify_verdict)
    initial = engine.get_public_state()
    initial_before = deepcopy(initial)
    initial_encoding = encoder.encode(initial)

    assert initial_encoding.active_clue_ids == ("clue_A1",)
    assert initial.characters[1].status is None
    assert initial.characters[1].clue is None

    hint = agent.next_hint(initial)
    assert (hint.character_id, hint.status) == ("B1", Status.CRIMINAL)
    assert hint.active_clue_ids == ("clue_A1",)
    assert initial == initial_before

    unknown = engine.submit_verdict("B2", Status.CRIMINAL, expected_token=initial.token)
    assert unknown.outcome == VerdictOutcome.NOT_PROVABLE
    assert unknown.revealed_clue is None
    assert engine.get_public_state() == initial_before

    contradicted = engine.submit_verdict("B1", Status.INNOCENT, expected_token=initial.token)
    assert contradicted.outcome == VerdictOutcome.CONTRADICTED
    assert engine.get_public_state() == initial_before

    unproved_target = agent.verify_verdict(initial, "B2", target_status)
    assert unproved_target.outcome == VerdictOutcome.NOT_PROVABLE
    target_queries = {
        query.purpose: query.result
        for query in unproved_target.queries
        if query.purpose in ("ASSUME_INNOCENT:B2", "ASSUME_CRIMINAL:B2")
    }
    assert target_queries == {
        "ASSUME_INNOCENT:B2": SATStatus.SAT,
        "ASSUME_CRIMINAL:B2": SATStatus.SAT,
    }

    accepted = engine.submit_verdict("B1", Status.CRIMINAL, expected_token=initial.token)
    assert accepted.outcome == VerdictOutcome.ACCEPTED
    assert accepted.proof is not None
    assert accepted.proof.outcome == VerdictOutcome.ACCEPTED
    assert accepted.revealed_clue is not None
    after = accepted.state
    assert after.token.session_id == initial.token.session_id
    assert after.token.version == initial.token.version + 1
    assert after.characters[1].status == Status.CRIMINAL
    assert after.characters[1].clue == Clue(
        "clue_B1",
        kind,
        region=Region(RegionType.COMMON_NEIGHBORS, first="A1", second="C1"),
    )
    assert engine.get_public_state() == after

    assert initial == initial_before
    assert encoder.encode(initial) == initial_encoding
    after_encoding = encoder.encode(after)
    assert after_encoding.active_clue_ids == ("clue_A1", "clue_B1")
    assert [2] in after_encoding.cnf

    opposite_proof = agent.verify_verdict(after, "B2", opposite_status)
    assert opposite_proof.outcome == VerdictOutcome.CONTRADICTED
    opposite_query = next(
        query
        for query in opposite_proof.queries
        if query.purpose == f"ASSUME_{opposite_status.value}:B2"
    )
    assert opposite_query.result == SATStatus.UNSAT

    forced_proof = agent.verify_verdict(after, "B2", target_status)
    assert forced_proof.outcome == VerdictOutcome.ACCEPTED
    forced_query = next(
        query
        for query in forced_proof.queries
        if query.purpose == f"ASSUME_{target_status.value}:B2"
    )
    assert forced_query.result == SATStatus.SAT

    hint_after = agent.next_hint(after)
    assert (hint_after.character_id, hint_after.status) == ("B2", target_status)
    assert hint_after.active_clue_ids == ("clue_A1", "clue_B1")

    fresh_engine = GameEngine(puzzle, agent.verify_verdict)
    solved = agent.auto_solve(fresh_engine)
    assert solved.outcome == SolveOutcome.STUCK
    assert [step.character_id for step in solved.steps] == ["B1", "B2"]
    assert solved.steps[0].active_clue_ids == ("clue_A1",)
    assert solved.steps[1].active_clue_ids == ("clue_A1", "clue_B1")
    assert solved.steps[0].newly_revealed_clue.id == "clue_B1"
    assert solved.steps[1].newly_revealed_clue.id == "clue_B2"


def test_real_rejection_keeps_state_and_does_not_reveal_then_restart_invalidates_token() -> None:
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    engine = GameEngine(chain_puzzle(), agent.verify_verdict)
    state = engine.get_public_state()
    before = deepcopy(state)
    unknown = engine.submit_verdict("C1", Status.CRIMINAL, expected_token=state.token)
    assert unknown.outcome == VerdictOutcome.NOT_PROVABLE
    assert unknown.revealed_clue is None
    assert engine.get_public_state() == before
    forced = agent.next_hint(state)
    opposite = Status.INNOCENT if forced.status == Status.CRIMINAL else Status.CRIMINAL
    rejected = engine.submit_verdict(forced.character_id, opposite, expected_token=state.token)
    assert rejected.outcome == VerdictOutcome.CONTRADICTED
    assert engine.get_public_state() == before
    restarted = engine.restart()
    assert restarted.token.version == state.token.version
    assert restarted.token.session_id != state.token.session_id
    assert (
        engine.submit_verdict("B1", forced.status, expected_token=state.token).outcome
        == VerdictOutcome.STALE_STATE
    )


def test_tv4_trace_matches_each_real_reveal_and_proves_every_verdict(tmp_path: Path) -> None:
    """Audit public transitions, proof checks, snapshot ownership and JSON handoff."""
    solver = CountingSolver()
    encoder = CNFEncoder()
    agent = DeductiveAgent(encoder, solver)
    verified: list[tuple[PublicState, PublicState, VerdictProof, VerdictProof]] = []
    transitions: list[tuple[PublicState, VerdictResult]] = []

    def verify(state: PublicState, cell: str, status: Status) -> VerdictProof:
        proof = agent.verify_verdict(state, cell, status)
        verified.append((state, deepcopy(state), proof, deepcopy(proof)))
        return proof

    real_engine = GameEngine(chain_puzzle(), verify)

    class AuditedPublicEngine:
        """Observe the real Engine exclusively through its public protocol."""

        def get_public_state(self) -> PublicState:
            return real_engine.get_public_state()

        def submit_verdict(
            self, character_id: str, status: Status, *, expected_token: StateToken
        ) -> VerdictResult:
            before = real_engine.get_public_state()
            receipt = real_engine.submit_verdict(
                character_id, status, expected_token=expected_token
            )
            transitions.append((before, receipt))
            return receipt

    initial = real_engine.get_public_state()
    result = agent.auto_solve(AuditedPublicEngine())
    assert result.outcome == SolveOutcome.SOLVED
    assert len(transitions) == len(verified) == len(result.steps) == 8
    assert len(result.queries) == solver.calls == 105
    assert [(q.assumptions, q.result, q.stats) for q in result.queries] == solver.records
    assert [q for step in result.steps for q in step.queries] == list(result.queries[:-1])

    oracle = DPLLSolver()  # Separate calls must not inflate the measured run.
    for step, (before, receipt), (snapshot, saved, original, saved_proof) in zip(
        result.steps, transitions, verified
    ):
        assert before == snapshot == saved
        assert original == saved_proof == receipt.proof
        assert receipt.proof is not original
        assert receipt.proof.queries[0] is not original.queries[0]
        assert receipt.outcome == VerdictOutcome.ACCEPTED
        assert step.token_before == before.token == original.token
        assert step.token_after == receipt.state.token
        assert step.token_after.session_id == step.token_before.session_id
        assert step.token_after.version == step.token_before.version + 1
        assert step.active_clue_ids == tuple(
            sorted(c.clue.id for c in before.characters if c.clue is not None)
        )
        assert step.newly_revealed_clue == receipt.revealed_clue
        assert step.newly_revealed_clue.id not in step.active_clue_ids
        assert tuple(step.queries[-len(original.queries) :]) == original.queries
        for previous, current in zip(before.characters, receipt.state.characters):
            if previous.id == step.character_id:
                assert previous.status is previous.clue is None
                assert current.status == step.verdict
                assert current.clue == step.newly_revealed_clue
            else:
                assert previous == current

        kb = encoder.encode(before)
        variables = kb.primary_variables + kb.auxiliary_variables
        assert oracle.solve(kb.cnf, variables).status == SATStatus.SAT
        forced: list[tuple[str, Status]] = []
        for cell in sorted(before.characters, key=lambda c: (c.row, c.col)):
            if cell.status is not None:
                continue
            variable = kb.variable_map[cell.id]
            if oracle.solve(kb.cnf, variables, (-variable,)).status == SATStatus.UNSAT:
                forced.append((cell.id, Status.CRIMINAL))
            elif oracle.solve(kb.cnf, variables, (variable,)).status == SATStatus.UNSAT:
                forced.append((cell.id, Status.INNOCENT))
        assert (step.character_id, step.verdict) == forced[0]

    exported = deepcopy(result)
    destination = tmp_path / "tv4" / "trace.json"
    save_trace(exported.steps, destination)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert len(payload) == 8
    for record, step in zip(payload, result.steps):
        assert record["token_before"] == {
            "session_id": step.token_before.session_id,
            "version": step.token_before.version,
        }
        assert record["active_clue_ids"] == list(step.active_clue_ids)
        assert record["newly_revealed_clue"]["id"] == step.newly_revealed_clue.id
        assert record["verdict"] == step.verdict.value
    text = destination.read_text(encoding="utf-8")
    assert "hidden_status" not in text and "assignment" not in text
    real_engine.restart()
    assert initial.token != real_engine.get_public_state().token
    assert result == exported
    for snapshot, saved, original, saved_proof in verified:
        assert snapshot == saved and original == saved_proof


@pytest.mark.parametrize("operation", ["restart", "load"])
@pytest.mark.parametrize("foreign_verifier", [False, True])
def test_real_reset_inside_verifier_cancels_without_reveal_or_duplicate_queries(
    operation: str, foreign_verifier: bool
) -> None:
    """Reset after a real proof exists but before Engine's atomic token recheck."""
    solver = CountingSolver()
    encoder = CNFEncoder()
    agent = DeductiveAgent(encoder, solver)
    verifier = DeductiveAgent(encoder, solver) if foreign_verifier else agent
    observations: list[tuple[PublicState, VerdictProof, PublicState]] = []

    def reset_after_proving(state: PublicState, cell: str, status: Status) -> VerdictProof:
        proof = verifier.verify_verdict(state, cell, status)
        assert proof.outcome == VerdictOutcome.ACCEPTED
        fresh = engine.restart() if operation == "restart" else engine.load(chain_puzzle())
        observations.append((state, proof, fresh))
        return proof

    engine = GameEngine(chain_puzzle(), reset_after_proving)
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.CANCELLED
    assert result.steps == ()
    assert len(observations) == 1
    before, proof, fresh = observations[0]
    assert proof.token == before.token
    assert before.token.version == fresh.token.version == 0
    assert before.token.session_id != fresh.token.session_id
    assert result.final_state == engine.get_public_state() == fresh
    assert sum(c.status is not None for c in fresh.characters) == 1
    assert len(result.queries) == solver.calls == 20
    assert [(q.assumptions, q.result, q.stats) for q in result.queries] == solver.records
