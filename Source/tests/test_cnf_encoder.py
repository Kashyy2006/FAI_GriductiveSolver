"""CNF truth tables, public knowledge boundaries, and deterministic snapshots."""

from copy import deepcopy
from dataclasses import replace
from itertools import product

import pytest

from game.models import CNF, Clue, ClueType, ContractError, PublicState, Region, RegionType, Status
from logic.clue_evaluator import evaluate_clue
from logic.cnf_encoder import CNFEncoder


def _with_clue(state: PublicState, clue: Clue, owner_status: Status | None = None) -> PublicState:
    return replace(
        state,
        characters=(replace(state.characters[0], status=owner_status, clue=clue),)
        + state.characters[1:],
    )


def _cnf_value(cnf: CNF, assignment: dict[int, bool]) -> bool:
    return all(
        any(assignment[abs(literal)] == (literal > 0) for literal in clause) for clause in cnf
    )


@pytest.mark.parametrize("public_state", [3, 4, 5], indirect=True)
def test_empty_public_knowledge_still_maps_every_primary_variable(
    public_state: PublicState,
) -> None:
    result = CNFEncoder().encode(public_state)
    assert result.variable_map == {
        cell.id: cell.row * public_state.size + cell.col + 1 for cell in public_state.characters
    }
    assert result.primary_variables == tuple(range(1, public_state.size**2 + 1))
    assert result.auxiliary_variables == ()
    assert result.cnf == []
    assert result.clause_count == 0
    assert result.active_clue_ids == ()


@pytest.mark.parametrize("public_state", [3, 4, 5], indirect=True)
def test_known_status_units_use_correct_sign_and_row_major_order(public_state: PublicState) -> None:
    cells = list(public_state.characters)
    cells[0] = replace(cells[0], status=Status.CRIMINAL)
    cells[1] = replace(cells[1], status=Status.INNOCENT)
    cells[-1] = replace(cells[-1], status=Status.CRIMINAL)
    state = replace(public_state, characters=tuple(reversed(cells)))
    result = CNFEncoder().encode(state)
    assert result.cnf == [[1], [-2], [public_state.size**2]]
    assert result.clause_count == 3
    assert result.active_clue_ids == ()


@pytest.mark.parametrize("owner_status", list(Status))
@pytest.mark.parametrize(
    ("clue", "clauses"),
    [
        (Clue("fact", ClueType.FACT, person="B1", status=Status.CRIMINAL), [[2]]),
        (Clue("fact", ClueType.FACT, person="B1", status=Status.INNOCENT), [[-2]]),
        (Clue("same", ClueType.SAME, first="B1", second="C1"), [[-2, 3], [2, -3]]),
        (Clue("different", ClueType.DIFFERENT, first="B1", second="C1"), [[2, 3], [-2, -3]]),
        (Clue("self-same", ClueType.SAME, first="B1", second="B1"), [[-2, 2], [2, -2]]),
        (Clue("self-different", ClueType.DIFFERENT, first="B1", second="B1"), [[2, 2], [-2, -2]]),
    ],
)
def test_basic_clues_match_evaluator_for_all_primary_assignments(
    public_state: PublicState, clue: Clue, clauses: CNF, owner_status: Status
) -> None:
    state = _with_clue(public_state, clue, owner_status)
    before = deepcopy(state)
    result = CNFEncoder().encode(state)
    unit = 1 if owner_status == Status.CRIMINAL else -1
    assert result.cnf == clauses + [[unit]]
    assert result.clause_count == len(result.cnf)
    assert result.active_clue_ids == (clue.id,)
    assert result.auxiliary_variables == ()
    assert all(0 < abs(literal) <= 9 for clause in result.cnf for literal in clause)
    for values in product((False, True), repeat=9):
        primary_assignment = dict(zip(result.primary_variables, values))
        assignment = {
            cell_id: Status.CRIMINAL if primary_assignment[variable] else Status.INNOCENT
            for cell_id, variable in result.variable_map.items()
        }
        expected = evaluate_clue(clue, assignment, state) and assignment["A1"] == owner_status
        assert _cnf_value(result.cnf, primary_assignment) is expected
    assert state == before


def test_clues_are_sorted_by_id_and_all_public_constraints_are_conjoined(
    public_state: PublicState,
) -> None:
    cells = list(public_state.characters)
    cells[0] = replace(
        cells[0],
        status=Status.CRIMINAL,
        clue=Clue("z-fact", ClueType.FACT, person="C3", status=Status.INNOCENT),
    )
    cells[1] = replace(
        cells[1],
        status=Status.INNOCENT,
        clue=Clue("a-same", ClueType.SAME, first="B1", second="C1"),
    )
    cells[2] = replace(
        cells[2],
        status=Status.INNOCENT,
        clue=Clue("m-different", ClueType.DIFFERENT, first="B2", second="C2"),
    )
    state = replace(public_state, characters=tuple(cells))
    encoder = CNFEncoder()
    result = encoder.encode(state)
    assert result.cnf == [[-2, 3], [2, -3], [5, 6], [-5, -6], [-9], [1], [-2], [-3]]
    assert result.active_clue_ids == ("a-same", "m-different", "z-fact")
    reversed_state = replace(
        state,
        characters=tuple(
            replace(cell, name="Renamed", profession="Other job") for cell in reversed(cells)
        ),
    )
    reordered = encoder.encode(reversed_state)
    assert reordered == result
    assert tuple(reordered.variable_map.items()) == tuple(result.variable_map.items())
    satisfying_count = 0
    for values in product((False, True), repeat=9):
        primary_assignment = dict(zip(result.primary_variables, values))
        assignment = {
            cell_id: Status.CRIMINAL if primary_assignment[variable] else Status.INNOCENT
            for cell_id, variable in result.variable_map.items()
        }
        expected = all(
            (cell.status is None or assignment[cell.id] == cell.status)
            and (cell.clue is None or evaluate_clue(cell.clue, assignment, state))
            for cell in cells
        )
        assert _cnf_value(result.cnf, primary_assignment) is expected
        satisfying_count += expected
    assert satisfying_count == 16


def test_contradictory_public_constraints_are_encoded_without_guessing(
    public_state: PublicState,
) -> None:
    state = _with_clue(
        public_state,
        Clue("contradiction", ClueType.FACT, person="A1", status=Status.INNOCENT),
        Status.CRIMINAL,
    )
    result = CNFEncoder().encode(state)
    assert result.cnf == [[-1], [1]]
    for value in (False, True):
        assignment = dict.fromkeys(result.primary_variables, value)
        assert not _cnf_value(result.cnf, assignment)


def test_encoder_does_not_call_the_semantic_evaluator(
    public_state: PublicState, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject_evaluation(*args: object, **kwargs: object) -> bool:
        raise AssertionError("CNF construction must not depend on semantic evaluation")

    monkeypatch.setattr("logic.clue_evaluator.evaluate_clue", reject_evaluation)
    state = _with_clue(public_state, Clue("independent", ClueType.SAME, first="B1", second="C1"))
    assert CNFEncoder().encode(state).cnf == [[-2, 3], [2, -3]]


def test_validation_snapshot_clue_without_status_does_not_add_a_verdict(
    public_state: PublicState,
) -> None:
    state = _with_clue(
        public_state, Clue("validation-fact", ClueType.FACT, person="B1", status=Status.CRIMINAL)
    )
    result = CNFEncoder().encode(state)
    assert result.cnf == [[2]]
    assert result.clause_count == 1
    assert result.active_clue_ids == ("validation-fact",)


def test_encoding_rebuilds_each_snapshot_and_owns_its_mutable_results(
    public_state: PublicState,
) -> None:
    encoder = CNFEncoder()
    state = _with_clue(
        public_state,
        Clue("first", ClueType.FACT, person="B1", status=Status.CRIMINAL),
        Status.INNOCENT,
    )
    result = encoder.encode(state)
    expected = deepcopy(result)
    result.cnf[0][0] = 0
    result.cnf.append([])
    result.variable_map["A1"] = 999
    assert encoder.encode(state) == expected
    next_state = replace(
        state,
        token=replace(state.token, version=1),
        characters=(
            state.characters[0],
            replace(
                state.characters[1],
                status=Status.CRIMINAL,
                clue=Clue("second", ClueType.SAME, first="B1", second="C1"),
            ),
        )
        + state.characters[2:],
    )
    next_result = encoder.encode(next_state)
    assert next_result.cnf == [[2], [-2, 3], [2, -3], [-1], [2]]
    assert next_result.active_clue_ids == ("first", "second")
    fresh_session = replace(public_state, token=replace(public_state.token, session_id="new"))
    assert encoder.encode(fresh_session).cnf == []
    assert encoder.encode(state) == expected


@pytest.mark.parametrize("status", ["CRIMINAL", False, 1])
def test_invalid_public_status_is_rejected(public_state: PublicState, status: Status) -> None:
    state = replace(
        public_state,
        characters=(replace(public_state.characters[0], status=status),)
        + public_state.characters[1:],
    )
    with pytest.raises(ContractError):
        CNFEncoder().encode(state)


@pytest.mark.parametrize(
    "clue",
    [
        {},
        Clue("", ClueType.FACT, person="B1", status=Status.CRIMINAL),
        Clue("fact", "FACT", person="B1", status=Status.CRIMINAL),
        Clue("fact", ClueType.FACT, person="B1", status="CRIMINAL"),
        Clue("fact", ClueType.FACT, person="B1"),
        Clue("fact", ClueType.FACT, person="D1", status=Status.CRIMINAL),
        Clue("fact", ClueType.FACT, person=[], status=Status.CRIMINAL),
        Clue("fact", ClueType.FACT, person="B1", status=Status.CRIMINAL, k=0),
        Clue("same", ClueType.SAME, first="B1"),
        Clue("same", ClueType.SAME, first="B1", second="D1"),
        Clue("different", ClueType.DIFFERENT, first=[], second="C1"),
        Clue("same", ClueType.SAME, first="B1", second="C1", status=Status.CRIMINAL),
    ],
)
def test_invalid_clues_raise_contract_error_without_mutation(
    public_state: PublicState, clue: Clue
) -> None:
    state = _with_clue(public_state, clue)
    before = deepcopy(state)
    with pytest.raises(ContractError):
        CNFEncoder().encode(state)
    assert state == before


def test_duplicate_active_clue_ids_are_rejected(public_state: PublicState) -> None:
    clue = Clue("duplicate", ClueType.FACT, person="B1", status=Status.CRIMINAL)
    state = _with_clue(public_state, clue)
    state = replace(
        state,
        characters=(state.characters[0], replace(state.characters[1], clue=clue))
        + state.characters[2:],
    )
    with pytest.raises(ContractError):
        CNFEncoder().encode(state)


def test_invalid_geometry_is_rejected(public_state: PublicState) -> None:
    for state in (None, replace(public_state, size=True), replace(public_state, characters=())):
        with pytest.raises(ContractError):
            CNFEncoder().encode(state)


@pytest.mark.parametrize(
    "kind", [ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST, ClueType.EVEN, ClueType.ODD]
)
def test_unimplemented_clues_raise_instead_of_returning_an_incomplete_kb(
    public_state: PublicState, kind: ClueType
) -> None:
    k = None if kind in (ClueType.EVEN, ClueType.ODD) else 0
    clue = Clue("z-unimplemented", kind, region=Region(RegionType.EXPLICIT), k=k)
    state = _with_clue(public_state, clue)
    state = replace(
        state,
        characters=(
            state.characters[0],
            replace(
                state.characters[1],
                clue=Clue("a-fact", ClueType.FACT, person="B1", status=Status.CRIMINAL),
            ),
        )
        + state.characters[2:],
    )
    encoder = CNFEncoder()
    with pytest.raises(NotImplementedError):
        encoder.encode(state)
    assert encoder.encode(public_state).cnf == []
