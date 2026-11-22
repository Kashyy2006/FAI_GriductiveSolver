"""Tkinter application and controller integration boundary."""

from __future__ import annotations

import queue
import threading
from dataclasses import replace
from pathlib import Path
from tkinter import (
    BOTH,
    LEFT,
    RIGHT,
    Canvas,
    Event,
    Frame,
    Label,
    StringVar,
    Tk,
    Toplevel,
    X,
    Y,
    filedialog,
    messagebox,
    ttk,
)
from typing import Callable

from agent.agent import DeductiveAgent
from agent.trace import save_trace
from game.engine import GameEngine
from game.models import (
    AutoSolveResult,
    Clue,
    HintResult,
    KBStatus,
    PublicState,
    SolutionMismatchError,
    SolveOutcome,
    SolverTimeout,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictResult,
)
from game.puzzle_loader import load_puzzle
from gui.board_view import BoardView
from gui.clue_text import format_clue
from gui.dialogs import show_help, show_library, show_replay
from gui.play_session import LEVELS, MARK_COLORS, SOURCE, PlaySession, ProgressStore
from logic.regions import resolve_region


class MainWindow:
    """Connect user actions to Engine and Agent while keeping Tk on its main thread."""

    _BASE = "#f3ecdf"
    _PANEL = "#ebe1d1"
    _TEXT = "#312a26"
    _MUTED = "#796f64"
    _ACCENT = "#c92f28"
    _EMPTY_CLUE = "Select a revealed card to inspect its clue."

    def __init__(self, root: Tk, engine: GameEngine, agent: DeductiveAgent) -> None:
        self.root = root
        self.engine = engine
        self.agent = agent
        self._state = engine.get_public_state()
        self.session = PlaySession(engine)
        self._progress_store: ProgressStore | None = None
        self._level_key: str | None = None
        self._result_window: Toplevel | None = None
        self._result_shown = False
        self._clock_ticks = 0
        self._selected_id: str | None = None
        self._busy = False
        self._active_task: object | None = None
        self._cancel_event: threading.Event | None = None
        self._last_solve: AutoSolveResult | None = None
        self._trace_window: Toplevel | None = None
        self._animation_generation = 0
        self._solve_start_state = self._state
        self._verdict_context: tuple[str, Status, bool] | None = None
        self._toast_window: Frame | None = None
        self._toast_after_ids: set[str] = set()
        self._messages: queue.Queue[tuple[object, str, object, StateToken]] = queue.Queue()
        self._configure_window()
        self._build_layout()
        self.refresh()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(80, self._poll_messages)
        self.root.after(1000, self._tick_clock)

    def refresh(self) -> None:
        """Render the latest public snapshot and update action state."""
        self._state = self.engine.get_public_state()
        if self.session.snapshots[0].token.session_id != self._state.token.session_id:
            self.session = PlaySession(self.engine)
        self._render_state(self._state)

    def _render_state(self, state: PublicState) -> None:
        """Render a public snapshot without querying the engine again."""
        self._state = state
        self.board.render(self._state)
        self.board.set_notes(self.session.marks, self.session.used_clues)
        level = next((level for level in LEVELS if level.key == self._level_key), None)
        self.puzzle_title.configure(
            text=level.title if level else self._format_title(self._state.puzzle_id)
        )
        revealed = sum(item.status is not None for item in self._state.characters)
        self.progress_label.configure(
            text=f"{revealed:02d} / {len(self._state.characters):02d} cards revealed"
        )
        selected = next(
            (item for item in self._state.characters if item.id == self._selected_id), None
        )
        self.selected_label.configure(
            text=(f"Selected: {selected.id}  ·  {selected.name}" if selected else "Select a card")
        )
        if selected is None:
            self.clue_label.configure(text=self._EMPTY_CLUE)
        elif selected.clue is None:
            self.clue_label.configure(text="This card is sealed. Its status and clue stay hidden.")
        else:
            self.clue_label.configure(text=self._describe_clue(selected.clue))
        self.note_color.set(self.session.marks.get(self._selected_id or "", "None"))
        used = bool(selected and selected.clue and selected.clue.id in self.session.used_clues)
        self.used_button.configure(text="Restore clue" if used else "Used clue ✓")
        self.clue_label.configure(
            foreground=self._MUTED if used else self._TEXT,
            font=("Segoe UI", -13, "overstrike" if used else "normal"),
        )
        self._update_controls()

    @staticmethod
    def _format_title(puzzle_id: str) -> str:
        words = puzzle_id.replace("_", " ").split()
        formatted: list[str] = []
        for word in words:
            lower = word.lower()
            if len(lower) == 3 and lower[0].isdigit() and lower[1] == "x" and lower[2].isdigit():
                formatted.append(f"{lower[0]}×{lower[2]}")
            else:
                formatted.append(word.title())
        return " ".join(formatted)

    def _configure_window(self) -> None:
        self.root.title("GRIDUCTIVE  /  Deduction bureau")
        self.root.geometry("1280x820")
        self.root.minsize(990, 680)
        self.root.configure(background=self._BASE)
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("App.TFrame", background=self._BASE)
        style.configure("Panel.TFrame", background=self._BASE)
        style.configure("Board.TFrame", background=self._BASE)
        style.configure("CardBox.TFrame", background=self._PANEL)
        style.configure(
            "Title.TLabel",
            background=self._BASE,
            foreground=self._TEXT,
            font=("Segoe UI", -28, "bold"),
        )
        style.configure(
            "Kicker.TLabel",
            background=self._BASE,
            foreground=self._ACCENT,
            font=("Segoe UI", -12, "bold"),
        )
        style.configure(
            "Body.TLabel",
            background=self._BASE,
            foreground=self._TEXT,
            font=("Segoe UI", -13),
        )
        style.configure(
            "CardBody.TLabel",
            background=self._PANEL,
            foreground=self._TEXT,
            font=("Segoe UI", -13),
        )
        style.configure(
            "Muted.TLabel",
            background=self._BASE,
            foreground=self._MUTED,
            font=("Segoe UI", -12),
        )
        style.configure(
            "PanelTitle.TLabel",
            background=self._PANEL,
            foreground=self._TEXT,
            font=("Segoe UI", -15, "bold"),
        )
        style.configure(
            "Coordinate.TLabel",
            background=self._BASE,
            foreground=self._MUTED,
            font=("Segoe UI", -13, "bold"),
        )
        style.configure(
            "Action.TButton",
            background="#4b4037",
            foreground="#fffaf2",
            font=("Segoe UI", -13, "bold"),
            padding=(10, 9),
            relief="flat",
        )
        style.map(
            "Action.TButton",
            background=[("disabled", "#b9afa3"), ("active", "#615449")],
            foreground=[("disabled", "#efe7dc")],
        )
        style.configure(
            "CriminalAction.TButton",
            background=BoardView.CRIMINAL,
            foreground="#fffaf2",
            font=("Segoe UI", -13, "bold"),
            padding=(10, 9),
            relief="flat",
        )
        style.map(
            "CriminalAction.TButton",
            background=[("disabled", "#c8aca5"), ("active", "#b12620")],
            foreground=[("disabled", "#f4ece6")],
        )
        style.configure(
            "InnocentAction.TButton",
            background=BoardView.INNOCENT,
            foreground="#fffaf2",
            font=("Segoe UI", -13, "bold"),
            padding=(10, 9),
            relief="flat",
        )
        style.map(
            "InnocentAction.TButton",
            background=[("disabled", "#aebcb4"), ("active", "#476555")],
            foreground=[("disabled", "#eef3f0")],
        )
        style.configure(
            "Primary.TButton",
            background="#d58b28",
            foreground="#fffaf2",
            font=("Segoe UI", -13, "bold"),
            padding=(10, 9),
            relief="flat",
        )
        style.map(
            "Primary.TButton",
            background=[("disabled", "#d3b992"), ("active", "#e1a544")],
            foreground=[("disabled", "#f5efe6")],
        )

    def _build_layout(self) -> None:
        shell = ttk.Frame(self.root, style="App.TFrame", padding=(24, 18))
        shell.pack(fill=BOTH, expand=True)
        header = ttk.Frame(shell, style="App.TFrame")
        header.pack(fill=X, pady=(0, 12))
        heading = ttk.Frame(header, style="App.TFrame")
        heading.pack(side=LEFT, fill=X, expand=True)
        ttk.Label(heading, text="THE GRIDUCTIVE FILES", style="Kicker.TLabel").pack(anchor="w")
        self.puzzle_title = ttk.Label(heading, text="", style="Title.TLabel")
        self.puzzle_title.pack(anchor="w", pady=(2, 0))
        self.progress_label = ttk.Label(header, text="", style="Body.TLabel")
        self.progress_label.pack(side=RIGHT, anchor="s", pady=(0, 5))
        ttk.Button(header, text="?", width=3, command=lambda: show_help(self.root)).pack(
            side=RIGHT, padx=12
        )

        body = ttk.Frame(shell, style="App.TFrame")
        body.pack(fill=BOTH, expand=True)
        board_panel = ttk.Frame(body, style="Panel.TFrame", padding=6)
        board_panel.pack(side=LEFT, fill=BOTH, expand=True)
        self.board = BoardView(board_panel, self._select_cell)
        self.board.pack(fill=BOTH, expand=True)

        sidebar_shell = ttk.Frame(body, style="App.TFrame", width=330)
        sidebar_shell.pack(side=RIGHT, fill=Y, padx=(18, 0))
        sidebar_shell.pack_propagate(False)
        sidebar_scroll = ttk.Scrollbar(sidebar_shell)
        sidebar_scroll.pack(side=RIGHT, fill=Y)
        self._sidebar_canvas = Canvas(
            sidebar_shell,
            bg=self._BASE,
            highlightthickness=0,
            bd=0,
            yscrollcommand=sidebar_scroll.set,
        )
        self._sidebar_canvas.pack(fill=BOTH, expand=True)
        sidebar_scroll.configure(command=self._sidebar_canvas.yview)
        sidebar = ttk.Frame(self._sidebar_canvas, style="App.TFrame")
        sidebar_window = self._sidebar_canvas.create_window(0, 0, window=sidebar, anchor="nw")
        sidebar.bind(
            "<Configure>",
            lambda _: self._sidebar_canvas.configure(scrollregion=self._sidebar_canvas.bbox("all")),
        )
        self._sidebar_canvas.bind(
            "<Configure>",
            lambda event: self._sidebar_canvas.itemconfigure(sidebar_window, width=event.width),
        )

        def scroll_notes(event: Event) -> None:
            canvas = self._sidebar_canvas
            x, y = canvas.winfo_pointerxy()
            if (
                canvas.winfo_rootx() <= x < canvas.winfo_rootx() + canvas.winfo_width()
                and canvas.winfo_rooty() <= y < canvas.winfo_rooty() + canvas.winfo_height()
            ):
                canvas.yview_scroll(-int(event.delta / 120), "units")

        self.root.bind("<MouseWheel>", scroll_notes, add="+")
        ttk.Label(sidebar, text="CASE NOTES", style="Kicker.TLabel").pack(anchor="w")
        selected_box = ttk.Frame(sidebar, style="CardBox.TFrame", padding=(10, 8))
        selected_box.pack(fill=X, pady=(6, 12))
        self.selected_label = ttk.Label(
            selected_box, text="Select a card", style="PanelTitle.TLabel", wraplength=286
        )
        self.selected_label.pack(anchor="w")

        ttk.Label(sidebar, text="Verdict", style="Muted.TLabel").pack(anchor="w", pady=(0, 4))
        verdict_row = ttk.Frame(sidebar, style="App.TFrame")
        verdict_row.pack(fill=X)
        verdict_row.columnconfigure((0, 1), weight=1, uniform="actions")
        self.criminal_button = ttk.Button(
            verdict_row,
            text="Mark Criminal",
            style="CriminalAction.TButton",
            command=lambda: self._submit(Status.CRIMINAL),
        )
        self.criminal_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)
        self.innocent_button = ttk.Button(
            verdict_row,
            text="Mark Innocent",
            style="InnocentAction.TButton",
            command=lambda: self._submit(Status.INNOCENT),
        )
        self.innocent_button.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)

        note_row = ttk.Frame(sidebar, style="App.TFrame")
        note_row.pack(fill=X, pady=(8, 0))
        ttk.Label(note_row, text="Temporary color", style="Muted.TLabel").pack(side=LEFT)
        self.note_color = StringVar(self.root, "None")
        self.note_picker = ttk.Combobox(
            note_row,
            textvariable=self.note_color,
            values=("None", *MARK_COLORS),
            state="readonly",
            width=9,
        )
        self.note_picker.pack(side=LEFT, padx=6)
        self.note_picker.bind("<<ComboboxSelected>>", lambda _: self._set_mark())
        self.used_button = ttk.Button(note_row, text="Used clue ✓", command=self._toggle_used)
        self.used_button.pack(side=LEFT)

        ttk.Separator(sidebar).pack(fill=X, pady=12)
        ttk.Label(sidebar, text="Deduction & Trace", style="Muted.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        solve_row = ttk.Frame(sidebar, style="App.TFrame")
        solve_row.pack(fill=X)
        solve_row.columnconfigure((0, 1), weight=1, uniform="solve")
        self.hint_button = ttk.Button(
            solve_row, text="Get a Hint", style="Primary.TButton", command=self._request_hint
        )
        self.hint_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)
        self.solve_button = ttk.Button(
            solve_row, text="Auto Solve", style="Action.TButton", command=self._auto_solve
        )
        self.solve_button.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)

        trace_row = ttk.Frame(sidebar, style="App.TFrame")
        trace_row.pack(fill=X, pady=(4, 0))
        trace_row.columnconfigure((0, 1), weight=1, uniform="trace")
        self.view_trace_button = ttk.Button(
            trace_row, text="Replay", style="Action.TButton", command=self._view_trace
        )
        self.view_trace_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)
        self.save_trace_button = ttk.Button(
            trace_row, text="Save Trace…", style="Action.TButton", command=self._save_trace
        )
        self.save_trace_button.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)

        ttk.Separator(sidebar).pack(fill=X, pady=12)
        ttk.Label(sidebar, text="Puzzle Session", style="Muted.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        session_row = ttk.Frame(sidebar, style="App.TFrame")
        session_row.pack(fill=X)
        session_row.columnconfigure((0, 1), weight=1, uniform="session")
        self.load_button = ttk.Button(
            session_row, text="Case Library", style="Action.TButton", command=self._load
        )
        self.load_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)
        self.restart_button = ttk.Button(
            session_row, text="Restart Case", style="Action.TButton", command=self._restart
        )
        self.restart_button.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)

        ttk.Label(sidebar, text="PUBLIC CLUES", style="Kicker.TLabel").pack(
            anchor="w", pady=(16, 6)
        )
        clue_box = ttk.Frame(sidebar, style="CardBox.TFrame", padding=(12, 10))
        clue_box.pack(fill=X)
        self.clue_label = ttk.Label(
            clue_box,
            text=self._EMPTY_CLUE,
            style="CardBody.TLabel",
            wraplength=280,
            justify=LEFT,
        )
        self.clue_label.pack(anchor="w")

        status_box = ttk.Frame(sidebar, style="App.TFrame")
        status_box.pack(side="bottom", fill=X, pady=(12, 0))
        ttk.Separator(status_box).pack(fill=X, pady=(0, 8))
        ttk.Label(status_box, text="STATUS", style="Kicker.TLabel").pack(anchor="w")
        self.status_label = ttk.Label(
            status_box, text="Ready", style="Body.TLabel", wraplength=300, justify=LEFT
        )
        self.status_label.pack(anchor="w", pady=(4, 0))
        self.clock_label = ttk.Label(status_box, text="", style="Muted.TLabel")
        self.clock_label.pack(anchor="w", pady=(4, 0))
        self.results_button = ttk.Button(
            status_box, text="Results / Details", command=self._show_results
        )
        self.results_button.pack(anchor="w", pady=(4, 0))

    def _select_cell(self, character_id: str) -> None:
        self._selected_id = character_id
        self._render_state(self._state)
        character = next((item for item in self._state.characters if item.id == character_id), None)
        if character is not None:
            self.board.highlight(
                (character_id,)
                if character.clue is None
                else self._clue_cells(character.clue, character_id)
            )

    def _clue_cells(self, clue: Clue, owner_id: str) -> tuple[str, ...]:
        if clue.type.value == "FACT" and clue.person is not None:
            return (clue.person,)
        if clue.type.value in ("SAME", "DIFFERENT"):
            return tuple(cell for cell in (clue.first, clue.second) if cell is not None)
        if clue.region is not None:
            return resolve_region(clue.region, self._state)
        return (owner_id,)

    def _describe_clue(self, clue: Clue) -> str:
        return format_clue(clue, self._state)

    def _submit(self, status: Status) -> None:
        if self._busy:
            return
        character_id = self._selected_id
        if character_id is None:
            return
        snapshot = self._state
        character = next(item for item in snapshot.characters if item.id == character_id)
        self._verdict_context = (character_id, status, character.clue is None)
        if character.clue is None:
            self.status_label.configure(
                text=f"Checking whether public clues prove {character_id} is {status.value.title()}…"
            )
            self._show_toast(
                f"Checking {character_id}",
                "This card has no revealed clue yet. Checking whether the public clues prove "
                f"it is {status.value.title()}.",
                "info",
            )
        self._start_task(
            "verdict",
            lambda: self.session.submit_verdict(
                character_id, status, expected_token=snapshot.token
            ),
            snapshot.token,
        )

    def _request_hint(self) -> None:
        if self._busy:
            return
        self.session.hints += 1
        self.session.persist()
        snapshot = self._state
        self._start_task("hint", lambda: self.agent.next_hint(snapshot), snapshot.token)

    def _auto_solve(self) -> None:
        if self._busy:
            return
        snapshot = self._state
        self._solve_start_state = snapshot
        cancel = threading.Event()

        # Capture the initiating session, not mutable GUI state. Even if the
        # worker starts after a reset, it must not solve the replacement game.
        def should_cancel() -> bool:
            return (
                cancel.is_set()
                or self.engine.get_public_state().token.session_id != snapshot.token.session_id
            )

        self._last_solve = None
        self._close_trace()
        session = self.session
        self._metrics_partial_before_run = session.metrics_partial
        self._solve_query_start = len(session.queries)
        session.metrics_partial = True
        session.persist()
        self._start_task(
            "solve",
            lambda: self.agent.auto_solve(session, should_cancel=should_cancel),
            snapshot.token,
            cancel_event=cancel,
        )

    def _load(self) -> None:
        show_library(
            self.root,
            self._progress_store.data["levels"] if self._progress_store else {},
            self._load_level,
        )

    def _load_level(self, key: str) -> None:
        if key not in {level.key for level in LEVELS}:
            raise ValueError("Unknown case")
        self._load_path(SOURCE / "puzzles" / key, key)

    def _load_path(self, path: Path, key: str | None = None) -> None:
        try:
            puzzle = load_puzzle(path)
            self.session.pause()
            self.session.persist()
            self._state = self.engine.load(puzzle)
            self._level_key = key
            if self._progress_store:
                self._progress_store.active_key = key
            self._reset_view()
            self.status_label.configure(text="Puzzle loaded.")
            self.refresh()
            record = self._progress_store.data["levels"].get(key) if self._progress_store else None
            if record:
                session = self.session
                self._start_task("restore", lambda: session.restore(record), self._state.token)
            else:
                self._attach_progress()
        except Exception as error:
            if not self._busy:
                self.status_label.configure(
                    text=f"Could not load puzzle ({type(error).__name__}: {error}). "
                    "Previous game kept."
                )
            self._show_error("Could not load puzzle", error)

    def _restart(self) -> None:
        try:
            self.session.pause()
            self._state = self.engine.restart()
            self._reset_view()
            self.status_label.configure(text="Case restarted.")
            self.refresh()
            self._attach_progress()
        except Exception as error:
            self._show_error("Could not restart case", error)

    def _cancel_task(self) -> None:
        """Invalidate queued messages and cooperatively stop the current worker."""
        if self._cancel_event is not None:
            self._cancel_event.set()
        self._cancel_event = None
        self._active_task = None
        self._busy = False

    def _close_trace(self) -> None:
        if self._trace_window is not None and self._trace_window.winfo_exists():
            self._trace_window.destroy()
        self._trace_window = None

    def _reset_view(self) -> None:
        """Clear public information and trace belonging to the previous session."""
        self._animation_generation += 1
        self.board.cancel_animations()
        self._dismiss_toast()
        self._cancel_task()
        self._selected_id = None
        self._last_solve = None
        self._verdict_context = None
        self._close_trace()
        if self._result_window is not None and self._result_window.winfo_exists():
            self._result_window.destroy()
        self._result_window = None
        self._result_shown = False
        self.session = PlaySession(self.engine)
        self.board.highlight(())
        self.clue_label.configure(text=self._EMPTY_CLUE)

    def _close(self) -> None:
        self._animation_generation += 1
        self.board.cancel_animations()
        self._dismiss_toast()
        self._cancel_task()
        self.session.pause()
        self.session.persist()
        if self.session.save_error:
            self._show_error("Could not save progress", self.session.save_error)
        self.root.destroy()

    def enable_progress(self, initial_key: str) -> None:
        """Enable local resume in the application composition root, not in isolated tests."""
        self._level_key = initial_key
        try:
            self._progress_store = ProgressStore(SOURCE / "outputs" / "player_progress.json")
        except (OSError, ValueError, TypeError) as error:
            self._show_error("Could not read progress; existing file kept", error)
            return
        key = self._progress_store.data["last_level"] or initial_key
        self._load_level(key)

    def _attach_progress(self) -> None:
        self.session.store = self._progress_store
        self.session.key = self._level_key
        self.session.persist()

    def _set_mark(self) -> None:
        if self._selected_id is None or self._busy:
            return
        color = self.note_color.get()
        if color in MARK_COLORS:
            self.session.marks[self._selected_id] = color
        else:
            self.session.marks.pop(self._selected_id, None)
        self.session.persist()
        self._render_state(self._state)

    def _toggle_used(self) -> None:
        if self._busy:
            return
        selected = next((c for c in self._state.characters if c.id == self._selected_id), None)
        if selected is None or selected.clue is None:
            return
        clue_id = selected.clue.id
        if clue_id in self.session.used_clues:
            self.session.used_clues.remove(clue_id)
        else:
            self.session.used_clues.add(clue_id)
        self.session.persist()
        self._render_state(self._state)

    def _tick_clock(self) -> None:
        minutes, seconds = divmod(int(self.session.elapsed), 60)
        self.clock_label.configure(
            text=(
                f"Time {minutes:02d}:{seconds:02d} · Hints {self.session.hints} · "
                f"Rejected {self.session.rejected}"
            )
        )
        if self.session.save_error:
            self.status_label.configure(
                text=f"Progress could not be saved: {self.session.save_error}"
            )
        self._clock_ticks += 1
        if self._clock_ticks % 15 == 0:
            self.session.persist()
        self.root.after(1000, self._tick_clock)

    def _maybe_completed(self) -> None:
        if not self._result_shown and all(c.status is not None for c in self._state.characters):
            self.session.pause()
            self.session.persist()
            self._result_shown = True
            self._show_results()

    def _show_results(self) -> None:
        if self._result_window is not None and self._result_window.winfo_exists():
            self._result_window.destroy()
        window = Toplevel(self.root)
        self._result_window = window
        complete = all(c.status is not None for c in self._state.characters)
        window.title("Case Results" if complete else "Session Details")
        window.geometry("520x440")
        panel = ttk.Frame(window, padding=22)
        panel.pack(fill=BOTH, expand=True)
        ttk.Label(
            panel,
            text="Case complete" if complete else "Case in progress",
            font=("Segoe UI", 19, "bold"),
        ).pack(anchor="w", pady=(0, 14))
        minutes, seconds = divmod(int(self.session.elapsed), 60)
        for label, value in (
            ("Play time", f"{minutes:02d}:{seconds:02d}"),
            ("Hints requested", str(self.session.hints)),
            ("Rejected verdicts", str(self.session.rejected)),
        ):
            ttk.Label(panel, text=f"{label}: {value}", font=("Segoe UI", 12)).pack(
                anchor="w", pady=3
            )
        details = ttk.Frame(panel)
        queries = self.session.queries
        stats = [q.stats for q in queries]
        text = (
            f"Completed SAT calls: {len(queries)}\n"
            f"Decisions: {sum(s.decisions for s in stats)}\n"
            f"Propagations: {sum(s.propagations for s in stats)}\n"
            f"Backtracks: {sum(s.backtracks for s in stats)}\n"
            f"SAT runtime: {sum(s.runtime_seconds for s in stats):.4f} s"
        )
        if self.session.metrics_partial:
            text += "\nPartial metrics: an interrupted operation did not return its full ledger."
        ttk.Label(details, text=text, wraplength=460).pack(anchor="w")

        def toggle() -> None:
            if details.winfo_manager():
                details.pack_forget()
                detail_button.configure(text="Show SAT details ▾")
            else:
                details.pack(fill=X, pady=8)
                detail_button.configure(text="Hide SAT details ▴")
                window.geometry("520x560")

        detail_button = ttk.Button(panel, text="Show SAT details ▾", command=toggle)
        detail_button.pack(anchor="w", pady=10)
        if complete:
            next_level = next(
                (i + 1 for i, level in enumerate(LEVELS) if level.key == self._level_key),
                len(LEVELS),
            )
            if next_level < len(LEVELS) and LEVELS[next_level].difficulty != "Practice":
                ttk.Button(
                    panel,
                    text="Play next case →",
                    command=lambda: self._load_level(LEVELS[next_level].key),
                ).pack(anchor="w")
            else:
                ttk.Button(panel, text="Return to Case Library", command=self._load).pack(
                    anchor="w"
                )

    def _start_task(
        self,
        kind: str,
        action: Callable[[], object],
        token: StateToken,
        *,
        cancel_event: threading.Event | None = None,
    ) -> None:
        if self._busy:
            return
        self._busy = True
        task_id = object()
        cancel = cancel_event if cancel_event is not None else threading.Event()
        self._active_task = task_id
        self._cancel_event = cancel
        self.status_label.configure(text="Working…")
        self._update_controls()

        def run() -> None:
            if cancel.is_set():
                return
            try:
                result: object = action()
            except Exception as error:
                result = error
            self._messages.put((task_id, kind, result, token))

        threading.Thread(target=run, name=f"griductive-{kind}", daemon=True).start()

    def _poll_messages(self) -> None:
        try:
            while True:
                task_id, kind, result, token = self._messages.get_nowait()
                if task_id is not self._active_task:
                    continue
                if token.session_id != self.engine.get_public_state().token.session_id:
                    context = self._verdict_context if kind == "verdict" else None
                    self._verdict_context = None
                    self._cancel_task()
                    self.refresh()
                    if context is not None and context[2]:
                        self._show_unrevealed_verdict_message(context, VerdictOutcome.STALE_STATE)
                    continue
                self._busy = False
                self._active_task = None
                self._cancel_event = None
                if isinstance(result, Exception):
                    self.session.metrics_partial = True
                    context = self._verdict_context if kind == "verdict" else None
                    self._verdict_context = None
                    self.refresh()
                    accepted = self._state.token.version - token.version
                    progress = (
                        f" Progress kept: {accepted} accepted "
                        f"{'reveal' if accepted == 1 else 'reveals'}."
                        if accepted > 0
                        else " No cards were changed."
                    )
                    if isinstance(result, SolverTimeout):
                        self.status_label.configure(
                            text="Solver timed out before finishing. No result was assumed."
                            + progress
                        )
                        if context is not None and context[2]:
                            self._show_toast("Solver timed out", str(result), "error")
                        else:
                            self._show_error("Solver timed out", result)
                    elif isinstance(result, SolutionMismatchError):
                        self.status_label.configure(
                            text="Puzzle data error: proved verdict conflicts with puzzle data."
                            + progress
                        )
                        self._show_error("Puzzle data error", result)
                    else:
                        self.status_label.configure(text="Operation failed." + progress)
                        if context is not None and context[2]:
                            self._show_toast(f"Could not check {context[0]}", str(result), "error")
                        else:
                            self._show_error("Operation failed", result)
                    if kind == "restore":
                        self.engine.restart()
                        self._reset_view()
                        self.refresh()
                        self.status_label.configure(
                            text="Saved progress could not be restored. Fresh public board loaded. "
                            "The saved record was kept."
                        )
                    else:
                        self.session.persist()
                elif kind == "restore":
                    self.refresh()
                    self._attach_progress()
                    self.status_label.configure(text="Saved case resumed.")
                    self._maybe_completed()
                elif kind == "verdict" and isinstance(result, VerdictResult):
                    context = self._verdict_context
                    self._verdict_context = None
                    self._handle_verdict(result, context)
                elif kind == "hint" and isinstance(result, HintResult):
                    self._handle_hint(result)
                elif kind == "solve" and isinstance(result, AutoSolveResult):
                    self._handle_solve(result)
        except queue.Empty:
            pass
        self._update_controls()
        self.root.after(80, self._poll_messages)

    def _handle_verdict(
        self,
        result: VerdictResult,
        context: tuple[str, Status, bool] | None = None,
    ) -> None:
        if result.proof is not None and result.outcome != VerdictOutcome.ACCEPTED:
            self.session.queries.extend(result.proof.queries)
        if result.outcome in (
            VerdictOutcome.NOT_PROVABLE,
            VerdictOutcome.CONTRADICTED,
            VerdictOutcome.INCONSISTENT,
        ):
            self.session.rejected += 1
        self.session.persist()
        labels = {
            VerdictOutcome.ACCEPTED: "Verdict accepted. New clue revealed.",
            VerdictOutcome.NOT_PROVABLE: "Not provable yet. No card was changed.",
            VerdictOutcome.CONTRADICTED: "That verdict contradicts the public clues.",
            VerdictOutcome.INCONSISTENT: "The public clues are inconsistent.",
            VerdictOutcome.STALE_STATE: "Board changed; your result was discarded.",
            VerdictOutcome.ALREADY_REVEALED: "That card is already revealed.",
        }
        self.status_label.configure(text=labels[result.outcome])
        if result.outcome == VerdictOutcome.ACCEPTED:
            previous_statuses = {item.id: item.status for item in self._state.characters}
            character_id = next(
                (
                    item.id
                    for item in result.state.characters
                    if item.status is not None and previous_statuses.get(item.id) is None
                ),
                self._selected_id,
            )
            generation = self._animation_generation
            self._busy = True
            self._update_controls()

            def reveal() -> None:
                if generation == self._animation_generation:
                    self._render_state(result.state)
                    if character_id and character_id == self._selected_id:
                        revealed = next(
                            (item for item in self._state.characters if item.id == character_id),
                            None,
                        )
                        if revealed is not None and revealed.clue is not None:
                            self.board.highlight(self._clue_cells(revealed.clue, character_id))

            def done() -> None:
                if generation == self._animation_generation:
                    self._busy = False
                    self._update_controls()
                    if context is not None and context[2]:
                        self._show_unrevealed_verdict_message(context, result.outcome)
                    self._maybe_completed()

            self.board.flip_card(character_id or "", reveal, done)
        else:
            self.refresh()
            if context is not None and context[2]:
                self._show_unrevealed_verdict_message(context, result.outcome)

    def _show_unrevealed_verdict_message(
        self, context: tuple[str, Status, bool], outcome: VerdictOutcome
    ) -> None:
        character_id, status, _had_no_clue = context
        messages = {
            VerdictOutcome.ACCEPTED: (
                f"{character_id} has been proven {status.value.title()} from public clues. "
                "Its clue is now revealed."
            ),
            VerdictOutcome.NOT_PROVABLE: (
                f"{character_id} has no revealed clue yet, and the current public clues do not "
                "prove this verdict. No card was changed. Try Get a Hint or Auto Solve."
            ),
            VerdictOutcome.CONTRADICTED: (
                f"The public clues contradict marking {character_id} as {status.value.title()}. "
                "No card was changed."
            ),
            VerdictOutcome.INCONSISTENT: "The revealed clues are inconsistent, so no verdict was accepted.",
            VerdictOutcome.STALE_STATE: "The board changed before this verdict could be applied.",
            VerdictOutcome.ALREADY_REVEALED: f"{character_id} is already revealed.",
        }
        tone = (
            "success"
            if outcome == VerdictOutcome.ACCEPTED
            else "error"
            if outcome in (VerdictOutcome.CONTRADICTED, VerdictOutcome.INCONSISTENT)
            else "info"
        )
        self._show_toast(f"{character_id} · {status.value.title()}", messages[outcome], tone)

    def _show_toast(self, title: str, message: str, tone: str) -> None:
        """Show a non-modal notification in the lower-right corner of the app."""
        self._dismiss_toast()
        colors = {
            "success": "#577967",
            "error": "#c92f28",
            "info": "#d58b28",
        }
        accent = colors[tone]
        toast = Frame(self.root, bg="#312a26", padx=1, pady=1, width=336, height=100)
        toast.pack_propagate(False)
        toast.place(relx=1.0, rely=1.0, x=-18, y=18, anchor="se")
        toast.lift()
        self._toast_window = toast

        outer = Frame(toast, bg="#312a26", padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        panel = Frame(outer, bg="#fffaf2")
        panel.pack(fill="both", expand=True)
        stripe = Frame(panel, bg=accent, width=5)
        stripe.pack(side=LEFT, fill="y")
        content = Frame(panel, bg="#fffaf2", padx=13, pady=10)
        content.pack(side=LEFT, fill="both", expand=True)
        Label(
            content,
            text=title,
            bg="#fffaf2",
            fg="#312a26",
            font=("Segoe UI", -13, "bold"),
            anchor="w",
        ).pack(fill="x")
        Label(
            content,
            text=message,
            bg="#fffaf2",
            fg="#796f64",
            font=("Segoe UI", -12),
            justify=LEFT,
            anchor="w",
            wraplength=288,
        ).pack(fill="x", pady=(4, 0))

        def enter(frame: int = 0) -> None:
            if self._toast_window is not toast or not toast.winfo_exists():
                return
            progress = frame / 8
            eased = 1 - (1 - progress) ** 3
            toast.place_configure(y=18 - round(36 * eased))
            if frame < 8:
                self._schedule_toast(enter, frame + 1, delay=16)
            else:
                self._schedule_toast(dismiss, delay=3200)

        def dismiss(frame: int = 0) -> None:
            if self._toast_window is not toast or not toast.winfo_exists():
                return
            progress = frame / 8
            toast.place_configure(y=-18 - round(10 * progress))
            if frame < 8:
                self._schedule_toast(dismiss, frame + 1, delay=16)
            else:
                toast.destroy()
                self._toast_window = None

        self._schedule_toast(enter, delay=16)

    def _schedule_toast(self, callback: Callable[..., None], *args: object, delay: int) -> None:
        after_id = ""

        def run() -> None:
            self._toast_after_ids.discard(after_id)
            callback(*args)

        after_id = self.root.after(delay, run)
        self._toast_after_ids.add(after_id)

    def _dismiss_toast(self) -> None:
        for after_id in tuple(self._toast_after_ids):
            self.root.after_cancel(after_id)
        self._toast_after_ids.clear()
        if self._toast_window is not None and self._toast_window.winfo_exists():
            self._toast_window.destroy()
        self._toast_window = None

    def _handle_hint(self, result: HintResult) -> None:
        if result.token != self._state.token:
            return
        self.session.queries.extend(result.queries)
        self.session.persist()
        if result.character_id is None or result.status is None:
            all_revealed = all(item.status is not None for item in self._state.characters)
            if result.kb_status == KBStatus.INCONSISTENT:
                self.status_label.configure(text="No forced move · Inconsistent public clues.")
            elif all_revealed:
                self.status_label.configure(text="All cards are already revealed · Consistent.")
            else:
                self.status_label.configure(
                    text=f"No forced move · {result.kb_status.value.title()}"
                )
        else:
            self._selected_id = result.character_id
            self.board.pulse((result.character_id,))
            self.status_label.configure(
                text=f"Hint: {result.character_id} is forced {result.status.value.title()}."
            )
            self._render_state(self._state)

    def _handle_solve(self, result: AutoSolveResult) -> None:
        if result.final_state.token != self.engine.get_public_state().token:
            self.refresh()
            return
        self.session.queries[self._solve_query_start :] = result.queries
        self.session.metrics_partial = self._metrics_partial_before_run
        self.session.persist()
        self._animation_generation += 1
        generation = self._animation_generation
        snapshots: list[tuple[str, PublicState]] = []
        current = self._solve_start_state
        for step in result.steps:
            characters = tuple(
                replace(
                    character,
                    status=step.verdict,
                    clue=step.newly_revealed_clue,
                )
                if character.id == step.character_id
                else character
                for character in current.characters
            )
            current = replace(current, token=step.token_after, characters=characters)
            snapshots.append((step.character_id, current))

        self._busy = True
        self._update_controls()

        def show_step(index: int) -> None:
            if generation != self._animation_generation:
                return
            if index >= len(snapshots):
                self._render_state(result.final_state)
                self._last_solve = result
                self._busy = False
                step_word = "step" if len(result.steps) == 1 else "steps"
                self.status_label.configure(
                    text=(
                        f"Auto Solve: {result.outcome.value.title()} · "
                        f"{len(result.steps)} {step_word}."
                    )
                )
                self._update_controls()
                if result.outcome == SolveOutcome.SOLVED:
                    self._show_toast(
                        "Case Solved",
                        f"All cards proven in {len(result.steps)} steps.",
                        "success",
                    )
                    self._maybe_completed()
                elif result.outcome == SolveOutcome.STUCK:
                    self._show_toast(
                        "Auto Solve Stuck",
                        f"Stopped after {len(result.steps)} step(s) with no remaining forced move.",
                        "info",
                    )
                elif result.outcome == SolveOutcome.INCONSISTENT:
                    self._show_toast(
                        "Inconsistent Clues",
                        "Public clues are inconsistent. Deduction stopped.",
                        "error",
                    )
                return
            character_id, next_state = snapshots[index]

            def reveal() -> None:
                if generation == self._animation_generation:
                    self._render_state(next_state)

            self.board.flip_card(character_id, reveal, lambda: show_step(index + 1))

        show_step(0)

    def _view_trace(self) -> None:
        if self._busy or (not self.session.steps and self._last_solve is None):
            return
        self._close_trace()
        self._trace_window = show_replay(
            self.root, tuple(self.session.snapshots), tuple(self.session.steps)
        )

    def _save_trace(self) -> None:
        if self._busy or (not self.session.steps and self._last_solve is None):
            return
        destination = filedialog.asksaveasfilename(
            title="Save deduction trace",
            initialdir=Path(__file__).resolve().parents[1] / "outputs" / "traces",
            initialfile="deduction_trace.json",
            defaultextension=".json",
            filetypes=(("JSON trace", "*.json"),),
        )
        if destination:
            try:
                save_trace(self.session.steps, Path(destination))
                self.status_label.configure(text="Trace saved.")
            except Exception as error:
                self._show_error("Could not save trace", error)

    def _update_controls(self) -> None:
        selected = next(
            (item for item in self._state.characters if item.id == self._selected_id), None
        )
        can_mark = not self._busy and selected is not None and selected.status is None
        self.criminal_button.configure(state="normal" if can_mark else "disabled")
        self.innocent_button.configure(state="normal" if can_mark else "disabled")
        self.hint_button.configure(state="disabled" if self._busy else "normal")
        self.solve_button.configure(state="disabled" if self._busy else "normal")
        can_trace = not self._busy and (bool(self.session.steps) or self._last_solve is not None)
        self.view_trace_button.configure(state="normal" if can_trace else "disabled")
        self.save_trace_button.configure(state="normal" if can_trace else "disabled")
        self.note_picker.configure(state="readonly" if selected and not self._busy else "disabled")
        self.used_button.configure(
            state="normal" if selected and selected.clue and not self._busy else "disabled"
        )
        self.results_button.configure(state="disabled" if self._busy else "normal")

    @staticmethod
    def _show_error(title: str, error: Exception) -> None:
        messagebox.showerror(title, str(error))
