"""Public coordinate-only region resolution, including common neighbors."""

from game.models import ContractError, PublicCharacter, PublicState, Region, RegionType


def _validated_cells(state: PublicState) -> tuple[PublicCharacter, ...]:
    """Validate only board geometry, leaving public statuses and clues untouched."""
    if (
        not isinstance(state, PublicState)
        or type(state.size) is not int
        or state.size not in (3, 4, 5)
    ):
        raise ContractError("Expected a PublicState with board size 3, 4, or 5")
    if not isinstance(state.characters, tuple) or len(state.characters) != state.size * state.size:
        raise ContractError("Characters must cover every board cell exactly once")
    for cell in state.characters:
        if not isinstance(cell, PublicCharacter):
            raise ContractError("Expected public character metadata")
        if (
            type(cell.row) is not int
            or type(cell.col) is not int
            or not 0 <= cell.row < state.size
            or not 0 <= cell.col < state.size
        ):
            raise ContractError("Cell coordinates must be integers inside the board")
        if cell.id != f"{chr(65 + cell.col)}{cell.row + 1}":
            raise ContractError("Cell ID does not match coordinates")
    if len({cell.id for cell in state.characters}) != len(state.characters):
        raise ContractError("Duplicate board cells")
    return tuple(sorted(state.characters, key=lambda cell: (cell.row, cell.col)))


def resolve_region(region: Region, state: PublicState) -> tuple[str, ...]:
    """Return distinct cells in row-major order; never inspect hidden labels."""
    cells = _validated_cells(state)
    by_id = {item.id: item for item in cells}
    if not isinstance(region, Region) or not isinstance(region.kind, RegionType):
        raise ContractError("Expected a Region with a RegionType tag")
    allowed_fields = {
        RegionType.ROW: ("index",),
        RegionType.COLUMN: ("index",),
        RegionType.NEIGHBORS: ("cell",),
        RegionType.EXPLICIT: ("cells",),
        RegionType.COMMON_NEIGHBORS: ("first", "second"),
    }
    for name in ("index", "cell", "cells", "first", "second"):
        default = () if name == "cells" else None
        if name not in allowed_fields[region.kind] and getattr(region, name) != default:
            raise ContractError(f"Unexpected {name} parameter for {region.kind.value}")

    def neighbors(cell_id: str | None) -> set[str]:
        if not isinstance(cell_id, str) or cell_id not in by_id:
            raise ContractError(f"Unknown cell: {cell_id}")
        center = by_id[cell_id]
        return {
            item.id
            for item in cells
            if item.id != cell_id
            and max(abs(item.row - center.row), abs(item.col - center.col)) == 1
        }

    if region.kind in (RegionType.ROW, RegionType.COLUMN):
        if type(region.index) is not int or not 0 <= region.index < state.size:
            raise ContractError("Region index is outside the board")
        selected = {
            item.id
            for item in cells
            if (item.row if region.kind == RegionType.ROW else item.col) == region.index
        }
    elif region.kind == RegionType.NEIGHBORS:
        selected = neighbors(region.cell)
    elif region.kind == RegionType.COMMON_NEIGHBORS:
        if region.first == region.second:
            raise ContractError("COMMON_NEIGHBORS requires two distinct cells")
        selected = neighbors(region.first) & neighbors(region.second)
    elif region.kind == RegionType.EXPLICIT:
        if not isinstance(region.cells, tuple) or any(
            not isinstance(cell_id, str) for cell_id in region.cells
        ):
            raise ContractError("EXPLICIT cells must be a tuple of cell IDs")
        selected = set(region.cells)
        if len(selected) != len(region.cells) or not selected <= by_id.keys():
            raise ContractError("EXPLICIT contains duplicate or unknown cells")
    else:
        raise ContractError(f"Unsupported region: {region.kind}")
    return tuple(item.id for item in cells if item.id in selected)
