"""TV2: reusable CNF encoding boundary."""

from game.models import EncodingResult, PublicState


class CNFEncoder:
    def encode(self, state: PublicState) -> EncodingResult:
        raise NotImplementedError("TV2: deterministic encoding of public clues and statuses")
