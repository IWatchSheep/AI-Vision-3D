"""Position keys used for repetition draws."""

from typing import TYPE_CHECKING, Optional

from .constants import BOARD_SIZE, WHITE, in_bounds

if TYPE_CHECKING:
    from .board import Board


def position_key(board: "Board") -> str:
    """Position identity, including EP only when a pawn can legally capture."""
    from .movegen import legal_move
    from .move import Move

    chars = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            chars.append(board.grid[r][c].key_char)

    chars.append("W" if board.turn == WHITE else "B")
    chars.append(
        "1" if (not board.white_king_moved and not board.white_rook_a_moved) else "0"
    )
    chars.append(
        "1" if (not board.white_king_moved and not board.white_rook_h_moved) else "0"
    )
    chars.append(
        "1" if (not board.black_king_moved and not board.black_rook_a_moved) else "0"
    )
    chars.append(
        "1" if (not board.black_king_moved and not board.black_rook_h_moved) else "0"
    )

    legal_ep = False
    if in_bounds(board.ep_row, board.ep_col):
        dir_step = 1 if board.turn == WHITE else -1
        starting_row = board.ep_row + dir_step
        for delta_col in (-1, 1):
            sc = board.ep_col + delta_col
            if in_bounds(starting_row, sc):
                pawn = board.grid[starting_row][sc]
                if pawn.type != "P" or pawn.color != board.turn:
                    continue
                candidate = Move(
                    sr=starting_row, sc=sc, er=board.ep_row, ec=board.ep_col
                )
                if legal_move(board, candidate):
                    legal_ep = True
                    break

    if legal_ep:
        chars.append(str(board.ep_row))
        chars.append(str(board.ep_col))
    else:
        chars.append("-")

    return "".join(chars)


def repetition_count(board: "Board", key: Optional[str] = None) -> int:
    """How many times key (or the current position) appears in history."""
    target_key = key if key is not None else position_key(board)
    return board.history.count(target_key)
