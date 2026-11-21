"""Stage 4 acceptance tests for DPLL, primary-variable uniqueness, and final benchmarks."""

import csv
import json
import sys
from dataclasses import replace
from itertools import product
from pathlib import Path
from typing import Any

import pytest

from experiments import benchmark, make_stage4_suite, phase4
from game.models import (
    Character,
    SATStatus,
    SolverTimeout,
    Status,
    UniquenessOutcome,
)
from game.puzzle_loader import load_puzzle
from logic.cnf_encoder import CNFEncoder
from solver import dpll
from solver.dpll import DPLLSolver
from solver.uniqueness import check_uniqueness

SOURCE = Path(__file__).resolve().parents[1]


def _parity_cnf(variables: tuple[int, ...], required_parity: int) -> list[list[int]]:
    return [
        [-v if val else v for v, val in zip(variables, values)]
        for values in product((False, True), repeat=len(variables))
        if sum(values) % 2 != required_parity
    ]


def test_dpll_branching_backtracking_and_complete_assignment_on_parity_system() -> None:
    """Verify deep branching, deterministic model, assumptions and UNSAT contradiction."""
    # Overlapping 4-variable parity constraints over 6 variables with 1 unconstrained variable (7).
    # Note: (x1+x2+x3+x4) = 1 and (x2+x3+x4+x5) = 0 imply x1 != x5 (mod 2).
    cnf = (
        _parity_cnf((1, 2, 3, 4), 1)
        + _parity_cnf((2, 3, 4, 5), 0)
        + _parity_cnf((3, 4, 5, 6), 1)
        + [[1, 5], [-1, -5]]  # consistent with x1 != x5
    )
    variables = (1, 2, 3, 4, 5, 6, 7)
    result = DPLLSolver().solve(cnf, variables)
    assert result.status == SATStatus.SAT
    assert result.assignment is not None
    assert set(result.assignment) == set(variables)
    # Free variable 7 is filled with False when clauses are already satisfied.
    assert result.assignment[7] is False
    # Non-unit overlapping parity forces genuine branching before solving.
    assert result.stats.decisions >= 1
    assert all(any(result.assignment[abs(lit)] == (lit > 0) for lit in clause) for clause in cnf)

    # Adding an assumption contradicting x1 == x5 while forcing parity mismatch must backtrack to UNSAT.
    unsat_cnf = _parity_cnf((1, 2, 3, 4), 0) + _parity_cnf((1, 2, 3, 4), 1)
    unsat = DPLLSolver().solve(unsat_cnf, (1, 2, 3, 4), assumptions=(1,))
    assert unsat.status == SATStatus.UNSAT
    assert unsat.assignment is None
    assert unsat.stats.decisions >= 1
    assert unsat.stats.backtracks >= 1


def test_stage4_suite_is_deterministic_valid_unique_and_triggers_branching(tmp_path: Path) -> None:
    paths = make_stage4_suite.create_stage4_suite(tmp_path / "stage4")
    assert len(paths) == 5
    first_bytes = [path.read_bytes() for path in paths]
    assert make_stage4_suite.create_stage4_suite(tmp_path / "stage4") == paths
    assert [path.read_bytes() for path in paths] == first_bytes

    branching_solve_seen = False
    branching_unique_seen = False
    for path in paths:
        puzzle = load_puzzle(path)
        unique_res = check_uniqueness(puzzle, CNFEncoder(), DPLLSolver(), timeout_seconds=10.0)
        assert unique_res.outcome == UniquenessOutcome.UNIQUE
        assert len(unique_res.primary_models) == 1
        assert len(unique_res.queries) == 2

        solve_row = benchmark._run_case(puzzle, "solve", 10.0)
        expected = "STUCK" if "stuck_unique" in puzzle.puzzle_id else "SOLVED"
        assert solve_row["outcome"] == expected
        assert solve_row["query_count_matches"] is True
        if puzzle.puzzle_id == "stage4_4x4_branching_counts":
            assert int(solve_row["decisions"]) > 0
            assert int(solve_row["backtracks"]) > 0
            branching_solve_seen = True
            uniq_row = benchmark._run_case(puzzle, "uniqueness", 10.0)
            assert int(uniq_row["decisions"]) > 0
            assert int(uniq_row["backtracks"]) > 0
            branching_unique_seen = True

    assert branching_solve_seen and branching_unique_seen


def test_uniqueness_never_reads_hidden_status_on_real_extension_puzzles() -> None:
    class GuardedCharacter(Character):
        def __getattribute__(self, name: str) -> Any:
            if name == "hidden_status":
                raise AssertionError("Uniqueness must not read hidden_status")
            return super().__getattribute__(name)

    path = SOURCE / "experiments/puzzles/stage4/stage4_4x4_extensions_parity.json"
    puzzle = load_puzzle(path)
    guarded = replace(
        puzzle,
        characters=tuple(
            GuardedCharacter(c.id, c.name, c.profession, c.row, c.col, Status.CRIMINAL, c.clue)
            for c in puzzle.characters
        ),
    )
    result = check_uniqueness(guarded, CNFEncoder(), DPLLSolver(), timeout_seconds=10.0)
    assert result.outcome == UniquenessOutcome.UNIQUE
    assert len(result.primary_models) == 1


def test_dpll_timeout_mid_branching_never_returns_unsat(monkeypatch: pytest.MonkeyPatch) -> None:
    ticks = {"now": 0.0, "steps": 0}
    original_reduce = dpll._reduce
    monkeypatch.setattr("solver._timing.perf_counter", lambda: ticks["now"])

    def slow_reduce(clauses: Any, literal: int, deadline: Any) -> Any:
        result = original_reduce(clauses, literal, deadline)
        ticks["steps"] += 1
        if ticks["steps"] >= 5:
            ticks["now"] = 2.0
        return result

    monkeypatch.setattr(dpll, "_reduce", slow_reduce)
    unsat_cnf = _parity_cnf((1, 2, 3, 4, 5), 0) + _parity_cnf((1, 2, 3, 4, 5), 1)
    with pytest.raises(SolverTimeout):
        DPLLSolver().solve(unsat_cnf, (1, 2, 3, 4, 5), timeout_seconds=1.0)
    assert ticks["steps"] >= 5


def test_phase4_runner_generates_validated_csv_tables_and_charts(tmp_path: Path) -> None:
    from PIL import Image

    output = tmp_path / "phase4"
    summary = phase4.run_phase4(output, repeats=1, charts=True)
    assert summary["passed"] is True
    profiles = summary["profiles"]
    assert profiles["normal"]["rows"] == profiles["normal"]["query_matches"] == 32
    assert profiles["errors"]["rows"] == 4
    assert profiles["timeouts"]["rows"] == 32

    for name, expected_outcome in (("errors", "ERROR"), ("timeouts", "TIMEOUT")):
        with (output / name / "benchmark.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        assert rows and all(row["outcome"] == expected_outcome for row in rows)
        assert all(row["metrics_partial"] == "True" for row in rows)

    charts_dir = output / "normal" / "charts"
    for filename in (
        "benchmark.png",
        "runtime_by_size_and_phase.png",
        "dpll_work_and_clauses.png",
        "sat_calls_and_outcomes.png",
    ):
        chart_path = charts_dir / filename
        assert chart_path.is_file()
        with Image.open(chart_path) as image:
            assert image.width > 600 and image.height > 300

    combined = (output / "combined_summary.md").read_text(encoding="utf-8")
    assert "stage4_4x4_branching_counts" in combined
    assert "demo_3x3_forced_unknown" in combined
    assert "hidden_status" not in combined
    acceptance = json.loads((output / "acceptance.json").read_text(encoding="utf-8"))
    assert acceptance["passed"] is True


def test_phase4_cli_returns_nonzero_when_normal_times_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "phase4",
            "--output",
            str(tmp_path / "phase4"),
            "--repeats",
            "1",
            "--timeout",
            "1e-12",
            "--no-charts",
        ],
    )
    with pytest.raises(SystemExit) as caught:
        phase4.main()
    assert caught.value.code == 1
