"""Create a reproducible synthetic sanity suite, not a representative performance set."""

import argparse
import json
from pathlib import Path
from typing import Any

from game.puzzle_loader import puzzle_from_dict


def create_suite(output: Path) -> tuple[Path, ...]:
    """Write six valid core-clue puzzles covering chains, counts and stuck states."""
    output.mkdir(parents=True, exist_ok=True)
    readme = output / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Synthetic benchmark puzzles\n\n"
            "Owner: TV3. Generated deterministically by experiments.make_suite.\n\n"
            "For each size 3 and 4: fact_chain, row_counts, and stuck_unique.\n"
            "These are correctness baselines; they do not represent difficult game instances.\n"
            "Expected full-clue uniqueness: UNIQUE for every case.\n"
            "Expected progressive result: SOLVED for chains/counts, STUCK for self facts.\n\n"
            "## AI log\n",
            encoding="utf-8",
        )
    paths = []
    for size in (3, 4):
        ids = tuple(f"{chr(65 + c)}{r + 1}" for r in range(size) for c in range(size))
        for kind in ("fact_chain", "row_counts", "stuck_unique"):
            characters = []
            for index, cell_id in enumerate(ids):
                row, col = divmod(index, size)
                clue: dict[str, Any] = {"id": f"clue_{cell_id}"}
                if kind == "row_counts":
                    clue.update(
                        type="EXACTLY", region={"kind": "ROW", "index": (row + 1) % size}, k=0
                    )
                else:
                    clue.update(
                        type="FACT",
                        person=cell_id if kind == "stuck_unique" else ids[(index + 1) % len(ids)],
                        status="INNOCENT",
                    )
                characters.append(
                    {
                        "id": cell_id,
                        "name": f"Person {index:02d}",
                        "profession": "Researcher",
                        "row": row,
                        "col": col,
                        "hidden_status": "INNOCENT",
                        "clue": clue,
                    }
                )
            data = {
                "schema_version": "1.0",
                "puzzle_id": f"synthetic_{size}x{size}_{kind}",
                "size": size,
                "characters": characters,
                "initially_revealed": ["A1"],
            }
            puzzle_from_dict(data)
            path = output / f"{data['puzzle_id']}.json"
            path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            paths.append(path)
    return tuple(paths)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "puzzles")
    args = parser.parse_args()
    paths = create_suite(args.output)
    print(f"Created {len(paths)} schema-validated synthetic puzzles in {args.output}")


if __name__ == "__main__":
    main()
