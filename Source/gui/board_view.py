"""TV5: public board display boundary."""

from collections.abc import Sequence
from tkinter import ttk

from game.models import PublicState


class BoardView(ttk.Frame):
    def render(self, state: PublicState) -> None:
        raise NotImplementedError("TV5: show public cards only")

    def highlight(self, cell_ids: Sequence[str]) -> None:
        raise NotImplementedError("TV5: highlight referenced cells")
