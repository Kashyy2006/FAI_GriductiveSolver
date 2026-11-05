"""TV3: self-implemented DPLL boundary."""

from collections.abc import Sequence

from game.models import CNF, Literal, SATResult


class DPLLSolver:
    def solve(
        self,
        cnf: CNF,
        variables: Sequence[int],
        assumptions: Sequence[Literal] = (),
        *,
        timeout_seconds: float | None = None,
    ) -> SATResult:
        raise NotImplementedError("TV3: DPLL, complete assignment and per-call statistics")
