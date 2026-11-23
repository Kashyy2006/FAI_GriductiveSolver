"""Human-readable public clues; narrative text is always preserved verbatim."""

from game.models import Clue, ClueType, PublicState, RegionType


def format_clue(clue: Clue | None, state: PublicState | None = None) -> str:
    if clue is None:
        return "Clue locked"
    names = {c.id: c.name for c in state.characters} if state else {}

    def person(cell: str | None) -> str:
        return names.get(cell, cell or "?")

    if clue.type == ClueType.REMARK:
        return clue.text or ""
    if clue.type == ClueType.FACT:
        return f"{person(clue.person)} is {clue.status.value.title() if clue.status else '?'}"
    if clue.type in (ClueType.SAME, ClueType.DIFFERENT):
        relation = "the same status as" if clue.type == ClueType.SAME else "a different status from"
        return f"{person(clue.first)} has {relation} {person(clue.second)}"
    region = clue.region
    if region is None:
        return clue.type.value.replace("_", " ").title()
    if region.kind == RegionType.EXPLICIT and region.cells:
        people = ", ".join(person(cell) for cell in region.cells)
        if len(region.cells) == 1:
            if clue.type in (ClueType.EVEN, ClueType.ODD):
                status = "Innocent" if clue.type == ClueType.EVEN else "Criminal"
            elif clue.type == ClueType.AT_LEAST and clue.k == 0:
                return f"{people} may be Criminal or Innocent"
            elif clue.type == ClueType.AT_MOST and clue.k == 1:
                return f"{people} may be Criminal or Innocent"
            else:
                status = "Criminal" if clue.k == 1 else "Innocent"
            return f"{people} is {status}"
        if clue.type in (ClueType.EVEN, ClueType.ODD):
            return f"The number of criminals among {people} is {clue.type.value.lower()}"
        verb = "is" if clue.k == 1 else "are"
        count = clue.type.value.replace("_", " ").capitalize()
        return f"{count} {clue.k} of these people {verb} Criminal: {people}"
    preposition = "in"
    if region.kind == RegionType.ROW:
        area = f"row {region.index + 1}" if region.index is not None else "row ?"
    elif region.kind == RegionType.COLUMN:
        area = f"column {chr(65 + region.index)}" if region.index is not None else "column ?"
    elif region.kind == RegionType.NEIGHBORS:
        area = f"neighbors of {person(region.cell)}"
        preposition = "among"
    elif region.kind == RegionType.COMMON_NEIGHBORS:
        area = f"common neighbors of {person(region.first)} and {person(region.second)}"
        preposition = "among"
    else:
        area = ", ".join(person(cell) for cell in region.cells) or "an empty region"
    if clue.type in (ClueType.EVEN, ClueType.ODD):
        return f"{clue.type.value.title()} number of criminals {preposition} {area}"
    noun = "criminal" if clue.k == 1 else "criminals"
    return f"{clue.type.value.replace('_', ' ').capitalize()} {clue.k} {noun} {preposition} {area}"
