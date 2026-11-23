"""Seeded puzzle construction with independent uniqueness and one-move-path checks."""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import monotonic
from typing import Any

from agent.agent import DeductiveAgent
from game.contracts import CancelCheck
from game.engine import GameEngine
from game.generation_patterns import build_candidate as _candidate
from game.models import (
    CNF,
    Classification,
    ContractError,
    KBStatus,
    Literal,
    Puzzle,
    PuzzleValidationError,
    SATResult,
    SolverTimeout,
    Status,
    UniquenessOutcome,
    VerdictOutcome,
)
from game.puzzle_loader import puzzle_from_dict
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver
from solver.uniqueness import check_uniqueness


def generate_puzzle(
    size: int,
    seed: int,
    *,
    timeout_seconds: float = 20.0,
    should_cancel: CancelCheck | None = None,
) -> Puzzle:
    """Return a verified candidate, never an unchecked or timed-out substitute."""
    if type(size) is not int or size not in (3, 4, 5):
        raise ContractError("Choose a board size of 3, 4, or 5")
    if type(seed) is not int or not 0 <= seed <= 2**31 - 1:
        raise ContractError("Seed must be an integer from 0 to 2147483647")
    if (
        type(timeout_seconds) not in (int, float)
        or not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0
    ):
        raise ContractError("Generation timeout must be positive and finite")
    deadline = monotonic() + timeout_seconds

    def remaining() -> float:
        if should_cancel is not None and should_cancel():
            raise InterruptedError("Puzzle generation cancelled")
        budget = deadline - monotonic()
        if budget <= 0:
            raise SolverTimeout("Puzzle generation timed out")
        return budget

    class BoundedSolver(DPLLSolver):
        def solve(
            self,
            cnf: CNF,
            variables: Sequence[int],
            assumptions: Sequence[Literal] = (),
            *,
            timeout_seconds: float | None = None,
        ) -> SATResult:
            budget = remaining()
            return super().solve(
                cnf, variables, assumptions, timeout_seconds=min(budget, timeout_seconds or budget)
            )

    remaining()
    puzzle = _candidate(size, seed)
    encoder, solver = CNFEncoder(), BoundedSolver()
    unique = check_uniqueness(puzzle, encoder, solver, timeout_seconds=remaining())
    if unique.outcome != UniquenessOutcome.UNIQUE:
        raise PuzzleValidationError("Generated puzzle does not have exactly one solution")
    agent = DeductiveAgent(encoder, solver)
    engine = GameEngine(puzzle, agent.verify_verdict)
    while True:
        remaining()
        state = engine.get_public_state()
        result = agent.classify_all(state)
        if result.kb_status != KBStatus.CONSISTENT:
            raise PuzzleValidationError("Generated puzzle has inconsistent public clues")
        forced = [
            (cell, value)
            for cell, value in result.classifications.items()
            if value != Classification.UNKNOWN
        ]
        if all(c.status is not None for c in state.characters):
            break
        if len(forced) != 1:
            raise PuzzleValidationError("Generated puzzle must have one forced move at every step")
        cell, value = forced[0]
        receipt = engine.submit_verdict(cell, Status(value.value), expected_token=state.token)
        if receipt.outcome != VerdictOutcome.ACCEPTED:
            raise PuzzleValidationError("Generated progressive proof was rejected")
    remaining()
    return puzzle


def write_generated_puzzle(
    size: int,
    seed: int,
    directory: Path,
    *,
    should_cancel: CancelCheck | None = None,
) -> Path:
    """Write only a certified puzzle, atomically; return its path, never private data to UI."""
    puzzle = generate_puzzle(size, seed, should_cancel=should_cancel)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{puzzle.puzzle_id}.json"

    def without_none(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: without_none(item)
                for key, item in value.items()
                if item is not None
                and not (key == "cells" and "kind" in value and value["kind"] != "EXPLICIT")
            }
        if isinstance(value, (list, tuple)):
            return [without_none(item) for item in value]
        return value

    data = without_none(asdict(puzzle))
    puzzle_from_dict(data)
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=".generating_",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        if should_cancel is not None and should_cancel():
            raise InterruptedError("Puzzle generation cancelled")
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, choices=(3, 4, 5), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parents[1] / "puzzles" / "generated"
    )
    args = parser.parse_args()
    path = write_generated_puzzle(args.size, args.seed, args.output)
    print(f"Saved verified UNIQUE puzzle with a one-move progressive path: {path}")


if __name__ == "__main__":
    main()
