"""Dependency-injection protocols; implementations must preserve these APIs."""

from collections.abc import Callable, Sequence
from typing import Protocol

from game.models import (
    CNF,
    EncodingResult,
    Literal,
    PublicState,
    SATResult,
    StateToken,
    Status,
    VerdictProof,
    VerdictResult,
)


class Encoder(Protocol):
    def encode(self, state: PublicState) -> EncodingResult: ...


class SATSolver(Protocol):
    def solve(
        self,
        cnf: CNF,
        variables: Sequence[int],
        assumptions: Sequence[Literal] = (),
        *,
        timeout_seconds: float | None = None,
    ) -> SATResult: ...


class PublicEngine(Protocol):
    """The only engine interface the Agent's loop may receive."""

    def get_public_state(self) -> PublicState: ...

    def submit_verdict(
        self, character_id: str, status: Status, *, expected_token: StateToken
    ) -> VerdictResult: ...


VerdictVerifier = Callable[[PublicState, str, Status], VerdictProof]
CancelCheck = Callable[[], bool]
