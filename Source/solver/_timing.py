"""Shared wall-clock deadlines for SAT and validation operations."""

from math import isfinite
from time import perf_counter

from game.models import ContractError, SolverTimeout


class _Deadline:
    """Use one deadline across all stages and nested SAT calls."""

    def __init__(self, timeout_seconds: float | None) -> None:
        if timeout_seconds is None:
            self._end: float | None = None
            return
        if type(timeout_seconds) not in (int, float):
            raise ContractError("Timeout must be None or a positive finite number")
        try:
            seconds = float(timeout_seconds)
        except OverflowError as error:
            raise ContractError("Timeout must be finite") from error
        if not isfinite(seconds) or seconds <= 0:
            raise ContractError("Timeout must be positive and finite")
        self._end = perf_counter() + seconds

    def remaining(self) -> float | None:
        """Return the remaining budget, raising rather than inventing UNSAT."""
        if self._end is None:
            return None
        remaining = self._end - perf_counter()
        if remaining <= 0:
            raise SolverTimeout("SAT operation exceeded its wall-clock deadline")
        return remaining

    def check(self) -> None:
        self.remaining()
