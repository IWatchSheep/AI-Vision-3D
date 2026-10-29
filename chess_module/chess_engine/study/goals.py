"""Stage 3D: goals, routes, PASS mode, distance order and support.

A "goal" is a set of squares (or squares around the enemy king) the side to
move wants to reach or hold defended. PASS routes (goal_routes_pass) ignore
opponent replies; REAL routes (goal_routes_real) do not. This package re-exports
parsers and report builders for the CLI.
"""

from .goal_basics import (
    goal_squares, goal_text, goal_holds, piece_distance,
    side_within, side_distance, parse_goal,
)
from .goal_routes import (
    mark_dominated, routes_report_with,
    second_from, second_goal_report, routes_real_report,
)
from .goal_marks import (
    goal_marks_selection, goal_marks_after,
    distance_lines, distance_selection, distance_after,
    support_report,
)

__all__ = [
    "goal_squares", "goal_text", "goal_holds", "piece_distance",
    "side_within", "side_distance", "parse_goal",
    "mark_dominated", "routes_report_with",
    "second_from", "second_goal_report", "routes_real_report",
    "goal_marks_selection", "goal_marks_after",
    "distance_lines", "distance_selection", "distance_after",
    "support_report",
]
