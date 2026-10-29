"""Goal marks, distance order, and support reports (Stage 3D).

Split across:
  goal_marks_pass.py  PASS goal marks
  distance_order.py   DISTANCE ORDER
  support_report.py   SUPPORT follow-ups
"""

from .distance_order import distance_after, distance_lines, distance_selection
from .goal_marks_pass import goal_marks_after, goal_marks_selection
from .support_report import support_report

__all__ = [
    "goal_marks_selection",
    "goal_marks_after",
    "distance_lines",
    "distance_selection",
    "distance_after",
    "support_report",
]
