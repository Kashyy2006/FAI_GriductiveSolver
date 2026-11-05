"""Public coordinate-only region resolution, including common neighbors."""

from game.models import ContractError, PublicState, Region, RegionType


def resolve_region(region: Region, state: PublicState) -> tuple[str, ...]:
    """Return distinct cells in row-major order; never inspect hidden labels."""
    cells = sorted(state.characters, key=lambda item: (item.row, item.col))
    by_id = {item.id: item for item in cells}

    def neighbors(cell_id: str | None) -> set[str]:
        if cell_id not in by_id:
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
        selected = set(region.cells)
        if len(selected) != len(region.cells) or not selected <= by_id.keys():
            raise ContractError("EXPLICIT contains duplicate or unknown cells")
    else:
        raise ContractError(f"Unsupported region: {region.kind}")
    return tuple(item.id for item in cells if item.id in selected)
