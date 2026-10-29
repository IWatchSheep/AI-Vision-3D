"""Whether pieces attack squares, and whether a king is in check.

These are geometric rules only — they do not know about pins or legality.
Move generation combines this with pseudo_legal / legal_move elsewhere.
"""

from typing import Optional, Tuple, TYPE_CHECKING

from .constants import (
    BOARD_SIZE, Color, WHITE, BLACK,
    MAX_SLIDE_STEPS,
    in_bounds, opposite,
)

if TYPE_CHECKING:
    from .board import Board


def pawn_direction(color: Color) -> int:
    """Returns step direction for pawn movement: -1 for White, +1 for Black."""
    return -1 if color == WHITE else 1


def is_knight_move(dr: int, dc: int) -> bool:
    """Checks whether (dr, dc) matches an L-shaped knight jump."""
    r, c = abs(dr), abs(dc)
    return (r == 2 and c == 1) or (r == 1 and c == 2)


def is_diagonal_move(dr: int, dc: int) -> bool:
    """Checks whether (dr, dc) is diagonal."""
    return abs(dr) == abs(dc)


def is_straight_move(dr: int, dc: int) -> bool:
    """Checks whether (dr, dc) is orthogonal (along rank or file)."""
    return dr == 0 or dc == 0


def is_queen_move(dr: int, dc: int) -> bool:
    """Checks whether (dr, dc) is straight or diagonal."""
    return is_straight_move(dr, dc) or is_diagonal_move(dr, dc)


def path_clear(board: 'Board', sr: int, sc: int, er: int, ec: int) -> bool:
    """True if every square strictly between start and end is empty.

    Only works for rook/bishop/queen rays (straight or diagonal).
    Caps steps so a bad step vector cannot loop forever.
    """
    if not in_bounds(sr, sc) or not in_bounds(er, ec):
        return False
    if sr == er and sc == ec:
        return False

    step_r = 0 if er == sr else (1 if er > sr else -1)
    step_c = 0 if ec == sc else (1 if ec > sc else -1)

    delta_r = abs(er - sr)
    delta_c = abs(ec - sc)
    straight = step_r == 0 or step_c == 0
    diagonal = delta_r == delta_c
    if not straight and not diagonal:
        return False

    curr_r = sr + step_r
    curr_c = sc + step_c
    for _ in range(MAX_SLIDE_STEPS):
        if curr_r == er and curr_c == ec:
            return True
        if not in_bounds(curr_r, curr_c):
            return False
        if not board.grid[curr_r][curr_c].is_empty:
            return False
        curr_r += step_r
        curr_c += step_c

    return False


def piece_attacks(board: 'Board', sr: int, sc: int, tr: int, tc: int) -> bool:
    """Determines whether a piece on (sr, sc) attacks target square (tr, tc)."""
    if not in_bounds(sr, sc) or not in_bounds(tr, tc):
        return False

    p = board.grid[sr][sc]
    if p.is_empty:
        return False
    if sr == tr and sc == tc:
        return False

    dr = tr - sr
    dc = tc - sc

    # Dispatch by piece type (same ray rules as move generation uses).
    ptype = p.type
    if ptype == 'P':
        return abs(dc) == 1 and dr == pawn_direction(p.color)
    elif ptype == 'N':
        return is_knight_move(dr, dc)
    elif ptype == 'B':
        return is_diagonal_move(dr, dc) and path_clear(board, sr, sc, tr, tc)
    elif ptype == 'R':
        return is_straight_move(dr, dc) and path_clear(board, sr, sc, tr, tc)
    elif ptype == 'Q':
        return is_queen_move(dr, dc) and path_clear(board, sr, sc, tr, tc)
    elif ptype == 'K':
        return abs(dr) <= 1 and abs(dc) <= 1
    return False


def square_attacked(board: 'Board', r: int, c: int, by: Color) -> bool:
    """Determines whether square (r, c) is attacked by any piece of color `by`."""
    if not in_bounds(r, c):
        return False
    for check_r in range(BOARD_SIZE):
        for check_c in range(BOARD_SIZE):
            attacker = board.grid[check_r][check_c]
            if attacker.color == by:
                if piece_attacks(board, check_r, check_c, r, c):
                    return True
    return False


def count_attackers(board: 'Board', r: int, c: int, by: Color) -> int:
    """Counts how many pieces of color `by` attack square (r, c)."""
    if not in_bounds(r, c):
        return 0
    attackers = 0
    for cr in range(BOARD_SIZE):
        for cc in range(BOARD_SIZE):
            if board.grid[cr][cc].color == by and piece_attacks(board, cr, cc, r, c):
                attackers += 1
    return attackers


def find_king(board: 'Board', side: Color) -> Optional[Tuple[int, int]]:
    """Locates the King of the specified color on the board."""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board.grid[r][c]
            if p.type == 'K' and p.color == side:
                return r, c
    return None


def has_king(board: 'Board', side: Color) -> bool:
    """Returns True if the specified side has a King on the board."""
    return find_king(board, side) is not None


def is_in_check(board: 'Board', side: Color) -> bool:
    """Checks whether the King of the specified side is currently under attack."""
    pos = find_king(board, side)
    if not pos:
        return False
    return square_attacked(board, pos[0], pos[1], opposite(side))
