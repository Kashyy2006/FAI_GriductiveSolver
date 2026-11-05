"""Independent clue semantics; this module must never call the CNF encoder."""

from collections.abc import Mapping

from game.models import Clue, ClueType, ContractError, PublicState, Status
from logic.regions import resolve_region


def evaluate_clue(clue: Clue, assignment: Mapping[str, Status], state: PublicState) -> bool:
    """Evaluate against a complete character-ID assignment, not SAT variable IDs."""
    if set(assignment) != {item.id for item in state.characters} or any(
        not isinstance(value, Status) for value in assignment.values()
    ):
        raise ContractError("Expected a complete assignment of Status values")
    if clue.type == ClueType.FACT:
        if clue.person not in assignment or clue.status is None:
            raise ContractError("Invalid FACT parameters")
        return assignment[clue.person] == clue.status
    if clue.type in (ClueType.SAME, ClueType.DIFFERENT):
        if clue.first not in assignment or clue.second not in assignment:
            raise ContractError("Unknown binary-clue character")
        same = assignment[clue.first] == assignment[clue.second]
        return same if clue.type == ClueType.SAME else not same
    if clue.region is None:
        raise ContractError("Counting/parity clue requires a region")
    region = resolve_region(clue.region, state)
    count = sum(assignment[cell] == Status.CRIMINAL for cell in region)
    if clue.type == ClueType.EVEN:
        return count % 2 == 0
    if clue.type == ClueType.ODD:
        return count % 2 == 1
    if type(clue.k) is not int or not 0 <= clue.k <= len(region):
        raise ContractError("Counting clue k is outside region bounds")
    if clue.type == ClueType.EXACTLY:
        return count == clue.k
    if clue.type == ClueType.AT_LEAST:
        return count >= clue.k
    if clue.type == ClueType.AT_MOST:
        return count <= clue.k
    raise ContractError(f"Unsupported clue type: {clue.type}")
