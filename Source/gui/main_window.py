"""Tkinter application and controller integration boundary."""

from __future__ import annotations

import queue
import threading
from pathlib import Path
from tkinter import BOTH, LEFT, RIGHT, Tk, X, Y, filedialog, messagebox, ttk
from typing import Callable

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.models import (
    AutoSolveResult,
    Clue,
    HintResult,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictResult,
)
from game.puzzle_loader import load_puzzle
from gui.board_view import BoardView
from logic.regions import resolve_region


class MainWindow:
    """Connect user actions to Engine and Agent while keeping Tk on its main thread."""

    _BASE = "#f3ecdf"
    _PANEL = "#ebe1d1"
    _TEXT = "#312a26"
    _MUTED = "#796f64"
    _ACCENT = "#c92f28"

    def __init__(self, root: Tk, engine: GameEngine, agent: DeductiveAgent) -> None:
        self.root = root
        self.engine = engine
        self.agent = agent
        self._state = engine.get_public_state()
        self._selected_id: str | None = None
        self._busy = False
        self._messages: queue.Queue[tuple[str, object, StateToken]] = queue.Queue()
        self._configure_window()
        self._build_layout()
        self.refresh()
        self.root.after(80, self._poll_messages)

    def refresh(self) -> None:
        """Render the latest public snapshot and update action state."""
        self._state = self.engine.get_public_state()
        self.board.render(self._state)
        self.puzzle_title.configure(text=self._state.puzzle_id.replace("_", " ").title())
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
        self._update_controls()

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
        style.configure(
            "Title.TLabel",
            background=self._BASE,
            foreground=self._TEXT,
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "Kicker.TLabel",
            background=self._BASE,
            foreground=self._ACCENT,
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "Body.TLabel", background=self._BASE, foreground=self._TEXT, font=("Segoe UI", 10)
        )
        style.configure(
            "Muted.TLabel", background=self._BASE, foreground=self._MUTED, font=("Segoe UI", 9)
        )
        style.configure(
            "PanelTitle.TLabel",
            background=self._PANEL,
            foreground=self._TEXT,
            font=("Segoe UI", 12, "bold"),
        )
        style.configure(
            "Coordinate.TLabel",
            background=self._BASE,
            foreground=self._MUTED,
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "Card.TButton",
            background="#fffaf2",
            foreground=self._TEXT,
            font=("Segoe UI", 9),
            padding=10,
            anchor="center",
            justify="center",
            relief="flat",
            borderwidth=1,
        )
        style.map(
            "Card.TButton",
            background=[("active", "#f7eee1")],
            foreground=[("disabled", "#9a9187")],
        )
        style.configure(
            "Criminal.TButton",
            background="#f7e7dd",
            foreground=BoardView.CRIMINAL,
            font=("Segoe UI", 9, "bold"),
            padding=10,
            anchor="center",
            justify="center",
            relief="flat",
            borderwidth=1,
        )
        style.map("Criminal.TButton", background=[("active", "#f2ded2")])
        style.configure(
            "Innocent.TButton",
            background="#fffaf2",
            foreground=BoardView.INNOCENT,
            font=("Segoe UI", 9, "bold"),
            padding=10,
            anchor="center",
            justify="center",
            relief="flat",
            borderwidth=1,
        )
        style.map("Innocent.TButton", background=[("active", "#f7eee1")])
        style.configure(
            "Highlighted.TButton",
            background="#f7c8c0",
            foreground="#312a26",
            font=("Segoe UI", 9, "bold"),
            padding=10,
            anchor="center",
            justify="center",
            relief="flat",
            borderwidth=2,
        )
        style.map("Highlighted.TButton", background=[("active", "#f1b2a7")])
        style.configure(
            "Action.TButton",
            background="#4b4037",
            foreground="#fffaf2",
            font=("Segoe UI", 9, "bold"),
            padding=(12, 9),
            relief="flat",
        )
        style.map("Action.TButton", background=[("active", "#615449")])
        style.configure(
            "Primary.TButton",
            background="#d58b28",
            foreground="#fffaf2",
            font=("Segoe UI", 9, "bold"),
            padding=(12, 9),
            relief="flat",
        )
        style.map("Primary.TButton", background=[("active", "#e1a544")])

    def _build_layout(self) -> None:
        shell = ttk.Frame(self.root, style="App.TFrame", padding=(24, 20))
        shell.pack(fill=BOTH, expand=True)
        header = ttk.Frame(shell, style="App.TFrame")
        header.pack(fill=X, pady=(0, 18))
        heading = ttk.Frame(header, style="App.TFrame")
        heading.pack(side=LEFT, fill=X, expand=True)
        ttk.Label(heading, text="THE GRIDUCTIVE FILES", style="Kicker.TLabel").pack(anchor="w")
        self.puzzle_title = ttk.Label(heading, text="", style="Title.TLabel")
        self.puzzle_title.pack(anchor="w", pady=(3, 0))
        self.progress_label = ttk.Label(header, text="", style="Body.TLabel")
        self.progress_label.pack(side=RIGHT, anchor="s", pady=(0, 5))

        body = ttk.Frame(shell, style="App.TFrame")
        body.pack(fill=BOTH, expand=True)
        board_panel = ttk.Frame(body, style="Panel.TFrame", padding=8)
        board_panel.pack(side=LEFT, fill=BOTH, expand=True)
        self.board = BoardView(board_panel, self._select_cell)
        self.board.pack(fill=BOTH, expand=True)

        sidebar = ttk.Frame(body, style="App.TFrame", width=300)
        sidebar.pack(side=RIGHT, fill=Y, padx=(18, 0))
        sidebar.pack_propagate(False)
        ttk.Label(sidebar, text="CASE NOTES", style="Kicker.TLabel").pack(anchor="w")
        self.selected_label = ttk.Label(
            sidebar, text="Select a card", style="PanelTitle.TLabel", wraplength=280
        )
        self.selected_label.pack(anchor="w", pady=(6, 13))
        ttk.Label(sidebar, text="Actions", style="Muted.TLabel").pack(anchor="w", pady=(0, 6))
        actions = ttk.Frame(sidebar, style="App.TFrame")
        actions.pack(fill=X)
        self.criminal_button = ttk.Button(
            actions,
            text="Mark Criminal",
            style="Action.TButton",
            command=lambda: self._submit(Status.CRIMINAL),
        )
        self.criminal_button.pack(fill=X, pady=3)
        self.innocent_button = ttk.Button(
            actions,
            text="Mark Innocent",
            style="Action.TButton",
            command=lambda: self._submit(Status.INNOCENT),
        )
        self.innocent_button.pack(fill=X, pady=3)
        ttk.Separator(sidebar).pack(fill=X, pady=15)
        self.hint_button = ttk.Button(
            sidebar, text="Get a Hint", style="Primary.TButton", command=self._request_hint
        )
        self.hint_button.pack(fill=X, pady=3)
        self.solve_button = ttk.Button(
            sidebar, text="Auto Solve", style="Action.TButton", command=self._auto_solve
        )
        self.solve_button.pack(fill=X, pady=3)
        ttk.Separator(sidebar).pack(fill=X, pady=15)
        self.load_button = ttk.Button(
            sidebar, text="Load Puzzle…", style="Action.TButton", command=self._load
        )
        self.load_button.pack(fill=X, pady=3)
        self.restart_button = ttk.Button(
            sidebar, text="Restart Case", style="Action.TButton", command=self._restart
        )
        self.restart_button.pack(fill=X, pady=3)
        ttk.Label(sidebar, text="PUBLIC CLUES", style="Kicker.TLabel").pack(
            anchor="w", pady=(19, 5)
        )
        self.clue_label = ttk.Label(
            sidebar,
            text="Select a revealed card to inspect its clue.",
            style="Body.TLabel",
            wraplength=280,
            justify=LEFT,
        )
        self.clue_label.pack(anchor="w")
        self.status_label = ttk.Label(
            sidebar, text="Ready", style="Muted.TLabel", wraplength=280, justify=LEFT
        )
        self.status_label.pack(side="bottom", anchor="w", pady=(12, 0))

    def _select_cell(self, character_id: str) -> None:
        self._selected_id = character_id
        character = next(item for item in self._state.characters if item.id == character_id)
        if character.clue is None:
            self.clue_label.configure(text="This card is sealed. Its status and clue stay hidden.")
            self.board.highlight((character_id,))
        else:
            self.clue_label.configure(text=self._describe_clue(character.clue))
            self.board.highlight(self._clue_cells(character.clue, character_id))
        self.refresh()

    def _clue_cells(self, clue: Clue, owner_id: str) -> tuple[str, ...]:
        if clue.type.value == "FACT" and clue.person is not None:
            return (owner_id, clue.person)
        if clue.type.value in ("SAME", "DIFFERENT"):
            return tuple(cell for cell in (clue.first, clue.second) if cell is not None)
        if clue.region is not None:
            return (owner_id, *resolve_region(clue.region, self._state))
        return (owner_id,)

    @staticmethod
    def _describe_clue(clue: Clue) -> str:
        return BoardView._format_clue(clue)

    def _submit(self, status: Status) -> None:
        character_id = self._selected_id
        if character_id is None:
            return
        snapshot = self._state
        self._start_task(
            "verdict",
            lambda: self.engine.submit_verdict(character_id, status, expected_token=snapshot.token),
            snapshot.token,
        )

    def _request_hint(self) -> None:
        snapshot = self._state
        self._start_task("hint", lambda: self.agent.next_hint(snapshot), snapshot.token)

    def _auto_solve(self) -> None:
        snapshot = self._state
        self._start_task("solve", lambda: self.agent.auto_solve(self.engine), snapshot.token)

    def _load(self) -> None:
        selected_path = filedialog.askopenfilename(
            title="Load a Griductive puzzle",
            initialdir=Path(__file__).resolve().parents[1] / "puzzles",
            filetypes=(("Puzzle JSON", "*.json"), ("All files", "*.*")),
        )
        if not selected_path:
            return
        try:
            puzzle = load_puzzle(Path(selected_path))
            self._state = self.engine.load(puzzle)
            self._busy = False
            self._selected_id = None
            self.board.highlight(())
            self.status_label.configure(text="Puzzle loaded.")
            self.refresh()
        except Exception as error:
            self._show_error("Could not load puzzle", error)

    def _restart(self) -> None:
        try:
            self._selected_id = None
            self._state = self.engine.restart()
            self._busy = False
            self.board.highlight(())
            self.status_label.configure(text="Case restarted.")
            self.refresh()
        except Exception as error:
            self._show_error("Could not restart case", error)

    def _start_task(self, kind: str, action: Callable[[], object], token: StateToken) -> None:
        if self._busy:
            return
        self._busy = True
        self.status_label.configure(text="Working…")
        self._update_controls()

        def run() -> None:
            try:
                result: object = action()
            except Exception as error:
                result = error
            self._messages.put((kind, result, token))

        threading.Thread(target=run, name=f"griductive-{kind}", daemon=True).start()

    def _poll_messages(self) -> None:
        try:
            while True:
                kind, result, token = self._messages.get_nowait()
                if token.session_id != self._state.token.session_id:
                    continue
                self._busy = False
                if isinstance(result, Exception):
                    self._show_error("Operation failed", result)
                elif kind == "verdict" and isinstance(result, VerdictResult):
                    self._handle_verdict(result)
                elif kind == "hint" and isinstance(result, HintResult):
                    self._handle_hint(result)
                elif kind == "solve" and isinstance(result, AutoSolveResult):
                    self._handle_solve(result)
        except queue.Empty:
            pass
        self._update_controls()
        self.root.after(80, self._poll_messages)

    def _handle_verdict(self, result: VerdictResult) -> None:
        self._state = result.state
        labels = {
            VerdictOutcome.ACCEPTED: "Verdict accepted. New clue revealed.",
            VerdictOutcome.NOT_PROVABLE: "Not provable yet. No card was changed.",
            VerdictOutcome.CONTRADICTED: "That verdict contradicts the public clues.",
            VerdictOutcome.INCONSISTENT: "The public clues are inconsistent.",
            VerdictOutcome.STALE_STATE: "Board changed; your result was discarded.",
            VerdictOutcome.ALREADY_REVEALED: "That card is already revealed.",
        }
        self.status_label.configure(text=labels[result.outcome])
        self.refresh()

    def _handle_hint(self, result: HintResult) -> None:
        if result.token != self._state.token:
            return
        if result.character_id is None or result.status is None:
            self.status_label.configure(text=f"No forced move · {result.kb_status.value.title()}")
        else:
            self._selected_id = result.character_id
            self.board.highlight((result.character_id,))
            self.status_label.configure(
                text=f"Hint: {result.character_id} is forced {result.status.value.title()}."
            )
            self.refresh()

    def _handle_solve(self, result: AutoSolveResult) -> None:
        if result.final_state.token.session_id != self._state.token.session_id:
            return
        self._state = result.final_state
        self.status_label.configure(text=f"Auto Solve: {result.outcome.value.title()}.")
        self.refresh()

    def _update_controls(self) -> None:
        selected = next(
            (item for item in self._state.characters if item.id == self._selected_id), None
        )
        can_mark = not self._busy and selected is not None and selected.status is None
        self.criminal_button.configure(state="normal" if can_mark else "disabled")
        self.innocent_button.configure(state="normal" if can_mark else "disabled")
        self.hint_button.configure(state="disabled" if self._busy else "normal")
        self.solve_button.configure(state="disabled" if self._busy else "normal")

    @staticmethod
    def _show_error(title: str, error: Exception) -> None:
        messagebox.showerror(title, str(error))
