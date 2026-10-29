"""Capture value helpers and the exchange minimax tree."""

from typing import List, Tuple

from ..search_budget import bounded_search
from ..constants import (
    BOARD_SIZE, TOTAL_SQUARES, Color,
    square_index, in_bounds, EXCHANGE_MAX,
)
from ..move import Move
from ..board import Board
from ..movegen import sorted_moves, make_move, move_is_en_passant, legal_move
from .common import MaterialResult, piece_value


def captured_type(board: Board, m: Move) -> str:
    """Returns captured piece type ('P', 'N', etc.) or empty string."""
    if not isinstance(m, Move) or not in_bounds(m.sr, m.sc) or not in_bounds(m.er, m.ec):
        return ""
    mover = board.grid[m.sr][m.sc]
    if mover.is_empty:
        return ""
    target = board.grid[m.er][m.ec]
    if not target.is_empty and target.color != mover.color:
        return target.type
    if mover.type == "P" and move_is_en_passant(board, m, mover):
        return "P"
    return ""


def captures_on(board: Board, sq: int) -> List[Move]:
    """All legal captures landing on sq for side to move."""
    if not isinstance(sq, int) or isinstance(sq, bool) or sq < 0 or sq >= TOTAL_SQUARES:
        return []
    if board.automatic_draw()[0]:
        return []
    all_moves = sorted_moves(board)
    return [
        m
        for m in all_moves
        if (m.er * BOARD_SIZE + m.ec == sq) and captured_type(board, m)
    ]


def promotion_gain(board: Board, move: Move) -> int:
    """Material created by replacing a pawn with its promotion piece."""
    if not isinstance(move, Move):
        return 0
    if not in_bounds(move.sr, move.sc) or not in_bounds(move.er, move.ec):
        return 0
    if board.grid[move.sr][move.sc].type == "P" and move.er in (0, 7):
        return piece_value(move.promotion) - piece_value("P")
    return 0


def capture_gain(board: Board, move: Move) -> int:
    return piece_value(captured_type(board, move)) + promotion_gain(board, move)


@bounded_search
def exchange_value(
    board: Board, mover: Color, sq: int, m: int, left: int
) -> Tuple[bool, bool, bool]:
    """Minimax exchange value: returns (forced, possible, bounded)."""
    if (
        not isinstance(left, int)
        or isinstance(left, bool)
        or not 0 <= left <= EXCHANGE_MAX
    ):
        raise ValueError(f"remaining captures must be between 0 and {EXCHANGE_MAX}")
    bounded = False
    caps = captures_on(board, sq) if left > 0 else []
    if left == 0 and len(captures_on(board, sq)) > 0:
        bounded = True

    stop_ok = m >= 0
    any_forced = False
    all_forced = True
    any_possible = stop_ok

    for c in caps:
        next_b = board.clone()
        v = capture_gain(board, c)
        child = (m + v) if board.turn == mover else (m - v)
        make_move(next_b, c)
        f, p, bnd = exchange_value(next_b, mover, sq, child, left - 1)
        if bnd:
            bounded = True
        any_forced = any_forced or f
        all_forced = all_forced and f
        any_possible = any_possible or p

    if board.turn == mover:
        forced = stop_ok or any_forced
    else:
        forced = stop_ok and all_forced

    return forced, any_possible, bounded


@bounded_search
def first_capture_class(
    board: Board, c: Move, limit: int
) -> Tuple[MaterialResult, bool]:
    """Classify the capture tree after playing ``c``."""
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= EXCHANGE_MAX
    ):
        raise ValueError(f"exchange limit must be between 1 and {EXCHANGE_MAX}")
    if not legal_move(board, c) or not captured_type(board, c):
        raise ValueError("Expected a legal capture")
    next_b = board.clone()
    v = capture_gain(board, c)
    make_move(next_b, c)
    sq = square_index(c.er, c.ec)
    forced, possible, bounded = exchange_value(
        next_b, board.turn, sq, v, limit - 1
    )
    if forced:
        return MaterialResult.MATERIAL_FORCED, bounded
    if possible:
        return MaterialResult.MATERIAL_POSSIBLE, bounded
    return MaterialResult.MATERIAL_ELSE, bounded


def material_text(r: MaterialResult) -> str:
    if r == MaterialResult.MATERIAL_FORCED:
        return "MATERIAL FORCED NONNEGATIVE"
    if r == MaterialResult.MATERIAL_POSSIBLE:
        return "MATERIAL POSSIBLE NONNEGATIVE"
    return "MATERIAL ELSE"
