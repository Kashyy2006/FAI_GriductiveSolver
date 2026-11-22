"""Acceptance of the distributed boards using the production verifier and solver."""

from pathlib import Path

import pytest

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.models import SolveOutcome, UniquenessOutcome, VerdictOutcome
from game.puzzle_loader import load_puzzle
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver
from solver.uniqueness import check_uniqueness

PUZZLES = Path(__file__).resolve().parents[1] / "puzzles"


@pytest.mark.parametrize("path", sorted(PUZZLES.glob("*x*/*.json")), ids=lambda p: p.stem)
def test_catalog_solution_and_progress(path: Path) -> None:
    puzzle = load_puzzle(path)
    encoder, solver = CNFEncoder(), DPLLSolver()
    agent = DeductiveAgent(encoder, solver)
    engine = GameEngine(puzzle, agent.verify_verdict)
    unique = check_uniqueness(puzzle, encoder, solver)
    run = agent.auto_solve(engine)
    if puzzle.puzzle_id == "demo_3x3_stuck":
        assert unique.outcome == UniquenessOutcome.MULTIPLE
        assert run.outcome == SolveOutcome.STUCK
        assert len(run.steps) == 1
        return
    answer = {c.id: c.hidden_status for c in puzzle.characters}
    assert unique.outcome == UniquenessOutcome.UNIQUE
    assert unique.primary_models == (answer,)
    assert run.outcome == SolveOutcome.SOLVED
    assert {c.id: c.status for c in run.final_state.characters} == answer
    assert len(run.steps) == puzzle.size**2 - len(puzzle.initially_revealed)


def test_cross_size_load_rejects_previous_proof_and_restart_restores_two_cards() -> None:
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    engine = GameEngine(load_puzzle(PUZZLES / "3x3/museum_shift.json"), agent.verify_verdict)
    old = engine.get_public_state()
    hint = agent.next_hint(old)
    board = engine.load(load_puzzle(PUZZLES / "4x4/night_market.json"))
    rejected = engine.submit_verdict(hint.character_id, hint.status, expected_token=old.token)
    assert rejected.outcome == VerdictOutcome.STALE_STATE
    assert rejected.revealed_clue is None
    assert rejected.state == engine.get_public_state() == board
    forced = agent.next_hint(board)
    accepted = engine.submit_verdict(forced.character_id, forced.status, expected_token=board.token)
    assert accepted.outcome == VerdictOutcome.ACCEPTED
    assert [a.id for a, b in zip(accepted.state.characters, board.characters) if a != b] == [
        forced.character_id
    ]
    reset = engine.restart()
    assert reset.characters == board.characters
    assert {c.id for c in reset.characters if c.clue} == {"A1", "D4"}
    assert reset.token.version == 0
    assert len({s.token.session_id for s in (old, board, reset)}) == 3
