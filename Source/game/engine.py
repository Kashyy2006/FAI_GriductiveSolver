"""Private puzzle ownership and atomic, proof-checked reveal transitions."""

import json
from copy import deepcopy
from dataclasses import asdict
from threading import RLock
from uuid import uuid4

from game.contracts import VerdictVerifier
from game.models import (
    ContractError,
    PublicCharacter,
    PublicState,
    Puzzle,
    PuzzleValidationError,
    SolutionMismatchError,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictProof,
    VerdictResult,
)
from game.puzzle_loader import puzzle_from_dict


def _validated_copy(puzzle: Puzzle) -> Puzzle:
    """Revalidate manually built models before replacing any live game state."""
    if not isinstance(puzzle, Puzzle):
        raise ContractError("Expected a Puzzle instance")
    try:
        data = json.loads(json.dumps(asdict(puzzle)))
        for character in data["characters"]:
            clue = character["clue"]
            character["clue"] = {key: value for key, value in clue.items() if value is not None}
            region = character["clue"].get("region")
            if region is not None:
                character["clue"]["region"] = {
                    key: value
                    for key, value in region.items()
                    if value is not None
                    and not (key == "cells" and value == [] and region["kind"] != "EXPLICIT")
                }
    except (TypeError, ValueError, KeyError, AttributeError) as error:
        raise PuzzleValidationError("Malformed Puzzle model") from error
    return puzzle_from_dict(data)


class GameEngine:
    """Expose public snapshots; only an engine-invoked verifier may permit reveal."""

    def __init__(self, puzzle: Puzzle, verifier: VerdictVerifier) -> None:
        if not callable(verifier):
            raise ContractError("verifier must be callable")
        self._lock = RLock()
        self._verifier = verifier
        self.load(puzzle)

    def _snapshot(self) -> PublicState:
        """Build a detached snapshot while the caller holds the engine lock."""
        return PublicState(
            self._puzzle.puzzle_id,
            self._puzzle.size,
            self._token,
            tuple(
                PublicCharacter(
                    c.id,
                    c.name,
                    c.profession,
                    c.row,
                    c.col,
                    c.hidden_status if c.id in self._revealed else None,
                    deepcopy(c.clue) if c.id in self._revealed else None,
                )
                for c in self._puzzle.characters
            ),
        )

    def get_public_state(self) -> PublicState:
        """Return all metadata but only the verdicts and clues already revealed."""
        with self._lock:
            return self._snapshot()

    def _reset(self) -> PublicState:
        self._revealed = set(self._puzzle.initially_revealed)
        self._token = StateToken(str(uuid4()), 0)
        return self._snapshot()

    def load(self, puzzle: Puzzle) -> PublicState:
        """Validate first, then atomically install a puzzle with a fresh session."""
        validated = _validated_copy(puzzle)
        with self._lock:
            self._puzzle = validated
            self._by_id = {c.id: c for c in validated.characters}
            return self._reset()

    def restart(self) -> PublicState:
        """Restore only initially revealed cards and invalidate all older tokens."""
        with self._lock:
            return self._reset()

    def submit_verdict(
        self, character_id: str, status: Status, *, expected_token: StateToken
    ) -> VerdictResult:
        """Verify outside the lock and commit only against the same state token."""
        with self._lock:
            if not isinstance(character_id, str) or character_id not in self._by_id:
                raise ContractError("Unknown character ID")
            if not isinstance(status, Status):
                raise ContractError("status must be a Status value")
            if (
                not isinstance(expected_token, StateToken)
                or not isinstance(expected_token.session_id, str)
                or not expected_token.session_id
                or type(expected_token.version) is not int
                or expected_token.version < 0
            ):
                raise ContractError("Expected a valid StateToken")
            if expected_token != self._token:
                return VerdictResult(VerdictOutcome.STALE_STATE, self._snapshot(), None, None)
            if character_id in self._revealed:
                return VerdictResult(VerdictOutcome.ALREADY_REVEALED, self._snapshot(), None, None)
            snapshot = self._snapshot()

        # Never hold the lock over a potentially expensive SAT call.
        proof = self._verifier(snapshot, character_id, status)
        with self._lock:
            if expected_token != self._token:
                return VerdictResult(
                    VerdictOutcome.STALE_STATE,
                    self._snapshot(),
                    None,
                    deepcopy(proof) if isinstance(proof, VerdictProof) else None,
                )
            if (
                not isinstance(proof, VerdictProof)
                or proof.token != expected_token
                or proof.character_id != character_id
                or not isinstance(proof.requested_status, Status)
                or proof.requested_status != status
                or not isinstance(proof.outcome, VerdictOutcome)
                or proof.outcome
                not in {
                    VerdictOutcome.ACCEPTED,
                    VerdictOutcome.NOT_PROVABLE,
                    VerdictOutcome.CONTRADICTED,
                    VerdictOutcome.INCONSISTENT,
                }
            ):
                raise ContractError("Verifier returned a malformed or mismatched proof")
            proof = deepcopy(proof)
            if proof.outcome != VerdictOutcome.ACCEPTED:
                return VerdictResult(proof.outcome, self._snapshot(), None, proof)
            character = self._by_id[character_id]
            if character.hidden_status != status:
                raise SolutionMismatchError("Proved verdict conflicts with the puzzle solution")
            self._revealed.add(character_id)
            self._token = StateToken(self._token.session_id, self._token.version + 1)
            return VerdictResult(
                VerdictOutcome.ACCEPTED, self._snapshot(), deepcopy(character.clue), proof
            )
