"""Shared paper-and-ink surfaces, readable controls and background-matched scrollbars."""

from tkinter import Misc, ttk

PAGE = "#f5f2eb"
PANEL = "#ebe7dd"
CARD = "#fffdf8"
INK = "#293b36"
MUTED = "#788078"
LINE = "#d8d3c7"
ACCENT = "#326c60"
CRIMINAL = "#b84c43"
INNOCENT = "#527c66"
CRIMINAL_FILL = "#f6e7e2"
INNOCENT_FILL = "#e7efe7"


def blend(background: str, foreground: str, amount: float) -> str:
    channels = [
        round(
            int(background[i : i + 2], 16) * (1 - amount) + int(foreground[i : i + 2], 16) * amount
        )
        for i in (1, 3, 5)
    ]
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def scrollbar_style(master: Misc, background: str, *, compact: bool = False) -> str:
    """Keep the track on its surface while leaving the draggable thumb visible."""
    style = ttk.Style(master)
    name = f"{'Clue' if compact else 'Surface'}{background[1:]}.Vertical.TScrollbar"
    if not style.configure(name):
        style.layout(
            name,
            [
                (
                    "Vertical.Scrollbar.trough",
                    {
                        "sticky": "ns",
                        "children": [
                            (
                                "Vertical.Scrollbar.thumb",
                                {
                                    "sticky": "nswe",
                                    "expand": True,
                                },
                            )
                        ],
                    },
                )
            ],
        )
        style.configure(
            name,
            troughcolor=background,
            background=blend(background, INK, 0.24),
            bordercolor=background,
            lightcolor=background,
            darkcolor=background,
            arrowcolor=background,
            borderwidth=0,
            relief="flat",
            width=8 if compact else 10,
        )
        style.map(
            name,
            background=[
                ("disabled", background),
                ("pressed", blend(background, INK, 0.50)),
                ("active", blend(background, INK, 0.36)),
            ],
        )
    return name


def install_theme(master: Misc) -> None:
    style = ttk.Style(master)
    style.theme_use("clam")
    style.configure(".", background=PAGE, foreground=INK, font=("Segoe UI", -13))
    for name, background in (
        ("TFrame", PAGE),
        ("App.TFrame", PAGE),
        ("Panel.TFrame", PAGE),
        ("Board.TFrame", PAGE),
        ("CardBox.TFrame", CARD),
    ):
        style.configure(name, background=background)
    for name, background, foreground, font in (
        ("TLabel", PAGE, INK, ("Segoe UI", -13)),
        ("Title.TLabel", PAGE, INK, ("Segoe UI", -30, "bold")),
        ("Kicker.TLabel", PAGE, ACCENT, ("Segoe UI", -11, "bold")),
        ("Body.TLabel", PAGE, INK, ("Segoe UI", -13)),
        ("Muted.TLabel", PAGE, MUTED, ("Segoe UI", -12)),
        ("CardBody.TLabel", CARD, INK, ("Segoe UI", -13)),
        ("PanelTitle.TLabel", CARD, INK, ("Segoe UI", -16, "bold")),
        ("Coordinate.TLabel", PAGE, MUTED, ("Segoe UI", -12, "bold")),
        ("Badge.TLabel", PANEL, INK, ("Segoe UI", -12, "bold")),
    ):
        style.configure(name, background=background, foreground=foreground, font=font)
    style.configure("Badge.TLabel", padding=(12, 7))
    style.configure("TSeparator", background=LINE)
    for name, background, foreground in (
        ("TButton", CARD, INK),
        ("Action.TButton", CARD, INK),
        ("Primary.TButton", ACCENT, CARD),
        ("CriminalAction.TButton", CRIMINAL_FILL, CRIMINAL),
        ("InnocentAction.TButton", INNOCENT_FILL, INNOCENT),
        ("Quiet.TButton", PAGE, MUTED),
    ):
        style.configure(
            name,
            background=background,
            foreground=foreground,
            font=("Segoe UI", -12, "bold"),
            padding=(10, 9),
            relief="flat",
            borderwidth=1,
            bordercolor=LINE,
            focuscolor=ACCENT,
        )
        style.map(
            name,
            background=[("disabled", PANEL), ("active", blend(background, foreground, 0.08))],
            foreground=[("disabled", "#a1a69d")],
            bordercolor=[("focus", ACCENT), ("active", blend(LINE, INK, 0.2))],
        )
    style.configure(
        "TCombobox",
        fieldbackground=CARD,
        background=PANEL,
        foreground=INK,
        arrowcolor=MUTED,
        bordercolor=LINE,
        padding=6,
        arrowsize=12,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", CARD)],
        foreground=[("readonly", INK)],
        selectbackground=[("readonly", CARD)],
        selectforeground=[("readonly", INK)],
    )
    style.configure("TEntry", fieldbackground=CARD, foreground=INK, bordercolor=LINE, padding=7)
    style.configure(
        "Treeview",
        background=CARD,
        fieldbackground=CARD,
        foreground=INK,
        borderwidth=0,
        rowheight=32,
    )
    style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", CARD)])
    style.configure(
        "Treeview.Heading",
        background=PANEL,
        foreground=INK,
        font=("Segoe UI", -12, "bold"),
        padding=(10, 9),
        relief="flat",
    )
    style.configure("TNotebook", background=PAGE, borderwidth=0)
    style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(14, 9))
    style.map("TNotebook.Tab", background=[("selected", CARD)], foreground=[("selected", INK)])
    style.configure(
        "Case.Horizontal.TProgressbar",
        background=ACCENT,
        troughcolor=PANEL,
        bordercolor=PAGE,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
        thickness=5,
    )
    scrollbar_style(master, PAGE)


def note_style(master: Misc, key: str, color: str) -> str:
    style = ttk.Style(master)
    name = f"{key}.Note.TRadiobutton"
    style.layout(name, style.layout("TButton"))
    style.configure(
        name,
        background=blend(PAGE, color, 0.12),
        foreground=blend(color, INK, 0.2),
        bordercolor=blend(PAGE, color, 0.25),
        borderwidth=1,
        relief="flat",
        padding=(3, 9),
        anchor="center",
        font=("Segoe UI", -11, "bold"),
    )
    style.map(
        name,
        background=[("disabled", PANEL), ("selected", color), ("active", blend(PAGE, color, 0.22))],
        foreground=[("disabled", "#a1a69d"), ("selected", INK if key == "Amber" else CARD)],
        bordercolor=[("selected", color), ("focus", color)],
    )
    return name
