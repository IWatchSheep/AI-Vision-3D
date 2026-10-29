"""Apply moves to the board and update clocks, turn, and castling flags.

apply_move_to_board only moves pieces on the grid; make_move is the full
"play this move" entry point used by the game and simulations.
"""

from typing import List, TYPE_CHECKING

from .constants import (
    Color, WHITE, BLACK,
    PROMOTION_PIECES,
    KING_START_COL,
    CASTLE_KINGSIDE_KING_DEST_COL, CASTLE_QUEENSIDE_KING_DEST_COL,
    CASTLE_KINGSIDE_ROOK_DEST_COL, CASTLE_QUEENSIDE_ROOK_DEST_COL,
    in_bounds, opposite, home_row_for, rook_col_for,
)
from .piece import Piece, empty_piece
from .move import Move

if TYPE_CHECKING:
    from .board import Board


def _castling_path_clear(board: 'Board', move: Move, piece: Piece) -> bool:
    """True when castling geometry is safe to apply on the grid.

    Checks home squares, empty path, and a friendly corner rook. Does not
    re-check castling *rights* — make_move may already have marked the king
    moved before calling apply_move_to_board.
    """
    home = home_row_for(piece.color)
    king_side = move.ec > move.sc
    dest_col = (
        CASTLE_KINGSIDE_KING_DEST_COL if king_side else CASTLE_QUEENSIDE_KING_DEST_COL
    )
    if (
        move.sr != home
        or move.er != home
        or move.sc != KING_START_COL
        or move.ec != dest_col
    ):
        return False

    rook_from_col = rook_col_for(king_side)
    rook = board.grid[move.sr][rook_from_col]
    if rook.type != "R" or rook.color != piece.color:
        return False

    first_empty = 5 if king_side else 1
    last_empty = 6 if king_side else 3
    for col in range(first_empty, last_empty + 1):
        if not board.grid[move.sr][col].is_empty:
            return False
    return True


def apply_move_to_board(board: 'Board', move: Move) -> None:
    """Update only the piece grid for this move (EP, castle rook, promote).

    Does not change turn, clocks, or castling flags — make_move does that.
    Empty start squares are ignored so a bad call cannot wipe the destination.
    A two-square king move needs a clear castling path and a corner rook;
    otherwise the board is left unchanged (no king teleport / piece overwrite).
    """
    from .move_legality import move_is_en_passant

    if not in_bounds(move.sr, move.sc) or not in_bounds(move.er, move.ec):
        return

    piece = board.grid[move.sr][move.sc]
    if piece.is_empty:
        return

    target = board.grid[move.er][move.ec]
    # Refuse own-piece overwrite / king capture (defensive; legal_move already blocks these).
    if target.color == piece.color or target.type == "K":
        return

    # En passant: remove the pawn that was jumped past.
    if move_is_en_passant(board, move, piece):
        if in_bounds(move.sr, move.ec):
            board.grid[move.sr][move.ec] = empty_piece()

    # Castling: slide the rook only when the path and corner rook look valid.
    if piece.type == "K" and move.sr == move.er and abs(move.ec - move.sc) == 2:
        if not _castling_path_clear(board, move, piece):
            return
        king_side = move.ec > move.sc
        rook_from_col = rook_col_for(king_side)
        rook_to_col = (
            CASTLE_KINGSIDE_ROOK_DEST_COL if king_side else CASTLE_QUEENSIDE_ROOK_DEST_COL
        )
        rook = board.grid[move.sr][rook_from_col]
        board.grid[move.sr][rook_to_col] = rook
        board.grid[move.sr][rook_from_col] = empty_piece()

    board.grid[move.sr][move.sc] = empty_piece()
    board.grid[move.er][move.ec] = piece

    # Pawn on last rank becomes the chosen piece. Only Q/R/B/N are allowed;
    # anything else (including a missing letter) falls back to Queen so a
    # bad caller cannot write an illegal piece letter onto the board.
    if piece.type == "P" and move.er in (0, 7):
        promo_type = (
            move.promotion if move.promotion in PROMOTION_PIECES else "Q"
        )
        board.grid[move.er][move.ec] = Piece(type=promo_type, color=piece.color)


def mark_rook_at_home_square(board: 'Board', row: int, col: int, side: Color) -> None:
    """Revokes castling rights if a rook moves or is captured on its home square."""
    home_row = home_row_for(side)
    if row != home_row or (col != 0 and col != 7):
        return
    is_kingside = (col == 7)
    if side == WHITE:
        if is_kingside:
            board.white_rook_h_moved = True
        else:
            board.white_rook_a_moved = True
    else:
        if is_kingside:
            board.black_rook_h_moved = True
        else:
            board.black_rook_a_moved = True


def update_castle_state(board: 'Board', piece: Piece, m: Move) -> None:
    """Updates the board's castling flags when a king or rook moves."""
    # Castling counts as moving both king and the touched rook.
    if piece.type == 'K' and m.sr == m.er and abs(m.ec - m.sc) == 2:
        is_ks = m.is_kingside_castle
        if piece.color == WHITE:
            if is_ks: board.white_rook_h_moved = True
            else: board.white_rook_a_moved = True
        else:
            if is_ks: board.black_rook_h_moved = True
            else: board.black_rook_a_moved = True

    if piece.type == 'K':
        if piece.color == WHITE:
            board.white_king_moved = True
        else:
            board.black_king_moved = True

    if piece.type == 'R':
        mark_rook_at_home_square(board, m.sr, m.sc, piece.color)


def make_move(board: 'Board', m: Move, *, record_history: bool = False) -> None:
    """Play move on the board: pieces, castling rights, EP, clocks, turn.

    Illegal moves are ignored without changing any game state. Promotion
    requires an explicit Q/R/B/N, just as it does in legal_move.
    Set record_history for simulations that need repetition adjudication.
    The CLI records finalized moves separately.
    """
    from .move_legality import legal_move, move_is_en_passant

    if not legal_move(board, m):
        return

    piece = board.grid[m.sr][m.sc]
    if piece.is_empty or piece.color != board.turn:
        return

    target = board.grid[m.er][m.ec]
    # Never capture own pieces or overwrite a king (guards buggy callers).
    if target.color == piece.color or target.type == "K":
        return

    # Castling-shaped king move: require the corner rook before touching flags
    # or the grid (otherwise a bad caller could teleport the king alone).
    if piece.type == "K" and m.sr == m.er and abs(m.ec - m.sc) == 2:
        rook = board.grid[m.sr][rook_col_for(m.ec > m.sc)]
        if rook.type != "R" or rook.color != piece.color:
            return

    pawn_move = piece.type == "P"
    capture = (not target.is_empty) or move_is_en_passant(board, m, piece)

    # Capturing a rook on its home square removes that castling right.
    if target.type == "R":
        mark_rook_at_home_square(board, m.er, m.ec, target.color)

    update_castle_state(board, piece, m)
    apply_move_to_board(board, m)

    # Double pawn push sets the en-passant target; anything else clears it.
    if pawn_move and abs(m.er - m.sr) == 2:
        board.ep_row = (m.sr + m.er) // 2
        board.ep_col = m.sc
    else:
        board.ep_row = -1
        board.ep_col = -1

    # Pawn move or capture resets the 50-move clock and repetition list.
    if pawn_move or capture:
        board.halfmove_clock = 0
        board.history = []
    else:
        board.halfmove_clock += 1

    if board.turn == BLACK:
        board.fullmove_number += 1

    board.turn = opposite(board.turn)
    if record_history:
        board.record_position()


def consider_move(board: 'Board', moves: List[Move], sr: int, sc: int, er: int, ec: int) -> None:
    """Considers candidate move from (sr, sc) to (er, ec) and appends if legal.

    Promoting pawns must name Q/R/B/N; check each letter separately because a
    bare move without a promotion letter is never legal on the last rank.
    """
    from .move_legality import legal_move

    if not in_bounds(sr, sc) or not in_bounds(er, ec):
        return

    # Last-rank pawn: letter is part of the move — try each promotion.
    if board.grid[sr][sc].type == "P" and er in (0, 7):
        for promo in ("Q", "R", "B", "N"):
            m = Move(sr=sr, sc=sc, er=er, ec=ec, promotion=promo)
            if legal_move(board, m):
                moves.append(m)
        return

    m = Move(sr=sr, sc=sc, er=er, ec=ec)
    if legal_move(board, m):
        moves.append(m)
