"""Boundary and schema regression tests for the shared contract, not stub tests."""

import copy
import json
from dataclasses import asdict, fields
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from game.models import (
    Clue,
    ClueType,
    ContractError,
    PublicCharacter,
    PublicState,
    PuzzleValidationError,
    Region,
    RegionType,
    StateToken,
    Status,
)
from game.puzzle_loader import SCHEMA_PATH, clue_from_dict, load_puzzle, puzzle_from_dict
from logic.clue_evaluator import evaluate_clue
from logic.regions import resolve_region

SOURCE = Path(__file__).resolve().parents[1]


@pytest.fixture
def raw_puzzle():
    return json.loads((SOURCE / "puzzles/3x3/example_01.json").read_text(encoding="utf-8"))


@pytest.fixture
def geometry(raw_puzzle):
    puzzle = puzzle_from_dict(raw_puzzle)
    return PublicState(
        puzzle.puzzle_id,
        puzzle.size,
        StateToken("test", 0),
        tuple(PublicCharacter(c.id, c.name, c.profession, c.row, c.col) for c in puzzle.characters),
    )


def test_public_types_cannot_hold_hidden_fields(geometry):
    assert {f.name for f in fields(PublicCharacter)} == {
        "id",
        "name",
        "profession",
        "row",
        "col",
        "status",
        "clue",
    }
    serialized = json.dumps(asdict(geometry))
    assert "hidden_status" not in serialized
    assert all(c.status is None and c.clue is None for c in geometry.characters)


def test_schema_and_example_are_valid(raw_puzzle):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(raw_puzzle)
    puzzle = load_puzzle(SOURCE / "puzzles/3x3/example_01.json")
    assert len(puzzle.characters) == 9
    assert puzzle.initially_revealed == ("A1",)


def test_extension_fixtures(geometry):
    data = json.loads((SOURCE / "tests/fixtures/extensions.json").read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    # A separate root ref must not retain puzzle root constraints.
    validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/clue"})
    assignment = {key: Status(value) for key, value in data["assignment"].items()}
    for raw in data["clues"]:
        validator.validate(raw)
        assert evaluate_clue(clue_from_dict(raw), assignment, geometry)
    for example in data["regions"]:
        raw = example["region"]
        region = Region(RegionType(raw["kind"]), first=raw["first"], second=raw["second"])
        assert resolve_region(region, geometry) == tuple(example["expected"])


def test_empty_region_truth_and_parity_complements(geometry):
    assignment = {c.id: Status.INNOCENT for c in geometry.characters}
    region = Region(RegionType.EXPLICIT)
    for kind in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        assert evaluate_clue(Clue("empty", kind, region=region, k=0), assignment, geometry)
    assert evaluate_clue(Clue("even", ClueType.EVEN, region=region), assignment, geometry)
    assert not evaluate_clue(Clue("odd", ClueType.ODD, region=region), assignment, geometry)
    for index, character in enumerate(geometry.characters):
        assignment[character.id] = Status.CRIMINAL
        region = Region(RegionType.ROW, index=character.row)
        even = evaluate_clue(Clue("even", ClueType.EVEN, region=region), assignment, geometry)
        odd = evaluate_clue(Clue("odd", ClueType.ODD, region=region), assignment, geometry)
        assert even != odd, index


def test_common_neighbors_is_symmetric_and_excludes_endpoints(geometry):
    forward = Region(RegionType.COMMON_NEIGHBORS, first="A1", second="B1")
    reverse = Region(RegionType.COMMON_NEIGHBORS, first="B1", second="A1")
    result = resolve_region(forward, geometry)
    assert result == resolve_region(reverse, geometry)
    assert result == ("A2", "B2")


def test_common_neighbors_can_be_empty_on_four_by_four():
    state = PublicState(
        "four",
        4,
        StateToken("four", 0),
        tuple(
            PublicCharacter(f"{chr(65 + c)}{r + 1}", "Name", "Job", r, c)
            for r in range(4)
            for c in range(4)
        ),
    )
    assert resolve_region(Region(RegionType.COMMON_NEIGHBORS, first="A1", second="D4"), state) == ()


@pytest.mark.parametrize("mode", ["extra", "duplicate", "reference", "false", "k", "float"])
def test_loader_rejects_bad_data_without_mutating_input(raw_puzzle, mode):
    data = copy.deepcopy(raw_puzzle)
    if mode == "extra":
        data["unrecognized"] = True
    elif mode == "duplicate":
        data["characters"][1]["clue"]["id"] = data["characters"][0]["clue"]["id"]
    elif mode == "reference":
        data["characters"][0]["clue"]["person"] = "D1"
    elif mode == "false":
        data["characters"][0]["clue"]["status"] = "CRIMINAL"
    elif mode == "float":
        data["size"] = 3.0
    else:
        data["characters"][0]["clue"] = {
            "id": "bad",
            "type": "EXACTLY",
            "k": 2,
            "region": {"kind": "EXPLICIT", "cells": ["A1"]},
        }
    before = copy.deepcopy(data)
    with pytest.raises(PuzzleValidationError):
        puzzle_from_dict(data)
    assert data == before


@pytest.mark.parametrize(
    "region",
    [
        Region(RegionType.COMMON_NEIGHBORS, first="A1", second="A1"),
        Region(RegionType.COMMON_NEIGHBORS, first="A1", second="D1"),
        Region(RegionType.EXPLICIT, cells=("A1", "A1")),
        Region(RegionType.ROW, index=True),
    ],
)
def test_invalid_regions_fail(region, geometry):
    with pytest.raises(ContractError):
        resolve_region(region, geometry)
