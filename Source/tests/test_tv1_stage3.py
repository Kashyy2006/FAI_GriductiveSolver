"""TV1 acceptance scenarios over the production Engine, Agent, CNF and DPLL."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path
from threading import Event

import pytest

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.models import Classification, PuzzleValidationError, SolveOutcome, Status, VerdictOutcome
from game.puzzle_loader import load_puzzle
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver

ROOT = Path(__file__).resolve().parents[1]


def build(name: str = "forced_unknown") -> tuple[GameEngine, DeductiveAgent]:
    """Compose real modules without exposing the private puzzle to the Agent."""
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    puzzle = load_puzzle(ROOT / f"puzzles/3x3/demo_{name}.json")
    return GameEngine(puzzle, agent.verify_verdict), agent


def test_demo_manual_reveal_and_proof_ownership() -> None:
    engine, agent = build()
    before = engine.get_public_state()
    classified = agent.classify_all(before)
    assert classified.classifications["B1"] == Classification.INNOCENT
    assert classified.classifications["C1"] == Classification.UNKNOWN
    assert agent.next_hint(before).character_id == "B1"
    assert engine.get_public_state() == before
    for cell, status, outcome in [
        ("C1", Status.CRIMINAL, VerdictOutcome.NOT_PROVABLE),
        ("C1", Status.INNOCENT, VerdictOutcome.NOT_PROVABLE),
        ("B1", Status.CRIMINAL, VerdictOutcome.CONTRADICTED),
    ]:
        receipt = engine.submit_verdict(cell, status, expected_token=before.token)
        assert receipt.outcome == outcome
        assert receipt.state == before == engine.get_public_state()
        assert receipt.revealed_clue is None
    proofs = []

    def verify(state, cell, status):
        proof = agent.verify_verdict(state, cell, status)
        proofs.append(proof)
        return proof

    # Use the public constructor to observe receipt copying with a real verifier.
    engine = GameEngine(load_puzzle(ROOT / "puzzles/3x3/demo_forced_unknown.json"), verify)
    before = engine.get_public_state()
    receipt = engine.submit_verdict("B1", Status.INNOCENT, expected_token=before.token)
    assert receipt.outcome == VerdictOutcome.ACCEPTED
    assert [a.id for a, b in zip(before.characters, receipt.state.characters) if a != b] == ["B1"]
    assert receipt.proof == proofs[0] and receipt.proof is not proofs[0]
    assert receipt.proof.queries == proofs[0].queries
    assert receipt.proof.queries[0] is not proofs[0].queries[0]
    assert "hidden_status" not in str(asdict(receipt.state))
    assert before.characters[1].clue is None
    assert agent.classify_all(receipt.state).classifications["C1"] == Classification.CRIMINAL
    assert (
        engine.submit_verdict("C1", Status.CRIMINAL, expected_token=before.token).outcome
        == VerdictOutcome.STALE_STATE
    )


@pytest.mark.parametrize(
    "name,outcome,steps",
    [("forced_unknown", SolveOutcome.SOLVED, 8), ("stuck", SolveOutcome.STUCK, 1)],
)
def test_demo_endpoints(name: str, outcome: SolveOutcome, steps: int) -> None:
    engine, agent = build(name)
    result = agent.auto_solve(engine)
    assert result.outcome == outcome and len(result.steps) == steps
    assert result.final_state.token.version == steps
    if outcome == SolveOutcome.STUCK:
        assert all(
            v == Classification.UNKNOWN
            for v in agent.classify_all(result.final_state).classifications.values()
        )


@pytest.mark.parametrize("operation", ["load", "restart"])
def test_real_proof_in_flight_cannot_commit_after_reset(operation: str) -> None:
    entered, release = Event(), Event()
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())

    def verify(state, cell, status):
        proof = agent.verify_verdict(state, cell, status)
        entered.set()
        assert release.wait(5)
        return proof

    puzzle = load_puzzle(ROOT / "puzzles/3x3/demo_forced_unknown.json")
    engine = GameEngine(puzzle, verify)
    before = engine.get_public_state()
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(
            engine.submit_verdict, "B1", Status.INNOCENT, expected_token=before.token
        )
        try:
            assert entered.wait(5)
            reset = (
                pool.submit(engine.restart)
                if operation == "restart"
                else pool.submit(engine.load, load_puzzle(ROOT / "puzzles/3x3/demo_stuck.json"))
            )
            current = reset.result(timeout=2)
        finally:
            release.set()
        receipt = pending.result(timeout=5)
    assert receipt.outcome == VerdictOutcome.STALE_STATE
    assert receipt.revealed_clue is None
    assert receipt.proof.token == before.token
    assert receipt.state == current == engine.get_public_state()
    assert current.token.session_id != before.token.session_id
    assert current.token.version == 0
    assert current.characters[1].clue is None


def test_invalid_load_preserves_progress_and_restart_clears_it() -> None:
    engine, agent = build()
    before = engine.get_public_state()
    accepted = engine.submit_verdict("B1", Status.INNOCENT, expected_token=before.token)
    puzzle = load_puzzle(ROOT / "puzzles/3x3/demo_stuck.json")
    with pytest.raises(PuzzleValidationError):
        engine.load(replace(puzzle, characters=puzzle.characters[:-1]))
    assert engine.get_public_state() == accepted.state
    restarted = engine.restart()
    assert restarted.characters == before.characters
    assert restarted.token.session_id != before.token.session_id
