"""TV1 state, privacy, validation and deterministic concurrency regressions."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path
from threading import Barrier, Event

import pytest

from game.engine import GameEngine
from game.models import (
    ContractError,
    PuzzleValidationError,
    SolutionMismatchError,
    SolverTimeout,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictProof,
)
from game.puzzle_loader import load_puzzle

SOURCE = Path(__file__).resolve().parents[1]


@pytest.fixture
def puzzle():
    return load_puzzle(SOURCE / "puzzles/3x3/example_01.json")


def accept(state, character_id, status):
    """A test double, deliberately not a solver or production verifier."""
    return VerdictProof(state.token, character_id, status, VerdictOutcome.ACCEPTED, ())


def test_initial_snapshot_is_private_and_row_major(puzzle):
    calls = []
    engine = GameEngine(puzzle, lambda *args: calls.append(args))
    state = engine.get_public_state()
    assert state.token.version == 0
    assert [(c.row, c.col) for c in state.characters] == sorted(
        (c.row, c.col) for c in state.characters
    )
    assert "hidden_status" not in json.dumps(asdict(state))
    for public, private in zip(state.characters, puzzle.characters, strict=True):
        if public.id in puzzle.initially_revealed:
            assert public.status == private.hidden_status and public.clue == private.clue
            assert public.clue is not private.clue
        else:
            assert public.status is None and public.clue is None
    assert calls == []


def test_accept_reveals_exactly_one_card_and_keeps_old_snapshot(puzzle):
    calls = []

    def verifier(state, character_id, status):
        calls.append(state)
        assert state.characters[1].clue is None
        return accept(state, character_id, status)

    engine = GameEngine(puzzle, verifier)
    before = engine.get_public_state()
    result = engine.submit_verdict("B1", Status.INNOCENT, expected_token=before.token)
    assert result.outcome == VerdictOutcome.ACCEPTED
    assert result.state.token == StateToken(before.token.session_id, 1)
    assert result.revealed_clue == puzzle.characters[1].clue
    assert result.state.characters[1].status == Status.INNOCENT
    assert sum(c.clue is not None for c in result.state.characters) == 2
    assert before.characters[1].clue is None and calls == [before]
    again = engine.submit_verdict("B1", Status.INNOCENT, expected_token=result.state.token)
    assert again.outcome == VerdictOutcome.ALREADY_REVEALED
    assert again.proof is None and again.revealed_clue is None and len(calls) == 1


@pytest.mark.parametrize(
    "outcome",
    [
        VerdictOutcome.NOT_PROVABLE,
        VerdictOutcome.CONTRADICTED,
        VerdictOutcome.INCONSISTENT,
    ],
)
def test_rejection_never_changes_state(puzzle, outcome):
    def verifier(state, character_id, status):
        return replace(accept(state, character_id, status), outcome=outcome)

    engine = GameEngine(puzzle, verifier)
    before = engine.get_public_state()
    result = engine.submit_verdict("B1", Status.INNOCENT, expected_token=before.token)
    assert result.outcome == outcome
    assert result.state == before == engine.get_public_state()
    assert result.revealed_clue is None


@pytest.mark.parametrize("operation", ["restart", "load"])
def test_new_sessions_reject_old_tokens(puzzle, operation):
    engine = GameEngine(puzzle, accept)
    initial = engine.get_public_state()
    accepted = engine.submit_verdict("B1", Status.INNOCENT, expected_token=initial.token)
    current = engine.restart() if operation == "restart" else engine.load(puzzle)
    assert current.token.session_id != initial.token.session_id
    assert current.token.version == 0
    assert current.characters == initial.characters
    for token in (initial.token, accepted.state.token):
        result = engine.submit_verdict("A1", Status.CRIMINAL, expected_token=token)
        assert result.outcome == VerdictOutcome.STALE_STATE
        assert result.proof is None and result.state == current


@pytest.mark.parametrize(
    "change",
    [
        {"character_id": "C1"},
        {"requested_status": Status.CRIMINAL},
        {"token": StateToken("wrong", 0)},
        {"outcome": VerdictOutcome.STALE_STATE},
        {"outcome": "ACCEPTED"},
    ],
)
def test_mismatched_proof_cannot_reveal(puzzle, change):
    engine = GameEngine(puzzle, lambda *args: replace(accept(*args), **change))
    before = engine.get_public_state()
    with pytest.raises(ContractError):
        engine.submit_verdict("B1", Status.INNOCENT, expected_token=before.token)
    assert engine.get_public_state() == before


@pytest.mark.parametrize("value", [None, True, "ACCEPTED"])
def test_non_proof_is_rejected(puzzle, value):
    engine = GameEngine(puzzle, lambda *args: value)
    before = engine.get_public_state()
    with pytest.raises(ContractError):
        engine.submit_verdict("B1", Status.INNOCENT, expected_token=before.token)
    assert engine.get_public_state() == before


def test_hidden_mismatch_is_error_without_reveal(puzzle):
    engine = GameEngine(puzzle, accept)
    before = engine.get_public_state()
    with pytest.raises(SolutionMismatchError):
        engine.submit_verdict("B1", Status.CRIMINAL, expected_token=before.token)
    assert engine.get_public_state() == before


def test_timeout_propagates_without_mutation(puzzle):
    def verifier(*args):
        raise SolverTimeout("test deadline")

    engine = GameEngine(puzzle, verifier)
    before = engine.get_public_state()
    with pytest.raises(SolverTimeout):
        engine.submit_verdict("B1", Status.INNOCENT, expected_token=before.token)
    assert engine.get_public_state() == before


@pytest.mark.parametrize(
    "character_id,status",
    [("Z9", Status.CRIMINAL), ([], Status.CRIMINAL), ("B1", "INNOCENT"), ("B1", True)],
)
def test_invalid_runtime_inputs(puzzle, character_id, status):
    engine = GameEngine(puzzle, accept)
    before = engine.get_public_state()
    with pytest.raises(ContractError):
        engine.submit_verdict(character_id, status, expected_token=before.token)
    assert engine.get_public_state() == before


def test_bad_load_preserves_existing_game(puzzle):
    engine = GameEngine(puzzle, accept)
    before = engine.get_public_state()
    with pytest.raises(PuzzleValidationError):
        engine.load(replace(puzzle, characters=puzzle.characters[:-1]))
    assert engine.get_public_state() == before
    with pytest.raises(ContractError):
        engine.load(None)
    assert engine.get_public_state() == before


@pytest.mark.parametrize("operation", ["restart", "load"])
def test_reset_during_verification_does_not_block_and_discards_proof(puzzle, operation):
    entered, release = Event(), Event()

    def verifier(*args):
        entered.set()
        assert release.wait(5)
        return accept(*args)

    engine = GameEngine(puzzle, verifier)
    before = engine.get_public_state()
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(
            engine.submit_verdict, "B1", Status.INNOCENT, expected_token=before.token
        )
        try:
            assert entered.wait(5)
            reset = pool.submit(
                engine.restart if operation == "restart" else engine.load,
                *(() if operation == "restart" else (puzzle,)),
            )
            current = reset.result(timeout=2)
        finally:
            release.set()
        result = pending.result(timeout=5)
    assert result.outcome == VerdictOutcome.STALE_STATE
    assert result.state == current == engine.get_public_state()
    assert result.revealed_clue is None


def test_two_concurrent_proofs_only_commit_once(puzzle):
    barrier = Barrier(2)

    def verifier(*args):
        barrier.wait(timeout=5)
        return accept(*args)

    engine = GameEngine(puzzle, verifier)
    token = engine.get_public_state().token
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(engine.submit_verdict, "B1", Status.INNOCENT, expected_token=token)
            for _ in range(2)
        ]
        results = [future.result(timeout=5) for future in futures]
    assert {r.outcome for r in results} == {VerdictOutcome.ACCEPTED, VerdictOutcome.STALE_STATE}
    assert engine.get_public_state().token.version == 1


def test_four_by_four_load(puzzle):
    engine = GameEngine(puzzle, accept)
    old = engine.get_public_state().token
    state = engine.load(load_puzzle(SOURCE / "puzzles/4x4/example_01.json"))
    assert state.size == 4 and len(state.characters) == 16
    assert state.token.session_id != old.session_id and state.token.version == 0


@pytest.mark.parametrize(
    "token", [None, "token", StateToken("", 0), StateToken("x", True), StateToken("x", -1)]
)
def test_invalid_token_is_contract_error(puzzle, token):
    engine = GameEngine(puzzle, accept)
    before = engine.get_public_state()
    with pytest.raises(ContractError):
        engine.submit_verdict("B1", Status.INNOCENT, expected_token=token)
    assert engine.get_public_state() == before


def test_constructor_requires_verifier(puzzle):
    with pytest.raises(ContractError):
        GameEngine(puzzle, None)


def test_mutable_containers_in_caller_model_are_detached(puzzle):
    characters = list(puzzle.characters)
    initial = list(puzzle.initially_revealed)
    engine = GameEngine(replace(puzzle, characters=characters, initially_revealed=initial), accept)
    before = engine.get_public_state()
    characters.clear()
    initial.append("B1")
    assert engine.get_public_state() == before
    assert engine.restart().characters == before.characters


def test_false_clue_cannot_replace_current_game(puzzle):
    engine = GameEngine(puzzle, accept)
    before = engine.get_public_state()
    first = puzzle.characters[0]
    bad = replace(first, clue=replace(first.clue, status=Status.CRIMINAL))
    with pytest.raises(PuzzleValidationError):
        engine.load(replace(puzzle, characters=(bad, *puzzle.characters[1:])))
    assert engine.get_public_state() == before
