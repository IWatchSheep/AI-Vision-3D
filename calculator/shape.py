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

from typing import Optional

from calculator.shape_compare import (
    Observation,
    ShapeCompare,
    ShapeObservation,
    compare,
    disagreeing_unlooked_cells,
    greatest_target_list_lines,
    print_fill,
    print_greatest_target_list,
    print_picture,
    print_shape_fill,
    print_strategy_forming_list,
    rank,
    require_observation,
    reveal,
    strategy_forming_list_lines,
)
from calculator.shape_grid import (
    ALLOWED_PICTURE_CHARS,
    COLS,
    EMPTY,
    FILL_MARKS,
    IMAGINE_STEP_LIMIT,
    OBJECT,
    PAST_LIMIT,
    PERSON_DOLL,
    PICTURES,
    ROWS,
    WHEEL,
    in_bounds,
    require_in_bounds,
    require_picture,
)
from calculator.shape_imagine import ImagineResult, ImagineStep, imagine, print_imagine
from calculator.window import MemoryWindow

# ---- ShapeWindow: short memory (past/current/accept; see window.py) ----

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
