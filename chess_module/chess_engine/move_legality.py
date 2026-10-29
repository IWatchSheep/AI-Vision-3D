"""Rules for whether a Move is allowed before it is played.

pseudo_legal = correct piece motion and captures; legal_move also forbids
leaving your own king in check (tested by applying the move on a clone).
"""

from typing import TYPE_CHECKING

from .constants import (
    Color, WHITE, BLACK,
    WHITE_PAWN_START_ROW, BLACK_PAWN_START_ROW,
    KING_START_COL, CASTLE_KINGSIDE_KING_DEST_COL, CASTLE_QUEENSIDE_KING_DEST_COL,
    CASTLE_KINGSIDE_ROOK_DEST_COL, CASTLE_QUEENSIDE_ROOK_DEST_COL,
    PROMOTION_PIECES,
    in_bounds, opposite, home_row_for, rook_col_for,
)
from .piece import Piece
from .move import Move
from .attacks import (
    pawn_direction, piece_attacks, square_attacked, is_in_check,
)

if TYPE_CHECKING:
    from .board import Board


def can_castle(board: 'Board', move: Move, side: Color) -> bool:
    """Validates whether the proposed castling move satisfies all chess rules."""
    if side not in (WHITE, BLACK):
        return False
    home_row = home_row_for(side)
    king_moved = board.white_king_moved if side == WHITE else board.black_king_moved
    enemy = opposite(side)
    castle_kingside = move.is_kingside_castle

    rook_col = rook_col_for(castle_kingside)
    # transit = square the king steps through; dest = where the king finishes.
    transit_col = CASTLE_KINGSIDE_ROOK_DEST_COL if castle_kingside else CASTLE_QUEENSIDE_ROOK_DEST_COL
    dest_col = CASTLE_KINGSIDE_KING_DEST_COL if castle_kingside else CASTLE_QUEENSIDE_KING_DEST_COL

    # 1. King path: correct start/end files and king must not have moved.
    # King must start on e-file home square and land on the castling destination.
    if (
        move.sr != home_row
        or move.er != home_row
        or move.sc != KING_START_COL
        or move.ec != dest_col
        or king_moved
    ):
        return False

    rook_moved = (
        (board.white_rook_h_moved if castle_kingside else board.white_rook_a_moved)
        if side == WHITE else
        (board.black_rook_h_moved if castle_kingside else board.black_rook_a_moved)
    )

    # 2. Rook present, unmoved, and squares between king and rook are empty.
    corner_piece = board.grid[home_row][rook_col]
    king = board.grid[home_row][KING_START_COL]
    if king.type != 'K' or king.color != side or is_in_check(board, side):
        return False
    if rook_moved or corner_piece.type != 'R' or corner_piece.color != side:
        return False

    first_empty = 5 if castle_kingside else 1
    last_empty = 6 if castle_kingside else 3
    for col in range(first_empty, last_empty + 1):
        if not board.grid[home_row][col].is_empty:
            return False

    # 3. King may not pass through or land on an attacked square.
    if square_attacked(board, home_row, transit_col, enemy) or \
       square_attacked(board, home_row, dest_col, enemy):
        return False

    return True


def move_is_en_passant(board: 'Board', move: Move, piece: Piece) -> bool:
    """Returns True if move made by piece is an en passant capture."""
    if piece.type != "P":
        return False
    if not in_bounds(move.sr, move.sc) or not in_bounds(move.er, move.ec):
        return False
    if not in_bounds(move.sr, move.ec):
        return False
    if (move.er - move.sr != pawn_direction(piece.color)
            or abs(move.ec - move.sc) != 1
            or move.sr != (3 if piece.color == WHITE else 4)):
        return False
    matches_ep = move.er == board.ep_row and move.ec == board.ep_col
    dest_empty = board.grid[move.er][move.ec].is_empty
    side_pawn = board.grid[move.sr][move.ec]
    enemy_pawn = side_pawn.type == "P" and side_pawn.color == opposite(piece.color)
    return matches_ep and dest_empty and enemy_pawn


def pawn_move_is_pseudo_legal(board: 'Board', move: Move, pawn: Piece, target: Piece) -> bool:
    """Validates the geometric rules for pawn moves."""
    direction = pawn_direction(pawn.color)
    starting_row = WHITE_PAWN_START_ROW if pawn.color == WHITE else BLACK_PAWN_START_ROW
    row_change = move.er - move.sr
    col_change = move.ec - move.sc

    # Straight forward
    if col_change == 0 and target.is_empty:
        if row_change == direction:
            return True
        intermediate_row = move.sr + direction
        if (
            row_change == 2 * direction
            and move.sr == starting_row
            and in_bounds(intermediate_row, move.sc)
            and board.grid[intermediate_row][move.sc].is_empty
        ):
            return True

    # Diagonal captures
    if abs(col_change) != 1 or row_change != direction:
        return False

    if not target.is_empty:
        return True

    # En passant
    if not in_bounds(move.sr, move.ec):
        return False
    return move_is_en_passant(board, move, pawn)


def king_move_is_pseudo_legal(board: 'Board', move: Move) -> bool:
    """Validates king motion: 1 square in any direction, or castling."""
    if piece_attacks(board, move.sr, move.sc, move.er, move.ec):
        return True

    is_two_horizontal = (move.sr == move.er and abs(move.ec - move.sc) == 2)
    if not is_two_horizontal:
        return False

    if is_in_check(board, board.turn):
        return False

    return can_castle(board, move, board.turn)


def promotion_is_valid(move: Move, piece: Piece) -> bool:
    """
    Promotion rules for a candidate move.

    A pawn that reaches the last rank must name Q, R, B, or N (FIDE: the
    choice is part of the move). Other pieces must not carry a promotion
    letter. Pawns that are not on the last rank also must not.
    """
    if not isinstance(move.promotion, str):
        return False
    has_promo = bool(move.promotion) and move.promotion != "\0"
    reached_end = move.er in (0, 7)

    if piece.type == "P" and reached_end:
        return move.promotion in PROMOTION_PIECES

    # Not a promoting pawn: any promotion letter is illegal.
    return not has_promo


def pseudo_legal(board: 'Board', m: Move) -> bool:
    """Checks whether move m is geometrically valid for the piece type."""
    if not in_bounds(m.sr, m.sc) or not in_bounds(m.er, m.ec):
        return False

    piece = board.grid[m.sr][m.sc]
    target = board.grid[m.er][m.ec]

    if piece.color != board.turn:
        return False
    if target.color == board.turn:
        return False
    if target.type == 'K':
        return False
    if not promotion_is_valid(m, piece):
        return False

    if piece.type == 'P':
        return pawn_move_is_pseudo_legal(board, m, piece, target)
    if piece.type == 'K':
        return king_move_is_pseudo_legal(board, m)

    return piece_attacks(board, m.sr, m.sc, m.er, m.ec)


def legal_move(board: 'Board', move: Move) -> bool:
    """Determines whether a move is fully legal in chess."""
    from .move_apply import apply_move_to_board

    if not isinstance(move, Move):
        return False
    if not pseudo_legal(board, move):
        return False

    # Simulate on a copy — moving must not expose our own king to check.
    after_move = board.clone()
    apply_move_to_board(after_move, move)
    return not is_in_check(after_move, board.turn)


def destination_is_legal(
    board: 'Board', sr: int, sc: int, er: int, ec: int
) -> bool:
    """
    True if some fully-specified legal move goes from (sr, sc) to (er, ec).

    For a pawn stepping onto the last rank, any of Q/R/B/N counts — the
    player still must pick the letter before the move is finalized.
    """
    if not in_bounds(sr, sc) or not in_bounds(er, ec):
        return False
    piece = board.grid[sr][sc]
    if piece.type == "P" and er in (0, 7):
        for promo in PROMOTION_PIECES:
            if legal_move(board, Move(sr=sr, sc=sc, er=er, ec=ec, promotion=promo)):
                return True
        return False
    return legal_move(board, Move(sr=sr, sc=sc, er=er, ec=ec))
