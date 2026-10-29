"""Stage 3F: multi-move comparison report.

Runs CALC + REPLIES (+ shared LOOP) once per candidate, then prints pairwise
SAME/DIFFERENT lines so you can see which facts diverge between two moves.
"""

from typing import Dict, List, Optional

from ..constants import COMPARE_MAX, color_name, in_bounds
from ..move import Move
from ..board import Board
from ..movegen import legal_move
from ..tracker import Tracker
from .common import Goal, MaterialResult, move_distance, order_label, piece_value
from .calc import calc_report
from .replies import replies_report
from .exchange_core import captured_type, first_capture_class


def _loop_match_uci(board: Board, m: Move) -> str:
    """UCI key used in LOOP FIRST lines (pawn promotions always include a letter)."""
    if m.promotion and m.promotion != "\0":
        return m.uci
    if in_bounds(m.sr, m.sc) and in_bounds(m.er, m.ec):
        piece = board.grid[m.sr][m.sc]
        if piece.type == "P" and m.er in (0, 7):
            return Move(m.sr, m.sc, m.er, m.ec, promotion="Q").uci
    return m.uci


def compare_report(
    board: Board, tracker: Tracker, goal: Optional[Goal], depth: int, moves: List[Move]
) -> str:
    """Side-by-side comparative analysis of candidate moves."""
    if not isinstance(depth, int) or isinstance(depth, bool) or not 1 <= depth <= 5:
        raise ValueError("compare depth must be between 1 and 5")
    if (not 2 <= len(moves) <= COMPARE_MAX or any(not legal_move(board, m) for m in moves)
            or len(set(moves)) != len(moves)):
        raise ValueError("Expected 2 to 6 distinct legal moves")
    lines: List[str] = [
        f"COMPARE BEGIN {color_name(board.turn)} DEPTH {depth}",
        "NOTE values P 1, N 3, B 3, R 5, Q 9 are logged only, not a score; a nonnegative material result is not proof that a move is good"
    ]

    # LOOP report once (shared by every candidate). Do not call order_report /
    # routes_real_report here — those results were never used and routes_real
    # at depth 5 can take a very long time.
    from .exchange import loop_report

    loop_txt = loop_report(board, depth) if depth >= 1 else ""

    # --- Build one summary dict per candidate move (CALC, REPLIES, LOOP, material) ---
    candidates = []
    all_values = []
    all_distances = []
    for m in moves:
        taken = captured_type(board, m)
        all_values.append(piece_value(taken))
        all_distances.append(move_distance(m))

    for m in moves:
        c: Dict = {'move': m, 'text': m.uci}
        r_txt = calc_report(board, tracker, m)
        c['r_white'] = "-"
        c['r_black'] = "-"
        c['check'] = "none"
        c['mate1_white'] = "none"
        c['mate1_black'] = "none"
        c['links'] = [0, 0, 0, 0]

        for line in r_txt.splitlines():
            if line.startswith("COUNT White "): c['r_white'] = line[12:]
            elif line.startswith("COUNT Black "): c['r_black'] = line[12:]
            elif line.startswith("CHECK "): c['check'] = line[6:]
            elif line.startswith("MATE1 White "): c['mate1_white'] = line[12:]
            elif line.startswith("MATE1 Black "): c['mate1_black'] = line[12:]
            elif line.startswith("PROTECT+ "): c['links'][0] += 1
            elif line.startswith("PROTECT- "): c['links'][1] += 1
            elif line.startswith("ATTACK+ "): c['links'][2] += 1
            elif line.startswith("ATTACK- "): c['links'][3] += 1

        rep_txt = replies_report(board, tracker, m)
        c['threat'] = "-"
        c['replies'] = "-"
        for line in rep_txt.splitlines():
            if line.startswith("NO REPLIES "): c['threat'] = f"GAME-OVER {line[11:]}"
            elif line.startswith("THREAT "): c['threat'] = line[7:]
            elif line.startswith("SUMMARY REPLIES "): c['replies'] = line[16:]

        # LOOP lines always use a promotion letter for pawns on the last rank.
        # Candidate moves typed as a7a8 (promo '\0') must look up as a7a8q.
        loop_uci = _loop_match_uci(board, m)
        prefix = f"FIRST {loop_uci} "
        c['loop_status'] = "-"
        c['loop_level'] = -1
        for line in loop_txt.splitlines():
            if line.startswith(prefix):
                rem = line[len(prefix):]
                c['loop_status'] = rem
                c['loop_level'] = 2 if "FORCED" in rem else (1 if "POSSIBLE" in rem else 0)
                break

        c['taken'] = captured_type(board, m)
        c['value'] = piece_value(c['taken'])
        c['squares'] = move_distance(m)
        c['squares_label'] = order_label(all_distances, c['squares'])

        if c['taken']:
            # Rank captures only against other captures (ignore non-capture 0s).
            capture_vals = [v for v in all_values if v > 0]
            neg_vals = [9 - v for v in capture_vals] if capture_vals else [9 - c['value']]
            c['value_label'] = order_label(neg_vals, 9 - c['value'])
            c['material'], c['bounded'] = first_capture_class(board, m, depth)
            c['material_known'] = True
        else:
            c['value_label'] = "none"
            c['material_known'] = False
            c['material'] = MaterialResult.MATERIAL_ELSE
            c['bounded'] = False

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
