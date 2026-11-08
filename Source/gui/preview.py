"""Static public-state preview for checking the Tkinter layout before integration."""

from tkinter import Tk
from typing import cast

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.models import (
    Clue,
    ClueType,
    PublicCharacter,
    PublicState,
    StateToken,
    Status,
)
from gui.main_window import MainWindow


class _PreviewEngine:
    """Supply a fixed public snapshot without emulating gameplay behavior."""

    def __init__(self) -> None:
        self._state = _preview_state()

    def get_public_state(self) -> PublicState:
        return self._state


class _PreviewWindow(MainWindow):
    """Display the real application layout with all game actions disabled."""

    def _update_controls(self) -> None:
        super()._update_controls()
        for button in (
            self.criminal_button,
            self.innocent_button,
            self.hint_button,
            self.solve_button,
            self.load_button,
            self.restart_button,
        ):
            button.configure(state="disabled")
        self.status_label.configure(text="Preview only · gameplay controls are disabled")


def _preview_state() -> PublicState:
    names = (
        ("Alice Morgan", "Doctor"),
        ("Ben Carter", "Baker"),
        ("Cara Singh", "Teacher"),
        ("David Kim", "Archivist"),
        ("Eva Brooks", "Engineer"),
        ("Felix Gray", "Gardener"),
        ("Grace Chen", "Reporter"),
        ("Hugo Patel", "Mechanic"),
        ("Iris Wells", "Pilot"),
    )
    characters = []
    for index, (name, profession) in enumerate(names):
        row, col = divmod(index, 3)
        cell_id = f"{chr(65 + col)}{row + 1}"
        revealed = index == 0
        characters.append(
            PublicCharacter(
                id=cell_id,
                name=name,
                profession=profession,
                row=row,
                col=col,
                status=Status.INNOCENT if revealed else None,
                clue=(
                    Clue(
                        id="preview_clue_a1",
                        type=ClueType.FACT,
                        person="B1",
                        status=Status.CRIMINAL,
                    )
                    if revealed
                    else None
                ),
            )
        )
    return PublicState(
        puzzle_id="preview_case",
        size=3,
        token=StateToken("static-preview", 0),
        characters=tuple(characters),
    )


def run_preview() -> None:
    """Open a static board preview without constructing unfinished backend modules."""
    root = Tk()
    root.title("GRIDUCTIVE / Static preview")
    preview_engine = cast(GameEngine, _PreviewEngine())
    preview_agent = cast(DeductiveAgent, object())
    _PreviewWindow(root, preview_engine, preview_agent)
    root.title("GRIDUCTIVE / Static preview")
    root.mainloop()


if __name__ == "__main__":
    run_preview()
