"""Partial 5x5 observations, compare/rank, and reveal on a copy.

ShapeObservation stores what cells were looked at (None = not yet).
compare() marks cells using the cheat sheet in calculator.shape.
Print helpers live in shape_print and are re-exported at the bottom.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from calculator.shape_grid import (
    COLS,
    EMPTY,
    OBJECT,
    PERSON_DOLL,
    PICTURES,
    ROWS,
    WHEEL,
    require_in_bounds,
    require_picture,
)


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

    See calculator.shape module docstring for the meaning of # + X ? -
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


from calculator.shape_print import (  # noqa: E402  re-export public API
    greatest_target_list_lines,
    print_fill,
    print_greatest_target_list,
    print_picture,
    print_shape_fill,
    print_strategy_forming_list,
    strategy_forming_list_lines,
)
