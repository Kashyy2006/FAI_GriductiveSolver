# Stage 4 Benchmark Combined Summary

- Repeats per puzzle & phase: `5`
- Normal/errors phase timeout: `10.0` s; timeout profile: `1e-12` s
- All raw rows (including `ERROR` and `TIMEOUT`) are retained in each profile's `benchmark.csv`.
- No hidden assignments or unrevealed clues are exported.

## 1. Progressive Solve Phase (Median across repeats)

| Puzzle | Size | Category | Outcome | Primary | Aux (i/m/f) | Clauses (i/m/f) | Calls/Trace | Decisions | Propagations | Backtracks | Steps | Median ms | Min–Max ms |
| --- | :---: | --- | --- | ---: | :---: | :---: | :---: | ---: | ---: | ---: | ---: | ---: | :---: |
| demo_3x3_forced_unknown | 3x3 | Shared repo puzzle | SOLVED | 9 | 0/0/0 | 2/18/18 | 105/105 | 0 | 393 | 0 | 8 | 39.593 | 24.852–39.693 |
| demo_3x3_stuck | 3x3 | Shared repo puzzle | STUCK | 9 | 0/0/0 | 2/5/5 | 35/35 | 0 | 64 | 0 | 1 | 13.602 | 12.784–13.619 |
| example_3x3_chain | 3x3 | Shared repo puzzle | SOLVED | 9 | 0/0/0 | 2/18/18 | 105/105 | 0 | 393 | 0 | 8 | 38.140 | 31.131–41.355 |
| fixture_ambiguous | 3x3 | Fixture | STUCK | 9 | 0/0/0 | 3/3/3 | 17/17 | 0 | 17 | 0 | 0 | 8.675 | 7.166–11.310 |
| stage4_3x3_branching_counts | 3x3 | Stage 4 (extensions/branching) | SOLVED | 9 | 0/0/0 | 109/135/135 | 67/67 | 14 | 450 | 1 | 6 | 175.794 | 145.632–261.045 |
| stage4_3x3_extensions_parity | 3x3 | Stage 4 (extensions/branching) | SOLVED | 9 | 0/0/0 | 5/32/32 | 85/85 | 0 | 406 | 0 | 7 | 66.478 | 53.653–97.764 |
| synthetic_3x3_fact_chain | 3x3 | Synthetic baseline | SOLVED | 9 | 0/0/0 | 2/18/18 | 105/105 | 0 | 393 | 0 | 8 | 40.540 | 35.763–40.840 |
| synthetic_3x3_row_counts | 3x3 | Synthetic baseline | SOLVED | 9 | 0/0/0 | 4/36/36 | 105/105 | 0 | 469 | 0 | 8 | 61.828 | 55.946–69.223 |
| synthetic_3x3_stuck_unique | 3x3 | Synthetic baseline | STUCK | 9 | 0/0/0 | 2/2/2 | 17/17 | 0 | 17 | 0 | 0 | 10.301 | 10.236–10.355 |
| example_4x4_chain | 4x4 | Shared repo puzzle | SOLVED | 16 | 0/0/0 | 2/32/32 | 301/301 | 0 | 1856 | 0 | 15 | 149.223 | 112.238–150.811 |
| stage4_4x4_branching_counts | 4x4 | Stage 4 (extensions/branching) | SOLVED | 16 | 0/0/0 | 181/354/354 | 205/205 | 286 | 2479 | 130 | 12 | 1843.715 | 1537.727–1969.449 |
| stage4_4x4_extensions_parity | 4x4 | Stage 4 (extensions/branching) | SOLVED | 16 | 0/0/0 | 14/87/87 | 235/235 | 23 | 2018 | 0 | 13 | 320.783 | 260.857–351.693 |
| stage4_4x4_stuck_unique_parity | 4x4 | Stage 4 (extensions/branching) | STUCK | 16 | 0/0/0 | 9/9/9 | 31/31 | 56 | 62 | 0 | 0 | 30.126 | 22.984–32.768 |
| synthetic_4x4_fact_chain | 4x4 | Synthetic baseline | SOLVED | 16 | 0/0/0 | 2/32/32 | 301/301 | 0 | 1856 | 0 | 15 | 133.864 | 104.594–147.711 |
| synthetic_4x4_row_counts | 4x4 | Synthetic baseline | SOLVED | 16 | 0/0/0 | 5/80/80 | 301/301 | 0 | 2265 | 0 | 15 | 282.076 | 217.305–295.320 |
| synthetic_4x4_stuck_unique | 4x4 | Synthetic baseline | STUCK | 16 | 0/0/0 | 2/2/2 | 31/31 | 0 | 31 | 0 | 0 | 17.911 | 17.856–18.105 |

## 2. Full-Clue Uniqueness Phase (Median across repeats)

| Puzzle | Size | Outcome | Primary | Aux (i/m/f) | Clauses (i/m/f) | Calls/Trace | Decisions | Propagations | Backtracks | Median ms | Min–Max ms |
| --- | :---: | --- | ---: | :---: | :---: | :---: | ---: | ---: | ---: | ---: | :---: |
| demo_3x3_forced_unknown | 3x3 | UNIQUE | 9 | 0/0/0 | 9/10/10 | 2/2 | 0 | 18 | 0 | 1.250 | 0.714–1.254 |
| demo_3x3_stuck | 3x3 | MULTIPLE | 9 | 0/0/0 | 17/18/18 | 2/2 | 1 | 2 | 0 | 1.296 | 0.758–1.299 |
| example_3x3_chain | 3x3 | UNIQUE | 9 | 0/0/0 | 9/10/10 | 2/2 | 0 | 18 | 0 | 1.302 | 0.735–1.312 |
| fixture_ambiguous | 3x3 | MULTIPLE | 9 | 0/0/0 | 18/19/19 | 2/2 | 1 | 0 | 0 | 0.754 | 0.748–1.355 |
| stage4_3x3_branching_counts | 3x3 | UNIQUE | 9 | 0/0/0 | 126/127/127 | 2/2 | 4 | 23 | 4 | 11.561 | 5.544–12.586 |
| stage4_3x3_extensions_parity | 3x3 | UNIQUE | 9 | 0/0/0 | 23/24/24 | 2/2 | 0 | 18 | 0 | 2.775 | 2.722–2.831 |
| synthetic_3x3_fact_chain | 3x3 | UNIQUE | 9 | 0/0/0 | 9/10/10 | 2/2 | 0 | 18 | 0 | 1.264 | 0.724–1.418 |
| synthetic_3x3_row_counts | 3x3 | UNIQUE | 9 | 0/0/0 | 27/28/28 | 2/2 | 0 | 18 | 0 | 2.820 | 2.815–2.900 |
| synthetic_3x3_stuck_unique | 3x3 | UNIQUE | 9 | 0/0/0 | 9/10/10 | 2/2 | 0 | 18 | 0 | 1.256 | 1.251–1.286 |
| example_4x4_chain | 4x4 | UNIQUE | 16 | 0/0/0 | 16/17/17 | 2/2 | 0 | 32 | 0 | 2.423 | 2.404–2.621 |
| stage4_4x4_branching_counts | 4x4 | UNIQUE | 16 | 0/0/0 | 338/339/339 | 2/2 | 9 | 63 | 12 | 58.670 | 30.771–63.750 |
| stage4_4x4_extensions_parity | 4x4 | UNIQUE | 16 | 0/0/0 | 71/72/72 | 2/2 | 0 | 32 | 0 | 4.878 | 4.321–8.389 |
| stage4_4x4_stuck_unique_parity | 4x4 | UNIQUE | 16 | 0/0/0 | 45/46/46 | 2/2 | 0 | 32 | 0 | 5.498 | 2.883–5.751 |
| synthetic_4x4_fact_chain | 4x4 | UNIQUE | 16 | 0/0/0 | 16/17/17 | 2/2 | 0 | 32 | 0 | 1.768 | 1.282–2.408 |
| synthetic_4x4_row_counts | 4x4 | UNIQUE | 16 | 0/0/0 | 64/65/65 | 2/2 | 0 | 32 | 0 | 4.368 | 3.541–7.275 |
| synthetic_4x4_stuck_unique | 4x4 | UNIQUE | 16 | 0/0/0 | 16/17/17 | 2/2 | 0 | 32 | 0 | 2.383 | 2.377–2.385 |

## 3. Profile Summary (Normal, Errors, Timeouts)

| Profile | Rows | Timeout (s) | Query Matches | Actual SAT Calls | Outcomes |
| --- | ---: | ---: | ---: | ---: | --- |
| normal | 160 | 10.0 | 160 | 10390 | solve:SOLVED=55, solve:STUCK=25, uniqueness:MULTIPLE=10, uniqueness:UNIQUE=70 |
| errors | 20 | 10.0 | 0 | 0 | solve:ERROR=10, uniqueness:ERROR=10 |
| timeouts | 160 | 1e-12 | 0 | 0 | solve:TIMEOUT=80, uniqueness:TIMEOUT=80 |
