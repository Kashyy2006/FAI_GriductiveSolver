"""Loader error boundaries and data ownership checks for TV1."""

import copy
import json
from pathlib import Path

import pytest

from game.models import PuzzleValidationError
from game.puzzle_loader import load_puzzle, puzzle_from_dict

SOURCE = Path(__file__).resolve().parents[1]


@pytest.fixture
def raw():
    return json.loads((SOURCE / "puzzles/3x3/example_01.json").read_text())


@pytest.mark.parametrize(
    "mode",
    [
        "missing",
        "status",
        "cell_duplicate",
        "coordinates",
        "outside",
        "bool_k",
        "float_k",
        "float_index",
        "explicit_duplicate",
        "initial_duplicate",
        "initial_unknown",
    ],
)
def test_invalid_data(raw, mode):
    character = raw["characters"][0]
    if mode == "missing":
        del character["name"]
    elif mode == "status":
        character["hidden_status"] = "UNKNOWN"
    elif mode == "cell_duplicate":
        raw["characters"][1] = copy.deepcopy(character)
    elif mode == "coordinates":
        character["col"] = 1
    elif mode == "outside":
        character["row"] = 3
    elif mode == "initial_duplicate":
        raw["initially_revealed"] = ["A1", "A1"]
    elif mode == "initial_unknown":
        raw["initially_revealed"] = ["D1"]
    else:
        region = {"kind": "ROW", "index": 0}
        k = 2
        if mode == "bool_k":
            k = True
        elif mode == "float_k":
            k = 2.0
        elif mode == "float_index":
            region["index"] = 0.0
        else:
            region = {"kind": "EXPLICIT", "cells": ["A1", "A1"]}
        character["clue"] = {"id": "clue_01", "type": "EXACTLY", "region": region, "k": k}
    before = copy.deepcopy(raw)
    with pytest.raises(PuzzleValidationError):
        puzzle_from_dict(raw)
    assert raw == before


def test_loader_normalizes_order_and_detaches_data(raw):
    raw["characters"].reverse()
    before = copy.deepcopy(raw)
    puzzle = puzzle_from_dict(raw)
    assert raw == before
    assert puzzle.characters[0].id == "A1"
    raw["characters"][-1]["clue"]["person"] = "C3"
    assert puzzle.characters[0].clue.person == "B1"


@pytest.mark.parametrize("payload", [b"{", b"\xff", b"[]", b"null"])
def test_bad_file_data_is_validation_error(tmp_path, payload):
    path = tmp_path / "bad.json"
    path.write_bytes(payload)
    with pytest.raises(PuzzleValidationError):
        load_puzzle(path)


def test_missing_file_remains_oserror(tmp_path):
    with pytest.raises(OSError):
        load_puzzle(tmp_path / "missing.json")


@pytest.mark.parametrize("name", ["inconsistent", "invalid_reference"])
def test_invalid_fixtures(name):
    with pytest.raises(PuzzleValidationError):
        load_puzzle(SOURCE / f"tests/fixtures/{name}.json")


def test_ambiguous_is_valid_input_not_loader_error():
    puzzle = load_puzzle(SOURCE / "tests/fixtures/ambiguous.json")
    assert len(puzzle.characters) == 9
    assert all(c.clue.first == c.clue.second for c in puzzle.characters)
