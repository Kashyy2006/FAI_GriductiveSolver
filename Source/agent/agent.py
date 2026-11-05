"""TV4: public-state deductive agent boundary."""

from game.contracts import CancelCheck, Encoder, PublicEngine, SATSolver
from game.models import (
    AutoSolveResult,
    ClassificationResult,
    HintResult,
    PublicState,
    Status,
    VerdictProof,
)


class DeductiveAgent:
    def __init__(self, encoder: Encoder, solver: SATSolver) -> None:
        self._encoder = encoder
        self._solver = solver

    def classify_all(self, state: PublicState) -> ClassificationResult:
        raise NotImplementedError("TV4: consistency first, then entailment per unresolved cell")

    def verify_verdict(self, state: PublicState, character_id: str, status: Status) -> VerdictProof:
        raise NotImplementedError("TV4: trusted callback for Engine, no hidden data")

    def next_hint(self, state: PublicState) -> HintResult:
        raise NotImplementedError("TV4: first forced cell in row-major order, no reveal")

    def auto_solve(
        self, engine: PublicEngine, *, should_cancel: CancelCheck | None = None
    ) -> AutoSolveResult:
        raise NotImplementedError("TV4: submit forced verdicts and record accepted steps")
