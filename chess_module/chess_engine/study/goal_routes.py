"""Entry point for goal route reports (PASS vs REAL).

Import from here for a stable API. Implementation is split:
  goal_routes_pass — opponent passes; lists concrete move paths
  goal_routes_real — opponent replies; FORCED / POSSIBLE / ELSE summaries
"""

from .goal_routes_pass import (
    mark_dominated,
    routes_report_with,
    second_from,
    second_goal_report,
)
from .goal_routes_real import routes_real_report

__all__ = [
    "mark_dominated",
    "routes_report_with",
    "second_from",
    "second_goal_report",
    "routes_real_report",
]
