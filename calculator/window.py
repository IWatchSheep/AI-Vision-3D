"""
Shared short-memory window used by chess and shape calculators.

Beginner picture
----------------
Think of a tiny notepad with two parts:

  current = what is on screen right now (or nothing)
  past    = up to `limit` accepted items, oldest first

accept() moves current into past. If past grows past `limit`, the oldest
item is dropped. clear_current() throws away only the preview.

This module does not know about chess boards or shape grids. It only
stores whatever item type the caller passes in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

T = TypeVar("T")

DEFAULT_PAST_LIMIT = 4


def _require_positive_limit(limit: object) -> int:
    """
    Accept only a real int >= 1.

    Rejects bool (True == 1 in Python) and values < 1.
    A negative limit would make `while len(past) > limit` stay true even
    after past is empty, and the next pop(0) would crash.
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError(f"limit must be an integer >= 1, got {limit!r}")
    return limit


@dataclass
class MemoryWindow(Generic[T]):
    """
    past / current notepad with a hard size limit on past.

    Behavior matches PatternWindow and ShapeWindow accept() rules.
    """

    limit: int = DEFAULT_PAST_LIMIT
    past: list[T] = field(default_factory=list)
    current: Optional[T] = None

    def __post_init__(self) -> None:
        # Validate and normalize limit; trim any oversized past given at creation.
        self.limit = _require_positive_limit(self.limit)
        if not isinstance(self.past, list):
            raise ValueError("past must be a list")
        self.past = list(self.past)
        self._trim_past()

    def _trim_past(self) -> None:
        """Drop oldest items until past length fits the limit."""
        self.limit = _require_positive_limit(self.limit)
        if len(self.past) > self.limit:
            del self.past[:-self.limit]

    def set_current(self, item: T) -> None:
        """Put a preview on screen (does not accept it into past)."""
        self.current = item

    def clear_current(self) -> None:
        """Drop only the preview. past is left alone."""
        self.current = None

    def replace_past(self, items: list[T]) -> None:
        """
        Replace past with a new list, then enforce the size limit.

        Use this instead of assigning to .past when you need a checked write.
        """
        if not isinstance(items, list):
            raise ValueError("past must be a list")
        self.limit = _require_positive_limit(self.limit)
        self.past = list(items)
        self._trim_past()

    def accept(self) -> None:
        """
        Move current into past.

        If past grows past limit, drop the oldest item (index 0).
        Doing nothing when current is None keeps the old behavior.
        """
        if self.current is None:
            return
        self.limit = _require_positive_limit(self.limit)
        self.past.append(self.current)
        self.current = None
        # limit >= 1, so len > limit means past is not empty and pop is safe.
        self._trim_past()
