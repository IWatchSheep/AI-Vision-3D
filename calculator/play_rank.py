"""Rank dolls and find legal moves that fill blueprint squares."""

from __future__ import annotations

from calculator.build_shape import (
    BoardRows,
    IMAGINE_STEP_LIMIT,
    apply_legal_move,
    build_view,
)
from calculator.pattern import rank
from calculator.play_types import RankedStrategy, TargetChoice
from calculator.strategies import Strategy
from chess_module.chess_engine.movegen import generate_moves


def as_engine_rows(board_rows: list[str]) -> BoardRows:
    """Require a live engine-backed board picture, not a bare string list."""
    if isinstance(board_rows, BoardRows):
        return board_rows
    raise TypeError("strategy building needs a live engine position, not a bare picture")


def rank_strategies(board_rows: list[str]) -> tuple[RankedStrategy, ...]:
    """Rank all 20 dolls. The board itself is not changed."""
    return tuple(
        RankedStrategy(
            item.strategy.number,
            item.strategy.id,
            item.strategy.name,
            item.strategy.sentence,
            item.score,
            item.hash_count,
            item.plus_count,
            item.x_count,
        )
        for item in rank(board_rows)
    )


def legal_fill_moves(
    doll: Strategy, board_rows: BoardRows
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Every legal move, in engine order, and the blueprint squares it newly matches."""
    board = board_rows.engine_copy()
    already = set(build_view(doll, board_rows).filled_squares)
    found = []
    for move in generate_moves(board):
        result = apply_legal_move(board_rows, move.uci, doll)
        if not result.legal:
            continue
        gained = tuple(
            square for square in result.view.filled_squares if square not in already
        )
        found.append((move.uci, gained))
    return tuple(found)


def target_choices(doll: Strategy, board_rows: BoardRows) -> tuple[TargetChoice, ...]:
    """Missing and mismatched squares, each with the legal moves that fill it now."""
    view = build_view(doll, board_rows)
    by_square: dict[str, list[str]] = {}
    for uci, gained in legal_fill_moves(doll, board_rows):
        for square in gained:
            by_square.setdefault(square, []).append(uci)
    return tuple(
        TargetChoice(
            target.square,
            target.expected,
            target.seen,
            target.mark,
            tuple(by_square.get(target.square, ())),
        )
        for target in view.targets
    )


def next_imaginary_move(doll: Strategy, board_rows: BoardRows) -> str | None:
    """First legal move that fills a required square, or the first legal move."""
    choices = legal_fill_moves(doll, board_rows)
    for uci, gained in choices:
        if gained:
            return uci
    if choices:
        return choices[0][0]
    return None


def auto_moves(
    doll: Strategy, board_rows: BoardRows, plies: int = 4
) -> tuple[str, ...]:
    """Up to four legal plies on a copy, preferring a move that fills the blueprint."""
    if (
        not isinstance(plies, int)
        or isinstance(plies, bool)
        or not 0 <= plies <= IMAGINE_STEP_LIMIT
    ):
        raise ValueError("Imaginary plies must be an integer from zero to four")
    current = board_rows.copy()
    chosen = []
    for _ in range(plies):
        text = next_imaginary_move(doll, current)
        if text is None:
            break
        result = apply_legal_move(current, text, doll)
        if not result.legal:
            break
        chosen.append(text)
        current = as_engine_rows(result.board_rows)
    return tuple(chosen)
