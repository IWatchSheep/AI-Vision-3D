"""Optional study commands: goals, routes, distance order, support.

These only print analysis; they never replace the select → preview → F move flow.
"""

from __future__ import annotations

from .movegen import legal_move
from .analysis import (
    parse_goal, goal_text,
    routes_report_with, routes_real_report, support_report,
)
from .cli_session import GameSession, err, warn_slow_search, parse_bounded_int


def handle_goal(session: GameSession, cmd: str) -> bool:
    """Set, show, or clear the primary goal (target squares + move limit)."""
    lower = cmd.lower()
    if lower != "goal" and not lower.startswith("goal "):
        return False

    if lower == "goal":
        if session.goal.active:
            print(f"GOAL ACTIVE {goal_text(session.goal)} LIMIT {session.goal.limit} PASS")
        else:
            print("No goal is active. Type goal f7 2 (squares, then a limit of own moves 1 to 4).")
        return True

    if lower == "goal off":
        session.goal.active = False
        print("Goal cleared.")
        return True

    parsed = parse_goal(cmd[5:])
    if parsed:
        session.goal = parsed
        print(f"GOAL ACTIVE {goal_text(session.goal)} LIMIT {session.goal.limit} PASS")
    else:
        err(
            "Type goal, squares and a limit from 1 to 4, for example "
            "goal f7 2, goal f7 g7 h7 3 or goal king 2; goal off clears it."
        )
    return True


def handle_goal2(session: GameSession, cmd: str) -> bool:
    """Same as goal, but for a second parallel target set."""
    lower = cmd.lower()
    if lower != "goal2" and not lower.startswith("goal2 "):
        return False

    if lower == "goal2":
        if session.second_goal.active:
            print(
                f"SECOND GOAL ACTIVE {goal_text(session.second_goal)} "
                f"LIMIT {session.second_goal.limit} PASS"
            )
        else:
            print(
                "No second goal is active. Type goal2 d5 2 "
                "(squares, then a limit of own moves 1 to 4)."
            )
        return True

    if lower == "goal2 off":
        session.second_goal.active = False
        print("Second goal cleared.")
        return True

    parsed = parse_goal(cmd[6:])
    if parsed:
        session.second_goal = parsed
        print(
            f"SECOND GOAL ACTIVE {goal_text(session.second_goal)} "
            f"LIMIT {session.second_goal.limit} PASS"
        )
    else:
        err(
            "Type goal2, squares and a limit from 1 to 4, "
            "for example goal2 d5 2; goal2 off clears it."
        )
    return True


def handle_distance(session: GameSession, cmd: str) -> bool:
    """Show or toggle distance-order hints during piece selection and preview."""
    lower = cmd.lower()
    if lower not in ("distance", "distance on", "distance off"):
        return False
    if " " in lower:
        session.distance_view = lower.split()[1] == "on"
    print(f"DISTANCE ORDER {'ON' if session.distance_view else 'OFF'}")
    return True


def handle_routes(session: GameSession, cmd: str) -> bool:
    """routes (PASS) or routes real <1..6>.

    Tokens must be exact: 'routes real 3' works; 'routes realx 3' does not.
    """
    parts = cmd.split()
    if not parts or parts[0].lower() != "routes":
        return False

    if len(parts) == 1:
        if not session.goal.active:
            err("No goal is active. Type goal f7 2 first, then routes.")
        else:
            second = session.second_goal if session.second_goal.active else None
            print(routes_report_with(session.board, session.goal, second), end="")
        return True

    # Require the exact second token "real" (not "realx", "reality", ...).
    if parts[1].lower() != "real":
        return False

    depth_val = parse_bounded_int(parts[2], 1, 6) if len(parts) == 3 else None
    if not session.goal.active:
        err("No goal is active. Type goal f7 2 first, then routes.")
    elif depth_val is None:
        err(
            "Type routes (PASS), or routes real and a depth from 1 to 6, "
            "for example routes real 3."
        )
    else:
        warn_slow_search(depth_val)
        print(routes_real_report(session.board, session.goal, depth_val), end="")
    return True


def handle_support(session: GameSession, cmd: str) -> bool:
    """Print a support report for the current preview (after destination, before F)."""
    if cmd.lower() != "support":
        return False
    if not session.preview_shown or not legal_move(session.board, session.preview_move):
        if session.preview_shown:
            session.invalidate_preview()
        err("No preview to support. Select a piece and preview a destination, then type support.")
    else:
        print(support_report(session.board, session.preview_move), end="")
    return True
