"""Analysis commands (R, replies, loop, compare, trace, memory, …).

Most need a preview first (select square → destination); they report facts only.
Depth limits use parse_bounded_int so huge numbers never reach the search code.
"""

from __future__ import annotations

from typing import List

from .constants import EXCHANGE_MAX, COMPARE_MAX, parse_square, square_index
from .move import Move, parse_move_text
from .movegen import legal_move
from .analysis import (
    calc_report, replies_report, reply_detail,
    loop_report, trace_report,
    exchange_report, order_report, compare_report,
    set_goal_show_risk, get_goal_show_risk,
)
from .cli_session import GameSession, err, warn_slow_search, parse_bounded_int

# Goal/routes/support live next door; re-export so older imports keep working.
from .cli_goal_cmds import (  # noqa: F401
    handle_goal,
    handle_goal2,
    handle_distance,
    handle_routes,
    handle_support,
)


def handle_calc_report(session: GameSession, cmd: str) -> bool:
    """R — calculator-style report for the move you are previewing (before F)."""
    if cmd.lower() != "r":
        return False
    if not session.preview_shown or not legal_move(session.board, session.preview_move):
        if session.preview_shown:
            session.invalidate_preview()
        err("No preview to report. Select a piece and preview a destination, then type R.")
    else:
        print(calc_report(session.board, session.tracker, session.preview_move), end="")
    return True


def handle_replies(session: GameSession, cmd: str) -> bool:
    """List or inspect opponent replies to your previewed move."""
    lower = cmd.lower()
    if lower != "replies" and not lower.startswith("replies "):
        return False

    if not session.preview_shown or not legal_move(session.board, session.preview_move):
        if session.preview_shown:
            session.invalidate_preview()
        err("No preview to answer. Select a piece and preview a destination, then type replies.")
        return True

    if lower == "replies":
        print(replies_report(session.board, session.tracker, session.preview_move), end="")
        return True

    reply_tok = cmd.split(None, 1)[1].strip()
    rep_move = parse_move_text(reply_tok)
    if not rep_move:
        err("Not a legal reply. Type replies to list them, or replies e7e5 for one.")
        return True

    detail = reply_detail(session.board, session.tracker, session.preview_move, rep_move)
    if detail:
        print(detail, end="")
    else:
        err("Not a legal reply. Type replies to list them, or replies e7e5 for one.")
    return True


def handle_loop(session: GameSession, cmd: str) -> bool:
    """Count positions to a ply depth (can be slow at depth 5–6)."""
    lower = cmd.lower()
    if lower != "loop" and not lower.startswith("loop "):
        return False

    parts = cmd.split()
    usage = (
        "Type loop and a depth from 1 to 6, for example loop 3 "
        "(or loop 3 6 to also count pieces that can't move)."
    )
    if len(parts) not in (2, 3):
        err(usage)
        return True
    depth_val = parse_bounded_int(parts[1], 1, 6)
    if depth_val is None:
        err(usage)
        return True
    zero_k = 0
    if len(parts) == 3:
        zero_k = parse_bounded_int(parts[2], 1, 16)
        if zero_k is None:
            err(usage)
            return True
    if depth_val >= 5:
        print(
            f"Searching {depth_val} plies. Analysis stops at its work limit; "
            "try a smaller depth if the search cannot finish."
        )
    print(loop_report(session.board, depth_val, zero_k), end="")
    return True


def handle_exchange(session: GameSession, cmd: str) -> bool:
    """Exchange analysis on one square with a bounded capture limit."""
    lower = cmd.lower()
    if lower != "exchange" and not lower.startswith("exchange "):
        return False

    parts = cmd.split()
    usage = (
        "Type exchange, a square and a limit of captures from 1 to 8, "
        "for example exchange e5 4."
    )
    if len(parts) != 3:
        err(usage)
        return True

    parsed_sq = parse_square(parts[1])
    lim = parse_bounded_int(parts[2], 1, EXCHANGE_MAX)
    if parsed_sq is None or lim is None:
        err(usage)
        return True

    sq_idx = square_index(parsed_sq[0], parsed_sq[1])
    print(exchange_report(session.board, sq_idx, lim), end="")
    return True


def handle_order(session: GameSession, cmd: str) -> bool:
    """Order report for captures up to the given exchange limit."""
    lower = cmd.lower()
    if lower != "order" and not lower.startswith("order "):
        return False

    parts = cmd.split()
    usage = "Type order and an exchange limit from 1 to 8, for example order 4."
    lim = parse_bounded_int(parts[1], 1, EXCHANGE_MAX) if len(parts) == 2 else None
    if lim is None:
        err(usage)
    else:
        print(order_report(session.board, lim), end="")
    return True


def handle_compare(session: GameSession, cmd: str) -> bool:
    """Compare several legal moves at a search depth (2–6 moves)."""
    lower = cmd.lower()
    if lower != "compare" and not lower.startswith("compare "):
        return False

    parts = cmd.split()
    usage = (
        "Type compare, a depth from 1 to 5, then 2 to 6 different legal moves, "
        "for example compare 3 d1h5 d1f3 g1f3."
    )
    # depth + 2..COMPARE_MAX moves => 3 .. 1+COMPARE_MAX extra tokens after "compare"
    if not (4 <= len(parts) <= 2 + COMPARE_MAX):
        err(usage)
        return True

    depth_val = parse_bounded_int(parts[1], 1, 5)
    if depth_val is None:
        err(usage)
        return True

    cand_moves: List[Move] = []
    valid = True
    for m_str in parts[2:]:
        pm = parse_move_text(m_str)
        if not pm or not legal_move(session.board, pm) or pm in cand_moves:
            valid = False
            break
        cand_moves.append(pm)

    if not valid or not (2 <= len(cand_moves) <= COMPARE_MAX):
        err(usage)
        return True

    warn_slow_search(depth_val)
    active_goal = session.goal if session.goal.active else None
    print(
        compare_report(session.board, session.tracker, active_goal, depth_val, cand_moves),
        end="",
    )
    return True


def handle_risk(_session: GameSession, cmd: str) -> bool:
    """Show or toggle AT-RISK markers on goal-related output."""
    lower = cmd.lower()
    if lower not in ("risk", "risk on", "risk off"):
        return False
    if " " in lower:
        set_goal_show_risk(lower.split()[1] == "on")
    print(f"AT-RISK {'ON' if get_goal_show_risk() else 'OFF'}")
    return True


def handle_trace(session: GameSession, cmd: str) -> bool:
    """Step through a typed sequence of moves from the current position."""
    lower = cmd.lower()
    if lower != "trace" and not lower.startswith("trace "):
        return False

    arg_str = cmd[6:].strip() if lower.startswith("trace ") else ""
    ok, report_text, bad_ply = trace_report(session.board, session.tracker, arg_str)
    if ok:
        print(report_text, end="")
    else:
        err(
            f"Not a legal sequence (move {bad_ply}). "
            "Type trace and moves, for example trace e2e4 e7e5."
        )
    return True


def handle_memory(session: GameSession, cmd: str) -> bool:
    """memory -> print the five-move window (past + optional current preview)."""
    if cmd.lower() != "memory":
        return False
    session.memory.print_report()
    return True
