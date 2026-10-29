"""CALC header: move identity, captures, promotion, and ZERO lines."""

from typing import List

from ..constants import (
    BOARD_SIZE, CALC_MAX_ID,
    WHITE, BLACK,
    color_name, square_index, square_text,
)
from ..move import Move
from ..board import Board
from ..tracker import Tracker
from .calc_helpers import zero_move_cause


def header_lines(
    board: Board, tracker: Tracker, move: Move, captured: List[bool]
) -> List[str]:
    """Move, castle, captures, and promotion lines."""
    mover = board.grid[move.sr][move.sc]
    from_sq = square_text(square_index(move.sr, move.sc))
    to_sq = square_text(square_index(move.er, move.ec))
    lines = [
        f"CALC BEGIN {move.uci}",
        f"MOVED {color_name(mover.color)} {mover.type} {from_sq} {to_sq}",
    ]

    if mover.type == "K" and move.sr == move.er and abs(move.ec - move.sc) == 2:
        is_ks = move.is_kingside_castle
        rf = square_text(square_index(move.sr, 7 if is_ks else 0))
        rt = square_text(square_index(move.sr, 5 if is_ks else 3))
        lines.append(f"CASTLE {color_name(mover.color)} {rf} {rt}")

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            pid = tracker.grid[r][c]
            if 0 < pid < CALC_MAX_ID and captured[pid]:
                sq = square_text(square_index(r, c))
                lines.append(
                    f"CAPTURED {color_name(tracker.color[pid])} "
                    f"{board.grid[r][c].type} {sq}"
                )

    if mover.type == "P" and (move.er == 0 or move.er == 7):
        promo_char = (
            move.promotion if move.promotion and move.promotion != "\0" else "Q"
        )
        lines.append(
            f"PROMOTED {color_name(mover.color)} {from_sq} {to_sq} {promo_char}"
        )
    return lines


def zero_lines(board: Board, after_board: Board, tracker: Tracker, s0, s1) -> List[str]:
    """Pieces with no legal moves before, after, or both."""
    lines: List[str] = []
    for side in (WHITE, BLACK):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                pid = tracker.grid[r][c]
                if (
                    pid <= 0
                    or pid >= CALC_MAX_ID
                    or tracker.color[pid] != side
                    or not s1.present[pid]
                ):
                    continue
                before_zero = s0.legal_count[pid] == 0
                after_zero = s1.legal_count[pid] == 0
                if not before_zero and not after_zero:
                    continue
                pname = f"{board.grid[r][c].type} {square_text(square_index(r, c))}"
                cause = (
                    zero_move_cause(after_board, s1.row[pid], s1.col[pid])
                    if after_zero
                    else zero_move_cause(board, r, c)
                )
                when = (
                    "both"
                    if (before_zero and after_zero)
                    else ("after" if after_zero else "before")
                )
                lines.append(f"ZERO {color_name(side)} {pname} {cause} {when}")
    return lines
