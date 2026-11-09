"""Region geometry, tagged parameters, and invalid public board inputs."""

from copy import deepcopy
from dataclasses import replace
from itertools import combinations

import pytest

from game.models import ContractError, PublicCharacter, PublicState, Region, RegionType
from logic.regions import resolve_region


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        (Region(RegionType.ROW, index=1), ("A2", "B2", "C2")),
        (Region(RegionType.COLUMN, index=1), ("B1", "B2", "B3")),
        (Region(RegionType.NEIGHBORS, cell="A1"), ("B1", "A2", "B2")),
        (Region(RegionType.NEIGHBORS, cell="B1"), ("A1", "C1", "A2", "B2", "C2")),
        (
            Region(RegionType.NEIGHBORS, cell="B2"),
            ("A1", "B1", "C1", "A2", "C2", "A3", "B3", "C3"),
        ),
        (Region(RegionType.EXPLICIT, cells=("C3", "A1", "B2")), ("A1", "B2", "C3")),
        (Region(RegionType.EXPLICIT), ()),
        (Region(RegionType.COMMON_NEIGHBORS, first="A1", second="C1"), ("B1", "B2")),
        (Region(RegionType.COMMON_NEIGHBORS, first="A1", second="C3"), ("B2",)),
        (Region(RegionType.COMMON_NEIGHBORS, first="A1", second="B1"), ("A2", "B2")),
    ],
)
def test_regions_return_expected_cells_without_mutation(
    public_state: PublicState, region: Region, expected: tuple[str, ...]
) -> None:
    before = deepcopy((public_state, region))
    assert resolve_region(region, public_state) == expected
    reversed_state = replace(public_state, characters=tuple(reversed(public_state.characters)))
    assert resolve_region(region, reversed_state) == expected
    assert (public_state, region) == before


@pytest.mark.parametrize("public_state", [3, 4, 5], indirect=True)
def test_rows_columns_and_common_neighbors_across_board_sizes(public_state: PublicState) -> None:
    cells = public_state.characters
    for index in range(public_state.size):
        assert resolve_region(Region(RegionType.ROW, index=index), public_state) == tuple(
            cell.id for cell in cells if cell.row == index
        )
        assert resolve_region(Region(RegionType.COLUMN, index=index), public_state) == tuple(
            cell.id for cell in cells if cell.col == index
        )
    offsets = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))
    neighbors = {cell.id: {(cell.row + dr, cell.col + dc) for dr, dc in offsets} for cell in cells}
    for cell in cells:
        expected = tuple(item.id for item in cells if (item.row, item.col) in neighbors[cell.id])
        assert resolve_region(Region(RegionType.NEIGHBORS, cell=cell.id), public_state) == expected
    for first, second in combinations(cells, 2):
        expected = tuple(
            cell.id
            for cell in cells
            if (cell.row, cell.col) in neighbors[first.id] & neighbors[second.id]
            and cell.id not in (first.id, second.id)
        )
        region = Region(RegionType.COMMON_NEIGHBORS, first=first.id, second=second.id)
        assert resolve_region(region, public_state) == expected
        assert resolve_region(replace(region, first=second.id, second=first.id), public_state) == (
            expected
        )


@pytest.mark.parametrize(
    "region",
    [
        None,
        {},
        Region("ROW", index=0),
        Region("UNSUPPORTED"),
        Region(RegionType.ROW),
        Region(RegionType.ROW, index=-1),
        Region(RegionType.ROW, index=3),
        Region(RegionType.ROW, index=True),
        Region(RegionType.COLUMN, index=1.0),
        Region(RegionType.COLUMN, index=3),
        Region(RegionType.NEIGHBORS),
        Region(RegionType.NEIGHBORS, cell="D1"),
        Region(RegionType.NEIGHBORS, cell=[]),
        Region(RegionType.EXPLICIT, cells=("A1", "A1")),
        Region(RegionType.EXPLICIT, cells=("D1",)),
        Region(RegionType.EXPLICIT, cells=["A1"]),
        Region(RegionType.EXPLICIT, cells=None),
        Region(RegionType.EXPLICIT, cells=([],)),
        Region(RegionType.COMMON_NEIGHBORS, first="A1", second="A1"),
        Region(RegionType.COMMON_NEIGHBORS, first="A1", second="D1"),
        Region(RegionType.COMMON_NEIGHBORS, first="A1"),
        Region(RegionType.COMMON_NEIGHBORS, first=[], second="B1"),
        Region(RegionType.ROW, index=0, cell="A1"),
        Region(RegionType.COLUMN, index=0, first="A1"),
        Region(RegionType.NEIGHBORS, cell="A1", cells=("B1",)),
        Region(RegionType.EXPLICIT, cells=("A1",), second="B1"),
        Region(RegionType.COMMON_NEIGHBORS, first="A1", second="B1", index=0),
    ],
)
def test_invalid_region_parameters_raise_contract_error(
    public_state: PublicState, region: Region
) -> None:
    before = deepcopy((region, public_state))
    with pytest.raises(ContractError):
        resolve_region(region, public_state)
    assert (region, public_state) == before


@pytest.mark.parametrize("size", [True, 3.0, 0, 2, 6, "3", None])
def test_invalid_board_sizes_raise_contract_error(public_state: PublicState, size: int) -> None:
    with pytest.raises(ContractError):
        resolve_region(Region(RegionType.ROW, index=0), replace(public_state, size=size))


@pytest.mark.parametrize(
    "cell",
    [
        None,
        PublicCharacter("B1", "Name", "Job", 0, 0),
        PublicCharacter("A1", "Name", "Job", 3, 0),
        PublicCharacter("A1", "Name", "Job", -1, 0),
        PublicCharacter("A1", "Name", "Job", 0.0, 0),
        PublicCharacter("A1", "Name", "Job", 0, False),
    ],
)
def test_invalid_board_cells_raise_contract_error(
    public_state: PublicState, cell: PublicCharacter
) -> None:
    state = replace(public_state, characters=(cell,) + public_state.characters[1:])
    with pytest.raises(ContractError):
        resolve_region(Region(RegionType.ROW, index=0), state)


def test_incomplete_or_duplicate_board_is_rejected(public_state: PublicState) -> None:
    for characters in (
        public_state.characters[:-1],
        public_state.characters[:-1] + (public_state.characters[0],),
        list(public_state.characters),
        None,
    ):
        with pytest.raises(ContractError):
            resolve_region(
                Region(RegionType.EXPLICIT), replace(public_state, characters=characters)
            )


@pytest.mark.parametrize("state", [None, {}])
def test_non_public_state_is_rejected(state: PublicState) -> None:
    with pytest.raises(ContractError):
        resolve_region(Region(RegionType.EXPLICIT), state)
