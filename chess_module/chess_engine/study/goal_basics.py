"""Goal squares, parsing, PASS distances, and hold checks.

PASS mode (used here) means only the side to move plays; the opponent always
passes. Distances count those hypothetical half-moves, not a real game turn
sequence. REAL-mode search lives in goal_routes_real.
"""

from ..search_budget import bounded_search

from typing import List, Optional

from ..constants import (
    BOARD_SIZE, TOTAL_SQUARES,
    Color,
    GOAL_MAX_SQUARES, GOAL_MAX_LIMIT,
    in_bounds, opposite, square_index, square_text, parse_square,
)
from ..board import Board
from ..movegen import find_king
from .common import (
    Goal, GoalCondition,
    pass_moves, pass_play, pieces_on_square,
)


def goal_squares(goal: Goal, board: Board, side: Color) -> List[int]:
    """Resolves target square indices for a goal."""
    if (not isinstance(goal.limit, int) or isinstance(goal.limit, bool)
            or not 1 <= goal.limit <= GOAL_MAX_LIMIT):
        raise ValueError(f"goal limit must be between 1 and {GOAL_MAX_LIMIT}")
    if (not isinstance(goal.count, int) or isinstance(goal.count, bool)
            or not 0 <= goal.count <= GOAL_MAX_SQUARES
            or goal.count > len(goal.squares)):
        raise ValueError("invalid goal square count")
    if any(not isinstance(sq, int) or isinstance(sq, bool)
           or not 0 <= sq < TOTAL_SQUARES for sq in goal.squares[:goal.count]):
        raise ValueError("invalid goal square")
    if not goal.king:
        return list(goal.squares[:goal.count])

    enemy = opposite(side)
    kpos = find_king(board, enemy)
    if not kpos:
        return []
    kr, kc = kpos
    squares = []
    for r in range(kr - 1, kr + 2):
        for c in range(kc - 1, kc + 2):
            if in_bounds(r, c) and (r != kr or c != kc):
                squares.append(r * BOARD_SIZE + c)
    return squares


def goal_text(goal: Goal) -> str:
    """Formats goal description."""
    if goal.king:
        return "king"
    return " ".join(square_text(sq) for sq in goal.squares[:goal.count])


def goal_holds(board: Board, side: Color, sq: int, cond: GoalCondition) -> bool:
    """Checks whether a goal condition currently holds on square sq."""
    if not isinstance(sq, int) or isinstance(sq, bool) or sq < 0 or sq >= TOTAL_SQUARES:
        return False
    r, c = sq // BOARD_SIZE, sq % BOARD_SIZE
    if board.grid[r][c].color != side:
        return False
    if cond == GoalCondition.COND_REACH:
        return True
    return pieces_on_square(board, sq, side) > 0


@bounded_search
def piece_distance(board: Board, r: int, c: int, side: Color, sq: int, max_depth: int) -> int:
    """Shortest number of moves for piece on (r, c) alone to reach sq."""
    _require_pass_depth(max_depth)
    if not isinstance(sq, int) or isinstance(sq, bool) or not 0 <= sq < TOTAL_SQUARES:
        return -1
    if not in_bounds(r, c) or board.grid[r][c].color != side:
        return -1
    if r * BOARD_SIZE + c == sq:
        return 0
    if max_depth <= 0:
        return -1

    best = -1
    moves = pass_moves(board, side)

    # 1-ply check first
    for m in moves:
        if m.sr == r and m.sc == c and (m.er * BOARD_SIZE + m.ec == sq):
            return 1

    # Recursive check
    for m in moves:
        if m.sr != r or m.sc != c:
            continue
        next_b = board.clone()
        pass_play(next_b, m, side)
        rem_max = (max_depth - 1) if best == -1 else (best - 2)
        if rem_max < 0:
            continue
        d = piece_distance(next_b, m.er, m.ec, side, sq, rem_max)
        if d >= 0 and (best == -1 or d + 1 < best):
            best = d + 1

    return best


def _require_pass_depth(depth: int) -> None:
    if (not isinstance(depth, int) or isinstance(depth, bool)
            or not 0 <= depth <= GOAL_MAX_LIMIT):
        raise ValueError(f"depth must be between 0 and {GOAL_MAX_LIMIT}")


@bounded_search
def side_within(board: Board, side: Color, sq: int, cond: GoalCondition, depth: int) -> bool:
    """Checks if any team piece can satisfy goal on sq within depth moves."""
    _require_pass_depth(depth)
    if not isinstance(sq, int) or isinstance(sq, bool) or not 0 <= sq < TOTAL_SQUARES:
        return False
    if goal_holds(board, side, sq, cond):
        return True
    if depth <= 0:
        return False

    moves = pass_moves(board, side)
    for m in moves:
        next_b = board.clone()
        pass_play(next_b, m, side)
        if side_within(next_b, side, sq, cond, depth - 1):
            return True
    return False


@bounded_search
def side_distance(board: Board, side: Color, sq: int, cond: GoalCondition, max_depth: int) -> int:
    """Shortest number of moves for any team pieces to satisfy goal on sq."""
    _require_pass_depth(max_depth)
    if not isinstance(sq, int) or isinstance(sq, bool) or not 0 <= sq < TOTAL_SQUARES:
        return -1
    for d in range(max_depth + 1):
        if side_within(board, side, sq, cond, d):
            return d
    return -1


def parse_goal(text: str) -> Optional[Goal]:
    """Parses 'f7 2', 'f7 g7 3', or 'king 2'.

    Squares (or 'king') come first; the final token is the move limit 1..4.
    Once the limit appears, no further tokens are allowed.
    """
    if not isinstance(text, str):
        return None
    tokens = text.strip().split()
    if not tokens:
        return None

    g = Goal()
    limit_set = False
    for tok in tokens:
        # After the limit is set, any extra token is a parse error.
        if limit_set:
            return None

        if tok == "king" and g.count == 0 and not g.king:
            g.king = True
        elif len(tok) == 2 and not g.king:
            parsed = parse_square(tok)
            if not parsed or g.count >= GOAL_MAX_SQUARES:
                return None
            sq = square_index(parsed[0], parsed[1])
            # square_index returns -1 when out of bounds; never store that.
            if sq < 0 or sq in g.squares:
                return None
            g.squares.append(sq)
            g.count += 1
        elif tok.isascii() and tok.isdigit() and (g.count > 0 or g.king):
            # Limit is 1..4 — reject long / non-ASCII digit strings before int().
            if len(tok) > 2:
                return None
            val = int(tok, 10)
            if 1 <= val <= GOAL_MAX_LIMIT:
                g.limit = val
                limit_set = True
            else:
                return None
        else:
            return None

    # Default limit stays 1 when the user omits it (Goal.limit default).
    # An explicit limit still locks the parse so "f7 1 g7" is rejected.
    if g.count == 0 and not g.king:
        return None

    g.active = True
    return g
