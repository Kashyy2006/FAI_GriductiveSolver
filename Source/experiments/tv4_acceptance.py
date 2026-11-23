"""Reproduce TV4 reasoning evidence; not the team's performance benchmark runner."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from importlib.metadata import PackageNotFoundError, version
from math import isfinite
from pathlib import Path

from agent.agent import DeductiveAgent
from agent.trace import save_trace
from game.engine import GameEngine
from game.models import (
    CNF,
    AutoSolveResult,
    Classification,
    Clue,
    ClueType,
    Literal,
    PublicState,
    SATResult,
    SATStatus,
    SolveOutcome,
    SolverStats,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictResult,
)
from game.puzzle_loader import load_puzzle
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver
from solver.uniqueness import check_uniqueness

SOURCE = Path(__file__).resolve().parents[1]
FIELDS = (
    "group",
    "puzzle_path",
    "puzzle_id",
    "size",
    "initial_known",
    "initial_criminal",
    "initial_innocent",
    "initial_unknown",
    "outcome",
    "deduction_steps",
    "actual_sat_calls",
    "trace_queries",
    "query_order_matches",
    "decisions",
    "propagations",
    "backtracks",
    "uniqueness",
    "expected_outcome",
    "expected_uniqueness",
    "checks_passed",
    "error_type",
)


class _ObservedSolver:
    """Observe actual Solver calls, without exporting model assignments."""

    def __init__(self, budget: float) -> None:
        self.budget = budget
        self.calls = 0
        self.records: list[tuple[tuple[int, ...], SATStatus, SolverStats]] = []
        self.inner = DPLLSolver()

    def solve(
        self,
        cnf: CNF,
        variables: Sequence[int],
        assumptions: Sequence[Literal] = (),
        *,
        timeout_seconds: float | None = None,
    ) -> SATResult:
        self.calls += 1
        budget = self.budget if timeout_seconds is None else min(self.budget, timeout_seconds)
        result = self.inner.solve(cnf, variables, assumptions, timeout_seconds=budget)
        self.records.append((tuple(assumptions), result.status, result.stats))
        return result


def _cases() -> tuple[tuple[str, str, str], ...]:
    # Same normal inputs as phase3, followed by TV1's two demonstration cases.
    shared = ["puzzles/3x3/example_01.json", "puzzles/4x4/example_01.json"]
    shared += [
        f"experiments/puzzles/synthetic_{n}x{n}_{kind}.json"
        for n in (3, 4)
        for kind in ("fact_chain", "row_counts", "stuck_unique")
    ]
    shared += ["tests/fixtures/ambiguous.json"]
    return tuple(
        (
            "shared_phase3",
            path,
            "STUCK" if "stuck_unique" in path or "ambiguous" in path else "SOLVED",
        )
        for path in shared
    ) + (
        ("demo", "puzzles/3x3/demo_forced_unknown.json", "SOLVED"),
        ("demo", "puzzles/3x3/demo_stuck.json", "STUCK"),
    )


def _diagnostics(budget: float) -> dict[str, object]:
    """Distinguish rejected manual actions from an injected inconsistent KB."""
    solver = _ObservedSolver(budget)
    agent = DeductiveAgent(CNFEncoder(), solver)
    engine = GameEngine(load_puzzle(SOURCE / "puzzles/3x3/example_01.json"), agent.verify_verdict)
    state = engine.get_public_state()
    classified = agent.classify_all(state)
    wrong = engine.submit_verdict("B1", Status.CRIMINAL, expected_token=state.token)
    unknown_id = next(
        cell_id
        for cell_id, value in classified.classifications.items()
        if value == Classification.UNKNOWN
    )
    unknown = engine.submit_verdict(unknown_id, Status.CRIMINAL, expected_token=state.token)
    unchanged = engine.get_public_state() == state
    bad_a1 = replace(
        state.characters[0],
        clue=Clue("injected_conflict", ClueType.FACT, person="B1", status=Status.CRIMINAL),
    )
    bad_b1 = replace(
        state.characters[1],
        status=Status.INNOCENT,
        clue=Clue("public_B1", ClueType.FACT, person="A1", status=Status.CRIMINAL),
    )
    inconsistent = replace(state, characters=(bad_a1, bad_b1) + state.characters[2:])
    inconsistent_classified = agent.classify_all(inconsistent)
    inconsistent_proof = agent.verify_verdict(inconsistent, "C1", Status.CRIMINAL)

    class FaultInjectedEngine:
        def get_public_state(self) -> PublicState:
            return inconsistent

        def submit_verdict(
            self, character_id: str, status: Status, *, expected_token: StateToken
        ) -> VerdictResult:
            raise AssertionError("Inconsistent KB attempted to submit a verdict")

    run = agent.auto_solve(FaultInjectedEngine())
    return {
        "source": "real dependencies; inconsistent PublicState is explicit fault injection",
        "initial_classifications": {
            key: value.value for key, value in classified.classifications.items()
        },
        "wrong_verdict": wrong.outcome.value,
        "unforced_character_id": unknown_id,
        "unforced_verdict": unknown.outcome.value,
        "rejected_actions_leave_state_unchanged": unchanged,
        "inconsistent_kb_status": inconsistent_classified.kb_status.value,
        "inconsistent_classifications": inconsistent_classified.classifications,
        "inconsistent_proof": inconsistent_proof.outcome.value,
        "inconsistent_loop": run.outcome.value,
        "inconsistent_loop_queries": len(run.queries),
        "checks_passed": (
            wrong.outcome == VerdictOutcome.CONTRADICTED
            and unknown.outcome == VerdictOutcome.NOT_PROVABLE
            and unchanged
            and not inconsistent_classified.classifications
            and inconsistent_proof.outcome == VerdictOutcome.INCONSISTENT
            and run.outcome == SolveOutcome.INCONSISTENT
            and not run.steps
        ),
    }


def _fingerprint(path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(SOURCE.parent).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> None:
    """Write reproducible call-count evidence and one public example trace."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True, type=date.fromisoformat)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="an existing directory with README; artifacts are overwritten",
    )
    parser.add_argument("--sat-timeout", type=float, default=10.0)
    args = parser.parse_args()
    if not isfinite(args.sat_timeout) or args.sat_timeout <= 0:
        parser.error("--sat-timeout must be positive and finite")
    if not args.output.is_dir() or not (args.output / "README.md").is_file():
        parser.error("--output must be an existing directory containing README.md")
    rows: list[dict[str, object]] = []
    example: AutoSolveResult | None = None
    for group, relative, expected in _cases():
        row: dict[str, object] = dict.fromkeys(FIELDS, "")
        row.update(
            group=group,
            puzzle_path=relative,
            expected_outcome=expected,
            checks_passed=False,
            expected_uniqueness=(
                "MULTIPLE"
                if "ambiguous" in relative or relative.endswith("demo_stuck.json")
                else "UNIQUE"
            ),
        )
        observer = _ObservedSolver(args.sat_timeout)
        try:
            puzzle = load_puzzle(SOURCE / relative)
            agent = DeductiveAgent(CNFEncoder(), observer)
            engine = GameEngine(puzzle, agent.verify_verdict)
            initial = engine.get_public_state()
            classification = agent.classify_all(initial)
            counts = Counter(classification.classifications.values())
            start, marker = observer.calls, len(observer.records)
            result = agent.auto_solve(engine)
            actual = observer.calls - start
            ordered = [(q.assumptions, q.result, q.stats) for q in result.queries]
            matches = actual == len(result.queries) and ordered == observer.records[marker:]
            unique = check_uniqueness(
                puzzle, CNFEncoder(), DPLLSolver(), timeout_seconds=args.sat_timeout
            )
            row.update(
                puzzle_id=puzzle.puzzle_id,
                size=puzzle.size,
                initial_known=sum(c.status is not None for c in initial.characters),
                initial_criminal=counts[Classification.CRIMINAL],
                initial_innocent=counts[Classification.INNOCENT],
                initial_unknown=counts[Classification.UNKNOWN],
                outcome=result.outcome.value,
                deduction_steps=len(result.steps),
                actual_sat_calls=actual,
                trace_queries=len(result.queries),
                query_order_matches=matches,
                decisions=sum(q.stats.decisions for q in result.queries),
                propagations=sum(q.stats.propagations for q in result.queries),
                backtracks=sum(q.stats.backtracks for q in result.queries),
                uniqueness=unique.outcome.value,
                checks_passed=(
                    result.outcome.value == expected
                    and matches
                    and unique.outcome.value == row["expected_uniqueness"]
                ),
            )
            if relative == "puzzles/3x3/example_01.json":
                example = result
        except Exception as error:
            row.update(outcome="ERROR", error_type=type(error).__name__)
        rows.append(row)
    try:
        diagnostics = _diagnostics(args.sat_timeout)
    except Exception as error:
        diagnostics = {"checks_passed": False, "error_type": type(error).__name__}
    with (args.output / "tv4_cases.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    if example is not None:
        save_trace(example.steps, args.output / "tv4_example_trace.json")
    else:
        # A failed rerun must not leave an old example looking like fresh evidence.
        (args.output / "tv4_example_trace.json").unlink(missing_ok=True)
    packages = {}
    for name in ("jsonschema", "pytest", "ruff"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    passed = all(row["checks_passed"] for row in rows) and diagnostics["checks_passed"]
    metadata = {
        "as_of": args.as_of.isoformat(),
        "timezone": "Asia/Saigon",
        "python": sys.version,
        "platform": platform.platform(),
        "packages": packages,
        "source_revision": revision,
        "sat_timeout_seconds_per_call": args.sat_timeout,
        "uniqueness_timeout_seconds_total": args.sat_timeout,
        "measurement": "solve only; initial classification and uniqueness calls are excluded",
        "purpose": "TV4 acceptance, not a repeated performance benchmark or a new puzzle suite",
        "all_passed": passed,
        "cases": len(rows),
        "diagnostics": diagnostics,
        "inputs": [_fingerprint(SOURCE / relative) for _, relative, _ in _cases()],
        "sources": [
            _fingerprint(SOURCE / relative)
            for relative in (
                "agent/agent.py",
                "agent/trace.py",
                "game/models.py",
                "game/contracts.py",
                "game/engine.py",
                "game/puzzle_loader.py",
                "logic/cnf_encoder.py",
                "logic/regions.py",
                "logic/clue_evaluator.py",
                "solver/dpll.py",
                "solver/_timing.py",
                "solver/uniqueness.py",
                "experiments/tv4_acceptance.py",
            )
        ],
    }
    (args.output / "tv4_environment.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "cases": len(rows),
                "all_passed": passed,
                "query_matches": sum(row["query_order_matches"] is True for row in rows),
            }
        )
    )
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
