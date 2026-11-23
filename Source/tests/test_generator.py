"""Certify generated cases through independent truth evaluation and real progressive proofs."""

from itertools import product
from pathlib import Path

import pytest

from agent.agent import DeductiveAgent
from agent.hints import find_clue_hint
from game.engine import GameEngine
from game.generator import generate_puzzle, write_generated_puzzle
from game.models import (
    Classification,
    ClueType,
    ContractError,
    KBStatus,
    PuzzleValidationError,
    SolveOutcome,
    SolverTimeout,
    Status,
    UniquenessOutcome,
    UniquenessResult,
    VerdictOutcome,
)
from game.puzzle_loader import load_puzzle
from gui.play_session import LEVELS, SOURCE, ProgressStore, level_for_key
from logic.clue_evaluator import evaluate_clue
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver
from solver.uniqueness import check_uniqueness


@pytest.mark.parametrize("size", [3, 4, 5])
@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4, 5, 10, 15, 17, 19, 42, 2147483647])
def test_generated_case_has_one_forced_move_at_every_step(size: int, seed: int) -> None:
    puzzle = generate_puzzle(size, seed)
    encoder, solver = CNFEncoder(), DPLLSolver()
    assert check_uniqueness(puzzle, encoder, solver).outcome == UniquenessOutcome.UNIQUE
    assert all(c.clue.type != ClueType.FACT for c in puzzle.characters)
    agent = DeductiveAgent(encoder, solver)
    engine = GameEngine(puzzle, agent.verify_verdict)
    steps = 0
    while any(c.status is None for c in engine.get_public_state().characters):
        before = engine.get_public_state()
        result = agent.classify_all(before)
        assert result.kb_status == KBStatus.CONSISTENT
        forced = [
            (cell, classification)
            for cell, classification in result.classifications.items()
            if classification != Classification.UNKNOWN
        ]
        assert len(forced) == 1
        cell, classification = forced[0]
        receipt = engine.submit_verdict(
            cell, Status(classification.value), expected_token=before.token
        )
        assert receipt.outcome == VerdictOutcome.ACCEPTED
        assert receipt.state.size == size and len(receipt.state.characters) == size**2
        assert [
            c.id for c, after in zip(before.characters, receipt.state.characters) if c != after
        ] == [cell]
        steps += 1
    assert steps == size**2 - len(puzzle.initially_revealed)
    assert agent.classify_all(engine.get_public_state()).kb_status == KBStatus.CONSISTENT


def test_same_seed_reproduces_case_and_different_seeds_change_it() -> None:
    assert generate_puzzle(4, 1234) == generate_puzzle(4, 1234)
    assert generate_puzzle(4, 1234) != generate_puzzle(4, 1235)


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_full_clue_uniqueness_matches_exhaustive_evaluator_without_initial_units(seed: int) -> None:
    puzzle = generate_puzzle(3, seed)
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    geometry = GameEngine(puzzle, agent.verify_verdict).get_public_state()
    solutions = []
    for values in product((Status.INNOCENT, Status.CRIMINAL), repeat=9):
        assignment = dict(zip((c.id for c in puzzle.characters), values))
        if all(evaluate_clue(c.clue, assignment, geometry) for c in puzzle.characters):
            solutions.append(assignment)
    assert solutions == [{c.id: c.hidden_status for c in puzzle.characters}]


@pytest.mark.parametrize(
    "size,seed", [(2, 0), (6, 0), (True, 0), (3, -1), (3, True), (3, 2147483648), (3, "42")]
)
def test_invalid_requests_are_rejected(size: int, seed: int) -> None:
    with pytest.raises(ContractError):
        generate_puzzle(size, seed)


def test_cancel_and_timeout_do_not_return_or_save_unchecked_puzzles(tmp_path: Path) -> None:
    with pytest.raises(InterruptedError):
        write_generated_puzzle(5, 5, tmp_path, should_cancel=lambda: True)
    assert list(tmp_path.iterdir()) == []
    with pytest.raises(SolverTimeout):
        generate_puzzle(5, 5, timeout_seconds=1e-12)


def test_nonunique_validation_is_an_error_not_a_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "game.generator.check_uniqueness",
        lambda *args, **kwargs: UniquenessResult(UniquenessOutcome.MULTIPLE, (), ()),
    )
    with pytest.raises(PuzzleValidationError, match="exactly one solution"):
        generate_puzzle(3, 0)


@pytest.mark.parametrize("seed", [1, 6, 11, 16, 123])
def test_generated_case_round_trip_and_progress_key(tmp_path: Path, seed: int) -> None:
    path = write_generated_puzzle(5, seed, tmp_path)
    assert load_puzzle(path) == generate_puzzle(5, seed)
    assert not list(tmp_path.glob("*.tmp"))
    key = f"generated/{path.name}"
    assert level_for_key(key).difficulty == "Generated"
    store = ProgressStore(tmp_path / "progress.json")
    store.active_key = key
    store.save(key, {"moves": [], "completed": False})
    assert ProgressStore(store.path).data["last_level"] == key


@pytest.mark.parametrize(
    "key",
    [
        "generated/../secret.json",
        "../generated_3x3_seed_2.json",
        "generated/generated_3x4_seed_2.json",
        "generated/generated_3x3_seed_9999999999.json",
    ],
)
def test_generated_keys_cannot_escape_the_puzzle_directory(key: str) -> None:
    assert level_for_key(key) is None


def test_every_main_case_is_unique_and_progressively_solvable() -> None:
    for level in LEVELS:
        if level.difficulty == "Practice":
            continue
        puzzle = load_puzzle(SOURCE / "puzzles" / level.key)
        encoder, solver = CNFEncoder(), DPLLSolver()
        assert check_uniqueness(puzzle, encoder, solver).outcome == UniquenessOutcome.UNIQUE
        agent = DeductiveAgent(encoder, solver)
        engine = GameEngine(puzzle, agent.verify_verdict)
        assert agent.auto_solve(engine).outcome == SolveOutcome.SOLVED


@pytest.mark.parametrize(
    "key", ["3x3/crossroads.json", "4x4/archive_case.json", "5x5/harbor_case.json"]
)
def test_mixed_main_cases_require_combining_public_clues(key: str) -> None:
    puzzle = load_puzzle(SOURCE / "puzzles" / key)
    assert all(c.clue.type != ClueType.FACT for c in puzzle.characters)
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    engine = GameEngine(puzzle, agent.verify_verdict)
    initial = engine.get_public_state()
    hint, support = find_clue_hint(initial, agent)
    assert len(support) == 3
    assert engine.get_public_state() == initial
    while any(c.status is None for c in engine.get_public_state().characters):
        state = engine.get_public_state()
        result = agent.classify_all(state)
        forced = [
            (cell, value)
            for cell, value in result.classifications.items()
            if value != Classification.UNKNOWN
        ]
        assert len(forced) == 1
        cell, value = forced[0]
        assert engine.submit_verdict(
            cell, Status(value.value), expected_token=state.token
        ).outcome == (VerdictOutcome.ACCEPTED)


@pytest.mark.parametrize("size", [3, 4, 5])
def test_public_openings_vary_logic_geometry_and_verdicts(size: int) -> None:
    types, regions, profiles, supports, verdicts = set(), set(), set(), set(), set()
    for seed in range(20):
        puzzle = generate_puzzle(size, seed)
        agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
        initial = GameEngine(puzzle, agent.verify_verdict).get_public_state()
        visible = [c.clue for c in initial.characters if c.clue is not None]
        types.update(clue.type for clue in visible)
        regions.update(clue.region.kind.value for clue in visible if clue.region)
        profiles.add(
            tuple(
                sorted(
                    (clue.type.value, clue.region.kind.value if clue.region else "BINARY")
                    for clue in visible
                )
            )
        )
        hint, support = find_clue_hint(initial, agent)
        supports.add(len(support))
        verdicts.add(hint.status)
        assert {c.status for c in initial.characters if c.status} == {
            Status.CRIMINAL,
            Status.INNOCENT,
        }
    assert {
        ClueType.SAME,
        ClueType.DIFFERENT,
        ClueType.EXACTLY,
        ClueType.EVEN,
        ClueType.ODD,
        ClueType.AT_LEAST,
        ClueType.AT_MOST,
    } <= types
    assert {"ROW", "COLUMN", "NEIGHBORS", "COMMON_NEIGHBORS"} <= regions
    assert len(profiles) >= 8
    assert {1, 3, 4} <= supports
    assert verdicts == {Status.CRIMINAL, Status.INNOCENT}


def test_new_generator_preserves_legacy_files_and_progress(tmp_path: Path) -> None:
    legacy_key = "generated/generated_3x3_seed_7.json"
    old = tmp_path / "generated_3x3_seed_7.json"
    old.write_text("Legacy file must remain untouched.", encoding="utf-8")
    store = ProgressStore(tmp_path / "progress.json")
    store.save(legacy_key, {"moves": [["A1", "CRIMINAL"]], "completed": False})
    new = write_generated_puzzle(3, 7, tmp_path)
    assert new.name == "generated_v2_3x3_seed_7.json"
    assert old.read_text(encoding="utf-8") == "Legacy file must remain untouched."
    new_key = f"generated/{new.name}"
    store.save(new_key, {"moves": [], "completed": False})
    reloaded = ProgressStore(store.path)
    assert len(reloaded.data["levels"]) == 2
    assert reloaded.data["levels"][legacy_key]["moves"] == [["A1", "CRIMINAL"]]
    assert "v2" not in level_for_key(legacy_key).title
    assert "v2" in level_for_key(new_key).title
