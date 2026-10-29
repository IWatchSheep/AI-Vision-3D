"""Stage 3F: multi-move comparison report.

Runs CALC + REPLIES (+ shared LOOP) once per candidate, then prints pairwise
SAME/DIFFERENT lines so you can see which facts diverge between two moves.
"""

from typing import Dict, List, Optional
from ..search_budget import bounded_search

from ..constants import COMPARE_MAX, color_name, in_bounds
from ..move import Move
from ..board import Board
from ..movegen import legal_move
from ..tracker import Tracker
from .common import Goal
from .calc import calc_report
from .replies import replies_report


def _loop_match_uci(board: Board, m: Move) -> str:
    """UCI key used in LOOP FIRST lines (pawn promotions always include a letter)."""
    if m.promotion and m.promotion != "\0":
        return m.uci
    if in_bounds(m.sr, m.sc) and in_bounds(m.er, m.ec):
        piece = board.grid[m.sr][m.sc]
        if piece.type == "P" and m.er in (0, 7):
            return Move(m.sr, m.sc, m.er, m.ec, promotion="Q").uci
    return m.uci


@bounded_search
def compare_report(
    board: Board, tracker: Tracker, goal: Optional[Goal], depth: int, moves: List[Move]
) -> str:
    """Side-by-side comparative analysis of candidate moves.

    `goal` is accepted for CLI compatibility; COMPARE does not print goal lines.
    """
    del goal  # Reserved for a future COMPARE+goal view; unused today.
    if not isinstance(depth, int) or isinstance(depth, bool) or not 1 <= depth <= 5:
        raise ValueError("compare depth must be between 1 and 5")
    if (not 2 <= len(moves) <= COMPARE_MAX or any(not legal_move(board, m) for m in moves)
            or len(set(moves)) != len(moves)):
        raise ValueError("Expected 2 to 6 distinct legal moves")
    lines: List[str] = [
        f"COMPARE BEGIN {color_name(board.turn)} DEPTH {depth}",
        "NOTE COMPARE prints COUNT, CHECK, THREAT, REPLIES, and LOOP only",
    ]

    # One shared LOOP report for every candidate (avoids repeating the tree).
    from .exchange import loop_report

    loop_txt = loop_report(board, depth)

    # --- Build one summary dict per candidate (only fields that are printed) ---
    candidates = []
    for m in moves:
        c: Dict = {'move': m, 'text': m.uci}
        r_txt = calc_report(board, tracker, m)
        c['r_white'] = "-"
        c['r_black'] = "-"
        c['check'] = "none"

        for line in r_txt.splitlines():
            if line.startswith("COUNT White "):
                c['r_white'] = line[12:]
            elif line.startswith("COUNT Black "):
                c['r_black'] = line[12:]
            elif line.startswith("CHECK "):
                c['check'] = line[6:]

        rep_txt = replies_report(board, tracker, m)
        c['threat'] = "-"
        c['replies'] = "-"
        for line in rep_txt.splitlines():
            if line.startswith("NO REPLIES "):
                c['threat'] = f"GAME-OVER {line[11:]}"
            elif line.startswith("THREAT "):
                c['threat'] = line[7:]
            elif line.startswith("SUMMARY REPLIES "):
                c['replies'] = line[16:]

        # LOOP lines always use a promotion letter for pawns on the last rank.
        loop_uci = _loop_match_uci(board, m)
        prefix = f"FIRST {loop_uci} "
        c['loop_status'] = "-"
        for line in loop_txt.splitlines():
            if line.startswith(prefix):
                c['loop_status'] = line[len(prefix):]
                break

        candidates.append(c)

    # --- Pairwise DIFFERENT/SAME lines for every ordered pair of moves ---
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            a = candidates[i]
            b = candidates[j]
            lines.append(f"COMPARE {a['text']} {b['text']} MOVE-PAIR")
            lines.append(f"COMPARE {a['text']} {b['text']} R White {a['r_white']} | {b['r_white']} {'SAME' if a['r_white'] == b['r_white'] else 'DIFFERENT'}")
            lines.append(f"COMPARE {a['text']} {b['text']} R Black {a['r_black']} | {b['r_black']} {'SAME' if a['r_black'] == b['r_black'] else 'DIFFERENT'}")
            lines.append(f"COMPARE {a['text']} {b['text']} CHECK {a['check']} | {b['check']} {'SAME' if a['check'] == b['check'] else 'DIFFERENT'}")
            lines.append(f"COMPARE {a['text']} {b['text']} THREAT {a['threat']} | {b['threat']} {'SAME' if a['threat'] == b['threat'] else 'DIFFERENT'}")
            lines.append(f"COMPARE {a['text']} {b['text']} REPLIES {a['replies']} | {b['replies']} {'SAME' if a['replies'] == b['replies'] else 'DIFFERENT'}")
            lines.append(f"COMPARE {a['text']} {b['text']} LOOP {a['loop_status']} | {b['loop_status']} {'SAME' if a['loop_status'] == b['loop_status'] else 'DIFFERENT'}")

    lines.append("COMPARE END\n")
    return "\n".join(lines)
