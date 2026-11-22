"""TV4 stage-4 acceptance: real SAT reasoning, privacy and concurrent run isolation."""

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from threading import Barrier, Lock, get_ident

import pytest

from agent.agent import DeductiveAgent
from game.contracts import PublicEngine
from game.engine import GameEngine
from game.models import (
    CNF,
    AutoSolveResult,
    Character,
    Classification,
    Clue,
    ClueType,
    KBStatus,
    Literal,
    PublicState,
    Puzzle,
    SATResult,
    SATStatus,
    SolveOutcome,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictResult,
)
from game.puzzle_loader import load_puzzle
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver

SOURCE = Path(__file__).resolve().parents[1]


def private_variant(mask: int) -> Puzzle:
    """Change labels/sealed clues while keeping the initial public board identical."""
    cells = []
    for index in range(9):
        row, col = divmod(index, 3)
        cell_id = f"{chr(65 + col)}{row + 1}"
        status = Status.CRIMINAL if index and mask & (1 << (index - 1)) else Status.INNOCENT
        clue = Clue(
            "public_A1" if index == 0 else f"sealed_{mask}_{cell_id}",
            ClueType.FACT,
            person=cell_id,
            status=status,
        )
        cells.append(Character(cell_id, f"Person {index:02d}", "Job", row, col, status, clue))
    return Puzzle("1.0", "privacy_equivalence", 3, tuple(cells), ("A1",))


def public_only(engine: GameEngine) -> PublicEngine:
    """Expose exactly PublicEngine; fail any attempt to inspect private state."""

    class PublicOnly:
        __slots__ = ()

        def get_public_state(self) -> PublicState:
            return engine.get_public_state()

        def submit_verdict(
            self, character_id: str, status: Status, *, expected_token: StateToken
        ) -> VerdictResult:
            return engine.submit_verdict(character_id, status, expected_token=expected_token)

        def __getattr__(self, name: str) -> object:
            raise AssertionError(f"Non-public Engine access: {name}")

    return PublicOnly()


@pytest.mark.parametrize("mask", [1, 85, 170, 255])
def test_private_labels_and_sealed_clues_cannot_change_public_reasoning(mask: int) -> None:
    encoder, solver = CNFEncoder(), DPLLSolver()
    agent = DeductiveAgent(encoder, solver)
    first = GameEngine(private_variant(0), agent.verify_verdict)
    other = GameEngine(private_variant(mask), agent.verify_verdict)
    baseline, changed = first.get_public_state(), other.get_public_state()
    assert replace(baseline, token=changed.token) == changed
    expected = {c.id: Classification.UNKNOWN for c in baseline.characters if c.status is None}
    results = []
    for engine, state in ((first, baseline), (other, changed)):
        before = deepcopy(state)
        encoding = encoder.encode(state)
        assert encoding.active_clue_ids == ("public_A1",)
        assert encoding.cnf == [[-1], [-1]]
        # The solver returns a complete model even though the eight sealed cells
        # are not logically forced. The Agent must not mistake this for a verdict.
        model = solver.solve(encoding.cnf, encoding.primary_variables)
        assert model.status == SATStatus.SAT and len(model.assignment) == 9
        classification = agent.classify_all(state)
        assert classification.kb_status == KBStatus.CONSISTENT
        assert classification.classifications == expected
        hint = agent.next_hint(state)
        assert hint.character_id is None and hint.status is None
        assert hint.active_clue_ids == ("public_A1",)
        for status in Status:
            rejected = engine.submit_verdict("B1", status, expected_token=state.token)
            assert rejected.outcome == VerdictOutcome.NOT_PROVABLE
            assert rejected.revealed_clue is None
            assert engine.get_public_state() == before
        run = agent.auto_solve(public_only(engine))
        assert run.outcome == SolveOutcome.STUCK and run.steps == ()
        assert len(run.queries) == 17
        assert run.final_state == state == before == engine.get_public_state()
        results.append([(q.purpose, q.assumptions, q.result) for q in run.queries])
    assert results[0] == results[1]


def test_real_inconsistent_public_kb_never_classifies_hints_or_submits() -> None:
    """Fault injection into public data; do not bypass Puzzle loader validation."""
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    puzzle = load_puzzle(SOURCE / "puzzles/3x3/example_01.json")
    engine = GameEngine(puzzle, agent.verify_verdict)
    initial = engine.get_public_state()
    a1 = replace(
        initial.characters[0],
        clue=Clue("contradiction", ClueType.FACT, person="B1", status=Status.CRIMINAL),
    )
    b1 = replace(
        initial.characters[1],
        status=Status.INNOCENT,
        clue=Clue("public_B1", ClueType.FACT, person="A1", status=Status.CRIMINAL),
    )
    state = replace(initial, characters=(a1, b1) + initial.characters[2:])
    before = deepcopy(state)
    classified = agent.classify_all(state)
    assert classified.kb_status == KBStatus.INCONSISTENT
    assert classified.classifications == {} and len(classified.queries) == 1
    hint = agent.next_hint(state)
    assert hint.kb_status == KBStatus.INCONSISTENT
    assert hint.character_id is None and hint.status is None
    proof = agent.verify_verdict(state, "C1", Status.CRIMINAL)
    assert proof.outcome == VerdictOutcome.INCONSISTENT and len(proof.queries) == 1

    class InconsistentPublicEngine:
        def get_public_state(self) -> PublicState:
            return state

        def submit_verdict(
            self, character_id: str, status: Status, *, expected_token: StateToken
        ) -> VerdictResult:
            raise AssertionError("An inconsistent KB must not submit any verdict")

    result = agent.auto_solve(InconsistentPublicEngine())
    assert result.outcome == SolveOutcome.INCONSISTENT
    assert result.steps == () and len(result.queries) == 1
    assert result.final_state == state == before
    assert engine.get_public_state() == initial


def test_real_user_cancellation_after_one_reveal_keeps_only_committed_progress() -> None:
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    engine = GameEngine(load_puzzle(SOURCE / "puzzles/3x3/example_01.json"), agent.verify_verdict)
    initial = engine.get_public_state()
    result = agent.auto_solve(
        public_only(engine), should_cancel=lambda: engine.get_public_state().token.version >= 1
    )
    assert result.outcome == SolveOutcome.CANCELLED
    assert len(result.steps) == 1 and len(result.queries) == 20
    assert result.steps[0].token_before == initial.token
    assert result.steps[0].token_after == result.final_state.token
    assert len(result.steps[0].queries) == len(result.queries)
    assert result.final_state.token.version == 1
    assert sum(c.status is not None for c in result.final_state.characters) == 2
    assert result.final_state == engine.get_public_state()
    assert initial.token.version == 0 and initial.characters[1].clue is None


def test_shared_agent_keeps_simultaneous_real_runs_and_query_ledgers_isolated() -> None:
    """Force overlap without sleeps; same Agent/Solver, separate public sessions."""
    barrier, lock = Barrier(2), Lock()
    started: set[int] = set()
    ledger: dict[int, list[tuple[tuple[int, ...], SATResult]]] = {}

    class ConcurrentSolver:
        def __init__(self) -> None:
            self.inner = DPLLSolver()

        def solve(
            self,
            cnf: CNF,
            variables: Sequence[int],
            assumptions: Sequence[Literal] = (),
            *,
            timeout_seconds: float | None = None,
        ) -> SATResult:
            worker = get_ident()
            with lock:
                first_call = worker not in started
                started.add(worker)
            if first_call:
                barrier.wait(timeout=5)
            result = self.inner.solve(cnf, variables, assumptions, timeout_seconds=timeout_seconds)
            with lock:
                ledger.setdefault(worker, []).append((tuple(assumptions), result))
            return result

    agent = DeductiveAgent(CNFEncoder(), ConcurrentSolver())
    puzzle = load_puzzle(SOURCE / "puzzles/3x3/example_01.json")
    engines = [GameEngine(puzzle, agent.verify_verdict) for _ in range(2)]

    def run(engine: GameEngine) -> tuple[int, AutoSolveResult]:
        return get_ident(), agent.auto_solve(public_only(engine))

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, engine) for engine in engines]
        results = [future.result(timeout=10) for future in futures]
    assert len(ledger) == 2
    assert results[0][1].final_state.token.session_id != results[1][1].final_state.token.session_id
    for worker, result in results:
        assert result.outcome == SolveOutcome.SOLVED
        assert len(result.steps) == 8 and len(result.queries) == len(ledger[worker]) == 105
        assert [(q.assumptions, q.result, q.stats) for q in result.queries] == [
            (assumptions, call.status, call.stats) for assumptions, call in ledger[worker]
        ]
        assert all(
            step.token_after.session_id == result.final_state.token.session_id
            for step in result.steps
        )
