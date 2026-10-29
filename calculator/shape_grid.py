"""Fixed 5x5 grids, hardcoded pictures, and safe index helpers.

Pictures use '#' (object) and '.' (empty). PICTURES lists every template
rank() compares. IMAGINE_STEP_LIMIT caps how many hypothetical reveals run
on a copy in shape_imagine.imagine().
"""

from __future__ import annotations

from typing import Sequence

from calculator.window import DEFAULT_PAST_LIMIT

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
