"""Create deterministic Stage 4 benchmark puzzles covering extensions and DPLL branching."""

import argparse
import json
from pathlib import Path
from typing import Any

from game.puzzle_loader import puzzle_from_dict

_NAMES_3X3 = (
    "Alice",
    "Ben",
    "Claire",
    "David",
    "Emma",
    "Felix",
    "Grace",
    "Henry",
    "Iris",
)
_NAMES_4X4 = (
    "Alice",
    "Ben",
    "Claire",
    "David",
    "Emma",
    "Felix",
    "Grace",
    "Henry",
    "Iris",
    "Jack",
    "Kate",
    "Liam",
    "Maya",
    "Noah",
    "Olga",
    "Paul",
)
_PROFESSIONS = (
    "Analyst",
    "Archivist",
    "Chemist",
    "Courier",
    "Detective",
    "Doctor",
    "Engineer",
    "Journalist",
    "Lawyer",
    "Librarian",
    "Mechanic",
    "Nurse",
    "Pilot",
    "Professor",
    "Scientist",
    "Surveyor",
)


def _build_puzzle(
    puzzle_id: str,
    size: int,
    statuses: dict[str, str],
    clues: dict[str, dict[str, Any]],
    initially_revealed: list[str],
) -> dict[str, Any]:
    names = _NAMES_3X3 if size == 3 else _NAMES_4X4
    characters = []
    for index in range(size * size):
        row, col = divmod(index, size)
        cell_id = f"{chr(65 + col)}{row + 1}"
        clue = {"id": f"clue_{cell_id}", **clues[cell_id]}
        characters.append(
            {
                "id": cell_id,
                "name": names[index],
                "profession": _PROFESSIONS[index],
                "row": row,
                "col": col,
                "hidden_status": statuses[cell_id],
                "clue": clue,
            }
        )
    data = {
        "schema_version": "1.0",
        "puzzle_id": puzzle_id,
        "size": size,
        "characters": characters,
        "initially_revealed": initially_revealed,
    }
    puzzle_from_dict(data)
    return data


def _stage4_definitions() -> tuple[dict[str, Any], ...]:
    # 1. 3x3 combining Parity (EVEN/ODD), COMMON_NEIGHBORS and core clues (SOLVED / UNIQUE).
    p1 = _build_puzzle(
        "stage4_3x3_extensions_parity",
        3,
        {
            "A1": "CRIMINAL",
            "B1": "INNOCENT",
            "C1": "CRIMINAL",
            "A2": "INNOCENT",
            "B2": "CRIMINAL",
            "C2": "INNOCENT",
            "A3": "CRIMINAL",
            "B3": "CRIMINAL",
            "C3": "INNOCENT",
        },
        {
            "A1": {
                "type": "EXACTLY",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "A1", "second": "C3"},
                "k": 1,
            },
            "B1": {
                "type": "AT_MOST",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "B1", "second": "B3"},
                "k": 1,
            },
            "C1": {
                "type": "AT_LEAST",
                "region": {"kind": "COLUMN", "index": 0},
                "k": 2,
            },
            "A2": {"type": "SAME", "first": "A1", "second": "C1"},
            "B2": {
                "type": "ODD",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "A1", "second": "C1"},
            },
            "C2": {"type": "DIFFERENT", "first": "A3", "second": "C3"},
            "A3": {"type": "ODD", "region": {"kind": "COLUMN", "index": 2}},
            "B3": {"type": "EVEN", "region": {"kind": "ROW", "index": 0}},
            "C3": {
                "type": "EVEN",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "A3", "second": "C3"},
            },
        },
        ["A1", "C3"],
    )

    # 2. 3x3 overlapping counting + parity constraints that force DPLL branching (SOLVED / UNIQUE).
    p2 = _build_puzzle(
        "stage4_3x3_branching_counts",
        3,
        {
            "A1": "CRIMINAL",
            "B1": "CRIMINAL",
            "C1": "INNOCENT",
            "A2": "CRIMINAL",
            "B2": "INNOCENT",
            "C2": "CRIMINAL",
            "A3": "INNOCENT",
            "B3": "CRIMINAL",
            "C3": "INNOCENT",
        },
        {
            # Overlapping counting + parity constraints force DPLL branching and backtracking.
            "A1": {"type": "EXACTLY", "region": {"kind": "NEIGHBORS", "cell": "B2"}, "k": 5},
            "B1": {
                "type": "EXACTLY",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "A2", "second": "C2"},
                "k": 2,
            },
            "C1": {"type": "EVEN", "region": {"kind": "EXPLICIT", "cells": ["B1", "B3"]}},
            "A2": {"type": "EVEN", "region": {"kind": "COLUMN", "index": 0}},
            "B2": {"type": "ODD", "region": {"kind": "ROW", "index": 2}},
            "C2": {"type": "EXACTLY", "region": {"kind": "COLUMN", "index": 1}, "k": 2},
            "A3": {"type": "EXACTLY", "region": {"kind": "ROW", "index": 1}, "k": 2},
            "B3": {
                "type": "ODD",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "A1", "second": "C1"},
            },
            "C3": {"type": "EXACTLY", "region": {"kind": "ROW", "index": 0}, "k": 2},
        },
        ["A1", "C3", "A2"],
    )

    # 3. 4x4 combining Parity (EVEN/ODD), COMMON_NEIGHBORS and core clues (SOLVED / UNIQUE).
    # Grid:
    # A1=C B1=I C1=C D1=I  (row0=2 EVEN)
    # A2=I B2=C C2=I D2=C  (row1=2 EVEN)
    # A3=C B3=C C3=I D3=I  (row2=2 EVEN)
    # A4=I B4=I C4=C D4=C  (row3=2 EVEN)
    # Cols: col0=2, col1=2, col2=2, col3=2 (all EVEN)
    p3 = _build_puzzle(
        "stage4_4x4_extensions_parity",
        4,
        {
            "A1": "CRIMINAL",
            "B1": "INNOCENT",
            "C1": "CRIMINAL",
            "D1": "INNOCENT",
            "A2": "INNOCENT",
            "B2": "CRIMINAL",
            "C2": "INNOCENT",
            "D2": "CRIMINAL",
            "A3": "CRIMINAL",
            "B3": "CRIMINAL",
            "C3": "INNOCENT",
            "D3": "INNOCENT",
            "A4": "INNOCENT",
            "B4": "INNOCENT",
            "C4": "CRIMINAL",
            "D4": "CRIMINAL",
        },
        {
            # CN(A1,C3) = [B2] -> B2=C
            "A1": {
                "type": "EXACTLY",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "A1", "second": "C3"},
                "k": 1,
            },
            # DIFFERENT(B1, C1) -> with B1=I forces C1=C
            "B1": {"type": "DIFFERENT", "first": "B1", "second": "C1"},
            # Row 0 has exactly 2 -> with A1=C,B1=I,C1=C -> D1=I
            "C1": {"type": "EXACTLY", "region": {"kind": "ROW", "index": 0}, "k": 2},
            # CN(B1,D1) = [C1,C2] -> C1=C, C2=I (ODD)
            "D1": {
                "type": "ODD",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "B1", "second": "D1"},
            },
            # CN(D1,D3) = [C2,D2] -> C2=I, D2=C (ODD)
            "A2": {
                "type": "ODD",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "D1", "second": "D3"},
            },
            # CN(A1,C1) = [B1,B2] -> B1=I, B2=C (ODD)
            "B2": {
                "type": "ODD",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "A1", "second": "C1"},
            },
            # Row 1 EVEN -> [A2=I,B2=C,C2=I,D2=C]
            "C2": {"type": "EVEN", "region": {"kind": "ROW", "index": 1}},
            # CN(B2,D2) = [C1,C2,C3] -> C1=C,C2=I,C3=I (EXACTLY 1)
            "D2": {
                "type": "EXACTLY",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "B2", "second": "D2"},
                "k": 1,
            },
            # Col 0 has exactly 2 -> A1=C,A2=I,A3=C,A4=I
            "A3": {"type": "EXACTLY", "region": {"kind": "COLUMN", "index": 0}, "k": 2},
            # CN(A3,C3) = [B2,B3,B4] -> B2=C,B3=C,B4=I (EXACTLY 2)
            "B3": {
                "type": "EXACTLY",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "A3", "second": "C3"},
                "k": 2,
            },
            # Row 2 EVEN -> [A3=C,B3=C,C3=I,D3=I]
            "C3": {"type": "EVEN", "region": {"kind": "ROW", "index": 2}},
            # Col 3 EVEN -> [D1=I,D2=C,D3=I,D4=C]
            "D3": {"type": "EVEN", "region": {"kind": "COLUMN", "index": 3}},
            # Explicit [A3,B3] AT_LEAST 2
            "A4": {
                "type": "AT_LEAST",
                "region": {"kind": "EXPLICIT", "cells": ["A3", "B3"]},
                "k": 2,
            },
            # Explicit [A4,B4] AT_MOST 0
            "B4": {
                "type": "AT_MOST",
                "region": {"kind": "EXPLICIT", "cells": ["A4", "B4"]},
                "k": 0,
            },
            # SAME(A1, B2) -> anchors A1=C in full-clue uniqueness
            "C4": {"type": "SAME", "first": "A1", "second": "B2"},
            # Row 3 has exactly 2 -> with A4=I,B4=I forces C4=C,D4=C
            "D4": {"type": "EXACTLY", "region": {"kind": "ROW", "index": 3}, "k": 2},
        },
        ["A1", "D4", "B4"],
    )

    # 4. 4x4 dense overlapping counting + parity constraints triggering deep DPLL branching.
    # Grid:
    # A1=C B1=C C1=I D1=I  (row0=2)
    # A2=C B2=I C2=C D2=I  (row1=2)
    # A3=I B3=C C3=C D3=I  (row2=2)
    # A4=I B4=I C4=I D4=C  (row3=1)
    # Cols: col0=2, col1=2, col2=2, col3=1
    p4 = _build_puzzle(
        "stage4_4x4_branching_counts",
        4,
        {
            "A1": "CRIMINAL",
            "B1": "CRIMINAL",
            "C1": "INNOCENT",
            "D1": "INNOCENT",
            "A2": "CRIMINAL",
            "B2": "INNOCENT",
            "C2": "CRIMINAL",
            "D2": "INNOCENT",
            "A3": "INNOCENT",
            "B3": "CRIMINAL",
            "C3": "CRIMINAL",
            "D3": "INNOCENT",
            "A4": "INNOCENT",
            "B4": "INNOCENT",
            "C4": "INNOCENT",
            "D4": "CRIMINAL",
        },
        {
            # Neighbors of B2: [A1=C,B1=C,C1=I,A2=C,C2=C,A3=I,B3=C,C3=C] -> sum=6
            "A1": {"type": "EXACTLY", "region": {"kind": "NEIGHBORS", "cell": "B2"}, "k": 6},
            # Neighbors of C3: [B2=I,C2=C,D2=I,B3=C,D3=I,B4=I,C4=I,D4=C] -> sum=3
            "B1": {"type": "EXACTLY", "region": {"kind": "NEIGHBORS", "cell": "C3"}, "k": 3},
            "C1": {"type": "EXACTLY", "region": {"kind": "ROW", "index": 0}, "k": 2},
            "D1": {"type": "EXACTLY", "region": {"kind": "COLUMN", "index": 3}, "k": 1},
            "A2": {"type": "EXACTLY", "region": {"kind": "ROW", "index": 1}, "k": 2},
            # CN(A2,C2) = [B1=C,B2=I,B3=C] -> sum=2 (EVEN)
            "B2": {
                "type": "EXACTLY",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "A2", "second": "C2"},
                "k": 2,
            },
            "C2": {"type": "EVEN", "region": {"kind": "COLUMN", "index": 0}},
            # CN(C1,C3) = [B2=I,C2=C,D2=I] -> sum=1 (ODD)
            "D2": {
                "type": "ODD",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "C1", "second": "C3"},
            },
            "A3": {"type": "EXACTLY", "region": {"kind": "ROW", "index": 2}, "k": 2},
            "B3": {"type": "EVEN", "region": {"kind": "COLUMN", "index": 1}},
            "C3": {"type": "EVEN", "region": {"kind": "COLUMN", "index": 2}},
            # CN(B3,D3) = [C2=C,C3=C,C4=I] -> sum=2 (EVEN)
            "D3": {
                "type": "EVEN",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "B3", "second": "D3"},
            },
            "A4": {"type": "EXACTLY", "region": {"kind": "ROW", "index": 3}, "k": 1},
            # CN(A1,A3) = [A2=C,B2=I] -> sum=1 (ODD)
            "B4": {
                "type": "ODD",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "A1", "second": "A3"},
            },
            "C4": {"type": "SAME", "first": "B3", "second": "C3"},
            # Neighbors of B3: [A2=C,B2=I,C2=C,A3=I,C3=C,A4=I,B4=I,C4=I] -> sum=3
            "D4": {"type": "EXACTLY", "region": {"kind": "NEIGHBORS", "cell": "B3"}, "k": 3},
        },
        ["A1", "D4", "C1", "A4"],
    )

    # 5. 4x4 full-clue UNIQUE with parity/common-neighbors, but progressive STUCK!
    # Same grid as p3, but initially_revealed=["A1"] only gives EVEN(ROW 0) which cannot force
    # any single cell on its own, while all 16 clues together uniquely determine the board.
    p5 = _build_puzzle(
        "stage4_4x4_stuck_unique_parity",
        4,
        {
            "A1": "CRIMINAL",
            "B1": "INNOCENT",
            "C1": "CRIMINAL",
            "D1": "INNOCENT",
            "A2": "INNOCENT",
            "B2": "CRIMINAL",
            "C2": "INNOCENT",
            "D2": "CRIMINAL",
            "A3": "CRIMINAL",
            "B3": "CRIMINAL",
            "C3": "INNOCENT",
            "D3": "INNOCENT",
            "A4": "INNOCENT",
            "B4": "INNOCENT",
            "C4": "CRIMINAL",
            "D4": "CRIMINAL",
        },
        {
            "A1": {"type": "EVEN", "region": {"kind": "ROW", "index": 0}},
            "B1": {"type": "FACT", "person": "A1", "status": "CRIMINAL"},
            "C1": {"type": "FACT", "person": "B1", "status": "INNOCENT"},
            "D1": {
                "type": "ODD",
                "region": {"kind": "COMMON_NEIGHBORS", "first": "A1", "second": "C1"},
            },
            "A2": {"type": "FACT", "person": "C1", "status": "CRIMINAL"},
            "B2": {"type": "FACT", "person": "D1", "status": "INNOCENT"},
            "C2": {"type": "FACT", "person": "A2", "status": "INNOCENT"},
            "D2": {"type": "FACT", "person": "C2", "status": "INNOCENT"},
            "A3": {"type": "EXACTLY", "region": {"kind": "ROW", "index": 1}, "k": 2},
            "B3": {"type": "FACT", "person": "A3", "status": "CRIMINAL"},
            "C3": {"type": "FACT", "person": "B3", "status": "CRIMINAL"},
            "D3": {"type": "FACT", "person": "C3", "status": "INNOCENT"},
            "A4": {"type": "EVEN", "region": {"kind": "ROW", "index": 2}},
            "B4": {"type": "FACT", "person": "A4", "status": "INNOCENT"},
            "C4": {"type": "FACT", "person": "B4", "status": "INNOCENT"},
            "D4": {"type": "EXACTLY", "region": {"kind": "ROW", "index": 3}, "k": 2},
        },
        ["A1"],
    )

    return (p1, p2, p3, p4, p5)


def create_stage4_suite(output: Path) -> tuple[Path, ...]:
    """Write five deterministic Stage 4 puzzles covering extensions and branching."""
    output.mkdir(parents=True, exist_ok=True)
    readme = output / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Stage 4 extension and branching benchmark puzzles\n\n"
            "Owner: TV3 (Mạnh). Generated deterministically by experiments.make_stage4_suite.\n\n"
            "Five schema-v1.0-validated 3x3 and 4x4 puzzles exercising Parity (EVEN/ODD),\n"
            "COMMON_NEIGHBORS, overlapping counting constraints (triggering real DPLL\n"
            "branching and backtracking), and a 4x4 full-clue UNIQUE / progressive STUCK case.\n\n"
            "## Nhật ký AI\n",
            encoding="utf-8",
        )
    paths = []
    for data in _stage4_definitions():
        path = output / f"{data['puzzle_id']}.json"
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    return tuple(paths)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "puzzles" / "stage4",
    )
    args = parser.parse_args()
    paths = create_stage4_suite(args.output)
    print(f"Created {len(paths)} schema-validated Stage 4 puzzles in {args.output}")


if __name__ == "__main__":
    main()
