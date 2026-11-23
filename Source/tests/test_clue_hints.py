"""Clue hints prove useful support using only public snapshots and record actual calls."""

from copy import deepcopy
from dataclasses import replace

from agent.agent import DeductiveAgent
from agent.hints import find_clue_hint
from game.engine import GameEngine
from game.generator import generate_puzzle
from game.models import Clue, ClueType, VerdictOutcome
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver


def test_clue_support_is_sufficient_irreducible_public_and_read_only() -> None:
    class LedgerSolver(DPLLSolver):
        calls = 0

        def solve(self, *args, **kwargs):
            self.calls += 1
            return super().solve(*args, **kwargs)

    puzzle = generate_puzzle(4, 0)
    solver = LedgerSolver()
    agent = DeductiveAgent(CNFEncoder(), solver)
    engine = GameEngine(puzzle, agent.verify_verdict)
    initial = engine.get_public_state()
    original = deepcopy(initial)
    hint, support = find_clue_hint(initial, agent)
    assert len(hint.queries) == solver.calls
    assert hint.token == initial.token
    assert hint.active_clue_ids == CNFEncoder().encode(initial).active_clue_ids
    assert len(support) in (3, 4)
    owners = [c for c in initial.characters if c.clue and c.clue.id in support]
    assert len(owners) == len(support) and all(c.status is not None for c in owners)
    for removed in (*support, None):
        trial = replace(
            initial,
            characters=tuple(
                replace(c, clue=Clue(c.clue.id, ClueType.REMARK, text="Omitted."))
                if c.clue and (c.clue.id not in support or c.clue.id == removed)
                else c
                for c in initial.characters
            ),
        )
        proof = agent.verify_verdict(trial, hint.character_id, hint.status)
        assert proof.outcome == (
            VerdictOutcome.ACCEPTED if removed is None else VerdictOutcome.NOT_PROVABLE
        )
    assert engine.get_public_state() == initial == original


def test_canonical_next_hint_still_lists_all_active_public_clues() -> None:
    puzzle = generate_puzzle(5, 99)
    encoder = CNFEncoder()
    agent = DeductiveAgent(encoder, DPLLSolver())
    initial = GameEngine(puzzle, agent.verify_verdict).get_public_state()
    assert agent.next_hint(initial).active_clue_ids == encoder.encode(initial).active_clue_ids
    hint, support = find_clue_hint(initial, agent)
    assert hint.active_clue_ids == encoder.encode(initial).active_clue_ids
    assert len(support) < len(hint.active_clue_ids)
