"""Real-stack regressions for proof ownership, SAT accounting, parity and resets."""

from collections.abc import Sequence
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.models import (
    CNF,
    Clue,
    ClueType,
    Literal,
    Puzzle,
    Region,
    RegionType,
    SATResult,
    SATStatus,
    SolveOutcome,
    SolverStats,
    Status,
    VerdictOutcome,
)
from game.puzzle_loader import load_puzzle, puzzle_from_dict
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver

SOURCE = Path(__file__).resolve().parents[1]


class CountingSolver:
    """Count actual calls without using the Agent's nested trace records."""

    def __init__(self, *, constant_stats: bool = False) -> None:
        self.inner = DPLLSolver()
        self.calls = 0
        self.constant_stats = constant_stats

    def solve(
        self,
        cnf: CNF,
        variables: Sequence[int],
        assumptions: Sequence[Literal] = (),
        *,
        timeout_seconds: float | None = None,
    ) -> SATResult:
        self.calls += 1
        result = self.inner.solve(cnf, variables, assumptions, timeout_seconds=timeout_seconds)
        return replace(result, stats=SolverStats(0, 0, 0, 0.0)) if self.constant_stats else result


def chain_puzzle(size: int = 3) -> Puzzle:
    return load_puzzle(SOURCE / f"puzzles/{size}x{size}/example_01.json")


def common_neighbors_parity_puzzle(kind: ClueType) -> Puzzle:
    """Build a 3x3 chain whose B1 parity clue stays hidden until B1 is proved."""
    target = Status.CRIMINAL if kind == ClueType.EVEN else Status.INNOCENT
    statuses = {
        "A1": Status.INNOCENT,
        "B1": Status.CRIMINAL,
        "C1": Status.INNOCENT,
        "A2": Status.INNOCENT,
        "B2": target,
        "C2": Status.INNOCENT,
        "A3": Status.INNOCENT,
        "B3": Status.INNOCENT,
        "C3": Status.INNOCENT,
    }
    clues = {
        "A1": {"id": "clue_A1", "type": "FACT", "person": "B1", "status": "CRIMINAL"},
        "B1": {
            "id": "clue_B1",
            "type": kind.value,
            "region": {"kind": "COMMON_NEIGHBORS", "first": "A1", "second": "C1"},
        },
    }
    for cell_id in ("C1", "A2", "B2", "C2", "A3", "B3", "C3"):
        clues[cell_id] = {
            "id": f"clue_{cell_id}",
            "type": "FACT",
            "person": cell_id,
            "status": statuses[cell_id].value,
        }
    characters = []
    for row in range(3):
        for col in range(3):
            cell_id = f"{chr(65 + col)}{row + 1}"
            characters.append(
                {
                    "id": cell_id,
                    "name": f"Person {row * 3 + col + 1:02d}",
                    "profession": "Detective",
                    "row": row,
                    "col": col,
                    "hidden_status": statuses[cell_id].value,
                    "clue": clues[cell_id],
                }
            )
    return puzzle_from_dict(
        {
            "schema_version": "1.0",
            "puzzle_id": f"common_neighbors_{kind.value.lower()}",
            "size": 3,
            "characters": characters,
            "initially_revealed": ["A1"],
        }
    )


@pytest.mark.parametrize(("size", "expected_calls"), [(3, 105), (4, 301)])
@pytest.mark.parametrize("foreign_verifier", [False, True])
@pytest.mark.parametrize("constant_stats", [False, True])
def test_real_engine_copies_proof_without_double_counting_actual_calls(
    size: int, expected_calls: int, foreign_verifier: bool, constant_stats: bool
) -> None:
    solver = CountingSolver(constant_stats=constant_stats)
    encoder = CNFEncoder()
    agent = DeductiveAgent(encoder, solver)
    verifier = DeductiveAgent(encoder, solver) if foreign_verifier else agent
    engine = GameEngine(chain_puzzle(size), verifier.verify_verdict)
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.SOLVED
    assert len(result.steps) == size * size - 1
    assert len(result.queries) == solver.calls == expected_calls
    assert sum(len(step.queries) for step in result.steps) + 1 == expected_calls
    assert [step.step for step in result.steps] == list(range(1, size * size))
    assert result.queries[-1].purpose == "CONSISTENCY"
    assert (
        len([q for q in result.queries if q.purpose == "CONSISTENCY"]) == 2 * len(result.steps) + 1
    )


@pytest.mark.parametrize("kind", [ClueType.EVEN, ClueType.ODD])
def test_real_parity_clue_reveals_and_solves_without_a_fake_encoder(kind: ClueType) -> None:
    puzzle = chain_puzzle()
    # For ODD, invert both labels and FACT semantics to preserve the real chain.
    if kind == ClueType.ODD:

        def opposite(status: Status) -> Status:
            return Status.INNOCENT if status == Status.CRIMINAL else Status.CRIMINAL

        puzzle = replace(
            puzzle,
            characters=tuple(
                replace(
                    c,
                    hidden_status=opposite(c.hidden_status),
                    clue=replace(c.clue, status=opposite(c.clue.status)),
                )
                for c in puzzle.characters
            ),
        )
    first = puzzle.characters[0]
    puzzle = replace(
        puzzle,
        characters=(
            replace(
                first,
                clue=Clue(
                    "parity_initial", kind, region=Region(RegionType.EXPLICIT, cells=("B1",))
                ),
            ),
        )
        + puzzle.characters[1:],
    )
    solver = CountingSolver()
    agent = DeductiveAgent(CNFEncoder(), solver)
    engine = GameEngine(puzzle, agent.verify_verdict)
    initial = engine.get_public_state()
    hint = agent.next_hint(initial)
    assert hint.character_id == "B1"
    assert hint.status == (Status.INNOCENT if kind == ClueType.EVEN else Status.CRIMINAL)
    calls_before = solver.calls
    result = agent.auto_solve(engine)
    assert result.outcome == SolveOutcome.SOLVED
    assert len(result.queries) == solver.calls - calls_before
    assert result.steps[0].active_clue_ids == ("parity_initial",)
    assert initial.characters[1].status is None
    assert engine.get_public_state().characters[1].status == hint.status


@pytest.mark.parametrize(
    ("kind", "target_status", "opposite_status"),
    [
        (ClueType.EVEN, Status.CRIMINAL, Status.INNOCENT),
        (ClueType.ODD, Status.INNOCENT, Status.CRIMINAL),
    ],
)
def test_hidden_common_neighbors_parity_clue_joins_kb_only_after_reveal(
    kind: ClueType, target_status: Status, opposite_status: Status
) -> None:
    puzzle = common_neighbors_parity_puzzle(kind)
    encoder = CNFEncoder()
    agent = DeductiveAgent(encoder, DPLLSolver())
    engine = GameEngine(puzzle, agent.verify_verdict)
    initial = engine.get_public_state()
    initial_before = deepcopy(initial)
    initial_encoding = encoder.encode(initial)

    assert initial_encoding.active_clue_ids == ("clue_A1",)
    assert initial.characters[1].status is None
    assert initial.characters[1].clue is None

    hint = agent.next_hint(initial)
    assert (hint.character_id, hint.status) == ("B1", Status.CRIMINAL)
    assert hint.active_clue_ids == ("clue_A1",)
    assert initial == initial_before

    unknown = engine.submit_verdict("B2", Status.CRIMINAL, expected_token=initial.token)
    assert unknown.outcome == VerdictOutcome.NOT_PROVABLE
    assert unknown.revealed_clue is None
    assert engine.get_public_state() == initial_before

    contradicted = engine.submit_verdict("B1", Status.INNOCENT, expected_token=initial.token)
    assert contradicted.outcome == VerdictOutcome.CONTRADICTED
    assert engine.get_public_state() == initial_before

    unproved_target = agent.verify_verdict(initial, "B2", target_status)
    assert unproved_target.outcome == VerdictOutcome.NOT_PROVABLE
    target_queries = {
        query.purpose: query.result
        for query in unproved_target.queries
        if query.purpose in ("ASSUME_INNOCENT:B2", "ASSUME_CRIMINAL:B2")
    }
    assert target_queries == {
        "ASSUME_INNOCENT:B2": SATStatus.SAT,
        "ASSUME_CRIMINAL:B2": SATStatus.SAT,
    }

    accepted = engine.submit_verdict("B1", Status.CRIMINAL, expected_token=initial.token)
    assert accepted.outcome == VerdictOutcome.ACCEPTED
    assert accepted.proof is not None
    assert accepted.proof.outcome == VerdictOutcome.ACCEPTED
    assert accepted.revealed_clue is not None
    after = accepted.state
    assert after.token.session_id == initial.token.session_id
    assert after.token.version == initial.token.version + 1
    assert after.characters[1].status == Status.CRIMINAL
    assert after.characters[1].clue == Clue(
        "clue_B1",
        kind,
        region=Region(RegionType.COMMON_NEIGHBORS, first="A1", second="C1"),
    )
    assert engine.get_public_state() == after

    assert initial == initial_before
    assert encoder.encode(initial) == initial_encoding
    after_encoding = encoder.encode(after)
    assert after_encoding.active_clue_ids == ("clue_A1", "clue_B1")
    assert [2] in after_encoding.cnf

    opposite_proof = agent.verify_verdict(after, "B2", opposite_status)
    assert opposite_proof.outcome == VerdictOutcome.CONTRADICTED
    opposite_query = next(
        query
        for query in opposite_proof.queries
        if query.purpose == f"ASSUME_{opposite_status.value}:B2"
    )
    assert opposite_query.result == SATStatus.UNSAT

    forced_proof = agent.verify_verdict(after, "B2", target_status)
    assert forced_proof.outcome == VerdictOutcome.ACCEPTED
    forced_query = next(
        query
        for query in forced_proof.queries
        if query.purpose == f"ASSUME_{target_status.value}:B2"
    )
    assert forced_query.result == SATStatus.SAT

    hint_after = agent.next_hint(after)
    assert (hint_after.character_id, hint_after.status) == ("B2", target_status)
    assert hint_after.active_clue_ids == ("clue_A1", "clue_B1")

    fresh_engine = GameEngine(puzzle, agent.verify_verdict)
    solved = agent.auto_solve(fresh_engine)
    assert solved.outcome == SolveOutcome.STUCK
    assert [step.character_id for step in solved.steps] == ["B1", "B2"]
    assert solved.steps[0].active_clue_ids == ("clue_A1",)
    assert solved.steps[1].active_clue_ids == ("clue_A1", "clue_B1")
    assert solved.steps[0].newly_revealed_clue.id == "clue_B1"
    assert solved.steps[1].newly_revealed_clue.id == "clue_B2"


def test_real_rejection_keeps_state_and_does_not_reveal_then_restart_invalidates_token() -> None:
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    engine = GameEngine(chain_puzzle(), agent.verify_verdict)
    state = engine.get_public_state()
    before = deepcopy(state)
    unknown = engine.submit_verdict("C1", Status.CRIMINAL, expected_token=state.token)
    assert unknown.outcome == VerdictOutcome.NOT_PROVABLE
    assert unknown.revealed_clue is None
    assert engine.get_public_state() == before
    forced = agent.next_hint(state)
    opposite = Status.INNOCENT if forced.status == Status.CRIMINAL else Status.CRIMINAL
    rejected = engine.submit_verdict(forced.character_id, opposite, expected_token=state.token)
    assert rejected.outcome == VerdictOutcome.CONTRADICTED
    assert engine.get_public_state() == before
    restarted = engine.restart()
    assert restarted.token.version == state.token.version
    assert restarted.token.session_id != state.token.session_id
    assert (
        engine.submit_verdict("B1", forced.status, expected_token=state.token).outcome
        == VerdictOutcome.STALE_STATE
    )
