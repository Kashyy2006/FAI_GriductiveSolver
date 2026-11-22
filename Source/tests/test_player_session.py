"""Resume and replay must preserve Engine proof checks and public information boundaries."""

import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.models import Clue, ClueType, Region, RegionType, Status, VerdictOutcome
from game.puzzle_loader import load_puzzle
from gui.clue_text import format_clue
from gui.play_session import LEVELS, SOURCE, PlaySession, ProgressStore
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver


def make_session(key: str = LEVELS[0].key) -> tuple[PlaySession, DeductiveAgent]:
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    engine = GameEngine(load_puzzle(SOURCE / "puzzles" / key), agent.verify_verdict)
    return PlaySession(engine), agent


def test_saved_moves_are_reproved_with_fresh_tokens_and_public_snapshots(tmp_path: Path) -> None:
    session, _ = make_session()
    session.store = ProgressStore(tmp_path / "progress.json")
    session.key = LEVELS[0].key
    initial = session.get_public_state()
    accepted = session.submit_verdict("B1", Status.INNOCENT, expected_token=initial.token)
    assert accepted.outcome == VerdictOutcome.ACCEPTED
    session.marks["C3"] = "Blue"
    session.used_clues.add(initial.characters[0].clue.id)
    session.hints, session.rejected = 2, 1
    session.elapsed_before = 123.0
    session.pause()
    session.persist()
    saved = json.loads(session.store.path.read_text(encoding="utf-8"))
    text = session.store.path.read_text(encoding="utf-8")
    assert "hidden_status" not in text and "newly_revealed_clue" not in text
    assert '"assignment"' not in text
    restored, _ = make_session()
    restored.restore(saved["levels"][session.key])
    assert restored.snapshots[0].token.session_id != initial.token.session_id
    assert restored.snapshots[0].characters[1].clue is None
    assert restored.snapshots[1].characters[1].clue == accepted.revealed_clue
    assert restored.snapshots[-1].characters == session.snapshots[-1].characters
    assert restored.steps[0].queries == session.steps[0].queries
    assert restored.queries == session.queries
    assert restored.hints == 2 and restored.rejected == 1
    assert restored.elapsed >= 123
    assert restored.marks == {"C3": "Blue"}
    assert restored.used_clues == session.used_clues


def test_tampered_saved_verdict_cannot_reveal_a_card(tmp_path: Path) -> None:
    session, _ = make_session()
    session.store, session.key = ProgressStore(tmp_path / "progress.json"), LEVELS[0].key
    session.persist()
    record = session.store.data["levels"][session.key]
    record["moves"] = [["B1", "CRIMINAL"]]
    record["step_queries"] = [[]]
    restored, _ = make_session()
    initial = restored.get_public_state()
    with pytest.raises(ValueError, match="no longer provable"):
        restored.restore(record)
    assert restored.get_public_state() == initial
    assert restored.steps == []


def test_rejection_does_not_create_history_or_change_kb() -> None:
    session, _ = make_session()
    initial = session.get_public_state()
    encoding = CNFEncoder().encode(initial)
    result = session.submit_verdict("A2", Status.CRIMINAL, expected_token=initial.token)
    assert result.outcome == VerdictOutcome.NOT_PROVABLE
    assert session.snapshots == [initial] and session.steps == []
    assert CNFEncoder().encode(session.get_public_state()) == encoding


def test_auto_solve_history_reveals_exactly_one_card_per_snapshot() -> None:
    session, agent = make_session()
    result = agent.auto_solve(session)
    assert len(session.snapshots) == len(result.steps) + 1 == 9
    assert session.snapshots[-1] == result.final_state
    for index, (before, after) in enumerate(zip(session.snapshots, session.snapshots[1:])):
        changed = [b.id for b, a in zip(before.characters, after.characters) if b != a]
        assert changed == [result.steps[index].character_id]
        for character in before.characters:
            if character.status is None:
                assert character.clue is None
        assert session.steps[index].newly_revealed_clue == result.steps[index].newly_revealed_clue


def test_stale_session_cannot_append_history_after_restart() -> None:
    session, _ = make_session()
    initial = session.get_public_state()
    session.engine.restart()
    result = session.submit_verdict("B1", Status.INNOCENT, expected_token=initial.token)
    assert result.outcome == VerdictOutcome.STALE_STATE
    assert session.snapshots == [initial] and session.steps == []


def test_progress_store_keeps_levels_separate_and_active_selection(tmp_path: Path) -> None:
    store = ProgressStore(tmp_path / "progress.json")
    store.active_key = LEVELS[1].key
    store.save(LEVELS[1].key, {"moves": [], "completed": False})
    store.save(LEVELS[0].key, {"moves": [["B1", "INNOCENT"]], "completed": False})
    reloaded = ProgressStore(store.path)
    assert reloaded.data["last_level"] == LEVELS[1].key
    assert len(reloaded.data["levels"]) == 2
    assert not store.path.with_suffix(".tmp").exists()


def test_save_failure_is_available_for_ui_and_keeps_previous_file(tmp_path: Path) -> None:
    session, _ = make_session()
    blocker = tmp_path / "file"
    blocker.write_text("keep", encoding="utf-8")
    session.store = ProgressStore(blocker / "progress.json")
    session.key = LEVELS[0].key
    session.persist()
    assert isinstance(session.save_error, OSError)
    assert blocker.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("text", ["{", "[]", '{"version": 99, "levels": {}}'])
def test_corrupt_progress_is_reported_without_overwriting(tmp_path: Path, text: str) -> None:
    path = tmp_path / "progress.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        ProgressStore(path)
    assert path.read_text(encoding="utf-8") == text


def test_clue_names_cover_fact_binary_and_regions_without_rewriting_remarks() -> None:
    session, _ = make_session()
    state = session.get_public_state()
    assert format_clue(Clue("fact", ClueType.FACT, person="B1", status=Status.CRIMINAL), state) == (
        "Ben is Criminal"
    )
    assert format_clue(Clue("same", ClueType.SAME, first="A1", second="B1"), state) == (
        "Alice has the same status as Ben"
    )
    for region, expected in (
        (
            Region(RegionType.NEIGHBORS, cell="B1"),
            "Even number of criminals among neighbors of Ben",
        ),
        (
            Region(RegionType.COMMON_NEIGHBORS, first="A1", second="C1"),
            "Even number of criminals among common neighbors of Alice and Chloe",
        ),
        (
            Region(RegionType.EXPLICIT, cells=("A1", "B1")),
            "The number of criminals among Alice, Ben is even",
        ),
        (Region(RegionType.EXPLICIT), "Even number of criminals in an empty region"),
    ):
        assert format_clue(Clue("even", ClueType.EVEN, region=region), state) == expected
    remark = Clue("story", ClueType.REMARK, text="A1 remembers B1. This is not evidence.")
    assert format_clue(remark, state) == remark.text


@pytest.mark.parametrize(
    "clue_type,k,expected",
    [
        (ClueType.EXACTLY, 1, "Tom is Criminal"),
        (ClueType.EXACTLY, 0, "Tom is Innocent"),
        (ClueType.AT_LEAST, 1, "Tom is Criminal"),
        (ClueType.AT_LEAST, 0, "Tom may be Criminal or Innocent"),
        (ClueType.AT_MOST, 0, "Tom is Innocent"),
        (ClueType.AT_MOST, 1, "Tom may be Criminal or Innocent"),
        (ClueType.EVEN, None, "Tom is Innocent"),
        (ClueType.ODD, None, "Tom is Criminal"),
    ],
)
def test_single_person_region_describes_the_person_not_a_location(
    clue_type: ClueType,
    k: int | None,
    expected: str,
) -> None:
    session, _ = make_session()
    original = session.get_public_state()
    state = replace(
        original,
        characters=tuple(
            replace(c, name="Tom") if c.id == "A1" else c for c in original.characters
        ),
    )
    clue = Clue("one_person", clue_type, region=Region(RegionType.EXPLICIT, cells=("A1",)), k=k)
    assert format_clue(clue, state) == expected
    assert session.get_public_state() == original


@pytest.mark.parametrize(
    "clue_type,k,expected",
    [
        (ClueType.EXACTLY, 1, "Exactly 1 of these people is Criminal: Alice, Ben"),
        (ClueType.AT_LEAST, 1, "At least 1 of these people is Criminal: Alice, Ben"),
        (ClueType.AT_MOST, 2, "At most 2 of these people are Criminal: Alice, Ben"),
        (ClueType.EXACTLY, 0, "Exactly 0 of these people are Criminal: Alice, Ben"),
    ],
)
def test_multiple_person_count_uses_a_group(
    clue_type: ClueType,
    k: int,
    expected: str,
) -> None:
    session, _ = make_session()
    clue = Clue("group", clue_type, region=Region(RegionType.EXPLICIT, cells=("A1", "B1")), k=k)
    assert format_clue(clue, session.get_public_state()) == expected


def test_catalogue_names_are_english_and_sorted_without_changing_logic() -> None:
    for level in LEVELS:
        puzzle = load_puzzle(SOURCE / "puzzles" / level.key)
        names = [character.name for character in puzzle.characters]
        assert names == sorted(names)
        assert all(name.isascii() and not any(c.isdigit() for c in name) for name in names)
        session, agent = make_session(level.key)
        result = agent.auto_solve(session)
        assert result.final_state.token.version == len(result.steps)
        assert "hidden_status" not in json.dumps(asdict(result.final_state))
