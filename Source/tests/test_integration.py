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
    SolveOutcome,
    SolverStats,
    Status,
    VerdictOutcome,
)
from game.puzzle_loader import load_puzzle
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
