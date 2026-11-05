"""TV4: public trace export boundary."""

from collections.abc import Sequence
from pathlib import Path

from game.models import DeductionStep


def save_trace(steps: Sequence[DeductionStep], path: Path) -> None:
    raise NotImplementedError("TV4: export stable UTF-8 JSON, no hidden clue content")
