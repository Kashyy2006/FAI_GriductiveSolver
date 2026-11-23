"""Level library, public replay, illustrated glossary and static player guide."""

from collections.abc import Callable, Sequence
from secrets import randbelow
from tkinter import BOTH, LEFT, Canvas, StringVar, Text, Toplevel, X, ttk
from typing import Any

from game.models import DeductionStep, PublicCharacter, PublicState, Region, RegionType, StateToken
from gui import theme
from gui.board_view import BoardView
from gui.clue_text import format_clue
from gui.play_session import available_levels
from logic.regions import resolve_region


def show_library(
    parent: Any,
    records: dict[str, Any],
    open_level: Callable[[str], None],
    generate: Callable[[int, int], None] | None = None,
) -> Toplevel:
    window = Toplevel(parent)
    window.configure(background=theme.PAGE)
    window.title("Case Library")
    window.geometry("820x520")
    window.minsize(700, 460)
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
        values=("All", "Easy", "Medium", "Hard", "Practice", "Generated"),
        state="readonly",
        width=18,
    )
    filter_box.pack(anchor="w", pady=(0, 10))
    list_panel = ttk.Frame(panel)
    list_panel.pack(fill=BOTH, expand=True)
    tree = ttk.Treeview(
        list_panel, columns=("difficulty", "progress"), show="tree headings", height=7
    )
    tree.heading("#0", text="Case")
    tree.heading("difficulty", text="Difficulty")
    tree.heading("progress", text="Progress")
    tree.column("#0", width=300)
    tree.column("difficulty", width=90)
    tree.column("progress", width=140)
    list_scroll = ttk.Scrollbar(
        list_panel,
        orient="vertical",
        command=tree.yview,
        style=theme.scrollbar_style(window, theme.CARD),
    )
    list_scroll.pack(side="right", fill="y")
    tree.configure(yscrollcommand=list_scroll.set)
    tree.pack(side=LEFT, fill=BOTH, expand=True)
    description = ttk.Label(panel, wraplength=670)
    description.pack(fill=X, pady=10)

    def populate(_event: object = None) -> None:
        tree.delete(*tree.get_children())
        for level in available_levels():
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
        level = next(
            (level for level in available_levels() if selection and level.key == selection[0]), None
        )
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
    actions = ttk.Frame(panel)
    actions.pack(fill=X)
    if generate is not None:

        def create() -> None:
            window.destroy()
            show_generator(parent, generate)

        ttk.Button(actions, text="Generate Puzzle…", command=create).pack(side=LEFT)
    ttk.Button(actions, text="Play / Continue", command=choose).pack(side="right")
    populate()
    return window


def show_generator(parent: Any, generate: Callable[[int, int], None]) -> Toplevel:
    window = Toplevel(parent)
    window.configure(background=theme.PAGE)
    window.title("Generate Puzzle")
    window.geometry("560x420")
    window.minsize(560, 420)
    panel = ttk.Frame(window, padding=22)
    panel.pack(fill=BOTH, expand=True)
    ttk.Label(panel, text="Generate a new case", font=("Segoe UI", 17, "bold")).pack(anchor="w")
    ttk.Label(
        panel,
        text=(
            "Fixed board size. Same version, size and seed reproduce the case.\n"
            "Verified UNIQUE, with exactly one forced move at every step.\n"
            "Varied relations, counts and parity; no FACT chains."
        ),
        wraplength=510,
    ).pack(anchor="w", pady=12)
    ttk.Label(panel, text="Board size").pack(anchor="w")
    size = StringVar(window, "3 × 3")
    ttk.Combobox(
        panel, textvariable=size, values=("3 × 3", "4 × 4", "5 × 5"), state="readonly", width=12
    ).pack(anchor="w", pady=(2, 8))
    ttk.Label(panel, text="Seed (0–2147483647)").pack(anchor="w")
    seed = StringVar(window, str(randbelow(2**31)))
    ttk.Entry(panel, textvariable=seed).pack(fill=X, pady=(2, 6))
    error = ttk.Label(panel, foreground="#c92f28")
    error.pack(anchor="w")

    def create() -> None:
        try:
            value = int(seed.get())
            if not 0 <= value <= 2**31 - 1:
                raise ValueError
        except ValueError:
            error.configure(text="Enter an integer from 0 to 2147483647.")
            return
        generate(int(size.get()[0]), value)
        window.destroy()

    ttk.Button(panel, text="Generate & Play", command=create).pack(anchor="e", pady=(8, 0))
    return window


def show_replay(
    parent: Any, snapshots: Sequence[PublicState], steps: Sequence[DeductionStep]
) -> Toplevel:
    """The viewer has no Engine reference and cannot reveal or submit anything."""
    window = Toplevel(parent)
    window.configure(background=theme.PAGE)
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
    info_panel = ttk.Frame(body)
    info_panel.pack(side="right", fill="y", padx=(8, 12), pady=(4, 12))
    info = Text(
        info_panel,
        width=34,
        wrap="word",
        padx=16,
        pady=16,
        font=("Segoe UI", -13),
        bg=theme.CARD,
        fg=theme.INK,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=theme.LINE,
    )
    info_scroll = ttk.Scrollbar(
        info_panel,
        orient="vertical",
        command=info.yview,
        style=theme.scrollbar_style(window, theme.CARD),
    )
    info_scroll.pack(side="right", fill="y")
    info.configure(yscrollcommand=info_scroll.set)
    info.pack(fill=BOTH, expand=True)

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
    window.configure(background=theme.PAGE)
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
            "First Hint highlights useful public clues; press it again on the same board "
            "to see a person and verdict. Neither Hint nor a rejected verdict opens cards. "
            "A Remark is story text, not evidence.",
        ),
        (
            "Your own notes",
            "Pencil colors have labels: Amber = Review, Blue = Maybe Innocent, "
            "Purple = Maybe Criminal. Clear note removes a pencil mark; Used clue crosses "
            "off a public clue. These are personal notes and guesses; they never change "
            "proof, verdicts, or reveals. "
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
        canvas = Canvas(row, width=155, height=94, highlightthickness=0, bg=theme.PAGE)
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
