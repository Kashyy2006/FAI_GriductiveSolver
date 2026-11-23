# Generated player cases

- Owner: TV1 (puzzle generation); TV5 (library integration).
- Runtime schema-v1 JSON cases created by `game.generator`; ignored by Git.
- Choose 3×3, 4×4 or 5×5 and a seed. Each board stays that size for the entire case.
- The generator verifies full-clue UNIQUE independently of hidden labels and checks
  exactly one forced verdict at every progressive step through the real Engine/Agent.
- Version 2 varies five opening styles (combined clues, counts, parity, SAME,
  DIFFERENT), three inequality families and both verdict directions. Counts can use
  rows, columns, neighbors and common neighbors; initial public labels are mixed.
- No FACT clues. Inequality groups require three or four public clues; bridges
  use relations/counts/parity with already public anchors. Same version/size/seed
  reproduces the case. Every case still contains stages combining several clues.
- New filenames start with `generated_v2_`; legacy cases and their progress remain
  available unchanged. Generate a new case to use the new patterns.
- Player progress is stored separately in `outputs/player_progress.json`.

## Nhật ký AI
