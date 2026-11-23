"""Reproduce Stage 4 benchmark experiments, charts, aggregated tables and acceptance checks."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path
from statistics import median

from experiments.benchmark import SOURCE, run_benchmark
from game.models import ContractError

STAGE4_REPEATS = 5
STAGE4_TIMEOUT_SECONDS = 10.0
STAGE4_TIMEOUT_PROFILE_SECONDS = 1e-12

_STUCK_IDS = frozenset(
    {
        "demo_3x3_stuck",
        "fixture_ambiguous",
        "synthetic_3x3_stuck_unique",
        "synthetic_4x4_stuck_unique",
        "stage4_4x4_stuck_unique_parity",
    }
)
_MULTIPLE_IDS = frozenset({"demo_3x3_stuck", "fixture_ambiguous"})


def stage4_inputs() -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    """Return the locked Stage 4 normal and invalid-input puzzle tuples."""
    normal = (
        SOURCE / "puzzles/3x3/example_01.json",
        SOURCE / "puzzles/3x3/demo_forced_unknown.json",
        SOURCE / "puzzles/3x3/demo_stuck.json",
        SOURCE / "puzzles/4x4/example_01.json",
        *(
            SOURCE / f"experiments/puzzles/synthetic_{size}x{size}_{kind}.json"
            for size in (3, 4)
            for kind in ("fact_chain", "row_counts", "stuck_unique")
        ),
        SOURCE / "experiments/puzzles/stage4/stage4_3x3_extensions_parity.json",
        SOURCE / "experiments/puzzles/stage4/stage4_3x3_branching_counts.json",
        SOURCE / "experiments/puzzles/stage4/stage4_4x4_extensions_parity.json",
        SOURCE / "experiments/puzzles/stage4/stage4_4x4_branching_counts.json",
        SOURCE / "experiments/puzzles/stage4/stage4_4x4_stuck_unique_parity.json",
        SOURCE / "tests/fixtures/ambiguous.json",
    )
    invalid = (
        SOURCE / "tests/fixtures/inconsistent.json",
        SOURCE / "tests/fixtures/invalid_reference.json",
    )
    return normal, invalid


def _puzzle_category(puzzle_id: str) -> str:
    if puzzle_id.startswith("stage4_"):
        return "Stage 4 (extensions/branching)"
    if puzzle_id.startswith("synthetic_"):
        return "Synthetic baseline"
    if puzzle_id.startswith("fixture_"):
        return "Fixture"
    return "Shared repo puzzle"


def _opt_int(value: object) -> int | None:
    if value == "" or value is None:
        return None
    return int(value)


def _fmt_triple(first: int | None, second: int | None, third: int | None) -> str:
    if first is None or second is None or third is None:
        return "-"
    return f"{first}/{second}/{third}"


def _aggregate_phase(rows: Sequence[dict[str, object]], mode: str) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        if row["mode"] == mode:
            grouped[str(row["puzzle_id"])].append(row)
    aggregated: list[dict[str, object]] = []
    for puzzle_id, group in grouped.items():
        sample = group[0]
        runtimes_ms = [float(r["runtime_seconds"]) * 1000.0 for r in group]
        trace_vals = [_opt_int(r["trace_query_count"]) for r in group]
        trace_nums = [v for v in trace_vals if v is not None]
        aggregated.append(
            {
                "puzzle_id": puzzle_id,
                "category": _puzzle_category(puzzle_id),
                "size": _opt_int(sample["size"]) or 0,
                "outcome": str(sample["outcome"]),
                "primary_count": _opt_int(sample["primary_count"]),
                "aux_initial": _opt_int(sample["auxiliary_count_initial"]),
                "aux_max": _opt_int(sample["auxiliary_count_max"]),
                "aux_final": _opt_int(sample["auxiliary_count_final"]),
                "clauses_initial": _opt_int(sample["clauses_initial"]),
                "clauses_max": _opt_int(sample["clauses_max"]),
                "clauses_final": _opt_int(sample["clauses_final"]),
                "sat_calls": int(median(int(r["sat_calls"]) for r in group)),
                "trace_queries": int(median(trace_nums)) if trace_nums else None,
                "all_matched": all(r["query_count_matches"] is True for r in group),
                "decisions": int(median(int(r["decisions"]) for r in group)),
                "propagations": int(median(int(r["propagations"]) for r in group)),
                "backtracks": int(median(int(r["backtracks"]) for r in group)),
                "deduction_steps": int(median(int(r["deduction_steps"]) for r in group)),
                "median_ms": median(runtimes_ms),
                "min_ms": min(runtimes_ms),
                "max_ms": max(runtimes_ms),
                "repeats": len(group),
            }
        )
    aggregated.sort(key=lambda item: (int(item["size"]), str(item["puzzle_id"])))
    return aggregated


def _plot_stage4_charts(
    normal_rows: Sequence[dict[str, object]],
    profile_outcomes: dict[str, dict[str, int]],
    charts_dir: Path,
) -> tuple[Path, ...]:
    """Generate analytical Stage 4 report charts without altering raw CSV data."""
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.patches import Patch

    charts_dir.mkdir(parents=True, exist_ok=True)
    solve_agg = _aggregate_phase(normal_rows, "solve")
    uniq_agg = {item["puzzle_id"]: item for item in _aggregate_phase(normal_rows, "uniqueness")}
    labels = [
        f"{item['puzzle_id']} ({item['size']}x{item['size']}, {item['outcome']})"
        for item in solve_agg
    ]
    positions = list(range(len(solve_agg)))

    # Chart 1: Runtime comparison (solve vs uniqueness) with log scale and exact ms labels.
    fig1, (ax_s, ax_u) = plt.subplots(1, 2, figsize=(15.5, 7.2), sharey=True)
    solve_ms = [float(item["median_ms"]) for item in solve_agg]
    uniq_ms = [float(uniq_agg[str(item["puzzle_id"])]["median_ms"]) for item in solve_agg]
    solve_colors = [
        "#d97706" if item["outcome"] == "STUCK" else ("#2563eb" if item["size"] == 4 else "#0f766e")
        for item in solve_agg
    ]
    uniq_colors = [
        "#9333ea"
        if uniq_agg[str(item["puzzle_id"])]["outcome"] == "MULTIPLE"
        else ("#2563eb" if item["size"] == 4 else "#0f766e")
        for item in solve_agg
    ]
    ax_s.barh(positions, solve_ms, color=solve_colors, height=0.68)
    ax_u.barh(positions, uniq_ms, color=uniq_colors, height=0.68)
    ax_s.set_xscale("log")
    ax_u.set_xscale("log")
    ax_s.set_yticks(positions, labels, fontsize=8.5)
    ax_s.invert_yaxis()
    ax_s.set_xlabel("Median solve runtime (ms, log scale)")
    ax_u.set_xlabel("Median uniqueness runtime (ms, log scale)")
    ax_s.set_title("Progressive Auto Solve (Engine + Agent + DPLL)")
    ax_u.set_title("Full-Clue Uniqueness (Primary-Variable Blocking)")
    ax_s.grid(axis="x", linestyle="--", alpha=0.4)
    ax_u.grid(axis="x", linestyle="--", alpha=0.4)
    ax_s.set_xlim(right=max(solve_ms) * 3.8)
    ax_u.set_xlim(right=max(uniq_ms) * 5.2)
    for pos, val in zip(positions, solve_ms):
        ax_s.text(val * 1.12, pos, f"{val:.2f} ms", va="center", fontsize=8)
    for pos, item, val in zip(positions, solve_agg, uniq_ms):
        u_out = uniq_agg[str(item["puzzle_id"])]["outcome"]
        ax_u.text(val * 1.12, pos, f"{val:.2f} ms [{u_out}]", va="center", fontsize=8)
    fig1.legend(
        handles=[
            Patch(color="#0f766e", label="3x3 SOLVED / UNIQUE"),
            Patch(color="#2563eb", label="4x4 SOLVED / UNIQUE"),
            Patch(color="#d97706", label="Progressive STUCK"),
            Patch(color="#9333ea", label="Uniqueness MULTIPLE"),
        ],
        loc="lower center",
        ncol=4,
        frameon=False,
    )
    fig1.suptitle(
        "Stage 4 Benchmark: Median Runtime Comparison by Board Size and Phase", fontsize=12
    )
    fig1.tight_layout(rect=(0, 0.05, 1, 0.95))
    chart1 = charts_dir / "runtime_by_size_and_phase.png"
    fig1.savefig(chart1, dpi=160)
    plt.close(fig1)

    # Chart 2: Max clauses and DPLL search effort (propagations, decisions, backtracks).
    fig2, (ax_c, ax_d) = plt.subplots(1, 2, figsize=(15.5, 7.2), sharey=True)
    cls_solve = [int(item["clauses_max"] or 0) for item in solve_agg]
    cls_uniq = [int(uniq_agg[str(item["puzzle_id"])]["clauses_max"] or 0) for item in solve_agg]
    bar_h = 0.36
    ax_c.barh(
        [p - bar_h / 2 for p in positions],
        cls_solve,
        height=bar_h,
        label="Solve max",
        color="#0f766e",
    )
    ax_c.barh(
        [p + bar_h / 2 for p in positions],
        cls_uniq,
        height=bar_h,
        label="Uniqueness max",
        color="#64748b",
    )
    ax_c.set_yticks(positions, [str(item["puzzle_id"]) for item in solve_agg], fontsize=8.5)
    ax_c.invert_yaxis()
    ax_c.set_xlabel("Maximum CNF clauses observed")
    ax_c.set_title("CNF Growth (Max Clauses: Solve vs Uniqueness)")
    ax_c.grid(axis="x", linestyle="--", alpha=0.4)
    ax_c.set_xlim(right=max(*cls_solve, *cls_uniq) * 1.18)
    for pos, val in zip(positions, cls_solve):
        ax_c.text(val + 4, pos - bar_h / 2, str(val), va="center", fontsize=7.5)
    ax_c.legend(loc="lower right", fontsize=8.5)

    props = [int(item["propagations"]) for item in solve_agg]
    decs = [int(item["decisions"]) for item in solve_agg]
    bts = [int(item["backtracks"]) for item in solve_agg]
    ax_d.barh(positions, props, height=0.62, label="Propagations", color="#38bdf8", alpha=0.85)
    ax_d.barh(positions, decs, height=0.42, label="Decisions", color="#f59e0b")
    ax_d.barh(positions, bts, height=0.22, label="Backtracks", color="#dc2626")
    ax_d.set_xlabel("Cumulative DPLL counters across solve run")
    ax_d.set_title("DPLL Search Work (Unit Propagation vs Branching/Backtracking)")
    ax_d.grid(axis="x", linestyle="--", alpha=0.4)
    ax_d.set_xlim(right=max(props) * 1.40)
    for pos, pr, dc, bt in zip(positions, props, decs, bts):
        ax_d.text(pr + 25, pos, f"P={pr}, D={dc}, B={bt}", va="center", fontsize=7.5)
    ax_d.legend(loc="lower right", fontsize=8.5)
    fig2.suptitle("Stage 4 Benchmark: CNF Clause Scale and DPLL Effort", fontsize=12)
    fig2.tight_layout(rect=(0, 0.02, 1, 0.95))
    chart2 = charts_dir / "dpll_work_and_clauses.png"
    fig2.savefig(chart2, dpi=160)
    plt.close(fig2)

    # Chart 3: Actual SAT calls & deduction steps + complete outcome summary across profiles.
    fig3, (ax_q, ax_o) = plt.subplots(
        1, 2, figsize=(15.5, 6.8), gridspec_kw={"width_ratios": [1.5, 1]}
    )
    calls = [int(item["sat_calls"]) for item in solve_agg]
    steps = [int(item["deduction_steps"]) for item in solve_agg]
    ax_q.barh(positions, calls, height=0.65, color=solve_colors)
    ax_q.set_yticks(positions, [str(item["puzzle_id"]) for item in solve_agg], fontsize=8.5)
    ax_q.invert_yaxis()
    ax_q.set_xlabel("Actual SAT calls per solve run (100% trace matched)")
    ax_q.set_title("Solve SAT Calls and Accepted Deduction Steps")
    ax_q.grid(axis="x", linestyle="--", alpha=0.4)
    ax_q.set_xlim(right=max(calls) * 1.26)
    for pos, call_count, step_count in zip(positions, calls, steps):
        ax_q.text(
            call_count + 4, pos, f"{call_count} calls / {step_count} steps", va="center", fontsize=8
        )

    outcome_labels = [
        "normal: solve SOLVED",
        "normal: solve STUCK",
        "normal: uniq UNIQUE",
        "normal: uniq MULTIPLE",
        "errors: ERROR (both)",
        "timeouts: TIMEOUT (both)",
    ]
    normal_counts = profile_outcomes.get("normal", {})
    error_counts = profile_outcomes.get("errors", {})
    timeout_counts = profile_outcomes.get("timeouts", {})
    outcome_vals = [
        normal_counts.get("solve:SOLVED", 0),
        normal_counts.get("solve:STUCK", 0),
        normal_counts.get("uniqueness:UNIQUE", 0),
        normal_counts.get("uniqueness:MULTIPLE", 0),
        error_counts.get("solve:ERROR", 0) + error_counts.get("uniqueness:ERROR", 0),
        timeout_counts.get("solve:TIMEOUT", 0) + timeout_counts.get("uniqueness:TIMEOUT", 0),
    ]
    outcome_colors = ["#0f766e", "#d97706", "#2563eb", "#9333ea", "#dc2626", "#991b1b"]
    o_pos = list(range(len(outcome_labels)))
    ax_o.barh(o_pos, outcome_vals, color=outcome_colors, height=0.6)
    ax_o.set_yticks(o_pos, outcome_labels, fontsize=8.5)
    ax_o.invert_yaxis()
    ax_o.set_xlabel("Recorded CSV rows across all repeats")
    ax_o.set_title("Retained Outcomes Across All 3 Profiles")
    ax_o.grid(axis="x", linestyle="--", alpha=0.4)
    ax_o.set_xlim(right=max(outcome_vals, default=1) * 1.2)
    for pos, val in zip(o_pos, outcome_vals):
        ax_o.text(val + 2, pos, str(val), va="center", fontsize=8.5)
    fig3.suptitle(
        "Stage 4 Benchmark: SAT Query Accounting and Complete Outcome Retention", fontsize=12
    )
    fig3.tight_layout(rect=(0, 0.02, 1, 0.95))
    chart3 = charts_dir / "sat_calls_and_outcomes.png"
    fig3.savefig(chart3, dpi=160)
    plt.close(fig3)
    return (chart1, chart2, chart3)


def _write_combined_summary(
    normal_rows: Sequence[dict[str, object]],
    summaries: dict[str, dict[str, object]],
    destination: Path,
    repeats: int,
    timeout_seconds: float,
) -> None:
    solve_agg = _aggregate_phase(normal_rows, "solve")
    uniq_agg = _aggregate_phase(normal_rows, "uniqueness")
    lines = [
        "# Stage 4 Benchmark Combined Summary",
        "",
        f"- Repeats per puzzle & phase: `{repeats}`",
        f"- Normal/errors phase timeout: `{timeout_seconds}` s; timeout profile: `{STAGE4_TIMEOUT_PROFILE_SECONDS}` s",
        "- All raw rows (including `ERROR` and `TIMEOUT`) are retained in each profile's `benchmark.csv`.",
        "- No hidden assignments or unrevealed clues are exported.",
        "",
        "## 1. Progressive Solve Phase (Median across repeats)",
        "",
        "| Puzzle | Size | Category | Outcome | Primary | Aux (i/m/f) | Clauses (i/m/f) | Calls/Trace | Decisions | Propagations | Backtracks | Steps | Median ms | Min–Max ms |",
        "| --- | :---: | --- | --- | ---: | :---: | :---: | :---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for item in solve_agg:
        trace_str = "-" if item["trace_queries"] is None else str(item["trace_queries"])
        primary_str = "-" if item["primary_count"] is None else str(item["primary_count"])
        lines.append(
            f"| {item['puzzle_id']} | {item['size']}x{item['size']} | {item['category']} | "
            f"{item['outcome']} | {primary_str} | "
            f"{_fmt_triple(item['aux_initial'], item['aux_max'], item['aux_final'])} | "
            f"{_fmt_triple(item['clauses_initial'], item['clauses_max'], item['clauses_final'])} | "
            f"{item['sat_calls']}/{trace_str} | {item['decisions']} | "
            f"{item['propagations']} | {item['backtracks']} | {item['deduction_steps']} | "
            f"{item['median_ms']:.3f} | {item['min_ms']:.3f}–{item['max_ms']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## 2. Full-Clue Uniqueness Phase (Median across repeats)",
            "",
            "| Puzzle | Size | Outcome | Primary | Aux (i/m/f) | Clauses (i/m/f) | Calls/Trace | Decisions | Propagations | Backtracks | Median ms | Min–Max ms |",
            "| --- | :---: | --- | ---: | :---: | :---: | :---: | ---: | ---: | ---: | ---: | :---: |",
        ]
    )
    for item in uniq_agg:
        trace_str = "-" if item["trace_queries"] is None else str(item["trace_queries"])
        primary_str = "-" if item["primary_count"] is None else str(item["primary_count"])
        lines.append(
            f"| {item['puzzle_id']} | {item['size']}x{item['size']} | {item['outcome']} | "
            f"{primary_str} | "
            f"{_fmt_triple(item['aux_initial'], item['aux_max'], item['aux_final'])} | "
            f"{_fmt_triple(item['clauses_initial'], item['clauses_max'], item['clauses_final'])} | "
            f"{item['sat_calls']}/{trace_str} | {item['decisions']} | "
            f"{item['propagations']} | {item['backtracks']} | "
            f"{item['median_ms']:.3f} | {item['min_ms']:.3f}–{item['max_ms']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## 3. Profile Summary (Normal, Errors, Timeouts)",
            "",
            "| Profile | Rows | Timeout (s) | Query Matches | Actual SAT Calls | Outcomes |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for name in ("normal", "errors", "timeouts"):
        prof = summaries[name]
        outcomes_str = ", ".join(f"{key}={val}" for key, val in dict(prof["outcomes"]).items())
        lines.append(
            f"| {name} | {prof['rows']} | {prof['timeout_seconds']} | "
            f"{prof['query_matches']} | {prof['actual_sat_calls']} | {outcomes_str} |"
        )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_phase4(
    output: Path,
    *,
    repeats: int = STAGE4_REPEATS,
    timeout_seconds: float = STAGE4_TIMEOUT_SECONDS,
    charts: bool = True,
) -> dict[str, object]:
    """Run locked Stage 4 profiles, verify query reconciliation, and generate report artifacts."""
    normal, invalid = stage4_inputs()
    profiles = (
        ("normal", normal, timeout_seconds),
        ("errors", invalid, timeout_seconds),
        ("timeouts", normal, STAGE4_TIMEOUT_PROFILE_SECONDS),
    )
    summaries: dict[str, dict[str, object]] = {}
    profile_outcomes: dict[str, dict[str, int]] = {}
    normal_rows: list[dict[str, object]] = []
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
        if name == "normal":
            normal_rows = rows
        mismatches = []
        for row in rows:
            puzzle_id = str(row["puzzle_id"])
            if name == "errors":
                expected = "ERROR"
            elif name == "timeouts":
                expected = "TIMEOUT"
            elif row["mode"] == "uniqueness":
                expected = "MULTIPLE" if puzzle_id in _MULTIPLE_IDS else "UNIQUE"
            else:
                expected = "STUCK" if puzzle_id in _STUCK_IDS else "SOLVED"
            accounting_ok = name != "normal" or row["query_count_matches"] is True
            if row["outcome"] != expected or not accounting_ok:
                mismatches.append(
                    {
                        "puzzle_id": puzzle_id,
                        "mode": row["mode"],
                        "repeat": row["repeat"],
                        "expected": expected,
                        "actual": row["outcome"],
                        "query_count_matches": row["query_count_matches"],
                    }
                )
        passed = not mismatches
        all_passed = all_passed and passed
        counts = dict(sorted(Counter(f"{row['mode']}:{row['outcome']}" for row in rows).items()))
        profile_outcomes[name] = counts
        summaries[name] = {
            "passed": passed,
            "rows": len(rows),
            "timeout_seconds": budget,
            "outcomes": counts,
            "query_matches": sum(row["query_count_matches"] is True for row in rows),
            "actual_sat_calls": sum(int(row["sat_calls"]) for row in rows),
            "mismatches": mismatches,
        }

    generated_charts: tuple[Path, ...] = ()
    if charts and normal_rows:
        generated_charts = _plot_stage4_charts(
            normal_rows, profile_outcomes, output / "normal" / "charts"
        )
    _write_combined_summary(
        normal_rows, summaries, output / "combined_summary.md", repeats, timeout_seconds
    )

    summary: dict[str, object] = {
        "passed": all_passed,
        "repeats": repeats,
        "timeout_seconds": timeout_seconds,
        "timeout_profile_seconds": STAGE4_TIMEOUT_PROFILE_SECONDS,
        "normal_puzzle_count": len(normal),
        "invalid_fixture_count": len(invalid),
        "analytical_charts": [path.name for path in generated_charts],
        "profiles": summaries,
        "notes": [
            "Locked Stage 4 benchmark combines shared repo 3x3/4x4 puzzles, synthetic baselines, and TV3 Stage 4 extension/branching puzzles.",
            "Solve and uniqueness are measured independently on the exact same ordered input list.",
            "Expected invalid-input ERROR rows and TIMEOUT rows remain intact in each profile CSV.",
            "Mid-SAT, mid-verifier, and second-uniqueness-call timeouts are verified separately via controlled-clock tests.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "acceptance.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if not (output / "README.md").exists():
        (output / "README.md").write_text(
            "# Stage 4 benchmark results\n\n"
            "Owner: TV3 (Mạnh). Reproduce from Source with `python -m experiments.phase4`.\n\n"
            "- `normal/`: 16 loader-valid 3x3/4x4 puzzles (shared repo + baselines + extensions/branching + ambiguous), 5 repeats, both phases, 100% query reconciliation, plus analytical charts.\n"
            "- `errors/`: 2 invalid-data fixtures, 5 repeats, both phases; raw ERROR rows retained.\n"
            "- `timeouts/`: 16 normal puzzles with `1e-12` s deadline; raw TIMEOUT rows retained.\n"
            "- `combined_summary.md` & `acceptance.json`: aggregated median tables and outcome verification.\n\n"
            "## Nhật ký AI\n",
            encoding="utf-8",
        )
    return summary


def main() -> None:
    """Run locked Stage 4 experiments from Source with python -m experiments.phase4."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=SOURCE / "experiments/results/phase4")
    parser.add_argument("--repeats", type=int, default=STAGE4_REPEATS)
    parser.add_argument("--timeout", type=float, default=STAGE4_TIMEOUT_SECONDS)
    parser.add_argument("--no-charts", action="store_true")
    args = parser.parse_args()
    try:
        summary = run_phase4(
            args.output,
            repeats=args.repeats,
            timeout_seconds=args.timeout,
            charts=not args.no_charts,
        )
    except (ContractError, OSError) as error:
        parser.exit(2, f"Stage 4 benchmark error: {error}\n")
    print(f"Stage 4 benchmark passed={summary['passed']}: {args.output / 'acceptance.json'}")
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
