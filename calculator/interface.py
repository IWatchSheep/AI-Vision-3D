
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Action:
    """
    Represents one possible action supplied by an application.

    The shared calculator does not decide whether an action
    is legal. That responsibility belongs to the application.
    """

    action_id: str
    description: str
    data: Any = None

@dataclass(frozen=True)
class Observation:
    """
    Represents information observed by an application.

    The calculator receives observations without needing
    to know the application's internal rules.
    """

    observation_id: str
    description: str
    data: Any = None
