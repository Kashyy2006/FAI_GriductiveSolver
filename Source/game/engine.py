"""TV1: engine implementation boundary."""

from game.contracts import VerdictVerifier
from game.models import PublicState, Puzzle, StateToken, Status, VerdictResult


class GameEngine:
    def __init__(self, puzzle: Puzzle, verifier: VerdictVerifier) -> None:
        raise NotImplementedError("TV1: construct engine with private puzzle and verifier")

    def get_public_state(self) -> PublicState:
        raise NotImplementedError("TV1: return detached immutable public snapshot")

    def load(self, puzzle: Puzzle) -> PublicState:
        raise NotImplementedError("TV1: replace puzzle, create a new session")

    def restart(self) -> PublicState:
        raise NotImplementedError("TV1: reset current puzzle, create a new session")

    def submit_verdict(
        self, character_id: str, status: Status, *, expected_token: StateToken
    ) -> VerdictResult:
        raise NotImplementedError("TV1: verify current public state before committing")
