"""Public-state-only character cards with illustrated portraits."""

from collections.abc import Callable, Sequence
from pathlib import Path
from tkinter import Canvas, Event, Frame, Label, Misc, ttk

from PIL import Image, ImageTk  # pyright: ignore[reportMissingImports]

from game.models import Clue, ClueType, PublicCharacter, PublicState, RegionType, Status


class BoardView(ttk.Frame):
    """Render public character cards and report selected cell IDs."""

    PAGE = "#f3ecdf"
    CARD = "#fffaf2"
    BORDER = "#312a26"
    INK = "#312a26"
    MUTED = "#796f64"
    CRIMINAL = "#c92f28"
    INNOCENT = "#577967"
    HIGHLIGHT = "#d8211c"
    HIGHLIGHT_FILL = "#f7c8c0"
    _CARD_SIZES = {3: (190, 175), 4: (166, 140), 5: (142, 105)}

    def __init__(self, master: Misc, on_select: Callable[[str], None]) -> None:
        super().__init__(master, padding=8)
        self.configure(style="Board.TFrame")
        self._on_select = on_select
        self._state: PublicState | None = None
        self._highlighted: set[str] = set()
        self._buttons: dict[str, Canvas] = {}
        self._card_size: tuple[int, int] | None = None
        self._canvas = Canvas(self, bg=self.PAGE, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True)
        self._grid_frame = Frame(self._canvas, bg=self.PAGE)
        self._grid_window = self._canvas.create_window((0, 0), window=self._grid_frame, anchor="nw")
        self._canvas.bind("<Configure>", self._resize_grid)
        self._portraits = self._load_portraits()

    def render(self, state: PublicState) -> None:
        """Rebuild the board using only the supplied public snapshot."""
        self._state = state
        self._highlighted.intersection_update(item.id for item in state.characters)
        width, height = self._canvas.winfo_width(), self._canvas.winfo_height()
        self._card_size = (
            self._fit_card_size(state.size, width, height)
            if width > 1 and height > 1
            else self._CARD_SIZES.get(state.size, (142, 105))
        )
        self._render_grid(*self._card_size)

    def _render_grid(self, card_width: int, card_height: int) -> None:
        if self._state is None:
            return
        for child in self._grid_frame.winfo_children():
            child.destroy()
        self._buttons.clear()
        state = self._state
        for index in range(6):
            self._grid_frame.grid_columnconfigure(index, minsize=0, weight=0)
            self._grid_frame.grid_rowconfigure(index, minsize=0, weight=0)
        self._grid_frame.grid_columnconfigure(0, minsize=24)
        self._grid_frame.grid_rowconfigure(0, minsize=25)
        for col in range(state.size):
            self._grid_frame.grid_columnconfigure(col + 1, minsize=card_width + 8)
            self._coordinate_label(chr(65 + col)).grid(
                row=0, column=col + 1, sticky="ew", pady=(0, 5)
            )
        by_coord = {(item.row, item.col): item for item in state.characters}
        for row in range(state.size):
            self._grid_frame.grid_rowconfigure(row + 1, minsize=card_height + 8)
            self._coordinate_label(str(row + 1)).grid(
                row=row + 1, column=0, sticky="ns", padx=(0, 4)
            )
            for col in range(state.size):
                character = by_coord[(row, col)]
                card = self._make_card(character, card_width, card_height)
                card.grid(row=row + 1, column=col + 1, padx=4, pady=4, sticky="nsew")
                self._buttons[character.id] = card
        self._refresh_card_colors()

    def highlight(self, cell_ids: Sequence[str]) -> None:
        """Mark clue-related cells without changing the public state."""
        self._highlighted = set(cell_ids)
        self._refresh_card_colors()

    def _coordinate_label(self, text: str) -> Label:
        return Label(
            self._grid_frame,
            text=text,
            bg=BoardView.PAGE,
            fg=BoardView.MUTED,
            font=("Segoe UI", 10, "bold"),
            anchor="center",
        )

    def _make_card(self, character: PublicCharacter, width: int, height: int) -> Canvas:
        border = Canvas(
            self._grid_frame,
            width=width,
            height=height,
            bg=self.PAGE,
            bd=0,
            highlightthickness=0,
        )
        border.create_polygon(
            *self._rounded_rectangle_points(width, height, min(15, width // 8, height // 8)),
            fill=self.BORDER,
            outline=self.BORDER,
            smooth=True,
            splinesteps=16,
            tags="card_border",
        )
        content = Frame(border, bg=self.CARD, padx=4 if width < 130 else 6, pady=2)
        border.create_window(
            (5, 5),
            window=content,
            width=width - 10,
            height=height - 10,
            anchor="nw",
        )
        card_font = 7 if width < 110 else 8 if width < 145 else 9
        name_font = 9 if width < 110 else 10 if width < 145 else 12
        portrait_width = max(34, min(76, width - 24))
        portrait_height = max(26, min(72, height // 3))
        self._bind_card(border, character.id)
        self._bind_card(content, character.id)
        id_label = Label(
            content,
            text=(
                f"{character.id} · {character.status.value.title()}"
                if character.status is not None
                else character.id
            ),
            bg=self.CARD,
            fg=self.MUTED,
            font=("Segoe UI", card_font, "bold"),
            anchor="w",
        )
        id_label.pack(fill="x")
        self._bind_card(id_label, character.id)
        portrait = self._portraits[(character.row * 5 + character.col) % len(self._portraits)]
        portrait = portrait.copy()
        portrait.thumbnail((portrait_width, portrait_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(portrait, master=self)
        avatar = Label(content, image=photo, bg=self.CARD, bd=0)
        setattr(avatar, "image", photo)
        avatar.pack(pady=(0, 1))
        self._bind_card(avatar, character.id)
        name = Label(
            content,
            text=character.name,
            bg=self.CARD,
            fg=self.INK,
            font=("Segoe UI", name_font, "bold"),
            wraplength=width - 18,
        )
        name.pack()
        self._bind_card(name, character.id)
        profession = Label(
            content,
            text=character.profession,
            bg=self.CARD,
            fg=self.MUTED,
            font=("Segoe UI", card_font, "bold"),
            wraplength=width - 18,
        )
        profession.pack(pady=(1, 0))
        self._bind_card(profession, character.id)
        if character.clue is None:
            clue_text = "Clue locked"
            clue_color = self.MUTED
        else:
            clue_text = self._format_clue(character.clue)
            clue_color = self.INK
        clue = Label(
            content,
            text=clue_text,
            bg=self.CARD,
            fg=clue_color,
            font=("Segoe UI", card_font),
            wraplength=width - 20,
            justify="center",
        )
        clue.pack(fill="both", expand=True, pady=(4, 0))
        self._bind_card(clue, character.id)
        return border

    def _bind_card(self, widget: Misc, character_id: str) -> None:
        widget.bind("<Button-1>", lambda _event: self._on_select(character_id))

    def _refresh_card_colors(self) -> None:
        if self._state is None:
            return
        for character in self._state.characters:
            card = self._buttons.get(character.id)
            if card is None:
                continue
            fill = self.HIGHLIGHT_FILL if character.id in self._highlighted else self.CARD
            border = self.HIGHLIGHT if character.id in self._highlighted else self.BORDER
            card.itemconfigure("card_border", fill=border, outline=border)
            for content in card.winfo_children():
                content.configure({"bg": fill})
                for child in content.winfo_children():
                    child.configure({"bg": fill})
                    if isinstance(child, Label) and str(child.cget("text")).startswith(
                        character.id
                    ):
                        status_color = (
                            self.CRIMINAL
                            if character.status == Status.CRIMINAL
                            else self.INNOCENT
                            if character.status == Status.INNOCENT
                            else self.MUTED
                        )
                        child.configure(fg=status_color)
                    elif isinstance(child, Label) and child.cget("text") == character.name:
                        child.configure(fg=self.INK)

    def _load_portraits(self) -> list[Image.Image]:
        path = Path(__file__).resolve().parent / "assets" / "avatar_sheet.png"
        with Image.open(path) as source:
            sheet = source.convert("RGBA")
            portraits = []
            for index in range(25):
                row, col = divmod(index, 5)
                left = round(col * sheet.width / 5)
                upper = round(row * sheet.height / 5)
                right = round((col + 1) * sheet.width / 5)
                lower = round((row + 1) * sheet.height / 5)
                crop = sheet.crop((left, upper, right, lower))
                portraits.append(crop)
        return portraits

    def _resize_grid(self, event: Event) -> None:
        self._canvas.itemconfigure(self._grid_window, width=event.width)
        self._canvas.itemconfigure(self._grid_window, height=event.height)
        if self._state is None or event.width < 100 or event.height < 100:
            return
        card_size = self._fit_card_size(self._state.size, event.width, event.height)
        if card_size != self._card_size:
            self._card_size = card_size
            self._render_grid(*card_size)

    @staticmethod
    def _fit_card_size(board_size: int, width: int, height: int) -> tuple[int, int]:
        card_width = min(220, max(72, (width - 32) // board_size - 8))
        card_height = min(210, max(72, (height - 34) // board_size - 8))
        return card_width, card_height

    @staticmethod
    def _rounded_rectangle_points(width: int, height: int, radius: int) -> tuple[int, ...]:
        return (
            radius,
            1,
            width - radius,
            1,
            width - 2,
            1,
            width - 1,
            radius,
            width - 1,
            height - radius,
            width - 1,
            height - 2,
            width - radius,
            height - 1,
            radius,
            height - 1,
            1,
            height - 1,
            1,
            height - radius,
            1,
            radius,
            1,
            1,
        )

    @staticmethod
    def _format_clue(clue: Clue | None) -> str:
        if clue is None:
            return "Clue locked"
        if clue.type == ClueType.FACT:
            if clue.person is None or clue.status is None:
                return "Incomplete fact clue"
            return f"{clue.person} is {clue.status.value.title()}"
        if clue.type in (ClueType.SAME, ClueType.DIFFERENT):
            relation = "same status as" if clue.type == ClueType.SAME else "different from"
            return f"{clue.first} is {relation} {clue.second}"
        if clue.region is None:
            return clue.type.value.replace("_", " ").title()
        region = clue.region
        region_text = BoardView._format_region(
            region.kind, region.index, region.cell, region.cells, region.first, region.second
        )
        if clue.type in (ClueType.EVEN, ClueType.ODD):
            return f"{clue.type.value.title()} criminals in {region_text}"
        return f"{clue.type.value.replace('_', ' ').title()} {clue.k} criminals in {region_text}"

    @staticmethod
    def _format_region(
        kind: RegionType,
        index: int | None,
        cell: str | None,
        cells: tuple[str, ...],
        first: str | None,
        second: str | None,
    ) -> str:
        if kind == RegionType.ROW:
            return f"row {index + 1}" if index is not None else "row ?"
        if kind == RegionType.COLUMN:
            return f"column {chr(65 + index)}" if index is not None else "column ?"
        if kind == RegionType.NEIGHBORS:
            return f"neighbors of {cell}"
        if kind == RegionType.COMMON_NEIGHBORS:
            return f"common neighbors of {first} and {second}"
        return ", ".join(cells) if cells else "an empty region"
