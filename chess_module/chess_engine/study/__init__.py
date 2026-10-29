"""Chess study reports: text facts about a position and candidate moves.

The engine already knows legal moves; these modules *describe* what would change
if you played a move, how replies look, whether goals are reachable, and how
captures compare. Each stage (3A–3F) prints a structured report the CLI or
tests can read.

Module map (read the file that matches the report you care about):
  common           shared types (Goal, RouteVector, risk toggle, helpers)
  calc             Stage 3A — CALC (one move, before/after facts)
  replies          Stage 3B — REPLIES (opponent answers + threat labels)
  search           Stage 3C — LOOP (tree search) and TRACE (move list + CALC)
  goal_basics      Stage 3D — parse goals, PASS distances
  goal_routes_pass Stage 3D — ROUTES in PASS mode (opponent passes)
  goal_routes_real Stage 3D — ROUTES in REAL mode (opponent replies)
  goal_marks       Stage 3D — GOAL MARKS, DISTANCE ORDER, SUPPORT
  exchange_core    Stage 3E — EXCHANGE and ORDER
  exchange_compare Stage 3F — COMPARE (side-by-side moves)
  goals / exchange thin re-exports so older ``from study import …`` paths work
"""

from .common import (
    GoalCondition, Goal, RealResult, MaterialResult, RouteVector,
    set_goal_show_risk, get_goal_show_risk,
    move_distance, order_label, pass_moves, pass_play, pieces_on_square,
)
from .calc import (
    zero_move_cause, linked, report_mates, count_mate_in_one, calc_report,
)
from .replies import replies_report, reply_detail
from .search import (
    zero_move_pieces, mate_forced, first_move_forces, loop_report, trace_report,
)
from .goals import (
    goal_squares, goal_text, goal_holds, piece_distance, side_within,
    side_distance, parse_goal, mark_dominated, routes_report_with,
    second_from, second_goal_report, goal_marks_selection, goal_marks_after,
    distance_lines, distance_selection, distance_after, routes_real_report,
    support_report,
)
from .exchange import (
    piece_value, captured_type, captures_on, exchange_value,
    first_capture_class, material_text, exchange_report, order_report,
    compare_report,
)

__all__ = [
    # common
    "GoalCondition", "Goal", "RealResult", "MaterialResult", "RouteVector",
    "set_goal_show_risk", "get_goal_show_risk",
    "move_distance", "order_label", "pass_moves", "pass_play", "pieces_on_square",
    # calc
    "zero_move_cause", "linked", "report_mates", "count_mate_in_one", "calc_report",
    # replies
    "replies_report", "reply_detail",
    # search
    "zero_move_pieces", "mate_forced", "first_move_forces", "loop_report", "trace_report",
    # goals
    "goal_squares", "goal_text", "goal_holds", "piece_distance", "side_within",
    "side_distance", "parse_goal", "mark_dominated", "routes_report_with",
    "second_from", "second_goal_report", "goal_marks_selection", "goal_marks_after",
    "distance_lines", "distance_selection", "distance_after", "routes_real_report",
    "support_report",
    # exchange
    "piece_value", "captured_type", "captures_on", "exchange_value",
    "first_capture_class", "material_text", "exchange_report", "order_report",
    "compare_report",
]
