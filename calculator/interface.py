"""
Shared calculator message types used by applications.

These are generic labels for "something an app can do" (Action) and
"something an app saw" (Observation).

They are NOT:
  - the 5x5 ShapeObservation in calculator.shape
  - a chess board / strategy doll

Security note for beginners:
  The optional "data" field can hold any Python object. Do not put passwords,
  API keys, or other secrets here, and do not pass untrusted data into code
  that might execute it. This calculator only stores and forwards the value.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Action:
    """
    One possible action supplied by an application.

    The shared calculator does not decide whether an action is legal.
    That responsibility belongs to the application.
    """

    action_id: str
    description: str
    data: Any = None

    def __post_init__(self) -> None:
        if not isinstance(self.action_id, str) or self.action_id.strip() == "":
            raise ValueError("action_id must be a non-empty string")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string")


@dataclass(frozen=True)
class Observation:
    """
    Information observed by an application.

    Name clash: calculator.shape.ShapeObservation is a 5x5 look-grid.
    Import the one you mean by full module path.
    """

    observation_id: str
    description: str
    data: Any = None

    def __post_init__(self) -> None:
        if not isinstance(self.observation_id, str) or self.observation_id.strip() == "":
            raise ValueError("observation_id must be a non-empty string")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string")
