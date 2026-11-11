"""CNF truth tables, public knowledge boundaries, and deterministic snapshots."""

from copy import deepcopy
from dataclasses import replace
from itertools import product
from math import comb

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


@pytest.mark.parametrize("kind", [ClueType.EVEN, ClueType.ODD])
@pytest.mark.parametrize(
    "region",
    [
        Region(RegionType.ROW, index=0),
        Region(RegionType.COLUMN, index=1),
        Region(RegionType.NEIGHBORS, cell="A1"),
        Region(RegionType.NEIGHBORS, cell="B2"),
        Region(RegionType.EXPLICIT, cells=("C3", "A1", "B2")),
        Region(RegionType.EXPLICIT, cells=("B2",)),
        Region(RegionType.EXPLICIT),
        Region(RegionType.COMMON_NEIGHBORS, first="A1", second="C1"),
    ],
)
def test_parity_matches_independent_evaluator_for_every_assignment(
    public_state: PublicState, kind: ClueType, region: Region
) -> None:
    state = _with_clue(public_state, Clue("parity", kind, region=region))
    before = deepcopy(state)
    result = CNFEncoder().encode(state)
    assert result.primary_variables == tuple(range(1, 10))
    assert result.auxiliary_variables == ()
    assert result.clause_count == len(result.cnf)
    assert result.active_clue_ids == ("parity",)
    for values in product((False, True), repeat=9):
        primary = dict(zip(result.primary_variables, values))
        assignment = {
            cell: Status.CRIMINAL if primary[var] else Status.INNOCENT
            for cell, var in result.variable_map.items()
        }
        assert _cnf_value(result.cnf, primary) == evaluate_clue(
            state.characters[0].clue, assignment, state
        )
    assert state == before


@pytest.mark.parametrize(
    ("kind", "region", "expected"),
    [
        (ClueType.EVEN, Region(RegionType.EXPLICIT), []),
        (ClueType.ODD, Region(RegionType.EXPLICIT), [[]]),
        (ClueType.EVEN, Region(RegionType.EXPLICIT, cells=("A1",)), [[-1]]),
        (ClueType.ODD, Region(RegionType.EXPLICIT, cells=("A1",)), [[1]]),
        (ClueType.EVEN, Region(RegionType.EXPLICIT, cells=("A1", "B1")), [[1, -2], [-1, 2]]),
        (ClueType.ODD, Region(RegionType.EXPLICIT, cells=("A1", "B1")), [[1, 2], [-1, -2]]),
    ],
)
def test_parity_clauses_and_known_status_units(
    public_state: PublicState, kind: ClueType, region: Region, expected: CNF
) -> None:
    state = _with_clue(public_state, Clue("parity", kind, region=region), Status.CRIMINAL)
    assert CNFEncoder().encode(state).cnf == expected + [[1]]


@pytest.mark.parametrize("kind", [ClueType.EVEN, ClueType.ODD])
@pytest.mark.parametrize("public_state", [4, 5], indirect=True)
def test_parity_on_larger_board_ignores_outside_cells(
    public_state: PublicState, kind: ClueType
) -> None:
    state = _with_clue(public_state, Clue("parity", kind, region=Region(RegionType.ROW, index=0)))
    result = CNFEncoder().encode(state)
    assert len(result.cnf) == 2 ** (state.size - 1)
    for outside in (False, True):
        for values in product((False, True), repeat=state.size):
            assignment = dict.fromkeys(result.primary_variables, outside)
            assignment.update(enumerate(values, 1))
            assert _cnf_value(result.cnf, assignment) == (sum(values) % 2 == (kind == ClueType.ODD))


@pytest.mark.parametrize("kind", [ClueType.EVEN, ClueType.ODD])
@pytest.mark.parametrize(
    "bad_region",
    [
        None,
        Region(RegionType.EXPLICIT, cells=("A1", "A1")),
        Region(RegionType.NEIGHBORS, cell="D1"),
        Region(RegionType.COMMON_NEIGHBORS, first="A1", second="A1"),
    ],
)
def test_invalid_parity_region_does_not_leave_encoder_state(
    public_state: PublicState, kind: ClueType, bad_region: Region
) -> None:
    encoder = CNFEncoder()
    state = _with_clue(public_state, Clue("bad", kind, region=bad_region))
    with pytest.raises(ContractError):
        encoder.encode(state)
    assert encoder.encode(public_state).cnf == []


@pytest.mark.parametrize("kind", [ClueType.EVEN, ClueType.ODD])
def test_parity_is_independent_and_cannot_accept_k(
    public_state: PublicState, kind: ClueType, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: object, **kwargs: object) -> bool:
        raise AssertionError("Encoder must not call evaluator")

    monkeypatch.setattr("logic.clue_evaluator.evaluate_clue", fail)
    state = _with_clue(public_state, Clue("parity", kind, region=Region(RegionType.ROW, index=0)))
    assert CNFEncoder().encode(state).clause_count == 4
    invalid = _with_clue(public_state, replace(state.characters[0].clue, k=0))
    with pytest.raises(ContractError):
        CNFEncoder().encode(invalid)


@pytest.mark.parametrize("kind", [ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST])
@pytest.mark.parametrize(
    ("region", "region_size"),
    [
        (Region(RegionType.ROW, index=0), 3),
        (Region(RegionType.COLUMN, index=1), 3),
        (Region(RegionType.NEIGHBORS, cell="A1"), 3),
        (Region(RegionType.NEIGHBORS, cell="B2"), 8),
        (Region(RegionType.EXPLICIT, cells=("C3", "A1", "B2")), 3),
        (Region(RegionType.EXPLICIT, cells=("B2",)), 1),
        (Region(RegionType.EXPLICIT), 0),
        (Region(RegionType.COMMON_NEIGHBORS, first="A1", second="C1"), 2),
    ],
)
def test_counting_matches_evaluator_for_every_k_and_primary_assignment(
    public_state: PublicState, kind: ClueType, region: Region, region_size: int
) -> None:
    encoder = CNFEncoder()
    for k in range(region_size + 1):
        clue = Clue("count", kind, region=region, k=k)
        state = _with_clue(public_state, clue)
        before = deepcopy(state)
        result = encoder.encode(state)
        at_most_count = comb(region_size, k + 1) if k < region_size else 0
        at_least_count = comb(region_size, region_size - k + 1) if k > 0 else 0
        expected_count = {
            ClueType.AT_MOST: at_most_count,
            ClueType.AT_LEAST: at_least_count,
            ClueType.EXACTLY: at_most_count + at_least_count,
        }[kind]
        assert result.clause_count == len(result.cnf) == expected_count
        assert result.primary_variables == tuple(range(1, 10))
        assert result.auxiliary_variables == ()
        assert result.active_clue_ids == ("count",)
        assert all(0 < abs(literal) <= 9 for clause in result.cnf for literal in clause)
        if expected_count == 0:
            assert result.cnf == []
        for values in product((False, True), repeat=9):
            primary_assignment = dict(zip(result.primary_variables, values))
            assignment = {
                cell_id: Status.CRIMINAL if primary_assignment[variable] else Status.INNOCENT
                for cell_id, variable in result.variable_map.items()
            }
            assert _cnf_value(result.cnf, primary_assignment) is evaluate_clue(
                clue, assignment, state
            )
        assert state == before


@pytest.mark.parametrize(
    ("kind", "k", "expected"),
    [
        (ClueType.AT_MOST, 1, [[-1, -2], [-1, -3], [-2, -3]]),
        (ClueType.AT_LEAST, 2, [[1, 2], [1, 3], [2, 3]]),
        (ClueType.EXACTLY, 1, [[-1, -2], [-1, -3], [-2, -3], [1, 2, 3]]),
        (ClueType.EXACTLY, 2, [[-1, -2, -3], [1, 2], [1, 3], [2, 3]]),
    ],
)
def test_counting_direct_combinatorial_clauses(
    public_state: PublicState, kind: ClueType, k: int, expected: CNF
) -> None:
    clue = Clue("count", kind, region=Region(RegionType.ROW, index=0), k=k)
    assert CNFEncoder().encode(_with_clue(public_state, clue)).cnf == expected


@pytest.mark.parametrize("public_state", [4, 5], indirect=True)
@pytest.mark.parametrize("kind", [ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST])
def test_counting_on_larger_boards_ignores_cells_outside_the_region(
    public_state: PublicState, kind: ClueType
) -> None:
    for k in range(public_state.size + 1):
        clue = Clue("row-count", kind, region=Region(RegionType.ROW, index=0), k=k)
        state = _with_clue(public_state, clue)
        result = CNFEncoder().encode(state)
        for outside in (False, True):
            for values in product((False, True), repeat=public_state.size):
                primary_assignment = dict.fromkeys(result.primary_variables, outside)
                primary_assignment.update(enumerate(values, start=1))
                assignment = {
                    cell_id: Status.CRIMINAL if primary_assignment[variable] else Status.INNOCENT
                    for cell_id, variable in result.variable_map.items()
                }
                count = sum(values)
                expected = {
                    ClueType.EXACTLY: count == k,
                    ClueType.AT_LEAST: count >= k,
                    ClueType.AT_MOST: count <= k,
                }[kind]
                assert _cnf_value(result.cnf, primary_assignment) is expected
                assert evaluate_clue(clue, assignment, state) is expected


@pytest.mark.parametrize("kind", [ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST])
@pytest.mark.parametrize("k", [None, True, False, 1.0, "1", -1, 4])
def test_counting_rejects_invalid_k_without_mutating_input(
    public_state: PublicState, kind: ClueType, k: int
) -> None:
    state = _with_clue(
        public_state, Clue("count", kind, region=Region(RegionType.ROW, index=0), k=k)
    )
    before = deepcopy(state)
    with pytest.raises(ContractError):
        CNFEncoder().encode(state)
    assert state == before


@pytest.mark.parametrize("kind", [ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST])
@pytest.mark.parametrize(
    "region",
    [
        None,
        "ROW",
        Region(RegionType.ROW, index=True),
        Region(RegionType.COLUMN, index=3),
        Region(RegionType.NEIGHBORS, cell="D1"),
        Region(RegionType.EXPLICIT, cells=("A1", "A1")),
        Region(RegionType.EXPLICIT, cells=("D1",)),
        Region(RegionType.COMMON_NEIGHBORS, first="A1", second="A1"),
    ],
)
def test_counting_rejects_invalid_regions(
    public_state: PublicState, kind: ClueType, region: Region
) -> None:
    state = _with_clue(public_state, Clue("count", kind, region=region, k=0))
    before = deepcopy(state)
    with pytest.raises(ContractError):
        CNFEncoder().encode(state)
    assert state == before


@pytest.mark.parametrize("public_state", [3, 4], indirect=True)
@pytest.mark.parametrize("kind", [ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST])
def test_empty_counting_region_is_true_only_with_k_zero(
    public_state: PublicState, kind: ClueType
) -> None:
    region = (
        Region(RegionType.EXPLICIT)
        if public_state.size == 3
        else Region(RegionType.COMMON_NEIGHBORS, first="A1", second="D4")
    )
    state = _with_clue(public_state, Clue("empty-count", kind, region=region, k=0))
    result = CNFEncoder().encode(state)
    assert result.cnf == []
    assert result.clause_count == 0
    assert result.active_clue_ids == ("empty-count",)
    known_state = _with_clue(public_state, state.characters[0].clue, Status.CRIMINAL)
    assert CNFEncoder().encode(known_state).cnf == [[1]]
    for k in (-1, 1):
        with pytest.raises(ContractError):
            CNFEncoder().encode(
                _with_clue(public_state, Clue("bad-count", kind, region=region, k=k))
            )


def test_six_core_clues_and_known_statuses_match_the_evaluator(public_state: PublicState) -> None:
    clues = (
        Clue("f-fact", ClueType.FACT, person="C3", status=Status.CRIMINAL),
        Clue("a-same", ClueType.SAME, first="B1", second="C1"),
        Clue("b-different", ClueType.DIFFERENT, first="A1", second="B1"),
        Clue("c-exactly", ClueType.EXACTLY, region=Region(RegionType.ROW, index=0), k=2),
        Clue("d-at-least", ClueType.AT_LEAST, region=Region(RegionType.COLUMN, index=0), k=1),
        Clue(
            "e-at-most",
            ClueType.AT_MOST,
            region=Region(RegionType.EXPLICIT, cells=("B1", "B2", "C2")),
            k=2,
        ),
    )
    statuses = (
        Status.INNOCENT,
        Status.CRIMINAL,
        Status.CRIMINAL,
        Status.INNOCENT,
        Status.CRIMINAL,
        Status.INNOCENT,
    )
    cells = tuple(
        replace(cell, clue=clues[index], status=statuses[index]) if index < len(clues) else cell
        for index, cell in enumerate(public_state.characters)
    )
    state = replace(public_state, characters=cells)
    before = deepcopy(state)
    encoder = CNFEncoder()
    result = encoder.encode(state)
    assert result.active_clue_ids == tuple(sorted(clue.id for clue in clues))
    assert result.cnf[-6:] == [[-1], [2], [3], [-4], [5], [-6]]
    assert result.clause_count == len(result.cnf)
    assert result.auxiliary_variables == ()
    assert encoder.encode(replace(state, characters=tuple(reversed(cells)))) == result
    satisfying_count = 0
    for values in product((False, True), repeat=9):
        primary_assignment = dict(zip(result.primary_variables, values))
        assignment = {
            cell_id: Status.CRIMINAL if primary_assignment[variable] else Status.INNOCENT
            for cell_id, variable in result.variable_map.items()
        }
        expected = all(evaluate_clue(clue, assignment, state) for clue in clues) and all(
            cell.status is None or cell.status == assignment[cell.id] for cell in cells
        )
        assert _cnf_value(result.cnf, primary_assignment) is expected
        satisfying_count += expected
    assert satisfying_count == 2
    assert state == before
