"""Deterministic DPLL with unit propagation and independent per-call statistics."""

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter

from game.models import CNF, Assignment, ContractError, Literal, SATResult, SATStatus, SolverStats
from solver._timing import _Deadline


def _validate_formula(
    cnf: CNF, variables: Sequence[int], assumptions: Sequence[Literal], deadline: _Deadline
) -> None:
    """Reject malformed input before performing any logical reasoning."""
    for name, values in (("variables", variables), ("assumptions", assumptions)):
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
            raise ContractError(f"{name} must be a sequence of integers")
    if any(type(variable) is not int or variable <= 0 for variable in variables):
        raise ContractError("Variable IDs must be positive integers")
    declared = set(variables)
    if len(declared) != len(variables):
        raise ContractError("Variable IDs must be distinct")
    if not isinstance(cnf, list) or any(not isinstance(clause, list) for clause in cnf):
        raise ContractError("CNF must be a list of clause lists")

    def validate_literal(literal: Literal) -> None:
        if type(literal) is not int or literal == 0 or abs(literal) not in declared:
            raise ContractError("Literals must be nonzero integers using declared variables")

    for clause in cnf:
        for literal in clause:
            validate_literal(literal)
        deadline.check()
    for literal in assumptions:
        validate_literal(literal)
    deadline.check()


@dataclass
class _Counters:
    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0


_Clauses = tuple[tuple[int, ...], ...]


def _normalize(cnf: CNF, deadline: _Deadline) -> _Clauses:
    """Copy clauses, collapse repeated literals, and remove tautologies."""
    clauses = []
    for clause in cnf:
        deadline.check()
        literals = dict.fromkeys(clause)
        if not any(-literal in literals for literal in literals):
            clauses.append(tuple(literals))
    return tuple(clauses)


def _reduce(clauses: _Clauses, literal: int, deadline: _Deadline) -> _Clauses:
    """Drop satisfied clauses and the opposite literal without mutating input."""
    reduced = []
    for clause in clauses:
        deadline.check()
        if literal not in clause:
            reduced.append(tuple(value for value in clause if value != -literal))
    return tuple(reduced)


def _search(
    clauses: _Clauses,
    assignment: Assignment,
    variables: tuple[int, ...],
    counters: _Counters,
    deadline: _Deadline,
) -> Assignment | None:
    """Propagate to a fixed point, then recursively try True before False."""
    while True:
        deadline.check()
        if any(not clause for clause in clauses):
            return None
        if not clauses:
            return assignment
        unit = next((clause[0] for clause in clauses if len(clause) == 1), None)
        if unit is None:
            break
        assignment[abs(unit)] = unit > 0
        counters.propagations += 1
        clauses = _reduce(clauses, unit, deadline)

    variable = next(variable for variable in variables if variable not in assignment)
    counters.decisions += 1
    for literal in (variable, -variable):
        child = assignment.copy()
        child[variable] = literal > 0
        result = _search(_reduce(clauses, literal, deadline), child, variables, counters, deadline)
        if result is not None:
            return result
        counters.backtracks += 1
    return None


class DPLLSolver:
    """Solve CNF using only local state; instances can be reused across calls."""

    def solve(
        self,
        cnf: CNF,
        variables: Sequence[int],
        assumptions: Sequence[Literal] = (),
        *,
        timeout_seconds: float | None = None,
    ) -> SATResult:
        """Return a complete SAT model, UNSAT, or raise for invalid input/timeout."""
        started = perf_counter()
        deadline = _Deadline(timeout_seconds)
        _validate_formula(cnf, variables, assumptions, deadline)
        ordered = tuple(sorted(variables))
        clauses = _normalize(cnf, deadline)
        counters = _Counters()
        assignment: Assignment = {}
        contradictory = False
        for literal in assumptions:
            deadline.check()
            variable, value = abs(literal), literal > 0
            if variable in assignment:
                if assignment[variable] != value:
                    contradictory = True
                    break
                continue
            assignment[variable] = value
            clauses = _reduce(clauses, literal, deadline)

        model = None if contradictory else _search(clauses, assignment, ordered, counters, deadline)
        if model is not None:
            model = {variable: model.get(variable, False) for variable in ordered}
        deadline.check()
        stats = SolverStats(
            counters.decisions,
            counters.propagations,
            counters.backtracks,
            perf_counter() - started,
        )
        return SATResult(SATStatus.UNSAT if model is None else SATStatus.SAT, model, stats)
