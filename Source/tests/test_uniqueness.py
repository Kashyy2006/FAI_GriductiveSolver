"""Uniqueness projection, hidden-data boundaries, immutability and shared budgets."""

from collections.abc import Sequence
from copy import deepcopy
from dataclasses import replace
from typing import Any

import pytest
from tv3_helpers import FixedEncoder, make_puzzle

from game.models import (
    CNF,
    Character,
    ContractError,
    EncodingResult,
    PublicState,
    SATResult,
    SATStatus,
    SolverStats,
    SolverTimeout,
    Status,
    UniquenessOutcome,
)
from solver.dpll import DPLLSolver
from solver.uniqueness import check_uniqueness


class RecordingSolver:
    def __init__(self) -> None:
        self.calls = []

    def solve(
        self,
        cnf: CNF,
        variables: Sequence[int],
        assumptions: Sequence[int] = (),
        *,
        timeout_seconds: float | None = None,
    ) -> SATResult:
        self.calls.append((deepcopy(cnf), tuple(variables), tuple(assumptions), timeout_seconds))
        return DPLLSolver().solve(cnf, variables, assumptions, timeout_seconds=timeout_seconds)


@pytest.mark.parametrize(
    ("cnf", "outcome", "count"),
    [
        ([[]], UniquenessOutcome.NO_SOLUTION, 0),
        ([[v] for v in range(1, 10)], UniquenessOutcome.UNIQUE, 1),
        ([[1]], UniquenessOutcome.MULTIPLE, 2),
    ],
)
def test_outcomes_and_query_recording(cnf: CNF, outcome: UniquenessOutcome, count: int) -> None:
    puzzle = make_puzzle()
    before = deepcopy(puzzle)
    encoder = FixedEncoder(cnf)
    solver = RecordingSolver()
    result = check_uniqueness(puzzle, encoder, solver)
    assert result.outcome == outcome
    assert len(result.primary_models) == count
    assert len(result.queries) == len(solver.calls) == (1 if count == 0 else 2)
    assert [q.purpose for q in result.queries] == ["UNIQUENESS_FIRST", "UNIQUENESS_SECOND"][
        : len(solver.calls)
    ]
    assert all(q.assumptions == () for q in result.queries)
    assert all(set(model) == {c.id for c in puzzle.characters} for model in result.primary_models)
    if count == 2:
        assert result.primary_models[0] != result.primary_models[1]
    assert puzzle == before
    assert all(c.status is None and c.clue is not None for c in encoder.states[0].characters)


def test_auxiliary_variants_do_not_make_primary_assignment_nonunique() -> None:
    cnf = [[v] for v in range(1, 10)] + [[10, 11]]
    encoder = FixedEncoder(cnf, (10, 11))
    solver = RecordingSolver()
    result = check_uniqueness(make_puzzle(), encoder, solver)
    assert result.outcome == UniquenessOutcome.UNIQUE
    assert solver.calls[1][0][-1] == list(range(-1, -10, -1))
    assert len(solver.calls[1][0][-1]) == 9
    assert encoder.cnf == cnf


def test_solver_mutating_its_cnf_cannot_corrupt_encoding_or_blocking_clause() -> None:
    encoder = FixedEncoder([[v] for v in range(1, 10)])

    class MutatingSolver(RecordingSolver):
        def solve(
            self,
            cnf: CNF,
            variables: Sequence[int],
            assumptions: Sequence[int] = (),
            *,
            timeout_seconds: float | None = None,
        ) -> SATResult:
            result = super().solve(cnf, variables, assumptions, timeout_seconds=timeout_seconds)
            cnf.clear()
            return result

    solver = MutatingSolver()
    assert check_uniqueness(make_puzzle(), encoder, solver).outcome == UniquenessOutcome.UNIQUE
    assert len(solver.calls[1][0]) == 10
    assert encoder.cnf == [[v] for v in range(1, 10)]


def test_hidden_status_is_never_read_and_initial_verdicts_are_not_encoded() -> None:
    class GuardedCharacter(Character):
        def __getattribute__(self, name: str) -> Any:
            if name == "hidden_status":
                raise AssertionError("Uniqueness must not inspect hidden labels")
            return super().__getattribute__(name)

    puzzle = make_puzzle()
    cells = tuple(
        GuardedCharacter(c.id, c.name, c.profession, c.row, c.col, Status.CRIMINAL, c.clue)
        for c in puzzle.characters
    )
    encoder = FixedEncoder([])
    result = check_uniqueness(replace(puzzle, characters=cells), encoder, DPLLSolver())
    assert result.outcome == UniquenessOutcome.MULTIPLE
    assert all(c.status is None for c in encoder.states[0].characters)


def test_one_budget_covers_encoding_and_both_solver_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    now = [0.0]
    monkeypatch.setattr("solver._timing.perf_counter", lambda: now[0])

    class SlowEncoder(FixedEncoder):
        def encode(self, state: PublicState) -> EncodingResult:
            now[0] += 0.2
            return super().encode(state)

    class SlowSolver(RecordingSolver):
        def solve(
            self,
            cnf: CNF,
            variables: Sequence[int],
            assumptions: Sequence[int] = (),
            *,
            timeout_seconds: float | None = None,
        ) -> SATResult:
            result = super().solve(cnf, variables, assumptions, timeout_seconds=timeout_seconds)
            now[0] += 0.3
            return result

    solver = SlowSolver()
    result = check_uniqueness(make_puzzle(), SlowEncoder([]), solver, timeout_seconds=1.0)
    assert result.outcome == UniquenessOutcome.MULTIPLE
    assert [call[3] for call in solver.calls] == pytest.approx([0.8, 0.5])


def test_timeout_after_second_call_is_not_reported_as_unique(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [0.0]
    monkeypatch.setattr("solver._timing.perf_counter", lambda: now[0])

    class SlowSolver(RecordingSolver):
        def solve(
            self,
            cnf: CNF,
            variables: Sequence[int],
            assumptions: Sequence[int] = (),
            *,
            timeout_seconds: float | None = None,
        ) -> SATResult:
            result = super().solve(cnf, variables, assumptions, timeout_seconds=timeout_seconds)
            now[0] += 0.6
            return result

    with pytest.raises(SolverTimeout):
        check_uniqueness(
            make_puzzle(),
            FixedEncoder([[v] for v in range(1, 10)]),
            SlowSolver(),
            timeout_seconds=1.0,
        )


def test_timeout_while_encoding_prevents_any_solver_call(monkeypatch: pytest.MonkeyPatch) -> None:
    now = [0.0]
    monkeypatch.setattr("solver._timing.perf_counter", lambda: now[0])

    class ExpiredEncoder(FixedEncoder):
        def encode(self, state: PublicState) -> EncodingResult:
            now[0] = 2.0
            return super().encode(state)

    solver = RecordingSolver()
    with pytest.raises(SolverTimeout):
        check_uniqueness(make_puzzle(), ExpiredEncoder([]), solver, timeout_seconds=1.0)
    assert solver.calls == []


def test_bad_solver_model_is_rejected() -> None:
    class InvalidSolver:
        def solve(self, *args: Any, **kwargs: Any) -> SATResult:
            return SATResult(SATStatus.SAT, {}, SolverStats(0, 0, 0, 0.0))

    with pytest.raises(ContractError, match="complete"):
        check_uniqueness(make_puzzle(), FixedEncoder([]), InvalidSolver())


def test_bad_encoding_and_puzzle_are_rejected() -> None:
    class InvalidEncoder(FixedEncoder):
        def encode(self, state: PublicState) -> EncodingResult:
            return replace(super().encode(state), primary_variables=(1,))

    with pytest.raises(ContractError):
        check_uniqueness(make_puzzle(), InvalidEncoder([]), DPLLSolver())
    for puzzle in (None, replace(make_puzzle(), size=True), replace(make_puzzle(), characters=())):
        with pytest.raises(ContractError):
            check_uniqueness(puzzle, FixedEncoder([]), DPLLSolver())
