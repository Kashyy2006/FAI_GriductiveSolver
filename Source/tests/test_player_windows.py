"""Exercise real Tk widgets for notes, replay navigation, help and next-case actions."""

from collections.abc import Iterator
from tkinter import Canvas, Misc, TclError, Text, Tk, ttk
from tkinter.font import Font

import pytest

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.puzzle_loader import load_puzzle
from gui import theme
from gui.board_view import BoardView
from gui.clue_text import format_clue
from gui.dialogs import show_generator, show_help, show_library, show_replay
from gui.main_window import MainWindow
from gui.play_session import LEVELS, MARK_COLORS, SOURCE, PlaySession, available_levels
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
    assert "Odd number of criminals" not in info.get("1.0", "end")
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
    card = window.board._buttons["A1"]
    assert card.itemcget("card_border", "fill") == MARK_COLORS["Purple"]
    assert card.itemcget("card_border", "outline") == BoardView.HIGHLIGHT
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


def test_temporary_frame_survives_highlighting_and_can_be_cleared(root: Tk) -> None:
    engine, agent = stack()
    initial = engine.get_public_state()
    session = PlaySession(engine)
    agent.auto_solve(session)
    final = engine.get_public_state()
    criminal = next(c.id for c in final.characters if c.status.value == "CRIMINAL")
    board = BoardView(root, lambda _: None)
    board.pack()
    for state, cell, fill in (
        (initial, "A1", BoardView.INNOCENT_FILL),
        (initial, "B1", BoardView.CARD),
        (final, criminal, BoardView.CRIMINAL_FILL),
    ):
        board.highlight(())
        board.render(state)
        board.set_notes({cell: "Blue"}, set())
        card = board._buttons[cell]
        assert card.itemcget("card_border", "fill") == MARK_COLORS["Blue"]
        assert card.winfo_children()[0].cget("bg") == fill
        board.highlight((cell,))
        assert card.itemcget("card_border", "fill") == MARK_COLORS["Blue"]
        assert card.itemcget("card_border", "outline") == BoardView.HIGHLIGHT
        board.pulse((cell,))
        assert card.itemcget("card_border", "fill") == MARK_COLORS["Blue"]
        board.cancel_animations()
        board.highlight(())
        board.set_notes({}, set())
        expected = BoardView.INNOCENT if cell == "A1" else BoardView.BORDER
        if state == final:
            expected = BoardView.CRIMINAL
        assert card.itemcget("card_border", "fill") == expected
    assert engine.get_public_state() == final


def test_help_button_is_next_to_case_notes(root: Tk, monkeypatch: pytest.MonkeyPatch) -> None:
    engine, agent = stack()
    window = MainWindow(root, engine, agent)
    root.update()
    help_button = window.help_button
    heading = next(
        c
        for c in help_button.master.winfo_children()
        if isinstance(c, ttk.Label) and c.cget("text") == "CASE NOTES"
    )
    assert help_button.winfo_y() <= heading.winfo_y() + heading.winfo_height()
    assert 0 <= help_button.winfo_x() - (heading.winfo_x() + heading.winfo_width()) <= 12
    opened = []
    monkeypatch.setattr("gui.main_window.show_help", lambda parent: opened.append(parent))
    help_button.invoke()
    assert opened == [root]


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
    assert tree.get_children() == tuple(level.key for level in available_levels())
    combo.set("Medium")
    combo.event_generate("<<ComboboxSelected>>")
    root.update()
    assert tree.get_children() == tuple(
        level.key for level in LEVELS if level.difficulty == "Medium"
    )
    button(library, "Play / Continue").invoke()
    assert selected == [next(level.key for level in LEVELS if level.difficulty == "Medium")]
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


def test_generator_form_validates_seed_and_passes_fixed_size(root: Tk) -> None:
    selected = []
    dialog = show_generator(root, lambda size, seed: selected.append((size, seed)))
    root.update()
    combo = next(c for c in descendants(dialog) if isinstance(c, ttk.Combobox))
    entry = next(c for c in descendants(dialog) if type(c) is ttk.Entry)
    combo.set("5 × 5")
    entry.delete(0, "end")
    entry.insert(0, "-1")
    button(dialog, "Generate & Play").invoke()
    assert selected == [] and dialog.winfo_exists()
    entry.delete(0, "end")
    entry.insert(0, "31415")
    button(dialog, "Generate & Play").invoke()
    assert selected == [(5, 31415)] and not dialog.winfo_exists()


def test_long_card_clue_scrolls_to_last_line_without_changing_game(root: Tk) -> None:
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    engine = GameEngine(load_puzzle(SOURCE / "puzzles/5x5/harbor_case.json"), agent.verify_verdict)
    result = agent.auto_solve(engine)
    before = engine.get_public_state()
    window = MainWindow(root, engine, agent)
    root.geometry("990x680")
    root.deiconify()
    root.update()
    last = result.steps[-1].character_id
    character = next(c for c in before.characters if c.id == last)
    label = window.board._card_labels[last]["clue"]
    viewport = window.board._clue_views[last]
    scrollbar = window.board._clue_scrollbars[last]
    assert label.cget("text") == format_clue(character.clue, before)
    board_canvas = window.board._canvas
    assert board_canvas.yview()[1] < 1
    board_scroll = window.board._board_scrollbar
    board_scroll.tk.call(board_scroll.cget("command"), "moveto", 1)
    root.update()
    bottom_card = window.board._buttons["E5"]
    assert bottom_card.winfo_rooty() >= board_canvas.winfo_rooty()
    assert (
        bottom_card.winfo_rooty() + bottom_card.winfo_height()
        <= board_canvas.winfo_rooty() + board_canvas.winfo_height()
    )
    assert viewport.winfo_height() >= Font(font=label.cget("font")).metrics("linespace")
    assert viewport.yview()[1] < 1
    assert scrollbar.winfo_ismapped()
    scrollbar.tk.call(scrollbar.cget("command"), "moveto", 1)
    root.update()
    assert viewport.yview()[0] > 0 and viewport.yview()[1] >= 0.999
    assert viewport.canvasy(viewport.winfo_height()) >= viewport.bbox("all")[3] - 1
    label.event_generate("<MouseWheel>", delta=120)
    root.update()
    assert viewport.yview()[1] < 1
    position = viewport.yview()
    board_position = board_canvas.yview()
    window._select_cell(last)
    root.update()
    assert viewport.yview() == position
    assert board_canvas.yview() == board_position
    assert engine.get_public_state() == before
    engine.restart()
    window.refresh()
    root.update()
    assert label.cget("text") == "Clue locked"
    assert viewport.yview() == (0.0, 1.0)
    assert not scrollbar.winfo_ismapped()
    assert board_canvas.yview()[0] == 0


def test_pencil_note_buttons_explain_their_roles_and_never_submit_a_verdict(root: Tk) -> None:
    engine, agent = stack()
    window = MainWindow(root, engine, agent)
    root.deiconify()
    root.update()
    before = engine.get_public_state()
    window._select_cell("B1")
    for color, text in (
        ("Blue", "Maybe Innocent"),
        ("Purple", "Maybe Criminal"),
        ("Amber", "Review"),
    ):
        note = window.note_buttons[color]
        assert note.cget("text") == text
        note.invoke()
        root.update()
        assert window.session.marks == {"B1": color}
        assert text in window.selected_note_label.cget("text")
        assert window.note_help_label.cget("text")
        assert note.instate(["selected"])
        assert engine.get_public_state() == before
        assert window.session.hints == window.session.rejected == 0
    window._busy = True
    window._update_controls()
    window.note_buttons["Purple"].invoke()
    assert window.session.marks == {"B1": "Amber"}
    window._busy = False
    window._update_controls()
    window.clear_note_button.invoke()
    assert window.session.marks == {}
    assert window.selected_note_label.cget("text") == "No pencil note"
    assert engine.get_public_state() == before


def test_scrollbar_tracks_match_their_current_surfaces(root: Tk) -> None:
    engine, agent = stack()
    window = MainWindow(root, engine, agent)
    root.update()
    styles = ttk.Style(root)
    board = window.board
    assert styles.lookup(board._board_scrollbar.cget("style"), "troughcolor") == theme.PAGE
    for cell, fill in (("A1", BoardView.INNOCENT_FILL), ("B1", BoardView.CARD)):
        scroll = board._clue_scrollbars[cell]
        assert styles.lookup(scroll.cget("style"), "troughcolor") == fill
        assert styles.lookup(scroll.cget("style"), "background") != fill
    board.highlight(("B1",))
    scroll = board._clue_scrollbars["B1"]
    assert styles.lookup(scroll.cget("style"), "troughcolor") == BoardView.HIGHLIGHT_FILL
    board.set_notes({"B1": "Blue"}, set())
    assert styles.lookup(scroll.cget("style"), "troughcolor") == BoardView.HIGHLIGHT_FILL
