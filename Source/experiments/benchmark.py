"""Benchmark progressive solving and complete-clue uniqueness without a GUI."""

from __future__ import annotations

import argparse
import csv
import hashlib
import inspect
import json
import platform
import sys
from collections import defaultdict
from collections.abc import Sequence
from importlib.metadata import version
from pathlib import Path
from statistics import median
from time import perf_counter

from agent.agent import DeductiveAgent
from game.contracts import Encoder, PublicEngine, SATSolver
from game.engine import GameEngine
from game.models import (
    CNF,
    ContractError,
    EncodingResult,
    Literal,
    PublicState,
    Puzzle,
    SATResult,
    SATStatus,
    SolverStats,
    SolverTimeout,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictResult,
)
from game.puzzle_loader import load_puzzle
from logic.cnf_encoder import CNFEncoder
from solver._timing import _Deadline
from solver.dpll import DPLLSolver
from solver.uniqueness import check_uniqueness

SOURCE = Path(__file__).resolve().parents[1]
FIELDS = (
    "puzzle_id",
    "puzzle_path",
    "mode",
    "repeat",
    "size",
    "outcome",
    "primary_count",
    "auxiliary_count_initial",
    "auxiliary_count_max",
    "auxiliary_count_final",
    "clauses_initial",
    "clauses_max",
    "clauses_final",
    "sat_calls",
    "trace_query_count",
    "query_count_matches",
    "failed_sat_calls",
    "decisions",
    "propagations",
    "backtracks",
    "deduction_steps",
    "runtime_seconds",
    "loader_runtime_seconds",
    "metrics_partial",
    "error",
)


class _MeasuredEncoder:
    def __init__(self, encoder: Encoder, deadline: _Deadline) -> None:
        self.encoder = encoder
        self.deadline = deadline
        self.counts: list[tuple[int, int]] = []

    def encode(self, state: PublicState) -> EncodingResult:
        self.deadline.check()
        result = self.encoder.encode(state)
        self.counts.append((len(result.auxiliary_variables), result.clause_count))
        self.deadline.check()
        return result


class _MeasuredSolver:
    def __init__(self, solver: SATSolver, deadline: _Deadline) -> None:
        self.solver = solver
        self.deadline = deadline
        self.calls = 0
        self.failed_calls = 0
        self.decisions = 0
        self.propagations = 0
        self.backtracks = 0
        self.clause_counts: list[int] = []
        self.completed: list[tuple[tuple[Literal, ...], SATStatus, SolverStats]] = []

    def solve(
        self,
        cnf: CNF,
        variables: Sequence[int],
        assumptions: Sequence[Literal] = (),
        *,
        timeout_seconds: float | None = None,
    ) -> SATResult:
        remaining = self.deadline.remaining()
        budget = timeout_seconds
        if remaining is not None:
            budget = remaining if budget is None else min(budget, remaining)
        self.calls += 1
        self.clause_counts.append(len(cnf))
        try:
            result = self.solver.solve(cnf, variables, assumptions, timeout_seconds=budget)
        except Exception:
            self.failed_calls += 1
            raise
        self.decisions += result.stats.decisions
        self.propagations += result.stats.propagations
        self.backtracks += result.stats.backtracks
        self.completed.append((tuple(assumptions), result.status, result.stats))
        self.deadline.check()
        return result


class _MeasuredEngine:
    def __init__(self, engine: PublicEngine) -> None:
        self.engine = engine
        self.accepted = 0

    def get_public_state(self) -> PublicState:
        return self.engine.get_public_state()

    def submit_verdict(
        self, character_id: str, status: Status, *, expected_token: StateToken
    ) -> VerdictResult:
        result = self.engine.submit_verdict(character_id, status, expected_token=expected_token)
        if result.outcome == VerdictOutcome.ACCEPTED:
            self.accepted += 1
        return result


def _error_description(error: Exception, stage: str) -> str:
    """Describe failures without exporting exception payloads containing private data."""
    if isinstance(error, SolverTimeout):
        reason = "wall-clock deadline exceeded"
    elif isinstance(error, NotImplementedError):
        reason = "backend is not implemented"
    else:
        reason = "operation failed; inspect the backend and input locally"
    return f"{type(error).__name__}: {stage}: {reason}"


def _run_case(puzzle: Puzzle, mode: str, timeout_seconds: float | None) -> dict[str, object]:
    """Record failures and completed statistics even when a run raises."""
    row: dict[str, object] = dict.fromkeys(FIELDS, "")
    row.update(puzzle_id=puzzle.puzzle_id, size=puzzle.size, primary_count=puzzle.size**2)
    started = perf_counter()
    deadline = _Deadline(timeout_seconds)
    encoder = _MeasuredEncoder(CNFEncoder(), deadline)
    solver = _MeasuredSolver(DPLLSolver(), deadline)
    engine: _MeasuredEngine | None = None
    try:
        if mode == "uniqueness":
            result = check_uniqueness(puzzle, encoder, solver, timeout_seconds=deadline.remaining())
            row["outcome"] = result.outcome.value
        else:
            agent = DeductiveAgent(encoder, solver)
            engine = _MeasuredEngine(GameEngine(puzzle, agent.verify_verdict))
            result = agent.auto_solve(engine)
            row["outcome"] = result.outcome.value
        recorded = [(query.assumptions, query.result, query.stats) for query in result.queries]
        row["trace_query_count"] = len(recorded)
        row["query_count_matches"] = len(recorded) == solver.calls and recorded == solver.completed
        if not row["query_count_matches"]:
            raise ContractError("Run queries do not match the actual Solver call sequence")
        deadline.check()
        row["metrics_partial"] = False
    except Exception as error:
        row["outcome"] = "TIMEOUT" if isinstance(error, SolverTimeout) else "ERROR"
        row["error"] = _error_description(error, mode)
        row["metrics_partial"] = True
    finally:
        row.update(
            runtime_seconds=perf_counter() - started,
            sat_calls=solver.calls,
            failed_sat_calls=solver.failed_calls,
            decisions=solver.decisions,
            propagations=solver.propagations,
            backtracks=solver.backtracks,
            deduction_steps=engine.accepted if engine is not None else 0,
        )
        if encoder.counts:
            auxiliary, clauses = zip(*encoder.counts)
            row.update(
                auxiliary_count_initial=auxiliary[0],
                auxiliary_count_max=max(auxiliary),
                auxiliary_count_final=auxiliary[-1],
                clauses_initial=clauses[0],
                clauses_max=max((*clauses, *solver.clause_counts)),
                clauses_final=solver.clause_counts[-1]
                if mode == "uniqueness" and solver.clause_counts
                else clauses[-1],
            )
    return row


def _plot(rows: Sequence[dict[str, object]], destination: Path) -> None:
    """Group repeats by outcome; retain every raw measurement in the CSV."""
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.ticker import MaxNLocator

    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["puzzle_id"]), str(row["mode"]), str(row["outcome"]))].append(row)
    labels = [f"{key[0]} / {key[1]} [{key[2]}; n={len(group)}]" for key, group in grouped.items()]
    colors = ["#b64b48" if key[2] in ("ERROR", "TIMEOUT") else "#377d71" for key in grouped]
    figure, axes = plt.subplots(1, 2, figsize=(16, max(4, len(grouped) * 0.4)), sharey=True)
    positions = list(range(len(grouped)))
    axes[0].barh(
        positions,
        [median(float(r["runtime_seconds"]) for r in group) for group in grouped.values()],
        color=colors,
    )
    axes[1].barh(
        positions,
        [median(int(r["sat_calls"]) for r in group) for group in grouped.values()],
        color=colors,
    )
    axes[0].set_yticks(positions, labels)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Median runtime (seconds)")
    axes[1].set_xlabel("Median actual SAT calls per run (including failed calls)")
    axes[0].set_xlim(left=0)
    axes[1].set_xlim(left=0)
    axes[1].xaxis.set_major_locator(MaxNLocator(integer=True))
    for axis, field, message in (
        (
            axes[0],
            "runtime_seconds",
            "All recorded phase runtimes are zero; see loader time in CSV",
        ),
        (axes[1], "sat_calls", "No SAT calls were started"),
    ):
        if not any(float(row[field]) for row in rows):
            axis.set_xlim(0, 1)
            axis.text(
                0.5, 0.5, message, ha="center", va="center", transform=axis.transAxes, wrap=True
            )
    figure.suptitle(
        "Griductive benchmark: grouped by puzzle, phase and outcome; red = error/timeout"
    )
    figure.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not (destination.parent / "README.md").exists():
        (destination.parent / "README.md").write_text(
            "# Benchmark charts\n\nOwner: TV3. Generated by experiments.benchmark.\n"
            "Medians grouped by puzzle, phase and outcome; all raw rows remain in CSV.\n\n## AI log\n",
            encoding="utf-8",
        )
    figure.savefig(destination, dpi=160)
    plt.close(figure)


def _write_results(
    rows: list[dict[str, object]],
    paths: tuple[Path, ...],
    output: Path,
    timeout_seconds: float | None,
    repeats: int,
    mode: str,
    charts: bool,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    if not (output / "README.md").exists():
        (output / "README.md").write_text(
            "# Benchmark results\n\nOwner: TV3. Generated by experiments.benchmark; all outcomes retained.\n\n## AI log\n",
            encoding="utf-8",
        )
    with (output / "benchmark.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    def fingerprint(path: Path) -> dict[str, object]:
        try:
            return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        except OSError as error:
            return {"path": str(path), "sha256": None, "error": f"{type(error).__name__}: {error}"}

    metadata = {
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "packages": {
            name: version(name) for name in ("pytest", "ruff", "jsonschema", "matplotlib")
        },
        "timeout_seconds_per_phase": timeout_seconds,
        "repeats": repeats,
        "mode": mode,
        "puzzles": [fingerprint(path) for path in paths],
        "backend_sources": {
            name: fingerprint(Path(inspect.getfile(backend)))
            for name, backend in (
                ("encoder", CNFEncoder),
                ("solver", DPLLSolver),
                ("agent", DeductiveAgent),
                ("engine", GameEngine),
            )
        },
        "support_sources": [
            fingerprint(SOURCE / name)
            for name in (
                "game/models.py",
                "game/contracts.py",
                "solver/_timing.py",
                "solver/uniqueness.py",
                "experiments/benchmark.py",
                "experiments/phase3.py",
            )
        ],
        "measurement": {
            "runtime": "Per phase wall time; includes encoding and engine/verifier; excludes loading, GUI and export",
            "sat_calls": "Actual calls, including calls that raise; no summing nested trace queries",
            "query_accounting": "Completed runs compare ordered assumptions/status/stats against the Solver ledger; failed runs leave trace fields unavailable",
            "charts": "Median across repeats, grouped separately by puzzle/phase/outcome; raw rows retained in CSV",
            "partial_metrics": "Counters include completed calls only when a call raises",
            "uniqueness_clauses": "Includes the primary blocking clause in maximum/final counts",
            "deadline": "Cooperative; checked around dependencies and inside DPLL, not a hard process kill",
        },
    }
    (output / "environment.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summary = [
        "# Benchmark observations",
        "",
        "All outcomes, including errors and timeouts, are retained. No hidden labels or clues are exported.",
        "",
        "| Puzzle | Phase | Repeat | Outcome | SAT calls | Trace queries | Match | Steps | Seconds |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        summary.append(
            f"| {row['puzzle_id']} | {row['mode']} | {row['repeat']} | {row['outcome']} | "
            f"{row['sat_calls']} | {row['trace_query_count']} | {row['query_count_matches']} | "
            f"{row['deduction_steps']} | {row['runtime_seconds']:.6f} |"
        )
    failures = [row for row in rows if row["error"]]
    summary.extend(["", "## Limitations", ""])
    if failures:
        summary.append("Failed rows do not establish solver performance or puzzle solvability.")
        summary.extend(f"- {message}" for message in sorted({str(r["error"]) for r in failures}))
    else:
        summary.append(
            "Results apply only to the recorded puzzle set, environment and configuration."
        )
    (output / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    if charts:
        _plot(rows, output / "charts" / "benchmark.png")


def run_benchmark(
    paths: Sequence[Path],
    output: Path,
    *,
    timeout_seconds: float | None = 10.0,
    repeats: int = 1,
    mode: str = "all",
    charts: bool = True,
) -> list[dict[str, object]]:
    """Run the same ordered inputs for both independent phases and export CSV."""
    _Deadline(timeout_seconds)
    if type(repeats) is not int or repeats < 1 or mode not in ("all", "solve", "uniqueness"):
        raise ContractError("Use positive repeats and mode all, solve, or uniqueness")
    files = set()
    for path in paths:
        path = Path(path)
        if path.is_dir():
            files.update(item.resolve() for item in path.rglob("*.json"))
        elif path.is_file():
            files.add(path.resolve())
        else:
            raise ContractError(f"Puzzle path does not exist: {path}")
    ordered = tuple(sorted(files))
    if not ordered:
        raise ContractError("No puzzle JSON files found")
    phases = ("solve", "uniqueness") if mode == "all" else (mode,)
    rows: list[dict[str, object]] = []
    for path in ordered:
        started = perf_counter()
        try:
            puzzle = load_puzzle(path)
            load_error = None
        except Exception as error:
            puzzle, load_error = None, _error_description(error, "load")
        loader_runtime = perf_counter() - started
        for repeat in range(1, repeats + 1):
            for phase in phases:
                if puzzle is not None:
                    row = _run_case(puzzle, phase, timeout_seconds)
                else:
                    row = dict.fromkeys(FIELDS, "")
                    row.update(
                        puzzle_id=path.stem,
                        outcome="ERROR",
                        error=load_error,
                        sat_calls=0,
                        failed_sat_calls=0,
                        decisions=0,
                        propagations=0,
                        backtracks=0,
                        deduction_steps=0,
                        runtime_seconds=0.0,
                        metrics_partial=True,
                    )
                row.update(
                    puzzle_path=str(path),
                    mode=phase,
                    repeat=repeat,
                    loader_runtime_seconds=loader_runtime,
                )
                rows.append(row)
    _write_results(rows, ordered, Path(output), timeout_seconds, repeats, mode, charts)
    return rows


def main() -> None:
    """Run from Source with python -m experiments.benchmark."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--puzzles",
        nargs="+",
        type=Path,
        default=[SOURCE / "puzzles", SOURCE / "experiments" / "puzzles"],
    )
    parser.add_argument("--output", type=Path, default=SOURCE / "experiments" / "results")
    parser.add_argument("--timeout", type=float, default=10.0, help="Seconds per phase; default 10")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--mode", choices=("all", "solve", "uniqueness"), default="all")
    parser.add_argument("--no-charts", action="store_true")
    args = parser.parse_args()
    try:
        rows = run_benchmark(
            args.puzzles,
            args.output,
            timeout_seconds=args.timeout,
            repeats=args.repeats,
            mode=args.mode,
            charts=not args.no_charts,
        )
    except (ContractError, OSError) as error:
        parser.exit(2, f"Benchmark error: {error}\n")
    failures = sum(row["outcome"] in ("ERROR", "TIMEOUT") for row in rows)
    print(f"Recorded {len(rows)} rows, {failures} errors/timeouts: {args.output / 'benchmark.csv'}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
