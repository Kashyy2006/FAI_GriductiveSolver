"""Find a sufficient set of public clues without changing the canonical next_hint API."""

from dataclasses import replace

from agent.agent import DeductiveAgent
from game.models import Clue, ClueType, HintResult, PublicState, VerdictOutcome


def find_clue_hint(
    state: PublicState,
    agent: DeductiveAgent,
) -> tuple[HintResult, tuple[str, ...]]:
    """Delete dispensable clues from a public proof, retaining all known verdicts.

    This is a sufficient, deletion-irreducible support, not a minimum-size explanation.
    Support is returned separately; HintResult.active_clue_ids keeps its v1 meaning.
    Omitted clues become tautological REMARKs in detached analysis copies only.
    Engine, gameplay snapshots and narrative clues are never modified.
    """
    hint = agent.next_hint(state)
    if hint.character_id is None or hint.status is None:
        return hint, ()
    working = state
    queries = list(hint.queries)
    for character in state.characters:
        if character.clue is None or character.clue.type == ClueType.REMARK:
            continue
        trial = replace(
            working,
            characters=tuple(
                replace(
                    c, clue=Clue(c.clue.id, ClueType.REMARK, text="Omitted for support analysis.")
                )
                if c.id == character.id
                else c
                for c in working.characters
            ),
        )
        proof = agent.verify_verdict(trial, hint.character_id, hint.status)
        queries.extend(proof.queries)
        if proof.outcome == VerdictOutcome.ACCEPTED:
            working = trial
    support = tuple(
        sorted(
            c.clue.id
            for c in working.characters
            if c.clue is not None and c.clue.type != ClueType.REMARK
        )
    )
    return replace(hint, queries=tuple(queries)), support
