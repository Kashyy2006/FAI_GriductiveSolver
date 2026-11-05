"""TV3: complete-clue uniqueness validation, separate from gameplay."""

from game.contracts import Encoder, SATSolver
from game.models import Puzzle, UniquenessResult


def check_uniqueness(
    puzzle: Puzzle,
    encoder: Encoder,
    solver: SATSolver,
    *,
    timeout_seconds: float | None = None,
) -> UniquenessResult:
    raise NotImplementedError("TV3: encode all clues without adding hidden labels")
