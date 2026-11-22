"""Level library, public replay, illustrated glossary and static player guide."""

from collections.abc import Callable, Sequence
from tkinter import BOTH, LEFT, Canvas, StringVar, Text, Toplevel, X, ttk
from typing import Any

from game.models import DeductionStep, PublicCharacter, PublicState, Region, RegionType, StateToken
from gui.board_view import BoardView
from gui.clue_text import format_clue
from gui.play_session import LEVELS
from logic.regions import resolve_region


def show_library(
    parent: Any, records: dict[str, Any], open_level: Callable[[str], None]
) -> Toplevel:
    window = Toplevel(parent)
    window.title("Case Library")
    window.geometry("760x470")
    window.minsize(620, 400)
    panel = ttk.Frame(window, padding=18)
    panel.pack(fill=BOTH, expand=True)
    ttk.Label(panel, text="Choose a case", font=("Segoe UI", 18, "bold")).pack(anchor="w")
    ttk.Label(
        panel, text="Difficulty is editorial. Progress is saved separately for each case."
    ).pack(anchor="w", pady=(4, 12))
    difficulty = StringVar(window, "All")
    filter_box = ttk.Combobox(
        panel,
        textvariable=difficulty,
        values=("All", "Easy", "Medium", "Practice"),
        state="readonly",
        width=18,
    )
    filter_box.pack(anchor="w", pady=(0, 10))
    tree = ttk.Treeview(panel, columns=("difficulty", "progress"), show="tree headings", height=7)
    tree.heading("#0", text="Case")
    tree.heading("difficulty", text="Difficulty")
    tree.heading("progress", text="Progress")
    tree.column("#0", width=300)
    tree.column("difficulty", width=90)
    tree.column("progress", width=140)
    tree.pack(fill=BOTH, expand=True)
    description = ttk.Label(panel, wraplength=670)
    description.pack(fill=X, pady=10)

    def populate(_event: object = None) -> None:
        tree.delete(*tree.get_children())
        for level in LEVELS:
            if difficulty.get() not in ("All", level.difficulty):
                continue
            record = records.get(level.key, {})
            progress = (
                "Completed"
                if record.get("completed")
                else (f"{len(record.get('moves', []))} moves · Continue" if record else "New case")
            )
            tree.insert(
                "", "end", iid=level.key, text=level.title, values=(level.difficulty, progress)
            )
        children = tree.get_children()
        if children:
            tree.selection_set(children[0])
            describe()

    def describe(_event: object = None) -> None:
        selection = tree.selection()
        level = next((level for level in LEVELS if selection and level.key == selection[0]), None)
        description.configure(text=level.description if level else "Select a case.")

    def choose(_event: object = None) -> None:
        selection = tree.selection()
        if selection:
            key = selection[0]
            window.destroy()
            open_level(key)

    filter_box.bind("<<ComboboxSelected>>", populate)
    tree.bind("<<TreeviewSelect>>", describe)
    tree.bind("<Double-1>", choose)
    ttk.Button(panel, text="Play / Continue", command=choose).pack(anchor="e")
    populate()
    return window


def show_replay(
    parent: Any, snapshots: Sequence[PublicState], steps: Sequence[DeductionStep]
) -> Toplevel:
    """The viewer has no Engine reference and cannot reveal or submit anything."""
    window = Toplevel(parent)
    window.title("Public Replay")
    window.geometry("1120x760")
    window.minsize(950, 650)
    position = 0
    header = ttk.Frame(window, padding=10)
    header.pack(fill=X)
    counter = ttk.Label(header)
    counter.pack(side=LEFT, padx=14)
    body = ttk.Frame(window)
    body.pack(fill=BOTH, expand=True)
    info = Text(body, width=34, wrap="word", padx=12, pady=12, font=("Segoe UI", 11))
    info.pack(side="right", fill="y")

    def inspect(character_id: str) -> None:
        state = snapshots[position]
        character = next(c for c in state.characters if c.id == character_id)
        board.highlight((character.id,))
        if character.clue is not None:
            clue = character.clue
            cells = (
                (clue.person,)
                if clue.person
                else tuple(cell for cell in (clue.first, clue.second) if cell is not None)
            )
            if clue.region:
                cells = resolve_region(clue.region, state)
            board.highlight(cells)
        set_info(
            f"{character.name} ({character.id})\n"
            f"Status: {character.status.value.title() if character.status else 'Hidden'}\n\n"
            f"{format_clue(character.clue, state)}"
        )

    def set_info(value: str) -> None:
        info.configure(state="normal")
        info.delete("1.0", "end")
        info.insert("1.0", value)
        info.configure(state="disabled")

    board = BoardView(body, inspect)
    board.pack(fill=BOTH, expand=True)

    def display(index: int) -> None:
        nonlocal position
        position = index
        state = snapshots[position]
        board.highlight(())
        board.render(state)
        counter.configure(text=f"Snapshot {position} / {len(snapshots) - 1}")
        previous.configure(state="normal" if position else "disabled")
        following.configure(state="normal" if position < len(snapshots) - 1 else "disabled")
        if position == 0:
            set_info("Initial public board.\n\nSelect a card to read what was public at this step.")
        else:
            step = steps[position - 1]
            name = next(c.name for c in state.characters if c.id == step.character_id)
            set_info(
                f"Step {position}: {name} is {step.verdict.value.title()}\n\n"
                f"New clue: {format_clue(step.newly_revealed_clue, state)}\n\n"
                f"Active logical clues before reveal (not a minimal explanation):\n"
                f"{', '.join(step.active_clue_ids) or 'None'}\n\n"
                f"Proof details: {len(step.queries)} SAT calls\n"
                + "\n".join(f"{q.purpose}: {q.result.value}" for q in step.queries)
            )

    previous = ttk.Button(header, text="← Previous", command=lambda: display(position - 1))
    previous.pack(side=LEFT)
    following = ttk.Button(header, text="Next →", command=lambda: display(position + 1))
    following.pack(side=LEFT, padx=8)
    window.bind("<Left>", lambda _: display(max(0, position - 1)))
    window.bind("<Right>", lambda _: display(min(len(snapshots) - 1, position + 1)))
    display(0)
    return window


def show_help(parent: Any) -> Toplevel:
    window = Toplevel(parent)
    window.title("? How to Play & Glossary")
    window.geometry("820x690")
    notebook = ttk.Notebook(window)
    notebook.pack(fill=BOTH, expand=True, padx=14, pady=14)
    guide = ttk.Frame(notebook, padding=20)
    notebook.add(guide, text="? How to play")
    instructions = (
        (
            "1 · Choose a public clue",
            "Click a revealed card. Read its clue in PUBLIC CLUES. "
            "Every revealed clue is true, even when its owner is Criminal.",
        ),
        (
            "2 · Read the amber highlight",
            "The amber border marks the people or region mentioned "
            "by that clue. Neighbors include diagonals. An empty region highlights no cards.",
        ),
        (
            "3 · Prove a verdict yourself",
            "Combine public clues and known verdicts. If a clue says "
            "Ben is Innocent, select Ben and choose Mark Innocent. For a count or parity clue, "
            "check whether the known cards force a single remaining possibility. Do not guess.",
        ),
        (
            "4 · Submit and repeat",
            "Only a proved verdict opens a card and its next clue. "
            "A rejected verdict or Hint opens nothing. A Remark is story text, not evidence.",
        ),
        (
            "Your own notes",
            "Use Temporary color on a selected card and Used clue on a public "
            "clue. These are reminders only: they never change proof, verdicts, or reveals. "
            "Replay lets you inspect earlier public snapshots without changing the game.",
        ),
    )
    for title, text in instructions:
        ttk.Label(guide, text=title, font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(12, 4))
        ttk.Label(guide, text=text, wraplength=710, justify="left").pack(anchor="w")

    glossary = ttk.Frame(notebook, padding=12)
    notebook.add(glossary, text="Illustrated glossary")
    state = PublicState(
        "glossary",
        4,
        StateToken("illustration", 0),
        tuple(
            PublicCharacter(f"{chr(65 + col)}{row + 1}", "Example", "", row, col)
            for row in range(4)
            for col in range(4)
        ),
    )
    examples = (
        (
            "Neighbors",
            Region(RegionType.NEIGHBORS, cell="B2"),
            ("B2",),
            "Eight directions around B2, including diagonals; B2 itself is excluded.",
        ),
        (
            "Common neighbors",
            Region(RegionType.COMMON_NEIGHBORS, first="A1", second="C1"),
            ("A1", "C1"),
            "The intersection of both neighbor sets: B1 and B2. "
            "Both endpoints are excluded; each cell is counted once.",
        ),
        (
            "Row / Column",
            Region(RegionType.ROW, index=1),
            (),
            "Amber: row 2, left to right. Blue: column C, top to bottom. "
            "A cell at the intersection belongs to both regions.",
        ),
        (
            "Parity",
            Region(RegionType.EXPLICIT, cells=("A1", "B1", "C1")),
            (),
            "Count Criminals in the amber region. EVEN allows 0 or 2; ODD allows 1 or 3. "
            "Parity alone does not identify which people are Criminal.",
        ),
        (
            "Empty region",
            Region(RegionType.COMMON_NEIGHBORS, first="A1", second="D4"),
            ("A1", "D4"),
            "These two cells have no common neighbors. The count is 0: "
            "EVEN and EXACTLY / AT LEAST / AT MOST 0 are true; ODD is false.",
        ),
    )
    for index, (title, region, endpoints, explanation) in enumerate(examples):
        row = ttk.Frame(glossary)
        row.pack(fill=X, pady=3)
        canvas = Canvas(row, width=155, height=94, highlightthickness=0)
        canvas.pack(side=LEFT, padx=(0, 12))
        cells = set(resolve_region(region, state))
        for cell in state.characters:
            x, y = cell.col * 38, cell.row * 23
            fill = "#faebd2" if cell.id in cells else "#fffaf2"
            if index == 2 and cell.col == 2:
                fill = "#ccdff4" if cell.id not in cells else "#dfd0ba"
            outline = "#c92f28" if cell.id in endpoints else "#b9afa3"
            canvas.create_rectangle(x + 2, y + 2, x + 37, y + 22, fill=fill, outline=outline)
            canvas.create_text(x + 19, y + 12, text=cell.id, font=("Segoe UI", 8))
        description = ttk.Frame(row)
        description.pack(side=LEFT, fill=X, expand=True)
        ttk.Label(description, text=title, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(description, text=explanation, wraplength=550, justify="left").pack(anchor="w")
    return window
