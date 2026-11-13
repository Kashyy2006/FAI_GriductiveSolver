"""Reproduce phase-3 acceptance with separate normal, invalid-data and timeout runs."""

import argparse
import json
from collections import Counter
from pathlib import Path

from experiments.benchmark import SOURCE, run_benchmark
from game.models import ContractError

TIMEOUT_SECONDS = 1e-12


def run_phase3(
    output: Path, *, repeats: int = 3, timeout_seconds: float = 10.0, charts: bool = True
) -> dict[str, object]:
    """Keep all rows and verify outcomes without treating expected errors as success."""
    normal = (
        SOURCE / "puzzles/3x3/example_01.json",
        SOURCE / "puzzles/4x4/example_01.json",
        *(
            SOURCE / f"experiments/puzzles/synthetic_{size}x{size}_{kind}.json"
            for size in (3, 4)
            for kind in ("fact_chain", "row_counts", "stuck_unique")
        ),
        SOURCE / "tests/fixtures/ambiguous.json",
    )
    invalid = (
        SOURCE / "tests/fixtures/inconsistent.json",
        SOURCE / "tests/fixtures/invalid_reference.json",
    )
    profiles = (
        ("normal", normal, timeout_seconds),
        ("errors", invalid, timeout_seconds),
        ("timeouts", normal, TIMEOUT_SECONDS),
    )
    summaries: dict[str, object] = {}
    all_passed = True
    for name, inputs, budget in profiles:
        rows = run_benchmark(
            inputs,
            output / name,
            timeout_seconds=budget,
            repeats=repeats,
            mode="all",
            charts=charts,
        )
        mismatches = []
        for row in rows:
            if name == "errors":
                expected = "ERROR"
            elif name == "timeouts":
                expected = "TIMEOUT"
            elif row["mode"] == "uniqueness":
                expected = "MULTIPLE" if row["puzzle_id"] == "fixture_ambiguous" else "UNIQUE"
            else:
                stuck = (
                    str(row["puzzle_id"]).endswith("_stuck_unique")
                    or row["puzzle_id"] == "fixture_ambiguous"
                )
                expected = "STUCK" if stuck else "SOLVED"
            accounting_ok = name != "normal" or row["query_count_matches"] is True
            if row["outcome"] != expected or not accounting_ok:
                mismatches.append(
                    {
                        "puzzle_id": row["puzzle_id"],
                        "mode": row["mode"],
                        "repeat": row["repeat"],
                        "expected": expected,
                        "actual": row["outcome"],
                        "query_count_matches": row["query_count_matches"],
                    }
                )
        passed = not mismatches
        all_passed = all_passed and passed
        summaries[name] = {
            "passed": passed,
            "rows": len(rows),
            "timeout_seconds": budget,
            "outcomes": dict(
                sorted(Counter(f"{row['mode']}:{row['outcome']}" for row in rows).items())
            ),
            "query_matches": sum(row["query_count_matches"] is True for row in rows),
            "actual_sat_calls": sum(int(row["sat_calls"]) for row in rows),
            "mismatches": mismatches,
        }
    summary = {
        "passed": all_passed,
        "repeats": repeats,
        "profiles": summaries,
        "notes": [
            "Expected invalid-input ERROR rows remain errors in their original CSV.",
            "Timeout profile deliberately expires before SAT; mid-SAT/verifier deadlines are covered by controlled-clock integration tests.",
            "Normal inputs are small synthetic/chain baselines, not a difficult performance set.",
            "Query reconciliation checks every completed run without exposing SAT assignments or clue contents.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "acceptance.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if not (output / "README.md").exists():
        (output / "README.md").write_text(
            "# Phase 3 acceptance results\n\n"
            "Owner: TV3. Reproduce from Source with python -m experiments.phase3.\n\n"
            "normal/: loader-valid inputs (including deliberate ambiguity), both phases and query reconciliation.\n"
            "errors/: intentionally invalid inputs; ERROR rows retained.\n"
            "timeouts/: deliberately tiny deadlines; TIMEOUT rows retained.\n"
            "acceptance.json checks expected outcomes; individual CSV files retain raw outcomes.\n\n"
            "## AI log\n",
            encoding="utf-8",
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=SOURCE / "experiments/results/phase3")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--no-charts", action="store_true")
    args = parser.parse_args()
    try:
        summary = run_phase3(
            args.output,
            repeats=args.repeats,
            timeout_seconds=args.timeout,
            charts=not args.no_charts,
        )
    except (ContractError, OSError) as error:
        parser.exit(2, f"Phase 3 configuration/export error: {error}\n")
    print(
        f"Phase 3 acceptance: {'PASS' if summary['passed'] else 'FAIL'}; {args.output / 'acceptance.json'}"
    )
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
