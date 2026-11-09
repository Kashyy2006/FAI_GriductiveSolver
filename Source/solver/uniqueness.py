"""TV3: complete-clue uniqueness validation, separate from gameplay."""

from copy import deepcopy

from game.contracts import Encoder, SATSolver
from game.models import (
    Character,
    Clue,
    ContractError,
    EncodingResult,
    PublicCharacter,
    PublicState,
    Puzzle,
    SATQuery,
    SATResult,
    SATStatus,
    StateToken,
    Status,
    UniquenessOutcome,
    UniquenessResult,
)
from solver._timing import _Deadline
from solver.dpll import _validate_formula


def _validation_state(puzzle: Puzzle) -> PublicState:
    """Copy all clues into a validation-only snapshot without reading labels."""
    if (
        not isinstance(puzzle, Puzzle)
        or type(puzzle.size) is not int
        or puzzle.size not in (3, 4, 5)
    ):
        raise ContractError("Expected a Puzzle of size 3, 4, or 5")
    if not isinstance(puzzle.characters, tuple) or len(puzzle.characters) != puzzle.size**2:
        raise ContractError("Puzzle must contain every board cell exactly once")
    for cell in puzzle.characters:
        if (
            not isinstance(cell, Character)
            or type(cell.row) is not int
            or type(cell.col) is not int
            or not 0 <= cell.row < puzzle.size
            or not 0 <= cell.col < puzzle.size
            or cell.id != f"{chr(65 + cell.col)}{cell.row + 1}"
            or not isinstance(cell.clue, Clue)
            or not isinstance(cell.clue.id, str)
            or not cell.clue.id
        ):
            raise ContractError("Invalid puzzle coordinates or clue")
    if len({cell.id for cell in puzzle.characters}) != len(puzzle.characters):
        raise ContractError("Duplicate puzzle cells")
    if len({cell.clue.id for cell in puzzle.characters}) != len(puzzle.characters):
        raise ContractError("Duplicate clue IDs")
    return PublicState(
        puzzle.puzzle_id,
        puzzle.size,
        StateToken("uniqueness-validation-only", 0),
        tuple(
            PublicCharacter(c.id, c.name, c.profession, c.row, c.col, clue=deepcopy(c.clue))
            for c in sorted(puzzle.characters, key=lambda c: (c.row, c.col))
        ),
    )


def _validate_encoding(encoding: EncodingResult, state: PublicState, deadline: _Deadline) -> None:
    expected = {cell.id: cell.row * state.size + cell.col + 1 for cell in state.characters}
    if (
        not isinstance(encoding, EncodingResult)
        or not isinstance(encoding.variable_map, dict)
        or encoding.variable_map != expected
        or any(type(value) is not int for value in encoding.variable_map.values())
    ):
        raise ContractError("Encoder must use the canonical primary variable map")
    if (
        not isinstance(encoding.primary_variables, tuple)
        or encoding.primary_variables != tuple(expected.values())
        or any(type(value) is not int for value in encoding.primary_variables)
    ):
        raise ContractError("Encoder must declare every primary variable in row-major order")
    auxiliary = encoding.auxiliary_variables
    if (
        not isinstance(auxiliary, tuple)
        or any(type(v) is not int or v <= state.size**2 for v in auxiliary)
        or len(set(auxiliary)) != len(auxiliary)
    ):
        raise ContractError("Auxiliary variables must be distinct and above primary IDs")
    _validate_formula(encoding.cnf, encoding.primary_variables + auxiliary, (), deadline)
    if (
        type(encoding.clause_count) is not int
        or encoding.clause_count != len(encoding.cnf)
        or encoding.active_clue_ids
        != tuple(sorted(cell.clue.id for cell in state.characters if cell.clue is not None))
    ):
        raise ContractError("Encoder must report all validation clues and actual clause counts")


def _validate_result(result: SATResult, variables: tuple[int, ...], cnf: list[list[int]]) -> None:
    if not isinstance(result, SATResult) or not isinstance(result.status, SATStatus):
        raise ContractError("Solver must return SATResult with a SATStatus")
    if result.status == SATStatus.UNSAT:
        if result.assignment is not None:
            raise ContractError("UNSAT must not contain an assignment")
        return
    model = result.assignment
    if (
        not isinstance(model, dict)
        or set(model) != set(variables)
        or any(type(variable) is not int for variable in model)
        or any(type(value) is not bool for value in model.values())
        or not all(any(model[abs(lit)] == (lit > 0) for lit in clause) for clause in cnf)
    ):
        raise ContractError("SAT must contain a complete satisfying assignment")


def check_uniqueness(
    puzzle: Puzzle,
    encoder: Encoder,
    solver: SATSolver,
    *,
    timeout_seconds: float | None = None,
) -> UniquenessResult:
    """Use at most two SAT calls, blocking only the first primary assignment."""
    deadline = _Deadline(timeout_seconds)
    state = _validation_state(puzzle)
    deadline.check()
    encoding = encoder.encode(state)
    deadline.check()
    _validate_encoding(encoding, state, deadline)
    variables = encoding.primary_variables + encoding.auxiliary_variables
    cnf = deepcopy(encoding.cnf)
    queries: list[SATQuery] = []

    def ask(purpose: str) -> SATResult:
        result = solver.solve(deepcopy(cnf), variables, timeout_seconds=deadline.remaining())
        deadline.check()
        _validate_result(result, variables, cnf)
        deadline.check()
        queries.append(SATQuery(purpose, (), result.status, result.stats))
        return result

    first = ask("UNIQUENESS_FIRST")
    if first.status == SATStatus.UNSAT:
        return UniquenessResult(UniquenessOutcome.NO_SOLUTION, (), tuple(queries))
    assert first.assignment is not None

    def primary_model(result: SATResult) -> dict[str, Status]:
        assert result.assignment is not None
        return {
            cell_id: Status.CRIMINAL if result.assignment[var] else Status.INNOCENT
            for cell_id, var in encoding.variable_map.items()
        }

    models = [primary_model(first)]
    cnf.append(
        [
            -variable if first.assignment[variable] else variable
            for variable in encoding.primary_variables
        ]
    )
    second = ask("UNIQUENESS_SECOND")
    if second.status == SATStatus.UNSAT:
        outcome = UniquenessOutcome.UNIQUE
    else:
        outcome = UniquenessOutcome.MULTIPLE
        models.append(primary_model(second))
    deadline.check()
    return UniquenessResult(outcome, tuple(models), tuple(queries))
