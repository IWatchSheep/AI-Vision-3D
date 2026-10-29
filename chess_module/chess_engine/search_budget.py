"""Cooperative work limits shared by nested analysis searches."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from time import monotonic


class SearchLimitExceeded(ValueError):
    """The analysis was interrupted; no complete result is available."""


@dataclass
class SearchBudget:
    max_nodes: int = 20_000
    seconds: float = 10.0
    nodes: int = 0
    started: float = field(default_factory=monotonic)

    def consume(self) -> None:
        self.nodes += 1
        if self.nodes > self.max_nodes or monotonic() - self.started >= self.seconds:
            raise SearchLimitExceeded(
                "Analysis work limit reached. Try a smaller depth or fewer goal squares."
            )


_active_budget: ContextVar[SearchBudget | None] = ContextVar("chess_search_budget", default=None)


def bounded_search(function):
    """Give a top-level call a budget; nested calls share the same allowance.

    Exceptions propagate rather than producing a misleading partial result.
    Context is reset even on failure so later commands get a fresh budget.
    Time is checked between search steps, not by interrupting a running step.
    """
    @wraps(function)
    def wrapped(*args, **kwargs):
        budget = _active_budget.get()
        token = None
        if budget is None:
            budget = SearchBudget()
            token = _active_budget.set(budget)
        try:
            budget.consume()
            return function(*args, **kwargs)
        finally:
            if token is not None:
                _active_budget.reset(token)
    return wrapped
