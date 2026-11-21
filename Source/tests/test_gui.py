"""Headless controller tests with real backends and controlled worker scheduling."""

import json
import threading
from pathlib import Path
from typing import Callable

import pytest

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.models import SolveOutcome, Status
from game.puzzle_loader import load_puzzle
from gui.main_window import MainWindow
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
        pass

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
        ):
            setattr(window, name, Widget())

    monkeypatch.setattr(MainWindow, "_configure_window", lambda self: None)
    monkeypatch.setattr(MainWindow, "_build_layout", build)
    monkeypatch.setattr(MainWindow, "_show_toast", lambda self, title, message, tone: None)
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
        monkeypatch.setattr(
            "gui.main_window.filedialog.askopenfilename",
            lambda **kwargs: str(SOURCE / "puzzles/4x4/example_01.json"),
        )
        ui._load()


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
    ui._select_cell("C1")
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
    popup, text, scrollbar = Widget(), Widget(), Widget()
    monkeypatch.setattr("gui.main_window.Toplevel", lambda root: popup)
    monkeypatch.setattr("gui.main_window.Text", lambda *args, **kwargs: text)
    monkeypatch.setattr("gui.main_window.ttk.Scrollbar", lambda *args, **kwargs: scrollbar)
    ui._view_trace()
    assert "SAT calls: 105" in text.contents
    assert "Step 1: B1 = INNOCENT" in text.contents
    assert "ASSUME_INNOCENT:B1" in text.contents
    assert text.values["state"] == "disabled"
    assert "assignment" not in text.contents and "hidden_status" not in text.contents
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
    monkeypatch.setattr(
        "gui.main_window.filedialog.askopenfilename",
        lambda **kwargs: str(tmp_path / "missing.json"),
    )
    ui._load()
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
    assert "No accepted deduction steps." in ui._trace_text(ui._last_solve)
    destination = tmp_path / "empty.json"
    monkeypatch.setattr(
        "gui.main_window.filedialog.asksaveasfilename", lambda **kwargs: str(destination)
    )
    ui._save_trace()
    assert json.loads(destination.read_text(encoding="utf-8")) == []
