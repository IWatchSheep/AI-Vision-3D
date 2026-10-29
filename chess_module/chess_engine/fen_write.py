"""Write a Board as a FEN string."""

from typing import TYPE_CHECKING

from .constants import BOARD_SIZE, WHITE, BLACK, in_bounds

if TYPE_CHECKING:
    from .board import Board


def board_to_fen(board: "Board") -> str:
    """Serializes board state into FEN notation."""
    parts = []
    # 1. Piece placement
    placement = []
    for r in range(BOARD_SIZE):
        empty_count = 0
        row_chars = []
        for c in range(BOARD_SIZE):
            p = board.grid[r][c]
            if p.is_empty:
                empty_count += 1
            else:
                if empty_count > 0:
                    row_chars.append(str(empty_count))
                    empty_count = 0
                row_chars.append(p.symbol)
        if empty_count > 0:
            row_chars.append(str(empty_count))
        placement.append("".join(row_chars))
    parts.append("/".join(placement))

    # 2. Side to move
    parts.append("w" if board.turn == WHITE else "b")

    # 3. Castling rights
    castling = []
    if not board.white_king_moved and not board.white_rook_h_moved:
        castling.append("K")
    if not board.white_king_moved and not board.white_rook_a_moved:
        castling.append("Q")
    if not board.black_king_moved and not board.black_rook_h_moved:
        castling.append("k")
    if not board.black_king_moved and not board.black_rook_a_moved:
        castling.append("q")
    parts.append("".join(castling) if castling else "-")

    # 4. En passant target square
    if in_bounds(board.ep_row, board.ep_col):
        parts.append(f"{chr(ord('a') + board.ep_col)}{8 - board.ep_row}")
    else:
        parts.append("-")

    # 5. Halfmove clock
    parts.append(str(board.halfmove_clock))

    # 6. Fullmove number
    parts.append(str(board.fullmove_number))

    return " ".join(parts)

