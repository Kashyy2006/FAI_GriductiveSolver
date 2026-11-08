"""TV4 acceptance tests using scripted fakes, never the production solver/encoder."""

import logging
from collections.abc import Callable, Sequence
from copy import deepcopy
from dataclasses import dataclass, replace

import pytest

from agent.agent import DeductiveAgent
from game.contracts import VerdictVerifier
from game.models import (
    CNF,
    Classification,
    Clue,
    ClueType,
    ContractError,
    EncodingResult,
    KBStatus,
    Literal,
    PublicCharacter,
    PublicState,
    SATResult,
    SATStatus,
    SolveOutcome,
    SolverStats,
    SolverTimeout,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictResult,
)

IDS = tuple(f"{chr(65 + c)}{r + 1}" for r in range(3) for c in range(3))


def make_state(unresolved: tuple[str, ...] = ("A1", "B1", "C1")) -> PublicState:
    """Keep all nine public coordinates, including initially revealed cards."""
    return PublicState(
        "test",
        3,
        StateToken("session-1", 0),
        tuple(
            PublicCharacter(
                cell,
                f"Person {index}",
                "Job",
                index // 3,
                index % 3,
                None if cell in unresolved else Status.INNOCENT,
                None
                if cell in unresolved
                else Clue(f"initial_{cell}", ClueType.FACT, person=cell, status=Status.INNOCENT),
            )
            for index, cell in enumerate(IDS)
        ),
    )


def revealed(state: PublicState, cell: str, status: Status, clue: Clue) -> PublicState:
    return replace(
        state,
        token=StateToken(state.token.session_id, state.token.version + 1),
        characters=tuple(
            replace(c, status=status, clue=clue) if c.id == cell else c for c in state.characters
        ),
    )


@dataclass
class Program:
    """A scripted SAT response table for one public state, not a SAT algorithm."""

    encoding: EncodingResult
    answers: dict[tuple[int, ...], tuple[SATStatus, dict[int, bool] | None]]


def program(
    state: PublicState,
    forced: dict[str, Status] | None = None,
    *,
    consistent: bool = True,
    auxiliary: bool = False,
) -> Program:
    known = {c.id: c.status for c in state.characters if c.status is not None}
    known.update(forced or {})
    mapping = {cell: index + 1 for index, cell in enumerate(IDS)}
    cnf = [
        [mapping[cell] if value == Status.CRIMINAL else -mapping[cell]]
        for cell, value in sorted(known.items())
    ]
    aux = (10,) if auxiliary else ()
    if aux:
        cnf.append([10])
    if not consistent:
        cnf.append([])
    variables = tuple(mapping.values()) + aux
    model = {v: False for v in variables}
    model.update({mapping[cell]: value == Status.CRIMINAL for cell, value in known.items()})
    if aux:
        model[10] = True
    answers = {(): (SATStatus.SAT, model) if consistent else (SATStatus.UNSAT, None)}
    for cell, variable in mapping.items():
        for value in (False, True):
            assumption = (variable if value else -variable,)
            conflict = cell in known and (known[cell] == Status.CRIMINAL) != value
            answers[assumption] = (
                (SATStatus.UNSAT, None)
                if conflict or not consistent
                else (SATStatus.SAT, {**model, variable: value})
            )
    return Program(
        EncodingResult(
            cnf,
            mapping,
            tuple(mapping.values()),
            aux,
            len(cnf),
            tuple(sorted(c.clue.id for c in state.characters if c.clue is not None)),
        ),
        answers,
    )


class FakeEncoder:
    def __init__(self, programs: dict[StateToken, Program]) -> None:
        self.programs = programs
        self.states: list[PublicState] = []

    def encode(self, state: PublicState) -> EncodingResult:
        assert isinstance(state, PublicState)
        self.states.append(state)
        return self.programs[state.token].encoding


class FakeSolver:
    def __init__(self, programs: Sequence[Program]) -> None:
        self.programs = {self._key(p.encoding.cnf): p for p in programs}
        self.calls: list[tuple[CNF, tuple[int, ...], tuple[int, ...]]] = []
        self.errors: dict[int, Exception] = {}
        self.after_call: Callable[[], None] | None = None
        self.mutate_input = False

    @staticmethod
    def _key(cnf: CNF) -> tuple[tuple[int, ...], ...]:
        return tuple(tuple(clause) for clause in cnf)

    def solve(
        self,
        cnf: CNF,
        variables: Sequence[int],
        assumptions: Sequence[Literal] = (),
        *,
        timeout_seconds: float | None = None,
    ) -> SATResult:
        self.calls.append((deepcopy(cnf), tuple(variables), tuple(assumptions)))
        if len(self.calls) in self.errors:
            raise self.errors[len(self.calls)]
        p = self.programs[self._key(cnf)]
        assert set(variables) == set(p.encoding.primary_variables + p.encoding.auxiliary_variables)
        status, assignment = p.answers[tuple(assumptions)]
        if self.mutate_input:
            cnf.clear()
        if self.after_call is not None:
            self.after_call()
        return SATResult(status, deepcopy(assignment), SolverStats(0, 0, 0, len(self.calls) / 1000))


class FakePublicEngine:
    """Simulate only the public Engine protocol, plus test controls."""

    def __init__(
        self,
        states: Sequence[PublicState],
        verifier: VerdictVerifier,
        reject: VerdictOutcome | None = None,
    ) -> None:
        self._states = tuple(states)
        self._state = states[0]
        self._verifier = verifier
        self._accepted = 0
        self.reject = reject
        self.restart_on_submit = False
        self.submissions: list[tuple[str, Status, StateToken]] = []

    @property
    def hidden_solution(self) -> None:
        raise AssertionError("Agent must not read hidden solution")

    @property
    def puzzle(self) -> None:
        raise AssertionError("Agent must not read private puzzle")

    @property
    def unrevealed_clues(self) -> None:
        raise AssertionError("Agent must not read unrevealed clues")

    def get_public_state(self) -> PublicState:
        return self._state

    def submit_verdict(
        self, character_id: str, status: Status, *, expected_token: StateToken
    ) -> VerdictResult:
        self.submissions.append((character_id, status, expected_token))
        if self.restart_on_submit:
            self._state = replace(
                self._state, token=StateToken("restarted", expected_token.version)
            )
        if expected_token != self._state.token:
            return VerdictResult(VerdictOutcome.STALE_STATE, self._state, None, None)
        if self.reject is not None:
            return VerdictResult(self.reject, self._state, None, None)
        proof = self._verifier(self._state, character_id, status)
        if proof.outcome != VerdictOutcome.ACCEPTED:
            return VerdictResult(proof.outcome, self._state, None, proof)
        self._accepted += 1
        self._state = self._states[self._accepted]
        card = next(c for c in self._state.characters if c.id == character_id)
        assert card.status == status
        return VerdictResult(VerdictOutcome.ACCEPTED, self._state, card.clue, proof)


def setup(
    state: PublicState,
    forced: dict[str, Status] | None = None,
    *,
    consistent: bool = True,
    auxiliary: bool = False,
) -> tuple[DeductiveAgent, FakeEncoder, FakeSolver]:
    p = program(state, forced, consistent=consistent, auxiliary=auxiliary)
    encoder, solver = FakeEncoder({state.token: p}), FakeSolver([p])
    return DeductiveAgent(encoder, solver), encoder, solver


def chain(
    *, inconsistent_end: bool = False, foreign_verifier: bool = False
) -> tuple[DeductiveAgent, FakeEncoder, FakeSolver, FakePublicEngine]:
    """Only A1 is initially forced; its revealed clue enables B1."""
    s0 = make_state(("A1", "B1"))
    s1 = revealed(
        s0,
        "A1",
        Status.CRIMINAL,
        Clue("new_A1", ClueType.FACT, person="B1", status=Status.INNOCENT),
    )
    s2 = revealed(
        s1,
        "B1",
        Status.INNOCENT,
        Clue("new_B1", ClueType.FACT, person="A1", status=Status.CRIMINAL),
    )
    ps = [
        program(s0, {"A1": Status.CRIMINAL}),
        program(s1, {"B1": Status.INNOCENT}),
        program(s2, consistent=not inconsistent_end),
    ]
    # The last consistent CNF can match the prior program; their answers agree.
    encoder = FakeEncoder({s.token: p for s, p in zip((s0, s1, s2), ps)})
    solver = FakeSolver(ps)
    agent = DeductiveAgent(encoder, solver)
    verifier = DeductiveAgent(encoder, solver) if foreign_verifier else agent
    engine = FakePublicEngine([s0, s1, s2], verifier.verify_verdict)
    return agent, encoder, solver, engine


def test_classification_signs_complete_variables_and_no_input_mutation() -> None:
    state = make_state()
    before = deepcopy(state)
    agent, encoder, solver = setup(
        state, {"A1": Status.CRIMINAL, "B1": Status.INNOCENT}, auxiliary=True
    )
    solver.mutate_input = True
    encoding_before = deepcopy(encoder.programs[state.token].encoding)
    result = agent.classify_all(state)
    assert result.kb_status == KBStatus.CONSISTENT
    assert result.classifications == {
        "A1": Classification.CRIMINAL,
        "B1": Classification.INNOCENT,
        "C1": Classification.UNKNOWN,
    }
    assert [call[2] for call in solver.calls] == [(), (-1,), (1,), (-2,), (2,), (-3,), (3,)]
    assert all(call[1] == tuple(range(1, 11)) for call in solver.calls)
    assert result.queries[1].purpose == "ASSUME_INNOCENT:A1"
    assert result.queries[2].purpose == "ASSUME_CRIMINAL:A1"
    assert state == before
    assert encoder.programs[state.token].encoding == encoding_before


def test_inconsistent_kb_stops_before_entailment() -> None:
    state = make_state()
    agent, _, solver = setup(state, consistent=False)
    result = agent.classify_all(state)
    assert result.kb_status == KBStatus.INCONSISTENT
    assert result.classifications == {}
    assert len(solver.calls) == 1


def test_empty_kb_is_consistent_and_all_unknown() -> None:
    state = make_state(IDS)
    agent, _, solver = setup(state)
    result = agent.classify_all(state)
    assert solver.calls[0][0] == []
    assert result.kb_status == KBStatus.CONSISTENT
    assert set(result.classifications.values()) == {Classification.UNKNOWN}
    assert len(solver.calls) == 19


@pytest.mark.parametrize(
    ("cell", "status", "outcome"),
    [
        ("A1", Status.CRIMINAL, VerdictOutcome.ACCEPTED),
        ("B1", Status.INNOCENT, VerdictOutcome.ACCEPTED),
        ("A1", Status.INNOCENT, VerdictOutcome.CONTRADICTED),
        ("B1", Status.CRIMINAL, VerdictOutcome.CONTRADICTED),
        ("C1", Status.CRIMINAL, VerdictOutcome.NOT_PROVABLE),
        ("C1", Status.INNOCENT, VerdictOutcome.NOT_PROVABLE),
    ],
)
def test_verify_verdict(cell: str, status: Status, outcome: VerdictOutcome) -> None:
    state = make_state()
    agent, _, solver = setup(state, {"A1": Status.CRIMINAL, "B1": Status.INNOCENT})
    proof = agent.verify_verdict(state, cell, status)
    assert (proof.token, proof.character_id, proof.requested_status) == (state.token, cell, status)
    assert proof.outcome == outcome
    assert len(proof.queries) == len(solver.calls) == 3
    assert next(c for c in state.characters if c.id == cell).clue is None


def test_verify_inconsistent_has_no_verdict() -> None:
    state = make_state()
    agent, _, solver = setup(state, consistent=False)
    assert agent.verify_verdict(state, "A1", Status.CRIMINAL).outcome == VerdictOutcome.INCONSISTENT
    assert len(solver.calls) == 1


@pytest.mark.parametrize(
    ("cell", "status"), [("Z9", Status.CRIMINAL), ("A2", Status.INNOCENT), ("A1", "CRIMINAL")]
)
def test_verify_invalid_arguments_do_not_call_solver(cell: str, status: Status) -> None:
    state = make_state()
    agent, encoder, solver = setup(state)
    with pytest.raises(ContractError):
        agent.verify_verdict(state, cell, status)
    assert solver.calls == encoder.states == []


def test_hint_is_row_major_even_if_snapshot_order_is_shuffled() -> None:
    state = make_state(("A1", "B1", "A2"))
    state = replace(state, characters=tuple(reversed(state.characters)))
    before = deepcopy(state)
    agent, _, _ = setup(state, {"A2": Status.CRIMINAL, "B1": Status.INNOCENT})
    hint = agent.next_hint(state)
    assert (hint.character_id, hint.status, hint.token) == ("B1", Status.INNOCENT, state.token)
    assert hint.active_clue_ids == tuple(sorted(c.clue.id for c in state.characters if c.clue))
    assert state == before


@pytest.mark.parametrize("consistent", [True, False])
def test_no_hint(consistent: bool) -> None:
    state = make_state()
    agent, _, _ = setup(state, consistent=consistent)
    hint = agent.next_hint(state)
    assert hint.character_id is hint.status is None
    assert hint.kb_status == (KBStatus.CONSISTENT if consistent else KBStatus.INCONSISTENT)


def test_no_cached_reasoning_across_calls_or_restart_with_same_revision() -> None:
    s0 = make_state()
    s1 = replace(s0, token=StateToken("different-session", s0.token.version))
    p0, p1 = program(s0, {"A1": Status.CRIMINAL}), program(s1, {"A1": Status.INNOCENT})
    encoder, solver = FakeEncoder({s0.token: p0, s1.token: p1}), FakeSolver([p0, p1])
    agent = DeductiveAgent(encoder, solver)
    assert agent.next_hint(s0).status == Status.CRIMINAL
    first_count = len(solver.calls)
    assert agent.next_hint(s0).status == Status.CRIMINAL
    assert len(solver.calls) == 2 * first_count
    assert agent.next_hint(s1).status == Status.INNOCENT
    assert encoder.states == [s0, s0, s1]


@pytest.mark.parametrize("foreign_verifier", [False, True])
def test_reveal_chain_solved_and_each_actual_sat_call_recorded_once(foreign_verifier: bool) -> None:
    agent, encoder, solver, engine = chain(foreign_verifier=foreign_verifier)
    initial = deepcopy(engine.get_public_state())
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.SOLVED
    assert [s.character_id for s in result.steps] == ["A1", "B1"]
    assert [s.verdict for s in result.steps] == [Status.CRIMINAL, Status.INNOCENT]
    assert [s.step for s in result.steps] == [1, 2]
    assert len(result.queries) == len(solver.calls) == 15
    assert len({id(q) for q in result.queries}) == 15
    assert [q.stats.runtime_seconds for q in result.queries] == [n / 1000 for n in range(1, 16)]
    assert [len(s.queries) for s in result.steps] == [8, 6]
    assert result.queries[-1].purpose == "CONSISTENCY"
    assert all(q.assumptions == call[2] for q, call in zip(result.queries, solver.calls))
    assert all(q.result in (SATStatus.SAT, SATStatus.UNSAT) for q in result.queries)
    assert "new_A1" not in result.steps[0].active_clue_ids
    assert "new_A1" in result.steps[1].active_clue_ids
    assert result.steps[0].newly_revealed_clue.id == "new_A1"
    assert result.steps[1].newly_revealed_clue.id == "new_B1"
    assert result.steps[0].token_after == result.steps[1].token_before
    assert {s.token.version for s in encoder.states} == {0, 1, 2}
    assert engine.submissions[1][2].version == 1
    assert initial.token.version == 0 and initial.characters[0].clue is None


@pytest.mark.parametrize(
    ("consistent", "expected"), [(True, SolveOutcome.STUCK), (False, SolveOutcome.INCONSISTENT)]
)
def test_loop_no_progress(consistent: bool, expected: SolveOutcome) -> None:
    state = make_state()
    agent, _, solver = setup(state, consistent=consistent)
    engine = FakePublicEngine([state], agent.verify_verdict)
    result = agent.auto_solve(engine)
    assert result.outcome == expected
    assert result.steps == () and engine.submissions == []
    assert len(result.queries) == len(solver.calls)


def test_last_reveal_is_checked_for_inconsistency_before_solved() -> None:
    agent, _, _, engine = chain(inconsistent_end=True)
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.INCONSISTENT
    assert len(result.steps) == 2
    assert result.queries[-1].purpose == "CONSISTENCY"
    assert result.queries[-1].result == SATStatus.UNSAT


def test_initially_solved_still_checks_consistency() -> None:
    state = make_state(())
    agent, _, solver = setup(state)
    result = agent.auto_solve(FakePublicEngine([state], agent.verify_verdict))
    assert result.outcome == SolveOutcome.SOLVED
    assert result.steps == () and len(solver.calls) == 1


@pytest.mark.parametrize("when", ["before", "after_analysis", "after_reveal"])
def test_user_cancellation_logged_distinctly(when: str, caplog: pytest.LogCaptureFixture) -> None:
    agent, _, solver, engine = chain()
    checks = 0

    def cancel() -> bool:
        nonlocal checks
        checks += 1
        return checks >= {"before": 1, "after_analysis": 2, "after_reveal": 3}[when]

    with caplog.at_level(logging.WARNING):
        result = agent.auto_solve(engine, should_cancel=cancel)
    assert result.outcome == SolveOutcome.CANCELLED
    assert "reason=USER_CANCELLED" in caplog.text
    assert len(result.steps) == (1 if when == "after_reveal" else 0)
    assert len(result.queries) == len(solver.calls)
    if when == "before":
        assert solver.calls == []


def test_load_restart_same_revision_rejects_old_token_without_trace(
    caplog: pytest.LogCaptureFixture,
) -> None:
    agent, _, _, engine = chain()
    engine.restart_on_submit = True
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.CANCELLED
    assert result.steps == ()
    assert result.final_state.token == StateToken("restarted", 0)
    assert "reason=STALE_STATE" in caplog.text
    assert engine.submissions[0][2] == StateToken("session-1", 0)


@pytest.mark.parametrize(
    "outcome",
    [
        VerdictOutcome.ALREADY_REVEALED,
        VerdictOutcome.NOT_PROVABLE,
        VerdictOutcome.CONTRADICTED,
        VerdictOutcome.INCONSISTENT,
    ],
)
def test_engine_rejection_never_creates_accepted_trace(
    outcome: VerdictOutcome, caplog: pytest.LogCaptureFixture
) -> None:
    agent, _, solver, engine = chain()
    engine.reject = outcome
    result = agent.auto_solve(engine)
    expected = (
        SolveOutcome.INCONSISTENT
        if outcome == VerdictOutcome.INCONSISTENT
        else SolveOutcome.CANCELLED
    )
    assert result.outcome == expected
    assert result.steps == () and len(engine.submissions) == 1
    assert len(result.queries) == len(solver.calls)
    if outcome == VerdictOutcome.ALREADY_REVEALED:
        assert "reason=ALREADY_REVEALED" in caplog.text


def test_state_changes_during_inference_even_without_forced_hint(
    caplog: pytest.LogCaptureFixture,
) -> None:
    state = make_state()
    agent, _, solver = setup(state)
    engine = FakePublicEngine([state], agent.verify_verdict)
    replacement = replace(state, token=StateToken("loaded", 0))
    solver.after_call = lambda: setattr(engine, "_state", replacement)
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.CANCELLED
    assert result.final_state == replacement
    assert result.steps == () and engine.submissions == []
    assert "reason=STATE_CHANGED" in caplog.text


@pytest.mark.parametrize("method", ["classify", "verify", "hint", "auto"])
@pytest.mark.parametrize("call", [1, 2])
@pytest.mark.parametrize("error", [SolverTimeout("deadline"), RuntimeError("solver failed")])
def test_solver_timeout_and_errors_propagate_without_false_results(
    method: str, call: int, error: Exception, caplog: pytest.LogCaptureFixture
) -> None:
    state = make_state()
    agent, _, solver = setup(state, {"A1": Status.CRIMINAL})
    solver.errors[call] = error
    engine = FakePublicEngine([state], agent.verify_verdict)
    with pytest.raises(type(error)) as caught:
        if method == "classify":
            agent.classify_all(state)
        elif method == "verify":
            agent.verify_verdict(state, "A1", Status.CRIMINAL)
        elif method == "hint":
            agent.next_hint(state)
        else:
            agent.auto_solve(engine)
    assert caught.value is error
    assert len(solver.calls) == call and engine.submissions == []
    assert engine.get_public_state() == state
    if method == "auto":
        assert "AUTO_SOLVE_ERROR" in caplog.text


def test_error_during_engine_verifier_does_not_reveal() -> None:
    agent, _, solver, engine = chain()
    solver.errors[6] = SolverTimeout("verifier timeout")
    before = engine.get_public_state()
    with pytest.raises(SolverTimeout):
        agent.auto_solve(engine)
    assert engine.get_public_state() == before
    assert len(engine.submissions) == 1


def test_inconsistent_solver_answers_are_not_treated_as_a_proof() -> None:
    state = make_state()
    agent, _, solver = setup(state)
    solver.programs[next(iter(solver.programs))].answers[(-1,)] = (SATStatus.UNSAT, None)
    solver.programs[next(iter(solver.programs))].answers[(1,)] = (SATStatus.UNSAT, None)
    with pytest.raises(ContractError, match="contradicted"):
        agent.next_hint(state)


def test_missing_public_clue_and_wrong_variable_mapping_fail_early() -> None:
    state = make_state()
    agent, encoder, solver = setup(state)
    bad = replace(
        state,
        characters=(replace(state.characters[0], status=Status.CRIMINAL),) + state.characters[1:],
    )
    with pytest.raises(ContractError):
        agent.classify_all(bad)
    encoder.programs[state.token].encoding.variable_map["A1"] = 99
    with pytest.raises(ContractError, match="row-major"):
        agent.classify_all(state)
    assert solver.calls == []


def test_malformed_engine_acceptance_is_an_error_not_a_success() -> None:
    agent, _, _, engine = chain()
    original_submit = engine.submit_verdict

    def bad_submit(
        character_id: str, status: Status, *, expected_token: StateToken
    ) -> VerdictResult:
        receipt = original_submit(character_id, status, expected_token=expected_token)
        return replace(receipt, proof=None)

    engine.submit_verdict = bad_submit
    with pytest.raises(ContractError, match="matching proof"):
        agent.auto_solve(engine)


def test_rejected_receipt_with_changed_revision_cancels_instead_of_reporting_old_kb(
    caplog: pytest.LogCaptureFixture,
) -> None:
    agent, _, _, engine = chain()

    def stale_rejection(
        character_id: str, status: Status, *, expected_token: StateToken
    ) -> VerdictResult:
        engine._state = replace(
            engine.get_public_state(), token=StateToken(expected_token.session_id, 5)
        )
        return VerdictResult(VerdictOutcome.INCONSISTENT, engine.get_public_state(), None, None)

    engine.submit_verdict = stale_rejection
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.CANCELLED
    assert result.steps == ()
    assert "reason=STATE_CHANGED" in caplog.text


def test_query_recording_context_is_restored_after_a_failed_run() -> None:
    agent, _, solver, engine = chain()
    solver.errors[1] = SolverTimeout("first run failed")
    with pytest.raises(SolverTimeout):
        agent.auto_solve(engine)
    solver.errors.clear()
    actual_calls_before = len(solver.calls)
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.SOLVED
    assert len(result.queries) == len(solver.calls) - actual_calls_before == 15
