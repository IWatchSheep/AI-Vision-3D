"""Build every legal move for the side to move and detect mate/stalemate.

Each candidate destination is passed through consider_move, which only
appends moves that pass legal_move (including the no-self-check rule).
"""

from typing import List, Optional, Tuple, TYPE_CHECKING

from .constants import BOARD_SIZE, Color, in_bounds
from .move import Move
from .attacks import is_in_check
from .move_rules import consider_move

if TYPE_CHECKING:
    from .board import Board


def generate_sliding_moves(board: 'Board', moves: List[Move], row: int, col: int, directions: List[Tuple[int, int]]) -> None:
    """Generates sliding moves along rays."""
    if not in_bounds(row, col):
        return
    for dr, dc in directions:
        if (not isinstance(dr, int) or isinstance(dr, bool)
                or not isinstance(dc, int) or isinstance(dc, bool)
                or dr not in (-1, 0, 1) or dc not in (-1, 0, 1)
                or (dr == 0 and dc == 0)):
            raise ValueError("Sliding directions must be nonzero unit steps")
        for step in range(1, BOARD_SIZE):
            er = row + dr * step
            ec = col + dc * step
            if not in_bounds(er, ec):
                break
            consider_move(board, moves, row, col, er, ec)
            if not board.grid[er][ec].is_empty:
                break


def generate_pawn_moves(board: 'Board', moves: List[Move], row: int, col: int) -> None:
    """Generates all candidate moves for the pawn at (row, col)."""
    if not in_bounds(row, col):
        return
    from .attacks import pawn_direction
    d = pawn_direction(board.grid[row][col].color)
    consider_move(board, moves, row, col, row + d, col)
    consider_move(board, moves, row, col, row + 2 * d, col)
    consider_move(board, moves, row, col, row + d, col - 1)
    consider_move(board, moves, row, col, row + d, col + 1)


def generate_knight_moves(board: 'Board', moves: List[Move], row: int, col: int) -> None:
    """Generates knight jumps."""
    if not in_bounds(row, col):
        return
    jumps = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    for dr, dc in jumps:
        consider_move(board, moves, row, col, row + dr, col + dc)


def generate_king_moves(board: 'Board', moves: List[Move], row: int, col: int) -> None:
    """Generates king moves and castling."""
    if not in_bounds(row, col):
        return
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            consider_move(board, moves, row, col, row + dr, col + dc)

    consider_move(board, moves, row, col, row, col + 2)
    consider_move(board, moves, row, col, row, col - 2)


def generate_piece_moves(board: 'Board', moves: List[Move], row: int, col: int) -> None:
    """Generates all legal moves for a piece at (row, col)."""
    if not in_bounds(row, col):
        return
    ptype = board.grid[row][col].type
    if ptype == 'P':
        generate_pawn_moves(board, moves, row, col)
    elif ptype == 'N':
        generate_knight_moves(board, moves, row, col)
    elif ptype == 'B':
        generate_sliding_moves(board, moves, row, col, [(-1, -1), (-1, 1), (1, -1), (1, 1)])
    elif ptype == 'R':
        generate_sliding_moves(board, moves, row, col, [(-1, 0), (1, 0), (0, -1), (0, 1)])
    elif ptype == 'Q':
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        generate_sliding_moves(board, moves, row, col, directions)
    elif ptype == 'K':
        generate_king_moves(board, moves, row, col)


def generate_moves(board: 'Board') -> List[Move]:
    """Generates all legal moves for the player whose turn it currently is."""
    moves: List[Move] = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board.grid[r][c].color == board.turn:
                generate_piece_moves(board, moves, r, c)
    return moves


def sorted_moves(board: 'Board') -> List[Move]:
    """Generates and canonically sorts all legal moves."""
    moves = generate_moves(board)
    moves.sort()
    return moves


def legal_destination_map(board: 'Board', row: int, col: int, side_to_move: Color) -> List[List[bool]]:
    """Returns an 8x8 matrix: [r][c] is True if the piece can legally move to (r, c)."""
    destinations = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    if (
        not in_bounds(row, col)
        or board.grid[row][col].is_empty
        or board.grid[row][col].color != side_to_move
    ):
        return destinations

    # Clone so we can ask "what if it were side_to_move's turn?" without mutating.
    view = board.clone()
    view.turn = side_to_move
    moves: List[Move] = []
    generate_piece_moves(view, moves, row, col)
    for m in moves:
        if m.sr == row and m.sc == col:
            destinations[m.er][m.ec] = True
    return destinations


def game_over(board: 'Board') -> Tuple[bool, bool, Optional[str]]:
    """Determines if the game has ended.
    Returns: (is_game_over, is_stalemate, draw_reason)
    """
    # 1. No legal moves → checkmate or stalemate.
    moves = generate_moves(board)
    if len(moves) == 0:
        in_chk = is_in_check(board, board.turn)
        if in_chk:
            return True, False, None  # Checkmate
        else:
            return True, True, None   # Stalemate

    # 2. Otherwise check FIDE automatic draws (75-move, fivefold, dead position).
    auto_draw, reason = board.automatic_draw()
    if auto_draw:
        return True, False, reason

    return False, False, None
