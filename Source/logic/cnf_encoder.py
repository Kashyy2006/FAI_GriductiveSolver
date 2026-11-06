"""Deterministic CNF encoding of public FACT, SAME, and DIFFERENT clues."""

from game.models import CNF, Clue, ClueType, ContractError, EncodingResult, PublicState, Status
from logic.clue_evaluator import _validate_clue_fields
from logic.regions import _validated_cells


class CNFEncoder:
    def encode(self, state: PublicState) -> EncodingResult:
        """Build a fresh KB from public clues and known statuses."""
        cells = _validated_cells(state)
        variable_map = {cell.id: cell.row * state.size + cell.col + 1 for cell in cells}
        clues: list[Clue] = []
        for cell in cells:
            if cell.status is not None and not isinstance(cell.status, Status):
                raise ContractError("Public status must be a Status value or None")
            if cell.clue is not None:
                _validate_clue_fields(cell.clue)
                clues.append(cell.clue)
        clues.sort(key=lambda clue: clue.id)
        if len({clue.id for clue in clues}) != len(clues):
            raise ContractError("Duplicate active clue IDs")

        def variable_for(cell_id: str | None) -> int:
            if not isinstance(cell_id, str) or cell_id not in variable_map:
                raise ContractError(f"Unknown clue character: {cell_id}")
            return variable_map[cell_id]

        cnf: CNF = []
        for clue in clues:
            if clue.type == ClueType.FACT:
                if not isinstance(clue.status, Status):
                    raise ContractError("FACT requires a Status value")
                variable = variable_for(clue.person)
                cnf.append([variable if clue.status == Status.CRIMINAL else -variable])
            elif clue.type in (ClueType.SAME, ClueType.DIFFERENT):
                first = variable_for(clue.first)
                second = variable_for(clue.second)
                if clue.type == ClueType.SAME:
                    cnf.extend([[-first, second], [first, -second]])
                else:
                    cnf.extend([[first, second], [-first, -second]])
            else:
                raise NotImplementedError(f"TV2: CNF encoding for {clue.type.value}")
        for cell in cells:
            if cell.status is not None:
                variable = variable_map[cell.id]
                cnf.append([variable if cell.status == Status.CRIMINAL else -variable])
        return EncodingResult(
            cnf=cnf,
            variable_map=variable_map,
            primary_variables=tuple(variable_map.values()),
            auxiliary_variables=(),
            clause_count=len(cnf),
            active_clue_ids=tuple(clue.id for clue in clues),
        )
