"""Private authoring patterns: varied public openings with a single progressive path."""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
from itertools import combinations
from random import Random
from typing import Any

from game.models import PublicCharacter, PublicState, Puzzle, Region, RegionType, StateToken
from game.puzzle_loader import puzzle_from_dict
from logic.regions import resolve_region

GENERATOR_VERSION = 2
OPENINGS = ("combine", "count", "parity", "same", "different")
FAMILIES = ("pairs", "overlap", "fan")
GROUP_SIZES = {"pairs": 3, "overlap": 4, "fan": 4}
PRE_COUNTS = {"pairs": 2, "overlap": 2, "fan": 3}
NAMES = (
    "Alice",
    "Ben",
    "Chloe",
    "David",
    "Emma",
    "Felix",
    "Grace",
    "Henry",
    "Iris",
    "Jack",
    "Kate",
    "Lily",
    "Mia",
    "Noah",
    "Oliver",
    "Paul",
    "Quinn",
    "Rose",
    "Sam",
    "Tara",
    "Uma",
    "Victor",
    "Will",
    "Yara",
    "Zoe",
)
PROFESSIONS = ("Archivist", "Baker", "Doctor", "Engineer", "Guide", "Librarian", "Pilot")


@lru_cache(maxsize=3)
def _geometry(size: int) -> tuple[tuple[Region, tuple[str, ...]], ...]:
    cells = tuple(f"{chr(65 + col)}{row + 1}" for row in range(size) for col in range(size))
    state = PublicState(
        "generation-geometry",
        size,
        StateToken("geometry-only", 0),
        tuple(
            PublicCharacter(cell, NAMES[index], "", index // size, index % size)
            for index, cell in enumerate(cells)
        ),
    )
    regions = [Region(RegionType.ROW, index=index) for index in range(size)]
    regions += [Region(RegionType.COLUMN, index=index) for index in range(size)]
    regions += [Region(RegionType.NEIGHBORS, cell=cell) for cell in cells]
    regions += [
        Region(RegionType.COMMON_NEIGHBORS, first=a, second=b) for a, b in combinations(cells, 2)
    ]
    return tuple((region, resolve_region(region, state)) for region in regions)


def _region_data(region: Region) -> dict[str, Any]:
    data = {
        key: value
        for key, value in asdict(region).items()
        if value is not None and not (key == "cells" and region.kind != RegionType.EXPLICIT)
    }
    if "cells" in data:
        data["cells"] = list(data["cells"])
    return data


def _rules(
    family: str,
    cells: list[str],
    positive: bool,
    rng: Random,
) -> tuple[list[tuple[str, list[str], int]], list[bool]]:
    """Three different count arguments; complementing them also changes the first verdict.

    pairs: a+b>=1, a+c>=1, b+c<=1.
    overlap: a+b+c>=2, a+b+d>=2, b+c+d<=2.
    fan: three a+other>=1 bounds, and b+c+d<=2.
    The chosen later bridge values leave every still-concealed card undecided.
    """
    a, b, c = cells[:3]
    if family == "pairs":
        rules = [("AT_LEAST", [a, b], 1), ("AT_LEAST", [a, c], 1), ("AT_MOST", [b, c], 1)]
        values = [True, False, rng.choice((False, True))]
    elif family == "overlap":
        d = cells[3]
        rules = [("AT_LEAST", [a, b, c], 2), ("AT_LEAST", [a, b, d], 2), ("AT_MOST", [b, c, d], 2)]
        values = [True, True, False, rng.choice((False, True))]
    else:
        d = cells[3]
        rules = [
            ("AT_LEAST", [a, b], 1),
            ("AT_LEAST", [a, c], 1),
            ("AT_LEAST", [a, d], 1),
            ("AT_MOST", [b, c, d], 2),
        ]
        values = [True, False, rng.choice((False, True)), rng.choice((False, True))]
    if not positive:
        rules = [
            ("AT_MOST" if kind == "AT_LEAST" else "AT_LEAST", scope, len(scope) - k)
            for kind, scope, k in rules
        ]
        values = [not value for value in values]
    return rules, values


def build_candidate(size: int, seed: int) -> Puzzle:
    """Author a candidate; the caller must independently certify UNIQUE and progression."""
    rng = Random(seed)
    cells = [f"{chr(65 + col)}{row + 1}" for row in range(size) for col in range(size)]
    opening = OPENINGS[seed % len(OPENINGS)]
    budget = len(cells) - 1 - (opening != "combine")
    families = []
    while budget >= 5:
        choices = [
            family for family in FAMILIES if GROUP_SIZES[family] + PRE_COUNTS[family] <= budget
        ]
        family = rng.choice(choices)
        families.append(family)
        budget -= GROUP_SIZES[family] + PRE_COUNTS[family]
    initial_count = 1 + sum(PRE_COUNTS[family] for family in families)
    geometry = _geometry(size)
    first_scope_size = (
        3
        if opening == "combine" and families[0] == "overlap"
        else (2 if opening == "combine" else 1)
    )
    kinds = (RegionType.ROW, RegionType.COLUMN, RegionType.NEIGHBORS, RegionType.COMMON_NEIGHBORS)
    preferred_kind = kinds[(seed // len(OPENINGS)) % len(kinds)]
    locations = [
        (region, members)
        for region, members in geometry
        if region.kind == preferred_kind
        and first_scope_size <= len(members) <= initial_count + first_scope_size
    ]
    first_region, members = rng.choice(locations)
    prefix = rng.sample(list(members), first_scope_size)
    required_known = [cell for cell in members if cell not in prefix]
    if opening == "combine":
        first_group = prefix + rng.sample(
            [cell for cell in cells if cell not in prefix and cell not in required_known],
            GROUP_SIZES[families[0]] - len(prefix),
        )
        excluded = set(first_group)
        opening_target = None
    else:
        first_group = []
        opening_target = prefix[0]
        excluded = {opening_target}
    initial = required_known + rng.sample(
        [cell for cell in cells if cell not in excluded and cell not in required_known],
        initial_count - len(required_known),
    )
    rng.shuffle(initial)
    remaining = rng.sample(
        [cell for cell in cells if cell not in initial and cell not in excluded],
        len(cells) - len(initial) - len(excluded),
    )
    groups = []
    for index, family in enumerate(families):
        if index == 0 and first_group:
            groups.append(first_group)
        else:
            groups.append(remaining[: GROUP_SIZES[family]])
            del remaining[: GROUP_SIZES[family]]
    tail = remaining
    labels = {cell: rng.choice((False, True)) for cell in initial}
    labels[initial[0]], labels[initial[1]] = False, True
    constraints = []
    for family, group in zip(families, groups):
        rules, values = _rules(family, group, rng.choice((False, True)), rng)
        constraints.append(rules)
        labels.update(zip(group, values))
    for cell in tail:
        labels[cell] = rng.choice((False, True))
    if opening_target:
        labels[opening_target] = rng.choice((False, True))
    clues: dict[str, dict[str, Any]] = {}
    known = set(initial)

    def region_for(scope: list[str], preferred: Region | None = None) -> Region:
        if preferred is not None:
            return preferred
        choices: dict[RegionType, list[Region]] = {}
        for region, region_cells in geometry:
            if set(region_cells) - known == set(scope):
                choices.setdefault(region.kind, []).append(region)
        explicit = list(scope)
        if len(scope) == 1:
            explicit += rng.sample(sorted(known), min(2, len(known)))
        choices[RegionType.EXPLICIT] = [Region(RegionType.EXPLICIT, cells=tuple(explicit))]
        return rng.choice(choices[rng.choice(list(choices))])

    resolved = dict(geometry)

    def count(
        kind: str, scope: list[str], k: int, preferred: Region | None = None
    ) -> dict[str, Any]:
        region = region_for(scope, preferred)
        region_cells = region.cells if region.kind == RegionType.EXPLICIT else resolved[region]
        total_known = sum(labels[cell] for cell in region_cells if cell in known)
        return {"type": kind, "region": _region_data(region), "k": k + total_known}

    def single(target: str, mode: str | None = None) -> dict[str, Any]:
        mode = mode or rng.choice(("count", "parity", "relation"))
        if mode in ("same", "different", "relation"):
            anchor = rng.choice(sorted(known))
            if mode in ("same", "different"):
                labels[target] = labels[anchor] if mode == "same" else not labels[anchor]
            return {
                "type": "SAME" if labels[target] == labels[anchor] else "DIFFERENT",
                "first": anchor,
                "second": target,
            }
        preferred = first_region if target == opening_target else None
        region = region_for([target], preferred)
        region_cells = region.cells if region.kind == RegionType.EXPLICIT else resolved[region]
        total = sum(labels[cell] for cell in region_cells)
        if mode == "parity":
            if target == opening_target:
                odd = bool((seed // len(OPENINGS)) % 2)
                if bool(total % 2) != odd:
                    labels[target] = not labels[target]
                    total += 1 if labels[target] else -1
            return {"type": "ODD" if total % 2 else "EVEN", "region": _region_data(region)}
        return {"type": "EXACTLY", "region": _region_data(region), "k": total}

    cursor = 0
    for index, rules in enumerate(constraints):
        for rule_index, (kind, scope, k) in enumerate(rules[:-1]):
            preferred = first_region if opening == "combine" and index == rule_index == 0 else None
            clues[initial[cursor]] = count(kind, scope, k, preferred)
            cursor += 1
    if opening_target:
        clues[initial[-1]] = single(opening_target, opening)
        known.add(opening_target)
        clues[opening_target] = count(*constraints[0][-1])
    else:
        clues[initial[-1]] = count(*constraints[0][-1])
    fixed_value = labels[groups[0][1]]
    for index, group in enumerate(groups):
        for step, (owner, target) in enumerate(zip(group, group[1:])):
            known.add(owner)
            if index == step == 0:
                anchors = [cell for cell in initial if labels[cell] == fixed_value]
                scope = anchors + [target]
                clues[owner] = {
                    "type": "EXACTLY",
                    "region": {
                        "kind": "EXPLICIT",
                        "cells": scope,
                    },
                    "k": len(scope) if fixed_value else 0,
                }
            else:
                clues[owner] = single(target)
        known.add(group[-1])
        if index + 1 < len(groups):
            clues[group[-1]] = count(*constraints[index + 1][-1])
    owner = groups[-1][-1]
    for target in tail:
        clues[owner] = single(target)
        known.add(target)
        owner = target
    anchors = [cell for cell in initial if labels[cell] != fixed_value]
    clues[owner] = {
        "type": "EXACTLY",
        "region": {"kind": "EXPLICIT", "cells": anchors},
        "k": 0 if fixed_value else len(anchors),
    }
    return puzzle_from_dict(
        {
            "schema_version": "1.0",
            "puzzle_id": f"generated_v{GENERATOR_VERSION}_{size}x{size}_seed_{seed}",
            "size": size,
            "initially_revealed": initial,
            "characters": [
                {
                    "id": cell,
                    "name": NAMES[index],
                    "profession": rng.choice(PROFESSIONS),
                    "row": index // size,
                    "col": index % size,
                    "hidden_status": "CRIMINAL" if labels[cell] else "INNOCENT",
                    "clue": {"id": f"clue_{cell}", **clues[cell]},
                }
                for index, cell in enumerate(cells)
            ],
        }
    )
