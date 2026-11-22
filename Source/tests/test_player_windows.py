"""Exercise real Tk widgets for notes, replay navigation, help and next-case actions."""

from collections.abc import Iterator
from tkinter import Canvas, Misc, TclError, Text, Tk, ttk
from tkinter.font import Font

import pytest

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.puzzle_loader import load_puzzle
from gui.board_view import BoardView
from gui.dialogs import show_help, show_library, show_replay
from gui.main_window import MainWindow
from gui.play_session import LEVELS, SOURCE, PlaySession
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver


@pytest.fixture
def root() -> Iterator[Tk]:
    try:
        root = Tk()
    except TclError as error:
        pytest.skip(f"Tk display unavailable: {error}")
    root.withdraw()
    yield root
    root.destroy()


def descendants(widget: Misc) -> Iterator[Misc]:
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def button(widget: Misc, text: str) -> ttk.Button:
    return next(
        c for c in descendants(widget) if isinstance(c, ttk.Button) and c.cget("text") == text
    )


def stack() -> tuple[GameEngine, DeductiveAgent]:
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    return (
        GameEngine(load_puzzle(SOURCE / "puzzles" / LEVELS[0].key), agent.verify_verdict),
        agent,
    )


def test_replay_next_previous_never_display_future_clues(root: Tk) -> None:
    engine, agent = stack()
    session = PlaySession(engine)
    agent.auto_solve(session)
    final = engine.get_public_state()
    replay = show_replay(root, session.snapshots, session.steps)
    root.update()
    board = next(c for c in descendants(replay) if isinstance(c, BoardView))
    info = next(c for c in descendants(replay) if isinstance(c, Text))
    assert board._state == session.snapshots[0]
    assert board._card_labels["B1"]["clue"].cget("text") == "Clue locked"
    assert str(button(replay, "← Previous").cget("state")) == "disabled"
    button(replay, "Next →").invoke()
    root.update()
    assert board._state == session.snapshots[1]
    assert "Step 1:" in info.get("1.0", "end")
    assert "Step 2:" not in info.get("1.0", "end")
    assert board._card_labels["B2"]["clue"].cget("text") == "Clue locked"
    button(replay, "← Previous").invoke()
    root.update()
    assert board._state == session.snapshots[0]
    assert "Odd criminals" not in info.get("1.0", "end")
    assert board._card_labels["B1"]["clue"].cget("text") == "Clue locked"
    for _ in session.steps:
        button(replay, "Next →").invoke()
    assert str(button(replay, "Next →").cget("state")) == "disabled"
    assert engine.get_public_state() == final


def test_notes_and_results_remain_accessible_at_minimum_size(root: Tk) -> None:
    engine, agent = stack()
    window = MainWindow(root, engine, agent)
    root.geometry("990x680")
    root.deiconify()
    root.update()
    initial = engine.get_public_state()
    window._select_cell("A1")
    window.note_color.set("Purple")
    window._set_mark()
    window._toggle_used()
    label = window.board._card_labels["A1"]["clue"]
    assert Font(font=label.cget("font")).actual("overstrike") == 1
    assert window.board._card_labels["A1"]["note"].cget("text") == "●"
    assert window.board._buttons["A1"].winfo_children()[0].cget("bg") == BoardView.INNOCENT_FILL
    assert engine.get_public_state() == initial
    window._sidebar_canvas.yview_moveto(1)
    root.update()
    results = window.results_button
    assert root.winfo_rooty() <= results.winfo_rooty()
    assert (
        results.winfo_rooty() + results.winfo_height() <= root.winfo_rooty() + root.winfo_height()
    )
    window._toggle_used()
    assert Font(font=label.cget("font")).actual("overstrike") == 0


def test_results_details_and_next_case_button(root: Tk) -> None:
    engine, agent = stack()
    window = MainWindow(root, engine, agent)
    window._level_key = LEVELS[0].key
    result = agent.auto_solve(window.session)
    window.session.queries = list(result.queries)
    window.refresh()
    window._maybe_completed()
    root.update()
    results = window._result_window
    button(results, "Show SAT details ▾").invoke()
    root.update()
    labels = [c.cget("text") for c in descendants(results) if isinstance(c, ttk.Label)]
    assert any("Completed SAT calls: 105" in text for text in labels)
    button(results, "Play next case →").invoke()
    root.update()
    assert window._level_key == LEVELS[1].key
    assert engine.get_public_state().token.version == 0
    assert not results.winfo_exists()


def test_library_filter_and_help_illustrations(root: Tk) -> None:
    selected = []
    library = show_library(root, {}, selected.append)
    root.update()
    tree = next(c for c in descendants(library) if isinstance(c, ttk.Treeview))
    combo = next(c for c in descendants(library) if isinstance(c, ttk.Combobox))
    assert len(tree.get_children()) == len(LEVELS)
    combo.set("Medium")
    combo.event_generate("<<ComboboxSelected>>")
    root.update()
    assert tree.get_children() == tuple(
        level.key for level in LEVELS if level.difficulty == "Medium"
    )
    button(library, "Play / Continue").invoke()
    assert selected == [LEVELS[2].key]
    help_window = show_help(root)
    notebook = next(c for c in descendants(help_window) if isinstance(c, ttk.Notebook))
    notebook.select(1)
    root.update()
    pictures = [c for c in descendants(help_window) if isinstance(c, Canvas)]
    assert len(pictures) == 5
    amber_counts = [
        sum(canvas.itemcget(item, "fill") == "#faebd2" for item in canvas.find_all())
        for canvas in pictures
    ]
    assert amber_counts[0] == 8
    assert amber_counts[1] == 2
    assert amber_counts[-1] == 0
