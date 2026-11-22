"""Headless controller tests with real backends and controlled worker scheduling."""

import json
import threading
from pathlib import Path
from tkinter import TclError, Tk
from typing import Callable

import pytest

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.models import (
    Clue,
    ClueType,
    PuzzleValidationError,
    Region,
    RegionType,
    SolutionMismatchError,
    SolveOutcome,
    SolverTimeout,
    Status,
)
from game.puzzle_loader import load_puzzle
from gui.board_view import BoardView
from gui.main_window import MainWindow
from gui.play_session import LEVELS, ProgressStore
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver

SOURCE = Path(__file__).resolve().parents[1]
REAL_THREAD = threading.Thread


class Widget:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}
        self.destroyed = False
        self.highlighted: tuple[str, ...] = ()
        self.contents = ""

    def configure(self, **kwargs: object) -> None:
        self.values.update(kwargs)

    def render(self, state: object) -> None:
        self.state = state

    def highlight(self, cells: tuple[str, ...]) -> None:
        self.highlighted = tuple(cells)

    def set_notes(self, marks: dict[str, str], used_clues: set[str]) -> None:
        self.marks, self.used_clues = dict(marks), set(used_clues)

    def flip_card(
        self,
        character_id: str,
        on_flip: Callable[[], None],
        on_done: Callable[[], None] | None = None,
    ) -> None:
        del character_id
        on_flip()
        if on_done is not None:
            on_done()

    def pulse(self, cells: tuple[str, ...]) -> None:
        self.highlight(cells)

    def cancel_animations(self) -> None:
        pass

    def pack(self, **kwargs: object) -> None:
        pass

    def set(self, *args: object) -> None:
        self.values["value"] = args[0] if args else None

    def get(self) -> object:
        return self.values.get("value")

    def yview(self, *args: object) -> None:
        pass

    def insert(self, index: str, contents: str) -> None:
        self.contents += contents

    def after(self, delay: int, callback: Callable[[], None]) -> None:
        pass

    def protocol(self, *args: object) -> None:
        pass

    def title(self, title: str) -> None:
        self.values["title"] = title

    def geometry(self, size: str) -> None:
        self.values["geometry"] = size

    def winfo_exists(self) -> bool:
        return not self.destroyed

    def destroy(self) -> None:
        self.destroyed = True


class DeferredThread:
    pending: list["DeferredThread"] = []

    def __init__(self, *, target: Callable[[], None], **kwargs: object) -> None:
        self.target = target

    def start(self) -> None:
        self.pending.append(self)

    def run(self) -> None:
        self.target()


@pytest.fixture
def ui(monkeypatch: pytest.MonkeyPatch) -> MainWindow:
    def build(window: MainWindow) -> None:
        for name in (
            "board",
            "puzzle_title",
            "progress_label",
            "selected_label",
            "clue_label",
            "status_label",
            "criminal_button",
            "innocent_button",
            "hint_button",
            "solve_button",
            "load_button",
            "restart_button",
            "view_trace_button",
            "save_trace_button",
            "note_color",
            "note_picker",
            "used_button",
            "clock_label",
            "results_button",
        ):
            setattr(window, name, Widget())

    monkeypatch.setattr(MainWindow, "_configure_window", lambda self: None)
    monkeypatch.setattr(MainWindow, "_build_layout", build)
    monkeypatch.setattr(MainWindow, "_show_toast", lambda self, title, message, tone: None)
    monkeypatch.setattr(MainWindow, "_show_results", lambda self: None)
    DeferredThread.pending = []
    monkeypatch.setattr("gui.main_window.threading.Thread", DeferredThread)
    agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
    engine = GameEngine(load_puzzle(SOURCE / "puzzles/3x3/example_01.json"), agent.verify_verdict)
    window = MainWindow(Widget(), engine, agent)
    window.errors = []
    window._show_error = lambda title, error: window.errors.append((title, error))
    return window


def run_task(ui: MainWindow) -> None:
    DeferredThread.pending.pop(0).run()
    ui._poll_messages()


def reset(ui: MainWindow, mode: str, monkeypatch: pytest.MonkeyPatch) -> None:
    if mode == "restart":
        ui._restart()
    else:
        ui._load_path(SOURCE / "puzzles/4x4/example_01.json")


@pytest.mark.parametrize("mode", ["restart", "load"])
def test_worker_queued_before_reset_never_solves_replacement_board(
    ui: MainWindow, mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    ui._auto_solve()
    old_event = ui._cancel_event
    old_token = ui._state.token
    reset(ui, mode, monkeypatch)
    fresh = ui.engine.get_public_state()
    assert fresh.token.session_id != old_token.session_id
    assert fresh.token.version == old_token.version == 0
    assert old_event.is_set()
    run_task(ui)
    assert ui.engine.get_public_state() == fresh
    assert ui._last_solve is None and not ui._busy
    assert ui.clue_label.values["text"] == ui._EMPTY_CLUE


@pytest.mark.parametrize("mode", ["restart", "load"])
def test_session_guard_also_protects_action_that_passed_worker_preflight(
    ui: MainWindow, mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    actions = []
    monkeypatch.setattr(
        ui, "_start_task", lambda kind, action, token, **kwargs: actions.append(action)
    )
    ui._auto_solve()
    # No task event was registered, so safety here depends on captured session.
    reset(ui, mode, monkeypatch)
    fresh = ui.engine.get_public_state()
    result = actions[0]()
    assert result.outcome == SolveOutcome.CANCELLED
    assert result.steps == ()
    assert ui.engine.get_public_state() == fresh


@pytest.mark.parametrize("mode", ["restart", "load"])
def test_reset_during_active_sat_call_does_not_allow_old_worker_to_reveal(
    ui: MainWindow, mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    started, release = threading.Event(), threading.Event()
    threads = []

    class BlockingSolver(DPLLSolver):
        blocked = False

        def solve(self, *args, **kwargs):
            if not self.blocked:
                self.blocked = True
                started.set()
                assert release.wait(3), "Test failed to release SAT worker"
            return super().solve(*args, **kwargs)

    solver = BlockingSolver()
    ui.agent = DeductiveAgent(CNFEncoder(), solver)
    # Match the composition root: Engine invokes this Agent's verifier.
    ui.engine = GameEngine(
        load_puzzle(SOURCE / "puzzles/3x3/example_01.json"), ui.agent.verify_verdict
    )
    ui.refresh()

    def start_thread(**kwargs):
        thread = REAL_THREAD(**kwargs)
        threads.append(thread)
        return thread

    monkeypatch.setattr("gui.main_window.threading.Thread", start_thread)
    ui._auto_solve()
    try:
        assert started.wait(3), "SAT worker never started"
        reset(ui, mode, monkeypatch)
        fresh = ui.engine.get_public_state()
    finally:
        release.set()
        for thread in threads:
            thread.join(3)
            assert not thread.is_alive()
    ui._poll_messages()
    assert ui.engine.get_public_state() == fresh
    assert fresh.token.version == 0
    assert ui._last_solve is None and not ui._busy


def test_old_message_cannot_clear_busy_flag_or_replace_new_task(ui: MainWindow) -> None:
    ui._request_hint()
    old_id, old_token = ui._active_task, ui._state.token
    ui._restart()
    ui._auto_solve()
    new_id = ui._active_task
    ui._messages.put((old_id, "hint", RuntimeError("old task"), old_token))
    ui._poll_messages()
    assert ui._active_task is new_id and ui._busy
    assert ui.errors == []
    assert ui.solve_button.values["state"] == "disabled"
    # Old pre-reset task is cancelled; the new task still completes normally.
    run_task(ui)
    assert ui._busy
    run_task(ui)
    assert ui._last_solve.outcome == SolveOutcome.SOLVED
    assert not ui._busy


@pytest.mark.parametrize("mode", ["restart", "load"])
def test_reset_clears_sidebar_selection_highlights_and_trace(
    ui: MainWindow, mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    ui._auto_solve()
    run_task(ui)
    ui._select_cell("B1")
    assert ui.clue_label.values["text"] != ui._EMPTY_CLUE
    popup = Widget()
    ui._trace_window = popup
    assert ui._last_solve is not None
    reset(ui, mode, monkeypatch)
    assert ui._selected_id is None
    assert ui.clue_label.values["text"] == ui._EMPTY_CLUE
    assert ui.selected_label.values["text"] == "Select a card"
    assert ui.board.highlighted == ()
    assert ui._last_solve is None
    assert popup.destroyed and ui._trace_window is None
    assert (
        ui.view_trace_button.values["state"] == ui.save_trace_button.values["state"] == "disabled"
    )
    ui._select_cell("B1")
    assert "sealed" in ui.clue_label.values["text"]


def test_verdict_refresh_updates_selected_clue_and_unknown_does_not_reveal(ui: MainWindow) -> None:
    ui._select_cell("A2")
    initial = ui.engine.get_public_state()
    ui._submit(Status.CRIMINAL)
    run_task(ui)
    assert ui.engine.get_public_state() == initial
    assert "Not provable" in ui.status_label.values["text"]
    ui._select_cell("B1")
    ui._submit(Status.INNOCENT)
    run_task(ui)
    card = next(c for c in ui._state.characters if c.id == "B1")
    assert card.clue is not None
    assert ui.clue_label.values["text"] == ui._describe_clue(card.clue)


def test_auto_solve_trace_can_be_viewed_and_saved(
    ui: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ui._auto_solve()
    run_task(ui)
    assert ui._last_solve.outcome == SolveOutcome.SOLVED
    assert len(ui._last_solve.steps) == 8 and len(ui._last_solve.queries) == 105
    assert ui.view_trace_button.values["state"] == ui.save_trace_button.values["state"] == "normal"
    popup = Widget()
    viewed = []
    monkeypatch.setattr(
        "gui.main_window.show_replay",
        lambda root, snapshots, steps: (viewed.append((snapshots, steps)) or popup),
    )
    ui._view_trace()
    snapshots, steps = viewed[0]
    assert len(snapshots) == 9 and len(steps) == 8
    assert snapshots[0].characters[1].clue is None
    assert snapshots[1].characters[1].clue == steps[0].newly_revealed_clue
    assert steps[0].character_id == "B1" and steps[0].verdict == Status.INNOCENT
    assert ui._trace_window is popup
    destination = tmp_path / "nested" / "trace.json"
    monkeypatch.setattr(
        "gui.main_window.filedialog.asksaveasfilename", lambda **kwargs: str(destination)
    )
    ui._save_trace()
    data = json.loads(destination.read_text(encoding="utf-8"))
    assert len(data) == 8
    assert data[0]["active_clue_ids"] == list(ui._last_solve.steps[0].active_clue_ids)
    assert data[0]["newly_revealed_clue"]["id"] == ui._last_solve.steps[0].newly_revealed_clue.id
    assert ui.status_label.values["text"] == "Trace saved."


def test_trace_cancel_and_io_error_are_handled_without_losing_result(
    ui: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ui._auto_solve()
    run_task(ui)
    result = ui._last_solve
    monkeypatch.setattr("gui.main_window.filedialog.asksaveasfilename", lambda **kwargs: "")
    ui._save_trace()
    assert ui.errors == []
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("blocker", encoding="utf-8")
    monkeypatch.setattr(
        "gui.main_window.filedialog.asksaveasfilename", lambda **kwargs: str(blocker / "trace.json")
    )
    ui._save_trace()
    assert isinstance(ui.errors[-1][1], OSError)
    assert ui._last_solve is result


def test_failed_load_preserves_existing_game_and_running_task(
    ui: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ui._request_hint()
    token, event = ui._state.token, ui._cancel_event
    ui._load_path(tmp_path / "missing.json")
    assert ui._state.token == token
    assert ui._busy and not event.is_set()
    assert len(ui.errors) == 1
    run_task(ui)
    assert not ui._busy


def test_close_cancels_pending_worker(ui: MainWindow) -> None:
    ui._auto_solve()
    event = ui._cancel_event
    before = ui.engine.get_public_state()
    ui._close()
    assert event.is_set() and ui.root.destroyed
    DeferredThread.pending.pop(0).run()
    assert ui.engine.get_public_state() == before


def test_empty_trace_is_viewable_and_exportable_for_stuck_run(
    ui: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ui.engine.load(load_puzzle(SOURCE / "experiments/puzzles/synthetic_3x3_stuck_unique.json"))
    ui.refresh()
    ui._auto_solve()
    run_task(ui)
    assert ui._last_solve.outcome == SolveOutcome.STUCK
    assert ui.session.steps == [] and len(ui.session.snapshots) == 1
    destination = tmp_path / "empty.json"
    monkeypatch.setattr(
        "gui.main_window.filedialog.asksaveasfilename", lambda **kwargs: str(destination)
    )
    ui._save_trace()
    assert json.loads(destination.read_text(encoding="utf-8")) == []


def test_clue_highlight_resolves_fact_binary_and_all_region_types(ui: MainWindow) -> None:
    ui.engine.load(load_puzzle(SOURCE / "puzzles/4x4/example_01.json"))
    ui.refresh()

    fact = Clue(id="c1", type=ClueType.FACT, person="B1", status=Status.INNOCENT)
    same = Clue(id="c2", type=ClueType.SAME, first="A1", second="C2")
    diff = Clue(id="c3", type=ClueType.DIFFERENT, first="B2", second="D4")
    row = Clue(id="c4", type=ClueType.EXACTLY, region=Region(kind=RegionType.ROW, index=1), k=1)
    col = Clue(id="c5", type=ClueType.AT_LEAST, region=Region(kind=RegionType.COLUMN, index=2), k=1)
    nbrs = Clue(
        id="c6", type=ClueType.AT_MOST, region=Region(kind=RegionType.NEIGHBORS, cell="A1"), k=2
    )
    explicit = Clue(
        id="c7", type=ClueType.EVEN, region=Region(kind=RegionType.EXPLICIT, cells=("A1", "D4"))
    )
    common = Clue(
        id="c8",
        type=ClueType.ODD,
        region=Region(kind=RegionType.COMMON_NEIGHBORS, first="A1", second="C1"),
    )
    empty_common = Clue(
        id="c9",
        type=ClueType.EVEN,
        region=Region(kind=RegionType.COMMON_NEIGHBORS, first="A1", second="D4"),
    )

    assert ui._clue_cells(fact, "A1") == ("B1",)
    assert ui._clue_cells(same, "A1") == ("A1", "C2")
    assert ui._clue_cells(diff, "A1") == ("B2", "D4")
    assert ui._clue_cells(row, "A1") == ("A2", "B2", "C2", "D2")
    assert ui._clue_cells(col, "A1") == ("C1", "C2", "C3", "C4")
    assert ui._clue_cells(nbrs, "A1") == ("B1", "A2", "B2")
    assert ui._clue_cells(explicit, "A1") == ("A1", "D4")
    assert ui._clue_cells(common, "A1") == ("B1", "B2")
    assert ui._clue_cells(empty_common, "A1") == ()


def test_contradicted_verdict_and_hint_preserve_state_and_highlight_on_accept(
    ui: MainWindow,
) -> None:
    initial = ui.engine.get_public_state()
    ui._request_hint()
    run_task(ui)
    assert ui.engine.get_public_state() == initial
    assert ui._selected_id == "B1"
    assert ui.board.highlighted == ("B1",)
    assert "Hint: B1 is forced Innocent." in ui.status_label.values["text"]

    ui._submit(Status.CRIMINAL)
    run_task(ui)
    assert ui.engine.get_public_state() == initial
    assert "contradicts" in ui.status_label.values["text"]

    ui._submit(Status.INNOCENT)
    run_task(ui)
    after = ui.engine.get_public_state()
    assert after.token.version == 1
    assert ui.board.highlighted == ("B2",)


def test_solver_timeout_and_solution_mismatch_report_distinct_errors(
    ui: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    initial = ui.engine.get_public_state()
    monkeypatch.setattr(
        ui.agent, "next_hint", lambda _state: (_ for _ in ()).throw(SolverTimeout("deadline hit"))
    )
    ui._request_hint()
    run_task(ui)
    assert not ui._busy
    assert ui.engine.get_public_state() == initial
    status_text = str(ui.status_label.values["text"]).lower()
    assert "timed out" in status_text
    assert "unsat" not in status_text and "stuck" not in status_text
    assert ui.errors[-1][0] == "Solver timed out"

    monkeypatch.setattr(
        ui.engine,
        "submit_verdict",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(SolutionMismatchError("hidden conflict")),
    )
    ui._select_cell("B1")
    ui._submit(Status.INNOCENT)
    run_task(ui)
    assert not ui._busy
    assert "Puzzle data error" in str(ui.status_label.values["text"])
    assert ui.errors[-1][0] == "Puzzle data error"


@pytest.mark.parametrize("accepted_reveals", [0, 1])
@pytest.mark.parametrize("error_type", [RuntimeError, SolverTimeout, SolutionMismatchError])
def test_auto_solve_error_reports_committed_progress(
    ui: MainWindow, accepted_reveals: int, error_type: type[Exception]
) -> None:
    class FailingSolver(DPLLSolver):
        def solve(self, *args, **kwargs):
            if engine.get_public_state().token.version >= accepted_reveals:
                raise error_type("Injected failure")
            return super().solve(*args, **kwargs)

    agent = DeductiveAgent(CNFEncoder(), FailingSolver())
    engine = GameEngine(load_puzzle(SOURCE / "puzzles/3x3/example_01.json"), agent.verify_verdict)
    ui.agent, ui.engine = agent, engine
    ui.refresh()
    initial = engine.get_public_state()
    ui._auto_solve()
    run_task(ui)

    current = engine.get_public_state()
    assert current.token.version == initial.token.version + accepted_reveals
    assert ui._state == current and not ui._busy
    assert sum(c.status is not None for c in current.characters) == (
        sum(c.status is not None for c in initial.characters) + accepted_reveals
    )
    message = str(ui.status_label.values["text"])
    if accepted_reveals:
        assert "Progress kept: 1 accepted reveal." in message
        assert "unchanged" not in message and "No cards were changed" not in message
    else:
        assert "No cards were changed." in message
    assert ui._last_solve is None
    assert ui.save_trace_button.values["state"] == ("normal" if accepted_reveals else "disabled")
    assert isinstance(ui.errors[-1][1], error_type)


@pytest.mark.parametrize("fixture_name", ["invalid_reference.json", "inconsistent.json"])
def test_loading_invalid_puzzle_fixture_keeps_existing_game(
    ui: MainWindow, monkeypatch: pytest.MonkeyPatch, fixture_name: str
) -> None:
    before = ui.engine.get_public_state()
    ui._load_path(SOURCE / "tests/fixtures" / fixture_name)
    assert ui.engine.get_public_state() == before
    assert len(ui.errors) == 1
    assert isinstance(ui.errors[0][1], PuzzleValidationError)
    assert "Previous game kept" in str(ui.status_label.values["text"])


def test_real_tk_board_renders_3x3_and_4x4_with_revealed_highlight() -> None:
    try:
        root = Tk()
    except TclError as error:
        pytest.skip(f"Tk display unavailable: {error}")
    root.withdraw()
    closed = False
    try:
        agent = DeductiveAgent(CNFEncoder(), DPLLSolver())
        engine = GameEngine(
            load_puzzle(SOURCE / "puzzles/3x3/demo_forced_unknown.json"), agent.verify_verdict
        )
        window = MainWindow(root, engine, agent)
        root.update()
        assert len(window.board._buttons) == 9
        assert window.board._card_labels["B1"]["clue"].cget("text") == "Clue locked"
        assert window.board._card_labels["A1"]["clue"].cget("text") == "Ben is Innocent"

        # Highlighting an already-revealed card uses the amber highlight border
        # while keeping its Criminal/Innocent fill intact.
        window.board.highlight(("A1", "B1"))
        a1_canvas = window.board._buttons["A1"]
        assert a1_canvas.itemcget("card_border", "outline") == BoardView.HIGHLIGHT
        a1_content = a1_canvas.winfo_children()[0]
        assert a1_content.cget("bg") == BoardView.CRIMINAL_FILL

        # Switch to a 4x4 puzzle and check minimum window size layout.
        window._state = engine.load(
            load_puzzle(SOURCE / "experiments/puzzles/synthetic_4x4_row_counts.json")
        )
        window._reset_view()
        window.refresh()
        root.geometry("990x680")
        root.update()
        assert len(window.board._buttons) == 16
        assert window.board._card_labels["A1"]["name"].cget("text") == "Person 00"
        assert window.board._card_labels["A1"]["profession"].cget("text") == "Researcher"
        window._select_cell("A1")
        assert window.board._highlighted == {"A2", "B2", "C2", "D2"}

        # Loading another puzzle of the same size must refresh names and professions.
        window._state = engine.load(load_puzzle(SOURCE / "puzzles/4x4/example_01.json"))
        window._reset_view()
        window.refresh()
        root.update()
        assert window.board._card_labels["A1"]["name"].cget("text") == "Alice"
        assert window.board._card_labels["A1"]["profession"].cget("text") == "Detective"
        window._close()
        closed = True
    finally:
        if not closed:
            root.destroy()


def test_notes_only_change_presentation_and_survive_level_resume(
    ui: MainWindow, tmp_path: Path
) -> None:
    store = ProgressStore(tmp_path / "player.json")
    ui._progress_store, ui._level_key = store, LEVELS[0].key
    ui._attach_progress()
    initial = ui.engine.get_public_state()
    initial_kb = CNFEncoder().encode(initial)
    ui._select_cell("A1")
    ui.note_color.set("Blue")
    ui._set_mark()
    ui._toggle_used()
    assert ui.engine.get_public_state() == initial
    assert CNFEncoder().encode(ui.engine.get_public_state()) == initial_kb
    assert ui.board.marks == {"A1": "Blue"}
    assert ui.board.used_clues == {initial.characters[0].clue.id}
    ui._select_cell("B1")
    ui._submit(Status.INNOCENT)
    run_task(ui)
    ui._request_hint()
    run_task(ui)
    previous = ui.engine.get_public_state()
    ui._load_level(LEVELS[2].key)
    assert len(ui._state.characters) == 16 and not ui.session.marks
    ui._load_level(LEVELS[0].key)
    assert ui._busy
    run_task(ui)
    assert ui.engine.get_public_state().characters == previous.characters
    assert ui.engine.get_public_state().token.session_id != previous.token.session_id
    assert ui.session.marks == {"A1": "Blue"}
    assert ui.session.hints == 1
    assert len(ui.session.snapshots) == 2
    assert ui.session.snapshots[0].characters[1].clue is None


def test_hint_rejection_and_auto_solve_metrics_count_each_call_once(ui: MainWindow) -> None:
    ui._request_hint()
    run_task(ui)
    hint_calls = len(ui.session.queries)
    ui._select_cell("B1")
    ui._submit(Status.CRIMINAL)
    run_task(ui)
    before_auto = len(ui.session.queries)
    assert before_auto > hint_calls > 0
    assert ui.session.hints == ui.session.rejected == 1
    assert len(ui.session.snapshots) == 1
    ui._auto_solve()
    run_task(ui)
    assert len(ui.session.queries) == before_auto + len(ui._last_solve.queries)
    assert ui.session.started is None
    assert ui._result_shown


def test_library_replaces_file_explorer(ui: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    seen = []
    monkeypatch.setattr(
        "gui.main_window.show_library", lambda root, records, choose: seen.append(choose)
    )
    ui._load()
    seen[0](LEVELS[2].key)
    assert ui._level_key == LEVELS[2].key
    assert ui.puzzle_title.values["text"] == "City Detectives"


def test_bad_resume_resets_partial_restoration_and_keeps_saved_record(
    ui: MainWindow, tmp_path: Path
) -> None:
    store = ProgressStore(tmp_path / "player.json")
    ui._progress_store, ui._level_key = store, LEVELS[0].key
    ui._attach_progress()
    record = store.data["levels"][LEVELS[0].key]
    record["moves"] = [["B1", "INNOCENT"], ["A2", "CRIMINAL"]]
    record["step_queries"] = [[], []]
    ui._load_level(LEVELS[2].key)
    # Install a deliberately unprovable second move after leaving the first case.
    store.data["levels"][LEVELS[0].key] = record
    ui._load_level(LEVELS[0].key)
    run_task(ui)
    assert ui._state.token.version == 0
    assert len(ui.session.snapshots) == 1
    assert "saved record was kept" in ui.status_label.values["text"]
    assert store.data["levels"][LEVELS[0].key]["moves"] == record["moves"]
