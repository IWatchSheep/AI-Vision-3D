"""Goal marks, distance order, and support reports (Stage 3D).

GOAL MARKS label how each candidate move advances a PASS goal. DISTANCE ORDER
sorts a piece's destinations by Chebyshev distance. SUPPORT finds follow-up
moves that newly defend the landing square (still in PASS mode).
"""

from typing import List

from ..constants import (
    BOARD_SIZE, TOTAL_SQUARES,
    WHITE, BLACK,
    in_bounds, opposite, color_name, square_index, square_text,
)
from ..move import Move
from ..board import Board
from ..movegen import (
    sorted_moves, make_move, legal_move, piece_attacks,
)
from .common import (
    Goal, GoalCondition,
    move_distance, order_label,
    pass_moves, pass_play, pieces_on_square,
)
from .goal_basics import (
    goal_squares, goal_text, goal_holds, piece_distance, side_distance,
)


def goal_marks_selection(board: Board, goal: Goal, r: int, c: int) -> str:
    """Marks destinations of selected piece according to goal progress."""
    if not in_bounds(r, c):
        return "GOAL MARKS END\n"
    squares = goal_squares(goal, board, board.turn)
    at = square_text(square_index(r, c))
    lines = [f"GOAL MARKS {board.grid[r][c].type} {at} GOAL {goal_text(goal)} LIMIT {goal.limit} PASS"]

    moves = sorted_moves(board)
    for m in moves:
        if m.sr != r or m.sc != c:
            continue
        after = board.clone()
        pass_play(after, m, board.turn)
        line = f"MARK {m.uci}"

        # --- Remaining PASS plies after this move: piece vs whole side ---
        p_done = False
        left = goal.limit - 1
        for sq in squares:
            if left >= 0:
                d = piece_distance(after, m.er, m.ec, after.turn, sq, left)
                if d >= 0:
                    line += f" PIECE CONDITION IF {square_text(sq)} MOVES {1 + d}"
                    p_done = True
                    break
        if not p_done:
            line += " PIECE CONDITION ELSE"

        # Side condition
        s_done = False
        for sq in squares:
            if left >= 0:
                d = side_distance(after, after.turn, sq, GoalCondition.COND_REACH, left)
                if d >= 0:
                    line += f" SIDE CONDITION IF {square_text(sq)} MOVES {1 + d}"
                    s_done = True
                    break
        if not s_done:
            line += " SIDE CONDITION ELSE"

        lines.append(line)

    lines.append("GOAL MARKS END\n")
    return "\n".join(lines)


def goal_marks_after(board: Board, goal: Goal, move: Move) -> str:
    """Marks progress after proposed move."""
    if not legal_move(board, move):
        raise ValueError("Cannot report an illegal move")
    after = board.clone()
    pass_play(after, move, board.turn)
    squares = goal_squares(goal, after, after.turn)
    lines = [f"GOAL MARKS AFTER {move.uci} GOAL {goal_text(goal)} LIMIT {goal.limit} PASS"]

    for sq in squares:
        if goal_holds(after, after.turn, sq, GoalCondition.COND_REACH):
            lines.append(f"REACHED {square_text(sq)} 1")

    moves = pass_moves(after, after.turn)
    for n in moves:
        next_b = after.clone()
        pass_play(next_b, n, after.turn)
        at = square_text(square_index(n.sr, n.sc))
        line = f"MARK {after.grid[n.sr][n.sc].type} {at} {n.uci}"

        p_done = False
        left = goal.limit - 2
        for sq in squares:
            if left >= 0:
                d = piece_distance(next_b, n.er, n.ec, after.turn, sq, left)
                if d >= 0:
                    line += f" PIECE CONDITION IF {square_text(sq)} MOVES {2 + d}"
                    p_done = True
                    break
        if not p_done:
            line += " PIECE CONDITION ELSE"

        s_done = False
        for sq in squares:
            if left >= 0:
                d = side_distance(next_b, after.turn, sq, GoalCondition.COND_REACH, left)
                if d >= 0:
                    line += f" SIDE CONDITION IF {square_text(sq)} MOVES {2 + d}"
                    s_done = True
                    break
        if not s_done:
            line += " SIDE CONDITION ELSE"

        lines.append(line)

    lines.append("GOAL MARKS END\n")
    return "\n".join(lines)


def distance_lines(board: Board, r: int, c: int, label: str) -> List[str]:
    """Generates distance order lines for piece on (r, c)."""
    if not in_bounds(r, c):
        return []
    view = board.clone()
    view.turn = board.grid[r][c].color
    all_moves = sorted_moves(view)
    piece_moves = [m for m in all_moves if m.sr == r and m.sc == c]
    if not piece_moves:
        return [f"NO-MOVES{label[4:]}"]

    distances = [move_distance(m) for m in piece_moves]
    lines = []
    for d in range(1, 8):
        for idx, m in enumerate(piece_moves):
            if distances[idx] != d:
                continue
            line = f"{label} {m.uci} DISTANCE {d} ORDER {order_label(distances, d)}"
            ptype = board.grid[r][c].type
            if ptype == 'N':
                line += " JUMP"
            elif ptype == 'K' and m.sr == m.er and abs(m.ec - m.sc) == 2:
                is_ks = (m.ec > m.sc)
                rf = square_text(square_index(r, 7 if is_ks else 0))
                rt = square_text(square_index(r, 5 if is_ks else 3))
                line += f" CASTLE {rf}{rt}"
            lines.append(line)
    return lines


def distance_selection(board: Board, r: int, c: int) -> str:
    """DISTANCE ORDER report for one selected piece."""
    if not in_bounds(r, c):
        return "DISTANCE ORDER END\n"
    at = square_text(square_index(r, c))
    lines = [f"DISTANCE ORDER {board.grid[r][c].type} {at}"]
    lines.extend(distance_lines(board, r, c, "MOVE"))
    lines.append("DISTANCE ORDER END\n")
    return "\n".join(lines)


def distance_after(board: Board, move: Move) -> str:
    """DISTANCE ORDER for every piece after a legal move is applied."""
    if not legal_move(board, move):
        raise ValueError("Cannot report an illegal move")
    after = board.clone()
    make_move(after, move)
    lines = [f"DISTANCE ORDER AFTER {move.uci}"]
    for side in (WHITE, BLACK):
        for i in range(TOTAL_SQUARES):
            r, c = i // BOARD_SIZE, i % BOARD_SIZE
            if after.grid[r][c].color == side:
                at = square_text(i)
                label = f"MOVE {color_name(side)} {after.grid[r][c].type} {at}"
                lines.extend(distance_lines(after, r, c, label))
    lines.append("DISTANCE ORDER END\n")
    return "\n".join(lines)


def support_report(board: Board, move: Move) -> str:
    """Generates Stage 3D SUPPORT report."""
    if not legal_move(board, move):
        raise ValueError("Cannot report an illegal move")
    side = board.turn
    enemy = opposite(side)
    after = board.clone()
    pass_play(after, move, side)
    sq = square_index(move.er, move.ec)
    ptype = after.grid[move.er][move.ec].type
    at = square_text(sq)

    lines = [
        f"SUPPORT BEGIN {move.uci} PASS",
        f"NOTE PASS is hypothetical: {color_name(side)} moves again, {color_name(enemy)} passes",
        f"SUPPORT NOW {ptype} {at} PROTECTORS {pieces_on_square(after, sq, side)}"
    ]

    # --- FOLLOW moves: other pieces that newly attack the landing square ---
    follows = 0
    moves = pass_moves(after, side)
    for f in moves:
        if f.sr == move.er and f.sc == move.ec:
            continue
        next_b = after.clone()
        pass_play(next_b, f, side)
        if next_b.grid[move.er][move.ec].color != side:
            continue

        before_att = piece_attacks(after, f.sr, f.sc, move.er, move.ec)
        now_att = piece_attacks(next_b, f.er, f.ec, move.er, move.ec)
        if now_att and not before_att:
            from_sq = square_text(square_index(f.sr, f.sc))
            ftype = after.grid[f.sr][f.sc].type
            prots = pieces_on_square(next_b, sq, side)
            lines.append(f"FOLLOW {f.uci} {ftype} {from_sq} PROTECTS {ptype} {at} PROTECTORS {prots}")
            follows += 1

    lines.append(f"SUMMARY FOLLOWS {follows}")
    lines.append("SUPPORT END\n")
    return "\n".join(lines)
