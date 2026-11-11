"""Independent clue truth tables and strict runtime input validation."""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
from itertools import product
from types import MappingProxyType

import pytest

from game.models import Clue, ClueType, ContractError, PublicState, Region, RegionType, Status
from logic.clue_evaluator import evaluate_clue


@pytest.fixture
def assignment(public_state: PublicState) -> dict[str, Status]:
    return {cell.id: Status.INNOCENT for cell in public_state.characters}


@pytest.mark.parametrize("actual", list(Status))
@pytest.mark.parametrize("claimed", list(Status))
def test_fact_truth_table(
    public_state: PublicState, assignment: dict[str, Status], actual: Status, claimed: Status
) -> None:
    assignment["A1"] = actual
    clue = Clue("fact", ClueType.FACT, person="A1", status=claimed)
    assert evaluate_clue(clue, assignment, public_state) is (actual == claimed)


@pytest.mark.parametrize(
    ("first", "second", "same", "different"),
    [
        (Status.INNOCENT, Status.INNOCENT, True, False),
        (Status.INNOCENT, Status.CRIMINAL, False, True),
        (Status.CRIMINAL, Status.INNOCENT, False, True),
        (Status.CRIMINAL, Status.CRIMINAL, True, False),
    ],
)
def test_binary_truth_tables(
    public_state: PublicState,
    assignment: dict[str, Status],
    first: Status,
    second: Status,
    same: bool,
    different: bool,
) -> None:
    assignment.update(A1=first, B1=second)
    assert (
        evaluate_clue(
            Clue("same", ClueType.SAME, first="A1", second="B1"), assignment, public_state
        )
        is same
    )
    assert (
        evaluate_clue(
            Clue("different", ClueType.DIFFERENT, first="A1", second="B1"), assignment, public_state
        )
        is different
    )


@pytest.mark.parametrize("status", list(Status))
def test_binary_clues_allow_identical_endpoints(
    public_state: PublicState, assignment: dict[str, Status], status: Status
) -> None:
    assignment["A1"] = status
    assert evaluate_clue(
        Clue("self-same", ClueType.SAME, first="A1", second="A1"), assignment, public_state
    )
    assert not evaluate_clue(
        Clue("self-different", ClueType.DIFFERENT, first="A1", second="A1"),
        assignment,
        public_state,
    )


@pytest.mark.parametrize(
    ("region", "cells"),
    [
        (Region(RegionType.ROW, index=0), ("A1", "B1", "C1")),
        (Region(RegionType.COLUMN, index=1), ("B1", "B2", "B3")),
        (Region(RegionType.NEIGHBORS, cell="A1"), ("B1", "A2", "B2")),
        (Region(RegionType.NEIGHBORS, cell="B2"), ("A1", "B1", "C1", "A2", "C2", "A3", "B3", "C3")),
        (Region(RegionType.EXPLICIT, cells=("C3", "A1")), ("A1", "C3")),
        (Region(RegionType.EXPLICIT), ()),
        (Region(RegionType.COMMON_NEIGHBORS, first="A1", second="C1"), ("B1", "B2")),
    ],
)
def test_counting_and_parity_match_all_region_assignments(
    public_state: PublicState, region: Region, cells: tuple[str, ...]
) -> None:
    for values in product((False, True), repeat=len(cells)):
        assignment = {cell.id: Status.CRIMINAL for cell in public_state.characters}
        assignment.update(
            (cell, Status.CRIMINAL if criminal else Status.INNOCENT)
            for cell, criminal in zip(cells, values)
        )
        count = sum(values)
        before = deepcopy((assignment, public_state, region))
        for k in range(len(cells) + 1):
            for kind, expected in (
                (ClueType.EXACTLY, count == k),
                (ClueType.AT_LEAST, count >= k),
                (ClueType.AT_MOST, count <= k),
            ):
                clue = Clue("count", kind, region=region, k=k)
                assert evaluate_clue(clue, assignment, public_state) is expected
        for kind, expected in ((ClueType.EVEN, count % 2 == 0), (ClueType.ODD, count % 2 == 1)):
            assert evaluate_clue(Clue("parity", kind, region=region), assignment, public_state) is (
                expected
            )
        assert (assignment, public_state, region) == before


@pytest.mark.parametrize("public_state", [4, 5], indirect=True)
def test_empty_common_neighbors_semantics(public_state: PublicState) -> None:
    region = Region(RegionType.COMMON_NEIGHBORS, first="A1", second="D4")
    assignment = {cell.id: Status.CRIMINAL for cell in public_state.characters}
    for kind in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        assert evaluate_clue(
            Clue("empty-count", kind, region=region, k=0), assignment, public_state
        )
        with pytest.raises(ContractError):
            evaluate_clue(Clue("bad-count", kind, region=region, k=1), assignment, public_state)
    assert evaluate_clue(Clue("even", ClueType.EVEN, region=region), assignment, public_state)
    assert not evaluate_clue(Clue("odd", ClueType.ODD, region=region), assignment, public_state)


def test_evaluator_uses_assignment_instead_of_public_status_or_clue(
    public_state: PublicState, assignment: dict[str, Status]
) -> None:
    clue = Clue("fact", ClueType.FACT, person="A1", status=Status.INNOCENT)
    state = replace(
        public_state,
        characters=tuple(
            replace(
                cell, name="Other name", profession="Other job", status=Status.CRIMINAL, clue=clue
            )
            for cell in public_state.characters
        ),
    )
    readonly_assignment: Mapping[str, Status] = MappingProxyType(assignment)
    before = deepcopy((state, clue, assignment))
    assert evaluate_clue(clue, readonly_assignment, state)
    assert (state, clue, assignment) == before


@pytest.mark.parametrize("mode", ["missing", "extra", "variable-id", "string", "bool", "none"])
def test_invalid_assignments_are_rejected(
    public_state: PublicState, assignment: dict[str, Status], mode: str
) -> None:
    if mode == "missing":
        del assignment["A1"]
    elif mode == "extra":
        assignment["D1"] = Status.INNOCENT
    elif mode == "variable-id":
        assignment[1] = assignment.pop("A1")
    else:
        assignment["A1"] = {"string": "INNOCENT", "bool": False, "none": None}[mode]
    clue = Clue("fact", ClueType.FACT, person="A1", status=Status.INNOCENT)
    before = deepcopy(assignment)
    with pytest.raises(ContractError):
        evaluate_clue(clue, assignment, public_state)
    assert assignment == before


@pytest.mark.parametrize("assignment", [None, [], "INNOCENT"])
def test_assignment_must_be_a_mapping(public_state: PublicState, assignment: Mapping) -> None:
    with pytest.raises(ContractError):
        evaluate_clue(
            Clue("fact", ClueType.FACT, person="A1", status=Status.INNOCENT),
            assignment,
            public_state,
        )


@pytest.mark.parametrize(
    "clue",
    [
        None,
        {},
        Clue("fact", "FACT", person="A1", status=Status.INNOCENT),
        Clue("unknown", "UNSUPPORTED"),
        Clue("", ClueType.FACT, person="A1", status=Status.INNOCENT),
        Clue(None, ClueType.FACT, person="A1", status=Status.INNOCENT),
        Clue("fact", ClueType.FACT, person="A1", status="INNOCENT"),
        Clue("fact", ClueType.FACT, person="A1"),
        Clue("fact", ClueType.FACT, status=Status.INNOCENT),
        Clue("fact", ClueType.FACT, person="D1", status=Status.INNOCENT),
        Clue("fact", ClueType.FACT, person=[], status=Status.INNOCENT),
        Clue("same", ClueType.SAME, first="A1"),
        Clue("different", ClueType.DIFFERENT, first="A1", second="D1"),
        Clue("different", ClueType.DIFFERENT, first=[], second="B1"),
        Clue("count", ClueType.EXACTLY, k=0),
        Clue("count", ClueType.AT_LEAST, region="ROW", k=0),
        Clue("fact", ClueType.FACT, person="A1", status=Status.INNOCENT, k=0),
        Clue("fact", ClueType.FACT, person="A1", status=Status.INNOCENT, first="B1"),
        Clue("same", ClueType.SAME, first="A1", second="B1", region=Region(RegionType.EXPLICIT)),
        Clue("different", ClueType.DIFFERENT, first="A1", second="B1", status=Status.CRIMINAL),
        Clue("count", ClueType.EXACTLY, region=Region(RegionType.EXPLICIT), k=0, person="A1"),
        Clue("even", ClueType.EVEN, region=Region(RegionType.EXPLICIT), k=0),
        Clue("odd", ClueType.ODD, region=Region(RegionType.EXPLICIT), second="A1"),
    ],
)
def test_invalid_clue_parameters_raise_contract_error(
    public_state: PublicState, assignment: dict[str, Status], clue: Clue
) -> None:
    before = deepcopy((clue, assignment, public_state))
    with pytest.raises(ContractError):
        evaluate_clue(clue, assignment, public_state)
    assert (clue, assignment, public_state) == before


@pytest.mark.parametrize("kind", [ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST])
@pytest.mark.parametrize("k", [None, True, False, 1.0, "1", -1, 4])
def test_counting_requires_integer_k_in_region_bounds(
    public_state: PublicState, assignment: dict[str, Status], kind: ClueType, k: int
) -> None:
    with pytest.raises(ContractError):
        evaluate_clue(
            Clue("count", kind, region=Region(RegionType.ROW, index=0), k=k),
            assignment,
            public_state,
        )


def test_fact_also_validates_public_geometry(
    public_state: PublicState, assignment: dict[str, Status]
) -> None:
    clue = Clue("fact", ClueType.FACT, person="A1", status=Status.INNOCENT)
    for state in (None, replace(public_state, size=True), replace(public_state, characters=())):
        with pytest.raises(ContractError):
            evaluate_clue(clue, assignment, state)
