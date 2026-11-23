"""REMARK is public narrative with no propositional or uniqueness constraint."""

import json
from copy import deepcopy
from dataclasses import replace
from itertools import product
from pathlib import Path

import pytest

from agent.agent import DeductiveAgent
from agent.trace import save_trace
from game.engine import GameEngine
from game.models import Clue, ClueType, PuzzleValidationError, SolveOutcome, Status
from game.puzzle_loader import load_puzzle, puzzle_from_dict
from logic.clue_evaluator import evaluate_clue
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver
from solver.uniqueness import check_uniqueness

SOURCE = Path(__file__).resolve().parents[1]


def test_remark_cannot_force_a_verdict_or_reduce_full_clue_models() -> None:
    puzzle = load_puzzle(SOURCE / "puzzles/3x3/demo_forced_unknown.json")
    puzzle = replace(
        puzzle,
        characters=tuple(
            replace(c, clue=Clue(c.clue.id, ClueType.REMARK, text="A quiet evening."))
            for c in puzzle.characters
        ),
    )
    encoder, solver = CNFEncoder(), DPLLSolver()
    agent = DeductiveAgent(encoder, solver)
    engine = GameEngine(puzzle, agent.verify_verdict)
    state = engine.get_public_state()
    before = deepcopy(state)
    assert encoder.encode(state).cnf == [[1]]
    assert encoder.encode(state).active_clue_ids == ()
    # The evaluator treats narrative as True under every assignment, including
    # assignments that differ from both the public units and private solution.
    for values in product(tuple(Status), repeat=9):
        assignment = dict(zip((c.id for c in state.characters), values))
        assert evaluate_clue(state.characters[0].clue, assignment, state)
    hint = agent.next_hint(state)
    assert hint.character_id is hint.status is None and hint.active_clue_ids == ()
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.STUCK and result.steps == ()
    assert engine.get_public_state() == before
    unique = check_uniqueness(puzzle, encoder, solver)
    assert unique.outcome.value == "MULTIPLE"


def test_revealed_remark_keeps_utf8_text_in_step_trace_without_becoming_active(
    tmp_path: Path,
) -> None:
    puzzle = load_puzzle(SOURCE / "puzzles/3x3/demo_forced_unknown.json")
    text = "Quiet evening at the café."
    last = replace(puzzle.characters[-1], clue=Clue("last_remark", ClueType.REMARK, text=text))
    puzzle = replace(puzzle, characters=puzzle.characters[:-1] + (last,))
    encoder, solver = CNFEncoder(), DPLLSolver()
    agent = DeductiveAgent(encoder, solver)
    engine = GameEngine(puzzle, agent.verify_verdict)
    assert engine.get_public_state().characters[-1].clue is None
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.SOLVED and len(result.steps) == 8
    assert len(result.queries) == 105
    assert result.steps[-1].newly_revealed_clue == last.clue
    assert all("last_remark" not in step.active_clue_ids for step in result.steps)
    assert "last_remark" not in encoder.encode(result.final_state).active_clue_ids
    path = tmp_path / "trace.json"
    save_trace(result.steps, path)
    exported = json.loads(path.read_text(encoding="utf-8"))
    assert exported[-1]["newly_revealed_clue"]["type"] == "REMARK"
    assert exported[-1]["newly_revealed_clue"]["text"] == text


@pytest.mark.parametrize("fields", [{"text": ""}, {"text": " \t"}, {"text": "Note", "k": 0}])
def test_loader_rejects_blank_or_logically_parameterized_remark(fields: dict[str, object]) -> None:
    data = json.loads((SOURCE / "puzzles/3x3/demo_forced_unknown.json").read_text(encoding="utf-8"))
    data["characters"][0]["clue"] = {"id": "bad_remark", "type": "REMARK", **fields}
    with pytest.raises(PuzzleValidationError):
        puzzle_from_dict(data)
