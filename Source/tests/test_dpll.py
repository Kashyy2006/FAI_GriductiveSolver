"""DPLL correctness checked against an independent exhaustive truth evaluator."""

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from itertools import combinations, product
from random import Random
from typing import Any

import pytest

from game.models import CNF, ContractError, SATStatus, SolverTimeout
from solver.dpll import DPLLSolver


def _models(
    cnf: CNF, variables: tuple[int, ...], assumptions: tuple[int, ...] = ()
) -> list[dict[int, bool]]:
    models = []
    for values in product((False, True), repeat=len(variables)):
        model = dict(zip(variables, values))
        if all(model[abs(literal)] == (literal > 0) for literal in assumptions) and all(
            any(model[abs(literal)] == (literal > 0) for literal in clause) for clause in cnf
        ):
            models.append(model)
    return models


def _compare(cnf: CNF, variables: tuple[int, ...], assumptions: tuple[int, ...] = ()) -> None:
    before = deepcopy((cnf, variables, assumptions))
    models = _models(cnf, variables, assumptions)
    result = DPLLSolver().solve(cnf, variables, assumptions)
    assert (cnf, variables, assumptions) == before
    assert result.status == (SATStatus.SAT if models else SATStatus.UNSAT)
    if models:
        assert result.assignment in models
        assert set(result.assignment) == set(variables)
        assert all(type(value) is bool for value in result.assignment.values())
    else:
        assert result.assignment is None
    assert result.stats.runtime_seconds >= 0


def test_all_two_variable_formulas_and_assumption_combinations() -> None:
    clauses = [[value for value in (a, b) if value] for a in (0, 1, -1) for b in (0, 2, -2)]
    assumptions = [
        tuple(value for value in pair if value) for pair in product((0, 1, -1), (0, 2, -2))
    ]
    assumptions.append((1, -1))
    for count in range(len(clauses) + 1):
        for selected in combinations(clauses, count):
            for assumed in assumptions:
                _compare(list(selected), (1, 2), assumed)


def test_seeded_formulas_with_sparse_ids_duplicates_and_tautologies() -> None:
    random = Random(20261109)
    variables = (2, 7, 11, 19)
    literals = tuple(value for variable in variables for value in (variable, -variable))
    for _ in range(600):
        cnf = [
            [random.choice(literals) for _ in range(random.randrange(5))]
            for _ in range(random.randrange(10))
        ]
        assumptions = tuple(random.choice(literals) for _ in range(random.randrange(4)))
        _compare(cnf, variables, assumptions)


@pytest.mark.parametrize(
    ("cnf", "variables", "assumptions", "model", "stats"),
    [
        ([], (), (), {}, (0, 0, 0)),
        ([], (1, 4), (), {1: False, 4: False}, (0, 0, 0)),
        ([[1]], (1, 2), (), {1: True, 2: False}, (0, 1, 0)),
        ([[1, 1], [2, -2]], (1, 2), (), {1: True, 2: False}, (0, 1, 0)),
        ([[1], [2]], (1, 2), (1, 1), {1: True, 2: True}, (0, 1, 0)),
        ([], (1,), (1, -1), None, (0, 0, 0)),
        ([[]], (1,), (), None, (0, 0, 0)),
        ([[1, 2], [-1, 2]], (2, 1), (), {1: True, 2: True}, (1, 1, 0)),
        ([[-1, 2], [-1, -2], [1, 2]], (1, 2), (), {1: False, 2: True}, (1, 2, 1)),
        ([[1, 2], [1, -2], [-1, 2], [-1, -2]], (1, 2), (), None, (1, 2, 2)),
        ([[2, 3], [-2, 3]], (3, 1, 2), (), {1: True, 2: True, 3: True}, (2, 1, 0)),
    ],
)
def test_deterministic_models_and_exact_counter_definitions(
    cnf: CNF,
    variables: Sequence[int],
    assumptions: Sequence[int],
    model: dict[int, bool] | None,
    stats: tuple[int, int, int],
) -> None:
    result = DPLLSolver().solve(cnf, variables, assumptions)
    assert result.assignment == model
    assert (result.stats.decisions, result.stats.propagations, result.stats.backtracks) == stats


@pytest.mark.parametrize(
    ("cnf", "variables", "assumptions"),
    [
        (None, (), ()),
        (([1],), (1,), ()),
        ([1], (1,), ()),
        ([[0]], (1,), ()),
        ([[True]], (1,), ()),
        ([[1.0]], (1,), ()),
        ([[2]], (1,), ()),
        ([["1"]], (1,), ()),
        ([], (0,), ()),
        ([], (-1,), ()),
        ([], (True,), ()),
        ([], (1, 1), ()),
        ([], {1}, ()),
        ([], "", ()),
        ([], (1,), None),
        ([], (1,), (0,)),
        ([], (1,), (False,)),
        ([], (1,), (2,)),
        ([], (1,), "1"),
    ],
)
def test_invalid_formula_inputs_raise_contract_error(
    cnf: Any, variables: Any, assumptions: Any
) -> None:
    with pytest.raises(ContractError):
        DPLLSolver().solve(cnf, variables, assumptions)


@pytest.mark.parametrize(
    "timeout",
    [
        0,
        -1,
        True,
        False,
        "1",
        float("nan"),
        float("inf"),
        -float("inf"),
        pytest.param(10**10000, id="huge_integer"),
    ],
)
def test_invalid_timeout(timeout: Any) -> None:
    with pytest.raises(ContractError):
        DPLLSolver().solve([], (), timeout_seconds=timeout)


@pytest.mark.parametrize("cnf", [[], [[]], [[1, 2], [-1, 2]]])
def test_expired_deadline_never_returns_sat_or_unsat(
    monkeypatch: pytest.MonkeyPatch, cnf: CNF
) -> None:
    ticks = iter((0.0, 2.0, 3.0, 4.0))
    monkeypatch.setattr("solver._timing.perf_counter", lambda: next(ticks))
    with pytest.raises(SolverTimeout):
        DPLLSolver().solve(cnf, (1, 2), timeout_seconds=1.0)


def test_one_instance_resets_statistics_and_has_no_shared_models() -> None:
    solver = DPLLSolver()
    first = solver.solve([[1, 2], [-1, 2]], (1, 2))
    first.assignment[1] = False
    empty = solver.solve([], (1, 2))
    again = solver.solve([[1, 2], [-1, 2]], (1, 2))
    assert empty.assignment == {1: False, 2: False}
    assert empty.stats.decisions == empty.stats.propagations == empty.stats.backtracks == 0
    assert again.assignment == {1: True, 2: True}
    assert again.stats.decisions == again.stats.propagations == 1


def test_same_instance_is_safe_for_independent_worker_calls() -> None:
    solver = DPLLSolver()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda literal: solver.solve([[literal]], (1,)), [1, -1] * 16))
    assert [result.assignment[1] for result in results] == [True, False] * 16
    assert all(result.stats.propagations == 1 for result in results)
