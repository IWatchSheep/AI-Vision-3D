"""PASS-mode goal marks for a selected piece or after a previewed move."""

from ..search_budget import bounded_search
from ..constants import in_bounds, square_index, square_text
from ..move import Move
from ..board import Board
from ..movegen import sorted_moves, legal_move
from .common import Goal, GoalCondition, pass_moves, pass_play
from .goal_basics import (
    goal_squares, goal_text, goal_holds, piece_distance, side_distance,
)


def _piece_side_conditions(line: str, after: Board, er: int, ec: int, side, squares, left: int, base: int) -> str:
    """Append PIECE CONDITION and SIDE CONDITION text for one candidate move."""
    p_done = False
    for sq in squares:
        if left >= 0:
            d = piece_distance(after, er, ec, side, sq, left)
            if d >= 0:
                line += f" PIECE CONDITION IF {square_text(sq)} MOVES {base + d}"
                p_done = True
                break
    if not p_done:
        line += " PIECE CONDITION ELSE"

    s_done = False
    for sq in squares:
        if left >= 0:
            d = side_distance(after, side, sq, GoalCondition.COND_REACH, left)
            if d >= 0:
                line += f" SIDE CONDITION IF {square_text(sq)} MOVES {base + d}"
                s_done = True
                break
    if not s_done:
        line += " SIDE CONDITION ELSE"
    return line


@bounded_search
def goal_marks_selection(board: Board, goal: Goal, r: int, c: int) -> str:
    """Marks destinations of selected piece according to goal progress."""
    if not in_bounds(r, c):
        return "GOAL MARKS END\n"
    squares = goal_squares(goal, board, board.turn)
    at = square_text(square_index(r, c))
    lines = [
        f"GOAL MARKS {board.grid[r][c].type} {at} "
        f"GOAL {goal_text(goal)} LIMIT {goal.limit} PASS"
    ]

    for m in sorted_moves(board):
        if m.sr != r or m.sc != c:
            continue
        after = board.clone()
        pass_play(after, m, board.turn)
        line = _piece_side_conditions(
            f"MARK {m.uci}", after, m.er, m.ec, after.turn, squares, goal.limit - 1, 1
        )
        lines.append(line)

    lines.append("GOAL MARKS END\n")
    return "\n".join(lines)


@bounded_search
def goal_marks_after(board: Board, goal: Goal, move: Move) -> str:
    """Marks progress after proposed move."""
    if not legal_move(board, move):
        raise ValueError("Cannot report an illegal move")
    after = board.clone()
    pass_play(after, move, board.turn)
    squares = goal_squares(goal, after, after.turn)
    lines = [
        f"GOAL MARKS AFTER {move.uci} GOAL {goal_text(goal)} LIMIT {goal.limit} PASS"
    ]

    for sq in squares:
        if goal_holds(after, after.turn, sq, GoalCondition.COND_REACH):
            lines.append(f"REACHED {square_text(sq)} 1")

    for n in pass_moves(after, after.turn):
        next_b = after.clone()
        pass_play(next_b, n, after.turn)
        at = square_text(square_index(n.sr, n.sc))
        line = _piece_side_conditions(
            f"MARK {after.grid[n.sr][n.sc].type} {at} {n.uci}",
            next_b,
            n.er,
            n.ec,
            after.turn,
            squares,
            goal.limit - 2,
            2,
        )
        lines.append(line)

    lines.append("GOAL MARKS END\n")
    return "\n".join(lines)
