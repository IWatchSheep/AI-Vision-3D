"""
Shape filling: hold small picture grids against a partial observation.

Worked example
--------------
Picture has "#" at (0, 2). Observation has not looked there -> mark "+"
After reveal sees "#", same cell -> mark "#"
Picture has "." at (2, 2). Reveal sees "." -> mark "-"
Picture has "." at (2, 2). Reveal sees "#" -> mark "X" (unexpected)

Marks cheat sheet
-----------------
  "#"  looked, and it agrees with the picture
  "+"  picture wants an object; we have not looked yet
  "X"  looked, and it disagrees with the picture
  "?"  not looked, and the picture wants empty
  "-"  looked, and both say empty

Unlooked cells are only "?" or "+". They are never "X" or "-".

Memory notepad (ShapeWindow) uses calculator.window.MemoryWindow:
  past / current / accept() / clear_current().

imagine() only reveals cells on a COPY. The real observation must not change.

Name note: ShapeObservation is NOT calculator.interface.Observation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from calculator.window import DEFAULT_PAST_LIMIT, MemoryWindow

# ---- Fixed sizes (never read or write outside these limits) ----
ROWS = 5
COLS = 5
PAST_LIMIT = DEFAULT_PAST_LIMIT
IMAGINE_STEP_LIMIT = 4  # max imaginary reveals on a copy

OBJECT = "#"
EMPTY = "."
ALLOWED_PICTURE_CHARS = (OBJECT, EMPTY)
FILL_MARKS = frozenset({"#", "+", "X", "?", "-"})


# ---- Hardcoded pictures (immutable tuples so nobody can edit them by accident) ----

WHEEL: tuple[str, ...] = (
    ".###.",
    "#...#",
    "#...#",
    "#...#",
    ".###.",
)

PERSON_DOLL: tuple[str, ...] = (
    "..#..",
    "..#..",
    ".###.",
    "..#..",
    ".#.#.",
)

# rank() sorts by score, then by name, so order in this list does not matter.
PICTURES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("person-doll", PERSON_DOLL),
    ("wheel", WHEEL),
)


# ---- Safe index helpers ----

def _is_whole_number(value: object) -> bool:
    """
    True for real ints like 0, 1, 2.

    Important: bool is a subclass of int in Python (True == 1), so we reject
    bools. Floats like 1.0 are also rejected so we never index with a float.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def in_bounds(row: object, col: object) -> bool:
    """True only for whole-number indices inside the 5x5 grid."""
    if not _is_whole_number(row) or not _is_whole_number(col):
        return False
    return 0 <= row < ROWS and 0 <= col < COLS


def require_in_bounds(row: object, col: object) -> None:
    """Raise ValueError if (row, col) is not a safe 5x5 index."""
    if not in_bounds(row, col):
        raise ValueError(
            f"cell ({row!r}, {col!r}) is outside the {ROWS}x{COLS} grid "
            f"or is not a whole number"
        )


def require_picture(picture: Sequence[str], label: str = "picture") -> None:
    """Raise ValueError if picture is not a 5x5 grid of '#' and '.'."""
    if len(picture) != ROWS:
        raise ValueError(f"{label} must have {ROWS} rows, got {len(picture)}")
    for i, row in enumerate(picture):
        if not isinstance(row, str):
            raise ValueError(f"{label} row {i} must be a string")
        if len(row) != COLS:
            raise ValueError(
                f"{label} row {i} must have {COLS} columns, got {len(row)}"
            )
        for ch in row:
            if ch not in ALLOWED_PICTURE_CHARS:
                raise ValueError(
                    f"{label} may only use '{OBJECT}' and '{EMPTY}', got {ch!r}"
                )


# Validate hardcoded pictures once when this file is imported.
require_picture(WHEEL, label="WHEEL")
require_picture(PERSON_DOLL, label="PERSON_DOLL")


# ---- Observation: what we have looked at ----

@dataclass(frozen=True)
class ShapeObservation:
    """
    Partial look at a 5x5 grid.

    cells[r][c]:
      None  -> not looked yet
      "#"   -> looked and saw an object
      "."   -> looked and saw empty
    """

    cells: tuple[tuple[Optional[str], ...], ...]

    def __post_init__(self) -> None:
        # Freeze caller-owned lists too, so stored observations cannot change
        # later through an alias despite this dataclass being frozen.
        try:
            rows = tuple(tuple(row) for row in self.cells)
        except TypeError as exc:
            raise ValueError("observation must be a 5x5 grid") from exc
        object.__setattr__(self, "cells", rows)
        require_observation(self)

    @staticmethod
    def blank() -> ShapeObservation:
        """Start with every cell unlooked (each row is its own tuple)."""
        return ShapeObservation(
            tuple(
                tuple(None for _ in range(COLS))
                for _ in range(ROWS)
            )
        )

    def get(self, row: int, col: int) -> Optional[str]:
        """Return the looked value, or None if unlooked."""
        require_in_bounds(row, col)
        require_observation(self)
        return self.cells[row][col]

    def is_looked(self, row: int, col: int) -> bool:
        """True if this cell has already been revealed."""
        require_in_bounds(row, col)
        require_observation(self)
        return self.cells[row][col] is not None

    def matches(self, other: ShapeObservation) -> bool:
        """True when every cell matches (looked or not)."""
        return self.cells == other.cells


def require_observation(observation: ShapeObservation) -> None:
    """Raise ValueError if the observation grid is not a valid 5x5 look-grid."""
    if not isinstance(observation, ShapeObservation):
        raise TypeError(
            f"observation must be ShapeObservation, got {type(observation).__name__}"
        )
    if len(observation.cells) != ROWS:
        raise ValueError(
            f"observation must have {ROWS} rows, got {len(observation.cells)}"
        )
    for i, row in enumerate(observation.cells):
        if len(row) != COLS:
            raise ValueError(
                f"observation row {i} must have {COLS} columns, got {len(row)}"
            )
        for value in row:
            if value not in (None, OBJECT, EMPTY):
                raise ValueError(
                    f"observation cells may be None, '{OBJECT}', or '{EMPTY}', "
                    f"got {value!r}"
                )


# Old name kept so existing imports (show_shapes, tests) still work.
Observation = ShapeObservation


def reveal(
    observation: ShapeObservation,
    row: int,
    col: int,
    hidden: Sequence[str],
) -> ShapeObservation:
    """
    Return a NEW observation with (row, col) filled from the hidden grid.

    Never changes the input observation.
    """
    require_in_bounds(row, col)
    require_observation(observation)
    require_picture(hidden, label="hidden")

    # Copy -> change one cell -> freeze again.
    new_rows: list[list[Optional[str]]] = [list(r) for r in observation.cells]
    new_rows[row][col] = hidden[row][col]
    return ShapeObservation(tuple(tuple(r) for r in new_rows))


# ---- Compare one picture to an observation ----

@dataclass(frozen=True)
class ShapeCompare:
    """Result of holding one picture against one observation."""

    name: str
    picture: tuple[str, ...]  # copy of the picture (safe from outside edits)
    fill: tuple[str, ...]
    confirmed: int
    predicted: int
    contradictions: int
    unknown: int
    confirmed_empty: int
    unexpected: int
    template_objects: int

    @property
    def score(self) -> int:
        """score = confirmed '#' marks minus contradiction 'X' marks."""
        return self.confirmed - self.contradictions

    @property
    def coverage(self) -> str:
        return f"confirmed {self.confirmed} of {self.template_objects}"

    @property
    def measurements_agree(self) -> bool:
        """True only when every picture object is confirmed and there is no X."""
        return (
            self.confirmed == self.template_objects
            and self.contradictions == 0
        )


def compare(
    picture: Sequence[str],
    observation: ShapeObservation,
    name: str,
) -> ShapeCompare:
    """
    Hold one shape picture against a partial observation and mark each cell.

    See the module docstring for the meaning of # + X ? -
    """
    require_picture(picture, label=name)
    require_observation(observation)

    fill_rows: list[str] = []
    confirmed = 0
    predicted = 0
    contradictions = 0
    unknown = 0
    confirmed_empty = 0
    unexpected = 0
    template_objects = 0

    for r in range(ROWS):
        marks: list[str] = []
        for c in range(COLS):
            expected = picture[r][c]
            if expected == OBJECT:
                template_objects += 1

            looked = observation.is_looked(r, c)
            seen = observation.get(r, c)

            if not looked:
                if expected == OBJECT:
                    marks.append("+")
                    predicted += 1
                else:
                    marks.append("?")
                    unknown += 1
            elif expected == seen:
                if expected == OBJECT:
                    marks.append("#")
                    confirmed += 1
                else:
                    marks.append("-")
                    confirmed_empty += 1
            else:
                marks.append("X")
                contradictions += 1
                # Saw an object where the picture said empty.
                if expected == EMPTY and seen == OBJECT:
                    unexpected += 1

        fill_rows.append("".join(marks))

    return ShapeCompare(
        name=name,
        picture=tuple(picture),
        fill=tuple(fill_rows),
        confirmed=confirmed,
        predicted=predicted,
        contradictions=contradictions,
        unknown=unknown,
        confirmed_empty=confirmed_empty,
        unexpected=unexpected,
        template_objects=template_objects,
    )


def rank(observation: ShapeObservation) -> list[ShapeCompare]:
    """
    Rank wheel and person-doll by score (highest first).

    If scores tie, sort by name (A before Z).
    """
    results = [
        compare(picture, observation, name) for name, picture in PICTURES
    ]
    results.sort(key=lambda item: (-item.score, item.name))
    return results


def disagreeing_unlooked_cells(
    observation: ShapeObservation,
) -> list[tuple[int, int]]:
    """
    Next looks: unlooked cells where wheel and person-doll disagree.

    Ordered by row, then column. These are looks, not captures.
    """
    require_observation(observation)
    cells: list[tuple[int, int]] = []
    for r in range(ROWS):
        for c in range(COLS):
            if observation.is_looked(r, c):
                continue
            if WHEEL[r][c] != PERSON_DOLL[r][c]:
                cells.append((r, c))
    return cells


# ---- Text lists ----

def strategy_forming_list_lines(observation: ShapeObservation) -> list[str]:
    """Build the Strategy Forming List as text lines (no identity line)."""
    lines = ["Strategy Forming List"]
    for i, result in enumerate(rank(observation), start=1):
        lines.append(
            f"{i}. {result.name}  score={result.score}  "
            f"#={result.confirmed}  +={result.predicted}  "
            f"X={result.contradictions}  ?={result.unknown}  "
            f"-={result.confirmed_empty}  unexpected={result.unexpected}"
        )
        lines.append(f"   {result.coverage}")
    return lines


def greatest_target_list_lines(observation: ShapeObservation) -> list[str]:
    """Build the Greatest Target List as text lines."""
    lines = ["Greatest Target List"]
    targets = disagreeing_unlooked_cells(observation)
    if len(targets) == 0:
        lines.append("(none)")
    else:
        for r, c in targets:
            lines.append(f"cell-{r}-{c}")
    return lines


def print_fill(result: ShapeCompare) -> None:
    """Print fill grid, coverage, agree line, and identity line."""
    for row in result.fill:
        print(row)
    print(result.coverage)
    if result.measurements_agree:
        print("MEASUREMENTS AGREE: yes")
    else:
        print("MEASUREMENTS AGREE: no")
    # Agreeing measurements still do not name the shape.
    print("IDENTITY CLAIMED: no")


# Clearer alias for beginners (same function, same output).
print_shape_fill = print_fill


def print_strategy_forming_list(observation: ShapeObservation) -> None:
    for line in strategy_forming_list_lines(observation):
        print(line)
    print("IDENTITY CLAIMED: no")


def print_greatest_target_list(observation: ShapeObservation) -> None:
    for line in greatest_target_list_lines(observation):
        print(line)


def print_picture(name: str, picture: Sequence[str]) -> None:
    require_picture(picture, label=name)
    print(f"{name}:")
    for row in picture:
        print(row)


def _print_lines_after_title(lines: list[str]) -> None:
    """Print every line after the title. Safe when the list is short."""
    if len(lines) <= 1:
        return
    for line in lines[1:]:
        print(line)


# ---- imagine: look only on a copy ----

@dataclass(frozen=True)
class ImagineStep:
    """One imaginary reveal and the theoretical lists after it."""

    cell: tuple[int, int]
    observation: ShapeObservation
    forming_list: tuple[str, ...]
    target_list: tuple[str, ...]


@dataclass(frozen=True)
class ImagineResult:
    """Steps from imagine, plus proof the real observation was not changed."""

    steps: tuple[ImagineStep, ...]
    real_before_forming: tuple[str, ...]
    real_before_targets: tuple[str, ...]
    real_after_forming: tuple[str, ...]
    real_after_targets: tuple[str, ...]
    real_unchanged: bool


def imagine(
    observation: ShapeObservation,
    hidden: Sequence[str],
) -> ImagineResult:
    """
    Copy the observation and reveal up to IMAGINE_STEP_LIMIT target cells
    on the COPY only.

    Stop early when no disagreeing unlooked cell remains.
    The real observation must still match the before-imagine snapshot.
    """
    require_observation(observation)
    require_picture(hidden, label="hidden")

    snapshot = ShapeObservation(
        tuple(tuple(row) for row in observation.cells)
    )
    real_before_forming = tuple(strategy_forming_list_lines(observation))
    real_before_targets = tuple(greatest_target_list_lines(observation))

    copy = ShapeObservation(observation.cells)
    steps: list[ImagineStep] = []

    for _ in range(IMAGINE_STEP_LIMIT):
        targets = disagreeing_unlooked_cells(copy)
        # Do not read targets[0] when the list is empty.
        if len(targets) == 0:
            break
        r, c = targets[0]
        copy = reveal(copy, r, c, hidden)
        steps.append(
            ImagineStep(
                cell=(r, c),
                observation=copy,
                forming_list=tuple(strategy_forming_list_lines(copy)),
                target_list=tuple(greatest_target_list_lines(copy)),
            )
        )

    real_after_forming = tuple(strategy_forming_list_lines(observation))
    real_after_targets = tuple(greatest_target_list_lines(observation))
    real_unchanged = (
        observation.matches(snapshot)
        and real_before_forming == real_after_forming
        and real_before_targets == real_after_targets
    )

    return ImagineResult(
        steps=tuple(steps),
        real_before_forming=real_before_forming,
        real_before_targets=real_before_targets,
        real_after_forming=real_after_forming,
        real_after_targets=real_after_targets,
        real_unchanged=real_unchanged,
    )


def print_imagine(
    observation: ShapeObservation,
    hidden: Sequence[str],
) -> ImagineResult:
    """Run imagine, print each theoretical step, then reprint the real lists."""
    result = imagine(observation, hidden)

    print("Real lists before imagine:")
    for line in result.real_before_forming:
        print(line)
    print("IDENTITY CLAIMED: no")
    for line in result.real_before_targets:
        print(line)
    print()

    for i, step in enumerate(result.steps, start=1):
        r, c = step.cell
        print(f"Imaginary step {i}: reveal cell-{r}-{c}")
        print("Theoretical Strategy Forming List")
        _print_lines_after_title(list(step.forming_list))
        print("IDENTITY CLAIMED: no")
        print("Theoretical Greatest Target List")
        _print_lines_after_title(list(step.target_list))
        print()

    print("Real lists after imagine (must match before):")
    for line in result.real_after_forming:
        print(line)
    print("IDENTITY CLAIMED: no")
    for line in result.real_after_targets:
        print(line)

    lists_match = (
        result.real_before_forming == result.real_after_forming
        and result.real_before_targets == result.real_after_targets
    )
    if result.real_unchanged and lists_match:
        print("REAL OBSERVATION UNCHANGED: yes")
    else:
        print("REAL OBSERVATION UNCHANGED: no")

    return result


# ---- ShapeWindow: short memory ----

class ShapeWindow:
    """
    Short memory of shape observations.

    Same public names as before (past, current, set_current, clear_current,
    accept). Storage is the shared MemoryWindow helper.
    """

    def __init__(self) -> None:
        self._memory: MemoryWindow[ShapeObservation] = MemoryWindow(
            limit=PAST_LIMIT
        )

    @property
    def past(self) -> list[ShapeObservation]:
        return self._memory.past

    @past.setter
    def past(self, value: list[ShapeObservation]) -> None:
        # Validate each item, then replace_past so the size limit is enforced.
        if not isinstance(value, list):
            raise ValueError("past must be a list")
        for item in value:
            require_observation(item)
        self._memory.replace_past(value)

    @property
    def current(self) -> Optional[ShapeObservation]:
        return self._memory.current

    @current.setter
    def current(self, value: Optional[ShapeObservation]) -> None:
        if value is not None:
            require_observation(value)
        self._memory.current = value

    def set_current(self, observation: ShapeObservation) -> None:
        """Put a preview on screen (does not accept it into past)."""
        require_observation(observation)
        self._memory.set_current(observation)
    def clear_current(self) -> None:
        """Drop only the preview."""
        self._memory.clear_current()

    def accept(self) -> None:
        """Move current into past; keep at most PAST_LIMIT items."""
        self._memory.accept()
