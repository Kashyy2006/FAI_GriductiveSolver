"""Strict JSON-to-model conversion and independent puzzle validation."""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from game.models import (
    Character,
    Clue,
    ClueType,
    ContractError,
    PublicCharacter,
    PublicState,
    Puzzle,
    PuzzleValidationError,
    Region,
    RegionType,
    StateToken,
    Status,
)
from logic.clue_evaluator import evaluate_clue
from logic.regions import resolve_region

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "puzzle.schema.json"


def clue_from_dict(data: dict[str, Any]) -> Clue:
    """Convert one schema-validated clue; not a standalone validator."""
    values = dict(data)
    values["type"] = ClueType(values["type"])
    if "status" in values:
        values["status"] = Status(values["status"])
    if "region" in values:
        fields = dict(values["region"])
        fields["kind"] = RegionType(fields["kind"])
        if "cells" in fields:
            fields["cells"] = tuple(fields["cells"])
        values["region"] = Region(**fields)
    return Clue(**values)


def puzzle_from_dict(data: dict[str, Any]) -> Puzzle:
    """Validate schema, references, board shape, clue truth; not uniqueness."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(data))
    if errors:
        raise PuzzleValidationError(errors[0].message)
    if type(data["size"]) is not int:
        raise PuzzleValidationError("size must be an integer, not bool or float")
    size = data["size"]
    raw = data["characters"]
    expected = {f"{chr(65 + col)}{row + 1}" for row in range(size) for col in range(size)}
    if len(raw) != size * size or {item["id"] for item in raw} != expected:
        raise PuzzleValidationError("Characters must cover every board cell exactly once")
    if not set(data["initially_revealed"]) <= expected:
        raise PuzzleValidationError("Unknown initially revealed cell")
    if len({item["clue"]["id"] for item in raw}) != len(raw):
        raise PuzzleValidationError("Duplicate clue IDs")
    for item in raw:
        row, col = item["row"], item["col"]
        if type(row) is not int or type(col) is not int:
            raise PuzzleValidationError("Coordinates must be integers")
        if not (0 <= row < size and 0 <= col < size):
            raise PuzzleValidationError("Coordinates outside the board")
        if item["id"] != f"{chr(65 + col)}{row + 1}":
            raise PuzzleValidationError("Cell ID does not match coordinates")
    characters = tuple(
        Character(
            id=item["id"],
            name=item["name"],
            profession=item["profession"],
            row=item["row"],
            col=item["col"],
            hidden_status=Status(item["hidden_status"]),
            clue=clue_from_dict(item["clue"]),
        )
        for item in sorted(raw, key=lambda item: (item["row"], item["col"]))
    )
    puzzle = Puzzle("1.0", data["puzzle_id"], size, characters, tuple(data["initially_revealed"]))
    # Metadata-only state used for geometry validation, never passed to Agent.
    geometry = PublicState(
        puzzle.puzzle_id,
        size,
        StateToken("validation-only", 0),
        tuple(PublicCharacter(c.id, c.name, c.profession, c.row, c.col) for c in characters),
    )
    assignment = {item.id: item.hidden_status for item in characters}
    try:
        for item in characters:
            clue = item.clue
            if clue.region is not None:
                resolve_region(clue.region, geometry)
            if not evaluate_clue(clue, assignment, geometry):
                raise PuzzleValidationError(f"Clue {clue.id} is false under the hidden solution")
    except ContractError as error:
        raise PuzzleValidationError(str(error)) from error
    return puzzle


def load_puzzle(path: Path) -> Puzzle:
    """Load UTF-8 JSON; wrap data errors, leave filesystem errors unchanged."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise PuzzleValidationError(str(error)) from error
    return puzzle_from_dict(data)
