"""Trace JSON tests independent of the Engine, Encoder and Solver implementations."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from agent.trace import save_trace
from game.models import (
    Clue,
    ClueType,
    DeductionStep,
    SATQuery,
    SATStatus,
    SolverStats,
    StateToken,
    Status,
)


def step(number: int = 1) -> DeductionStep:
    return DeductionStep(
        number,
        StateToken("session", number - 1),
        StateToken("session", number),
        ("public_clue_before",),
        (
            SATQuery("CONSISTENCY", (), SATStatus.SAT, SolverStats(1, 2, 0, 0.001)),
            SATQuery("ASSUME_INNOCENT:A1", (-1,), SATStatus.UNSAT, SolverStats(0, 3, 1, 0.002)),
        ),
        "A1",
        Status.CRIMINAL,
        Clue("newly_public_đã_mở", ClueType.FACT, person="B1", status=Status.INNOCENT),
    )


def test_json_schema_values_and_no_mutation(tmp_path: Path) -> None:
    steps = [step()]
    before = deepcopy(steps)
    destination = tmp_path / "nested" / "trace.json"
    save_trace(steps, destination)
    text = destination.read_text(encoding="utf-8")
    payload = json.loads(text)
    assert steps == before
    assert len(payload) == 1
    record = payload[0]
    assert record["step"] == 1
    assert record["token_before"] == {"session_id": "session", "version": 0}
    assert record["token_after"] == {"session_id": "session", "version": 1}
    assert record["verdict"] == "CRIMINAL"
    assert record["active_clue_ids"] == ["public_clue_before"]
    assert record["queries"][0]["assumptions"] == []
    assert record["queries"][1]["assumptions"] == [-1]
    assert record["queries"][1]["result"] == "UNSAT"
    assert record["queries"][1]["stats"]["backtracks"] == 1
    assert record["newly_revealed_clue"]["status"] == "INNOCENT"
    assert "đã_mở" in text
    assert "hidden_status" not in text and "assignment" not in text
    assert set(record) == {
        "step",
        "token_before",
        "token_after",
        "active_clue_ids",
        "queries",
        "character_id",
        "verdict",
        "newly_revealed_clue",
    }


def test_export_is_stable_preserves_order_and_does_not_append_duplicates(tmp_path: Path) -> None:
    destination = tmp_path / "trace.json"
    steps = (step(1), step(2))
    save_trace(steps, destination)
    first = destination.read_bytes()
    save_trace(steps, destination)
    assert destination.read_bytes() == first
    assert [item["step"] for item in json.loads(first)] == [1, 2]
    assert first.endswith(b"\n")


def test_empty_trace_is_valid_json_array(tmp_path: Path) -> None:
    destination = tmp_path / "empty.json"
    save_trace((), destination)
    assert json.loads(destination.read_text(encoding="utf-8")) == []


def test_io_errors_are_not_swallowed(tmp_path: Path) -> None:
    blocker = tmp_path / "file-not-a-directory"
    blocker.write_text("blocker", encoding="utf-8")
    with pytest.raises(OSError):
        save_trace((step(),), blocker / "trace.json")
