"""Benchmark accounting with real Agent/DPLL and explicitly test-only Engine fakes."""

import csv
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from tv3_helpers import FactEncoder, PublicTestEngine, make_puzzle

from experiments import benchmark
from experiments.make_suite import create_suite
from game.models import CNF, ContractError, SATResult, SolverTimeout, UniquenessOutcome
from game.puzzle_loader import load_puzzle
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver
from solver.uniqueness import check_uniqueness


@pytest.fixture
def suite(tmp_path: Path) -> tuple[Path, ...]:
    return create_suite(tmp_path / "puzzles")


def test_generated_suite_is_valid_reproducible_and_unique_with_real_encoder(
    suite: tuple[Path, ...], tmp_path: Path
) -> None:
    assert len(suite) == 6
    before = [path.read_bytes() for path in suite]
    assert create_suite(tmp_path / "puzzles") == suite
    assert [path.read_bytes() for path in suite] == before
    for path in suite:
        puzzle = load_puzzle(path)
        assert (
            check_uniqueness(puzzle, CNFEncoder(), DPLLSolver()).outcome == UniquenessOutcome.UNIQUE
        )


def test_progressive_measurements_include_real_verifier_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(benchmark, "CNFEncoder", FactEncoder)
    monkeypatch.setattr(benchmark, "GameEngine", PublicTestEngine)
    row = benchmark._run_case(make_puzzle(), "solve", 5.0)
    assert row["outcome"] == "SOLVED"
    assert row["deduction_steps"] == 8
    assert row["sat_calls"] == sum(1 + 2 * remaining + 3 for remaining in range(8, 0, -1)) + 1
    assert row["clauses_initial"] == 2
    assert row["clauses_final"] == row["clauses_max"] == 18
    assert row["auxiliary_count_max"] == 0
    assert row["failed_sat_calls"] == 0
    assert row["metrics_partial"] is False


def test_full_clue_unique_does_not_imply_progressive_solved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(benchmark, "GameEngine", PublicTestEngine)
    puzzle = make_puzzle(self_facts=True)
    assert benchmark._run_case(puzzle, "solve", 5.0)["outcome"] == "STUCK"
    row = benchmark._run_case(puzzle, "uniqueness", 5.0)
    assert row["outcome"] == "UNIQUE"
    assert row["sat_calls"] == 2
    assert row["clauses_initial"] == 9
    assert row["clauses_final"] == row["clauses_max"] == 10


def test_failed_sat_call_and_prior_reveals_are_retained(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(benchmark, "CNFEncoder", FactEncoder)
    monkeypatch.setattr(benchmark, "GameEngine", PublicTestEngine)

    class FailingSolver(DPLLSolver):
        def __init__(self) -> None:
            self.calls = 0

        def solve(
            self,
            cnf: CNF,
            variables: Sequence[int],
            assumptions: Sequence[int] = (),
            *,
            timeout_seconds: float | None = None,
        ) -> SATResult:
            self.calls += 1
            if self.calls == 21:
                raise SolverTimeout("test deadline after the first reveal")
            return super().solve(cnf, variables, assumptions, timeout_seconds=timeout_seconds)

    monkeypatch.setattr(benchmark, "DPLLSolver", FailingSolver)
    row = benchmark._run_case(make_puzzle(), "solve", 5.0)
    assert row["outcome"] == "TIMEOUT"
    assert row["sat_calls"] == 21 and row["failed_sat_calls"] == 1
    assert row["deduction_steps"] == 1
    assert row["metrics_partial"] is True
    assert "SolverTimeout" in row["error"]


def test_unimplemented_dependency_is_an_error_row_not_solved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MissingEngine:
        def __init__(self, *args: Any) -> None:
            raise NotImplementedError("test missing Engine")

    monkeypatch.setattr(benchmark, "GameEngine", MissingEngine)
    row = benchmark._run_case(make_puzzle(), "solve", 5.0)
    assert row["outcome"] == "ERROR"
    assert row["clauses_initial"] == ""
    assert row["sat_calls"] == 0
    assert "NotImplementedError" in row["error"]


def test_export_retains_malformed_inputs_repeats_and_environment(
    suite: tuple[Path, ...], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(benchmark, "GameEngine", PublicTestEngine)
    broken = suite[0].parent / "invalid.json"
    broken.write_text("{", encoding="utf-8")
    output = tmp_path / "results"
    rows = benchmark.run_benchmark([suite[0].parent], output, repeats=2, charts=False)
    assert len(rows) == 7 * 2 * 2
    bad = [row for row in rows if row["puzzle_id"] == "invalid"]
    assert len(bad) == 4 and all(row["outcome"] == "ERROR" for row in bad)
    with (output / "benchmark.csv").open(encoding="utf-8", newline="") as stream:
        exported = list(csv.DictReader(stream))
    assert len(exported) == len(rows)
    metadata = json.loads((output / "environment.json").read_text(encoding="utf-8"))
    assert len(metadata["puzzles"]) == 7
    assert metadata["repeats"] == 2
    assert metadata["packages"]["pytest"] == "8.3.5"
    text = (output / "summary.md").read_text(encoding="utf-8")
    assert "ERROR" in text and "STUCK" in text and "SOLVED" in text
    for path in (output / "benchmark.csv", output / "environment.json", output / "summary.md"):
        assert "hidden_status" not in path.read_text(encoding="utf-8")


def test_chart_includes_failures(tmp_path: Path) -> None:
    from PIL import Image

    rows = [
        {
            "puzzle_id": "case",
            "mode": "solve",
            "repeat": 1,
            "outcome": "TIMEOUT",
            "runtime_seconds": 0.01,
            "sat_calls": 3,
        }
    ]
    output = tmp_path / "charts" / "benchmark.png"
    benchmark._plot(rows, output)
    with Image.open(output) as image:
        assert image.width > 500 and image.height > 300


@pytest.mark.parametrize(
    "kwargs", [{"repeats": 0}, {"repeats": True}, {"mode": "invalid"}, {"timeout_seconds": -1}]
)
def test_invalid_configuration_is_rejected(
    suite: tuple[Path, ...], tmp_path: Path, kwargs: dict[str, Any]
) -> None:
    with pytest.raises(ContractError):
        benchmark.run_benchmark(suite, tmp_path / "results", charts=False, **kwargs)


def test_empty_or_missing_inputs_are_reported(tmp_path: Path) -> None:
    for paths in ([tmp_path], [tmp_path / "missing.json"]):
        with pytest.raises(ContractError):
            benchmark.run_benchmark(paths, tmp_path / "results", charts=False)


def test_exception_payloads_cannot_export_unrevealed_data(monkeypatch: pytest.MonkeyPatch) -> None:
    class PrivateFailure:
        def __init__(self, *args: object) -> None:
            raise RuntimeError("PRIVATE_UNREVEALED_CLUE_AND_ASSIGNMENT")

    monkeypatch.setattr(benchmark, "GameEngine", PrivateFailure)
    row = benchmark._run_case(make_puzzle(), "solve", 5.0)
    assert row["outcome"] == "ERROR"
    assert "RuntimeError" in row["error"]
    assert "PRIVATE_UNREVEALED" not in row["error"]


def test_cli_exports_errors_and_returns_nonzero(
    suite: tuple[Path, ...],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MissingEngine:
        def __init__(self, *args: object) -> None:
            raise NotImplementedError("test dependency unavailable")

    output = tmp_path / "results"
    monkeypatch.setattr(benchmark, "GameEngine", MissingEngine)
    monkeypatch.setattr(
        benchmark.sys,
        "argv",
        [
            "benchmark",
            "--puzzles",
            str(suite[0]),
            "--output",
            str(output),
            "--no-charts",
        ],
    )
    with pytest.raises(SystemExit) as caught:
        benchmark.main()
    assert caught.value.code == 1
    with (output / "benchmark.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [row["outcome"] for row in rows] == ["ERROR", "UNIQUE"]
