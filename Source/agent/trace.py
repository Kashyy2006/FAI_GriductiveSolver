"""Export accepted deduction steps using the existing contract-v1 JSON shape."""

import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from game.models import DeductionStep


def save_trace(steps: Sequence[DeductionStep], path: Path) -> None:
    """Write deterministic UTF-8 JSON; preserve inputs and propagate I/O errors."""
    # Each accepted verdict opens one card, hence one newly_revealed_clue per step.
    # asdict copies nested containers; str Enums serialize as their value and
    # tuples serialize as JSON arrays. No Engine object or model assignment is used.
    payload = json.dumps(
        [asdict(step) for step in steps],
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload + "\n", encoding="utf-8")
