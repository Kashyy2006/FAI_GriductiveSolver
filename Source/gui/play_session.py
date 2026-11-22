"""Player history and local progress, kept outside the deduction knowledge base."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from threading import RLock
from time import monotonic
from typing import Any

from game.contracts import PublicEngine
from game.models import (
    ContractError,
    DeductionStep,
    PublicState,
    SATQuery,
    SATStatus,
    SolverStats,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictResult,
)

SOURCE = Path(__file__).resolve().parents[1]
MARK_COLORS = {"Amber": "#d58b28", "Blue": "#3a78ad", "Purple": "#8857aa"}


@dataclass(frozen=True)
class Level:
    """Editorial catalogue metadata; never contains puzzle clues or solutions."""

    key: str
    title: str
    difficulty: str
    description: str


LEVELS = (
    Level("3x3/example_01.json", "Museum Opening", "Easy", "3 × 3 · Follow a clue chain."),
    Level("3x3/museum_shift.json", "Museum Shift", "Easy", "3 × 3 · Meet the museum staff."),
    Level("4x4/example_01.json", "City Detectives", "Medium", "4 × 4 · A longer clue chain."),
    Level("4x4/night_market.json", "Night Market", "Medium", "4 × 4 · Investigate the market."),
    Level(
        "3x3/demo_forced_unknown.json",
        "Open Questions",
        "Practice",
        "3 × 3 · Some verdicts remain unknown; completion is not guaranteed.",
    ),
    Level(
        "3x3/demo_stuck.json",
        "Insufficient Evidence",
        "Practice",
        "3 × 3 · Learn why deduction can stop without a forced move.",
    ),
)


def query_from_dict(data: dict[str, Any]) -> SATQuery:
    """Decode diagnostic data only; no saved proof can authorize a reveal."""
    stats = data["stats"]
    counts = [stats[key] for key in ("decisions", "propagations", "backtracks")]
    runtime = stats["runtime_seconds"]
    if any(type(value) is not int or value < 0 for value in counts):
        raise ValueError("Invalid saved SAT counters")
    if type(runtime) not in (float, int) or not math.isfinite(runtime) or runtime < 0:
        raise ValueError("Invalid saved SAT runtime")
    if not isinstance(data["purpose"], str) or not isinstance(data["assumptions"], (list, tuple)):
        raise ValueError("Invalid saved SAT query")
    if any(type(value) is not int or value == 0 for value in data["assumptions"]):
        raise ValueError("Invalid saved assumptions")
    return SATQuery(
        data["purpose"],
        tuple(data["assumptions"]),
        SATStatus(data["result"]),
        SolverStats(*counts, runtime),
    )


class ProgressStore:
    """Atomically save public player actions; malformed files are reported to the UI."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = RLock()
        self.data: dict[str, Any] = {"version": 1, "last_level": None, "levels": {}}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if (
                not isinstance(data, dict)
                or data.get("version") != 1
                or not isinstance(data.get("levels"), dict)
                or data.get("last_level") not in (None, *(level.key for level in LEVELS))
                or any(
                    key not in {level.key for level in LEVELS} or not isinstance(record, dict)
                    for key, record in data.get("levels", {}).items()
                )
            ):
                raise ValueError("Unsupported or malformed player progress")
            self.data = data
        self.active_key = self.data["last_level"]

    def save(self, key: str, record: dict[str, Any]) -> None:
        with self.lock:
            self.data["last_level"] = self.active_key or key
            self.data["levels"][key] = record
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            temporary.replace(self.path)


class PlaySession:
    """Record only receipts from Engine; annotations never enter an Engine call."""

    def __init__(self, engine: PublicEngine) -> None:
        self.engine = engine
        self.lock = RLock()
        self.snapshots = [engine.get_public_state()]
        self.steps: list[DeductionStep] = []
        self.queries: list[SATQuery] = []
        self.hints = 0
        self.rejected = 0
        self.marks: dict[str, str] = {}
        self.used_clues: set[str] = set()
        self.elapsed_before = 0.0
        self.started: float | None = monotonic()
        self.store: ProgressStore | None = None
        self.key: str | None = None
        self.save_error: OSError | None = None
        self.metrics_partial = False

    @property
    def elapsed(self) -> float:
        return self.elapsed_before + (
            monotonic() - self.started if self.started is not None else 0.0
        )

    def get_public_state(self) -> PublicState:
        return self.engine.get_public_state()

    def submit_verdict(
        self, character_id: str, status: Status, *, expected_token: StateToken
    ) -> VerdictResult:
        result = self.engine.submit_verdict(character_id, status, expected_token=expected_token)
        with self.lock:
            if (
                result.outcome == VerdictOutcome.ACCEPTED
                and expected_token == self.snapshots[-1].token
            ):
                if result.proof is None or result.revealed_clue is None:
                    raise ContractError("Accepted reveal requires an Engine receipt")
                before = self.snapshots[-1]
                self.steps.append(
                    DeductionStep(
                        len(self.steps) + 1,
                        before.token,
                        result.state.token,
                        tuple(
                            sorted(
                                item.clue.id
                                for item in before.characters
                                if item.clue is not None and item.clue.type.value != "REMARK"
                            )
                        ),
                        result.proof.queries,
                        character_id,
                        status,
                        result.revealed_clue,
                    )
                )
                self.snapshots.append(result.state)
                self.queries.extend(result.proof.queries)
                if all(item.status is not None for item in result.state.characters):
                    self.pause()
                self.persist()
        return result

    def pause(self) -> None:
        with self.lock:
            self.elapsed_before = self.elapsed
            self.started = None

    def persist(self) -> None:
        with self.lock:
            if self.store is None or self.key is None:
                return
            record = {
                "moves": [[step.character_id, step.verdict.value] for step in self.steps],
                "step_queries": [[asdict(q) for q in step.queries] for step in self.steps],
                "queries": [asdict(q) for q in self.queries],
                "elapsed": self.elapsed,
                "hints": self.hints,
                "rejected": self.rejected,
                "marks": dict(self.marks),
                "used_clues": sorted(self.used_clues),
                "completed": all(c.status is not None for c in self.snapshots[-1].characters),
                "metrics_partial": self.metrics_partial,
            }
            try:
                self.store.save(self.key, record)
                self.save_error = None
            except OSError as error:
                self.save_error = error

    def restore(self, record: dict[str, Any]) -> None:
        """Reprove saved moves in order, with fresh session tokens and genuine receipts."""
        if not isinstance(record, dict):
            raise ValueError("Malformed saved level")
        elapsed = record["elapsed"]
        if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("Invalid saved play time")
        for field in ("hints", "rejected"):
            if type(record[field]) is not int or record[field] < 0:
                raise ValueError("Invalid saved counter")
        moves = record["moves"]
        step_queries = record["step_queries"]
        if not isinstance(moves, list) or not isinstance(step_queries, list):
            raise ValueError("Invalid saved moves")
        if len(moves) != len(step_queries):
            raise ValueError("Saved trace length mismatch")
        queries = [query_from_dict(q) for q in record["queries"]]
        decoded_steps = [tuple(query_from_dict(q) for q in qs) for qs in step_queries]
        ids = {c.id for c in self.snapshots[0].characters}
        marks, used = record["marks"], record["used_clues"]
        if not isinstance(marks, dict) or any(
            key not in ids or color not in MARK_COLORS for key, color in marks.items()
        ):
            raise ValueError("Invalid saved card marks")
        if not isinstance(used, list) or any(not isinstance(key, str) for key in used):
            raise ValueError("Invalid saved clue marks")
        for move, saved_queries in zip(moves, decoded_steps):
            if not isinstance(move, list) or len(move) != 2 or move[0] not in ids:
                raise ValueError("Invalid saved move")
            result = self.submit_verdict(
                move[0], Status(move[1]), expected_token=self.snapshots[-1].token
            )
            if result.outcome != VerdictOutcome.ACCEPTED:
                raise ValueError("Saved verdict is no longer provable from public clues")
            self.steps[-1] = replace(self.steps[-1], queries=saved_queries)
        revealed_clues = {c.clue.id for c in self.snapshots[-1].characters if c.clue is not None}
        if not set(used) <= revealed_clues:
            raise ValueError("Saved annotations refer to unrevealed clues")
        self.queries = queries
        self.elapsed_before = float(elapsed)
        self.started = (
            None
            if all(c.status is not None for c in self.snapshots[-1].characters)
            else monotonic()
        )
        self.hints, self.rejected = record["hints"], record["rejected"]
        self.marks, self.used_clues = dict(marks), set(used)
        self.metrics_partial = bool(record.get("metrics_partial", False))
