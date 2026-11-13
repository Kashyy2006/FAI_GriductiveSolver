"""Phase-3 checks using real Engine, Encoder, Agent and DPLL with a controlled clock."""

import csv
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from agent.agent import DeductiveAgent
from agent.trace import save_trace
from experiments import benchmark, phase3
from game.contracts import CancelCheck, PublicEngine, VerdictVerifier
from game.engine import GameEngine
from game.models import (
    CNF,
    AutoSolveResult,
    Literal,
    PublicState,
    Puzzle,
    SATResult,
    SATStatus,
    SolverTimeout,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictProof,
    VerdictResult,
)
from game.puzzle_loader import load_puzzle
from logic.cnf_encoder import CNFEncoder
from solver import dpll
from solver._timing import _Deadline
from solver.uniqueness import check_uniqueness

SOURCE = Path(__file__).resolve().parents[1]


@dataclass
class _WorkClock:
    now: float = 0.0
    armed: bool = True
    reductions: int = 0
    expired: bool = False


def _expire_during_work(monkeypatch: pytest.MonkeyPatch, *, armed: bool = True) -> _WorkClock:
    """Expire only after the original DPLL reduction has performed real work."""
    clock = _WorkClock(armed=armed)
    original = dpll._reduce
    monkeypatch.setattr("solver._timing.perf_counter", lambda: clock.now)

    def reduce_then_tick(
        clauses: tuple[tuple[int, ...], ...],
        literal: int,
        deadline: _Deadline,
    ) -> tuple[tuple[int, ...], ...]:
        result = original(clauses, literal, deadline)
        clock.reductions += 1
        if clock.armed:
            clock.now = 2.0
            clock.expired = True
            clock.armed = False
        return result

    monkeypatch.setattr(dpll, "_reduce", reduce_then_tick)
    return clock


def _chain(size: int = 3) -> Puzzle:
    return load_puzzle(SOURCE / f"puzzles/{size}x{size}/example_01.json")


@pytest.mark.parametrize(("size", "calls"), [(3, 105), (4, 301)])
def test_real_completed_benchmark_reconciles_the_entire_trace(size: int, calls: int) -> None:
    row = benchmark._run_case(_chain(size), "solve", 10.0)
    assert row["outcome"] == "SOLVED"
    assert row["sat_calls"] == row["trace_query_count"] == calls
    assert row["query_count_matches"] is True
    assert row["deduction_steps"] == size * size - 1
    assert row["metrics_partial"] is False


@pytest.mark.parametrize("mode", ["solve", "uniqueness"])
def test_real_stuck_puzzle_remains_unique_with_matching_queries(mode: str) -> None:
    puzzle = load_puzzle(SOURCE / "experiments/puzzles/synthetic_3x3_stuck_unique.json")
    row = benchmark._run_case(puzzle, mode, 10.0)
    assert row["outcome"] == ("STUCK" if mode == "solve" else "UNIQUE")
    assert row["query_count_matches"] is True
    assert row["trace_query_count"] == row["sat_calls"]
    assert row["deduction_steps"] == 0


@pytest.mark.parametrize("corruption", ["duplicate", "wrong_assumption"])
def test_completed_run_with_corrupted_query_is_an_error(
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    original = DeductiveAgent.auto_solve

    def duplicate_last_query(
        self: DeductiveAgent,
        engine: PublicEngine,
        *,
        should_cancel: CancelCheck | None = None,
    ) -> AutoSolveResult:
        result = original(self, engine, should_cancel=should_cancel)
        if corruption == "duplicate":
            return replace(result, queries=result.queries + result.queries[-1:])
        changed = replace(result.queries[0], assumptions=(999,))
        return replace(result, queries=(changed, *result.queries[1:]))

    monkeypatch.setattr(DeductiveAgent, "auto_solve", duplicate_last_query)
    row = benchmark._run_case(_chain(), "solve", 10.0)
    assert row["outcome"] == "ERROR"
    assert row["sat_calls"] == 105
    assert row["trace_query_count"] == (106 if corruption == "duplicate" else 105)
    assert row["query_count_matches"] is False
    assert "ContractError" in row["error"]


def test_timeout_inside_real_engine_verifier_never_reveals(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = _expire_during_work(monkeypatch)
    solver = benchmark._MeasuredSolver(dpll.DPLLSolver(), _Deadline(1.0))
    agent = DeductiveAgent(CNFEncoder(), solver)
    engine = GameEngine(_chain(), agent.verify_verdict)
    before = engine.get_public_state()
    with pytest.raises(SolverTimeout):
        engine.submit_verdict("B1", Status.INNOCENT, expected_token=before.token)
    assert clock.expired and clock.reductions >= 1
    assert solver.calls == solver.failed_calls == 1
    assert engine.get_public_state() == before


@pytest.mark.parametrize(
    ("when", "calls", "accepted"),
    [("analysis", 1, 0), ("verifier", 18, 0), ("after_reveal", 21, 1)],
)
def test_real_benchmark_timeout_keeps_calls_and_prior_reveals(
    monkeypatch: pytest.MonkeyPatch,
    when: str,
    calls: int,
    accepted: int,
) -> None:
    clock = _expire_during_work(monkeypatch, armed=when == "analysis")
    observed: list[GameEngine] = []

    def engine_factory(puzzle: Puzzle, verifier: VerdictVerifier) -> GameEngine:
        def verify(state: PublicState, cell: str, status: Status) -> VerdictProof:
            if when == "verifier":
                clock.armed = True
            return verifier(state, cell, status)

        engine = GameEngine(puzzle, verify)
        original = engine.submit_verdict

        def submit(cell: str, status: Status, *, expected_token: StateToken) -> VerdictResult:
            result = original(cell, status, expected_token=expected_token)
            if when == "after_reveal" and result.outcome == VerdictOutcome.ACCEPTED:
                clock.armed = True
            return result

        monkeypatch.setattr(engine, "submit_verdict", submit)
        observed.append(engine)
        return engine

    monkeypatch.setattr(benchmark, "GameEngine", engine_factory)
    row = benchmark._run_case(_chain(), "solve", 1.0)
    assert clock.expired and clock.reductions >= 1
    assert row["outcome"] == "TIMEOUT"
    assert row["sat_calls"] == calls and row["failed_sat_calls"] == 1
    assert row["deduction_steps"] == accepted
    assert row["metrics_partial"] is True
    assert row["trace_query_count"] == row["query_count_matches"] == ""
    state = observed[0].get_public_state()
    assert state.token.version == accepted
    assert sum(c.status is not None for c in state.characters) == accepted + 1


def test_second_uniqueness_call_can_timeout_during_real_dpll_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _expire_during_work(monkeypatch, armed=False)

    class ArmAfterFirstCall(dpll.DPLLSolver):
        def __init__(self) -> None:
            self.calls = 0
            self.returned: list[SATStatus] = []

        def solve(
            self,
            cnf: CNF,
            variables: Sequence[int],
            assumptions: Sequence[Literal] = (),
            *,
            timeout_seconds: float | None = None,
        ) -> SATResult:
            self.calls += 1
            result = super().solve(cnf, variables, assumptions, timeout_seconds=timeout_seconds)
            self.returned.append(result.status)
            clock.armed = True
            return result

    solver = ArmAfterFirstCall()
    with pytest.raises(SolverTimeout):
        check_uniqueness(_chain(), CNFEncoder(), solver, timeout_seconds=1.0)
    assert clock.expired and clock.reductions > 1
    assert solver.calls == 2 and solver.returned == [SATStatus.SAT]


def test_real_engine_trace_exports_public_steps_and_matches_the_solver(tmp_path: Path) -> None:
    solver = benchmark._MeasuredSolver(dpll.DPLLSolver(), _Deadline(10.0))
    agent = DeductiveAgent(CNFEncoder(), solver)
    engine = GameEngine(_chain(), agent.verify_verdict)
    result = agent.auto_solve(engine)
    assert len(result.queries) == solver.calls == 105
    assert sum(len(step.queries) for step in result.steps) + 1 == solver.calls
    destination = tmp_path / "trace.json"
    save_trace(result.steps, destination)
    text = destination.read_text(encoding="utf-8")
    rows = json.loads(text)
    assert len(rows) == 8
    assert [row["step"] for row in rows] == list(range(1, 9))
    assert all(row["token_after"]["version"] == row["token_before"]["version"] + 1 for row in rows)
    assert "hidden_status" not in text and "assignment" not in text


def test_phase3_profiles_retain_all_outcomes_and_validate_queries(tmp_path: Path) -> None:
    output = tmp_path / "phase3"
    summary = phase3.run_phase3(output, repeats=1, charts=False)
    assert summary["passed"] is True
    profiles = summary["profiles"]
    assert profiles["normal"]["rows"] == profiles["normal"]["query_matches"] == 18
    assert profiles["errors"]["rows"] == 4
    assert profiles["timeouts"]["rows"] == 18
    assert profiles["timeouts"]["actual_sat_calls"] == 0
    for name, outcome in (("errors", "ERROR"), ("timeouts", "TIMEOUT")):
        with (output / name / "benchmark.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        assert rows and all(row["outcome"] == outcome for row in rows)
        assert all(row["metrics_partial"] == "True" for row in rows)
    assert json.loads((output / "acceptance.json").read_text(encoding="utf-8"))["passed"] is True


def test_phase3_cli_fails_if_normal_runs_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "phase3",
            "--output",
            str(tmp_path / "phase3"),
            "--repeats",
            "1",
            "--timeout",
            "1e-12",
            "--no-charts",
        ],
    )
    with pytest.raises(SystemExit) as caught:
        phase3.main()
    assert caught.value.code == 1
