"""Canonical domain and result types for all Griductive modules (contract v1)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

Literal: TypeAlias = int
Clause: TypeAlias = list[Literal]
CNF: TypeAlias = list[Clause]
Assignment: TypeAlias = dict[int, bool]


class Status(str, Enum):
    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"


class Classification(str, Enum):
    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"
    UNKNOWN = "UNKNOWN"


class ClueType(str, Enum):
    FACT = "FACT"
    SAME = "SAME"
    DIFFERENT = "DIFFERENT"
    EXACTLY = "EXACTLY"
    AT_LEAST = "AT_LEAST"
    AT_MOST = "AT_MOST"
    EVEN = "EVEN"
    ODD = "ODD"


class RegionType(str, Enum):
    ROW = "ROW"
    COLUMN = "COLUMN"
    NEIGHBORS = "NEIGHBORS"
    EXPLICIT = "EXPLICIT"
    COMMON_NEIGHBORS = "COMMON_NEIGHBORS"


class SATStatus(str, Enum):
    SAT = "SAT"
    UNSAT = "UNSAT"


class KBStatus(str, Enum):
    CONSISTENT = "CONSISTENT"
    INCONSISTENT = "INCONSISTENT"


class VerdictOutcome(str, Enum):
    ACCEPTED = "ACCEPTED"
    NOT_PROVABLE = "NOT_PROVABLE"
    CONTRADICTED = "CONTRADICTED"
    INCONSISTENT = "INCONSISTENT"
    STALE_STATE = "STALE_STATE"
    ALREADY_REVEALED = "ALREADY_REVEALED"


class SolveOutcome(str, Enum):
    SOLVED = "SOLVED"
    STUCK = "STUCK"
    INCONSISTENT = "INCONSISTENT"
    CANCELLED = "CANCELLED"


class UniquenessOutcome(str, Enum):
    NO_SOLUTION = "NO_SOLUTION"
    UNIQUE = "UNIQUE"
    MULTIPLE = "MULTIPLE"


class PuzzleValidationError(ValueError):
    """Invalid puzzle structure, references, or semantics."""


class ContractError(ValueError):
    """Invalid arguments at a public API boundary."""


class SolverTimeout(TimeoutError):
    """A SAT deadline was exceeded; never equivalent to UNSAT."""


class SolutionMismatchError(RuntimeError):
    """A proved verdict conflicts with the engine's hidden solution."""


@dataclass(frozen=True)
class StateToken:
    """session_id changes on load/restart; version increments on reveal."""

    session_id: str
    version: int


@dataclass(frozen=True)
class Region:
    """Only fields belonging to kind may be populated; see puzzle schema."""

    kind: RegionType
    index: int | None = None
    cell: str | None = None
    cells: tuple[str, ...] = ()
    first: str | None = None
    second: str | None = None


@dataclass(frozen=True)
class Clue:
    """Tagged clue: person/status, first/second, or region/k fields."""

    id: str
    type: ClueType
    person: str | None = None
    status: Status | None = None
    first: str | None = None
    second: str | None = None
    region: Region | None = None
    k: int | None = None


@dataclass(frozen=True)
class Character:
    """Private engine/validation data; do not pass to Agent or GUI."""

    id: str
    name: str
    profession: str
    row: int
    col: int
    hidden_status: Status
    clue: Clue


@dataclass(frozen=True)
class Puzzle:
    schema_version: str
    puzzle_id: str
    size: int
    characters: tuple[Character, ...]
    initially_revealed: tuple[str, ...]


@dataclass(frozen=True)
class PublicCharacter:
    id: str
    name: str
    profession: str
    row: int
    col: int
    status: Status | None = None
    clue: Clue | None = None


@dataclass(frozen=True)
class PublicState:
    puzzle_id: str
    size: int
    token: StateToken
    characters: tuple[PublicCharacter, ...]


@dataclass(frozen=True)
class EncodingResult:
    cnf: CNF
    variable_map: dict[str, int]
    primary_variables: tuple[int, ...]
    auxiliary_variables: tuple[int, ...]
    clause_count: int
    active_clue_ids: tuple[str, ...]


@dataclass(frozen=True)
class SolverStats:
    decisions: int
    propagations: int
    backtracks: int
    runtime_seconds: float


@dataclass(frozen=True)
class SATResult:
    status: SATStatus
    assignment: Assignment | None
    stats: SolverStats


@dataclass(frozen=True)
class SATQuery:
    purpose: str
    assumptions: tuple[Literal, ...]
    result: SATStatus
    stats: SolverStats


@dataclass(frozen=True)
class ClassificationResult:
    token: StateToken
    kb_status: KBStatus
    classifications: dict[str, Classification]
    queries: tuple[SATQuery, ...]


@dataclass(frozen=True)
class VerdictProof:
    """Diagnostic result only; Engine must call its verifier itself."""

    token: StateToken
    character_id: str
    requested_status: Status
    outcome: VerdictOutcome
    queries: tuple[SATQuery, ...]


@dataclass(frozen=True)
class VerdictResult:
    outcome: VerdictOutcome
    state: PublicState
    revealed_clue: Clue | None
    proof: VerdictProof | None


@dataclass(frozen=True)
class HintResult:
    token: StateToken
    kb_status: KBStatus
    character_id: str | None
    status: Status | None
    active_clue_ids: tuple[str, ...]
    queries: tuple[SATQuery, ...]


@dataclass(frozen=True)
class DeductionStep:
    step: int
    token_before: StateToken
    token_after: StateToken
    active_clue_ids: tuple[str, ...]
    queries: tuple[SATQuery, ...]
    character_id: str
    verdict: Status
    newly_revealed_clue: Clue


@dataclass(frozen=True)
class AutoSolveResult:
    outcome: SolveOutcome
    final_state: PublicState
    steps: tuple[DeductionStep, ...]
    queries: tuple[SATQuery, ...]


@dataclass(frozen=True)
class UniquenessResult:
    outcome: UniquenessOutcome
    primary_models: tuple[dict[str, Status], ...]
    queries: tuple[SATQuery, ...]
