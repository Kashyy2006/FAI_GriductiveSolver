"""Test-only puzzle builders and Protocol fakes; never production backends."""

from copy import deepcopy
from dataclasses import replace

from game.contracts import VerdictVerifier
from game.models import (
    CNF,
    Character,
    Clue,
    ClueType,
    EncodingResult,
    PublicCharacter,
    PublicState,
    Puzzle,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictResult,
)


def make_puzzle(size: int = 3, *, self_facts: bool = False) -> Puzzle:
    ids = tuple(f"{chr(65 + c)}{r + 1}" for r in range(size) for c in range(size))
    cells = tuple(
        Character(
            cell_id,
            f"Person {index:02d}",
            "Tester",
            index // size,
            index % size,
            Status.INNOCENT,
            Clue(
                f"clue_{cell_id}",
                ClueType.FACT,
                person=cell_id if self_facts else ids[(index + 1) % len(ids)],
                status=Status.INNOCENT,
            ),
        )
        for index, cell_id in enumerate(ids)
    )
    return Puzzle("1.0", "test_puzzle", size, cells, ("A1",))


class FixedEncoder:
    """Return a predetermined CNF while checking validation metadata."""

    def __init__(self, cnf: CNF, auxiliary: tuple[int, ...] = ()) -> None:
        self.cnf = cnf
        self.auxiliary = auxiliary
        self.states: list[PublicState] = []

    def encode(self, state: PublicState) -> EncodingResult:
        self.states.append(state)
        mapping = {c.id: c.row * state.size + c.col + 1 for c in state.characters}
        return EncodingResult(
            deepcopy(self.cnf),
            mapping,
            tuple(mapping.values()),
            self.auxiliary,
            len(self.cnf),
            tuple(sorted(c.clue.id for c in state.characters if c.clue)),
        )


class FactEncoder:
    """Minimal test fake for FACT-only snapshots; not a general CNF encoder."""

    def encode(self, state: PublicState) -> EncodingResult:
        mapping = {c.id: c.row * state.size + c.col + 1 for c in state.characters}
        clauses: CNF = []
        clues = []
        for cell in state.characters:
            if cell.status is not None:
                clauses.append(
                    [mapping[cell.id] if cell.status == Status.CRIMINAL else -mapping[cell.id]]
                )
            if cell.clue is not None:
                assert cell.clue.type == ClueType.FACT
                variable = mapping[cell.clue.person]
                clauses.append([variable if cell.clue.status == Status.CRIMINAL else -variable])
                clues.append(cell.clue.id)
        return EncodingResult(
            clauses, mapping, tuple(mapping.values()), (), len(clauses), tuple(sorted(clues))
        )


class PublicTestEngine:
    """Test Engine role: own a private puzzle and use the real Agent verifier."""

    def __init__(self, puzzle: Puzzle, verifier: VerdictVerifier) -> None:
        self._puzzle = puzzle
        self._verifier = verifier
        self._state = PublicState(
            puzzle.puzzle_id,
            puzzle.size,
            StateToken("test-only", 0),
            tuple(
                PublicCharacter(
                    c.id,
                    c.name,
                    c.profession,
                    c.row,
                    c.col,
                    c.hidden_status if c.id in puzzle.initially_revealed else None,
                    c.clue if c.id in puzzle.initially_revealed else None,
                )
                for c in puzzle.characters
            ),
        )

    def get_public_state(self) -> PublicState:
        return self._state

    def submit_verdict(
        self, character_id: str, status: Status, *, expected_token: StateToken
    ) -> VerdictResult:
        if expected_token != self._state.token:
            return VerdictResult(VerdictOutcome.STALE_STATE, self._state, None, None)
        proof = self._verifier(self._state, character_id, status)
        if proof.outcome != VerdictOutcome.ACCEPTED:
            return VerdictResult(proof.outcome, self._state, None, proof)
        private = next(c for c in self._puzzle.characters if c.id == character_id)
        assert private.hidden_status == status
        self._state = replace(
            self._state,
            token=StateToken(self._state.token.session_id, self._state.token.version + 1),
            characters=tuple(
                replace(c, status=status, clue=private.clue) if c.id == character_id else c
                for c in self._state.characters
            ),
        )
        return VerdictResult(VerdictOutcome.ACCEPTED, self._state, private.clue, proof)
