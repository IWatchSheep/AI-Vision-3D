"""Stage 3B: opponent reply analysis (REPLIES report)."""

from typing import List, Optional
from ..constants import color_name
from ..move import Move
from ..board import Board
from ..movegen import sorted_moves, legal_move, make_move, game_over
from ..tracker import Tracker, position_after
from .calc import calc_report, report_mates, count_mate_in_one


def replies_report(board: Board, tracker: Tracker, move: Move) -> str:
    """Generates the Stage 3B Replies report for `move`."""
    if not legal_move(board, move):
        raise ValueError("Cannot report an illegal move")
    lines: List[str] = []
    mover = board.grid[move.sr][move.sc].color
    after_board, tracker_after = position_after(board, tracker, move)

    lines.append(f"REPLIES BEGIN {move.uci}")
    replies = sorted_moves(after_board)
    ended, stalemate, draw_reason = game_over(after_board)
    if ended:
        status = draw_reason or ("stalemate" if stalemate else "checkmate")
        lines.extend([f"NO REPLIES {status}",
                      "SUMMARY REPLIES 0 STOPS 0 LEAVES 0 NO-THREAT 0 ALLOWS 0",
                      "REPLIES END\n"])
        return "\n".join(lines)

    threat_mates = report_mates(after_board, mover)
    threat = len(threat_mates) > 0

    if threat:
        lines.append(f"THREAT {color_name(mover)} {' '.join(threat_mates)}")
    else:
        lines.append(f"THREAT {color_name(mover)} none")

    stops = leaves = allows = no_threat = 0

    for rep in replies:
        after_rep = after_board.clone()
        make_move(after_rep, rep, record_history=True)
        still_threat = (count_mate_in_one(after_rep, mover) > 0)

        if threat and still_threat:
            label = "LEAVES"
            leaves += 1
        elif threat:
            label = "STOPS"
            stops += 1
        elif still_threat:
            label = "ALLOWS"
            allows += 1
        else:
            label = "NO-THREAT"
            no_threat += 1

        # Calculate counts for this reply
        rep_report_text = calc_report(after_board, tracker_after, rep)
        count_white = ""
        count_black = ""
        for line in rep_report_text.splitlines():
            if line.startswith("COUNT White "):
                count_white = line
            elif line.startswith("COUNT Black "):
                count_black = line

        lines.append(f"REPLY {rep.uci} {label} {count_white} {count_black}")

    lines.append(f"SUMMARY REPLIES {len(replies)} STOPS {stops} LEAVES {leaves} NO-THREAT {no_threat} ALLOWS {allows}")
    lines.append("REPLIES END\n")
    return "\n".join(lines)


def reply_detail(board: Board, tracker: Tracker, move: Move, reply: Move) -> Optional[str]:
    """Generates full CALC report for a single specific reply."""
    after_board, tracker_after = position_after(board, tracker, move)
    if game_over(after_board)[0] or not legal_move(after_board, reply):
        return None
    return calc_report(after_board, tracker_after, reply)
