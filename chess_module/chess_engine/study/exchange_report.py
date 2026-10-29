"""Printed EXCHANGE report for captures on one square."""

from typing import List

from ..search_budget import bounded_search
from ..constants import (
    TOTAL_SQUARES, Color, WHITE, BLACK,
    color_name, square_text, EXCHANGE_MAX,
)
from ..move import Move
from ..board import Board
from ..movegen import make_move
from .common import piece_value, order_label
from .exchange_gain import (
    captured_type,
    captures_on,
    first_capture_class,
    material_text,
    promotion_gain,
)


@bounded_search
def exchange_report(board: Board, sq: int, limit: int) -> str:
    """Generates Stage 3E exchange report for square sq."""
    if not isinstance(sq, int) or isinstance(sq, bool) or not 0 <= sq < TOTAL_SQUARES:
        raise ValueError(f"invalid square index: {sq}")
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= EXCHANGE_MAX
    ):
        raise ValueError(f"exchange limit must be between 1 and {EXCHANGE_MAX}")
    lines: List[str] = [
        f"EXCHANGE BEGIN {color_name(board.turn)} {square_text(sq)} LIMIT {limit}",
        "NOTE values P 1, N 3, B 3, R 5, Q 9 include promotion gains in material "
        "totals; a nonnegative material result is not proof that a move is good",
    ]
    first_caps = captures_on(board, sq)
    if not first_caps:
        lines.append("NO CAPTURES")
        lines.append("EXCHANGE END\n")
        return "\n".join(lines)

    sequences_count = 0
    was_cut = False

    @bounded_search
    def exchange_walk(
        b: Board,
        path: List[Move],
        taken: List[str],
        by: List[Color],
        promoted: List[int],
        length: int,
    ) -> None:
        nonlocal sequences_count, was_cut
        caps = captures_on(b, sq)
        cut = length == limit and len(caps) > 0
        if length > 0:
            lines.append(_sequence_line(path, taken, by, promoted, length, cut))
            sequences_count += 1
        if cut:
            was_cut = True
        if length < limit:
            for c in caps:
                next_b = b.clone()
                make_move(next_b, c)
                path.append(c)
                taken.append(captured_type(b, c))
                by.append(b.turn)
                promoted.append(promotion_gain(b, c))
                exchange_walk(next_b, path, taken, by, promoted, length + 1)
                path.pop()
                taken.pop()
                by.pop()
                promoted.pop()

    exchange_walk(board, [], [], [], [], 0)
    values = [piece_value(captured_type(board, c)) for c in first_caps]

    for idx, c in enumerate(first_caps):
        mat_res, bounded = first_capture_class(board, c, limit)
        bnd_str = " BOUNDED" if bounded else ""
        lines.append(
            f"FIRST {c.uci} TAKES {captured_type(board, c)} VALUE {values[idx]} "
            f"{material_text(mat_res)} ORDER {order_label(values, values[idx])}"
            f"{bnd_str}"
        )

    lines.append(f"SUMMARY SEQUENCES {sequences_count}")
    if was_cut:
        lines.append(f"LIMIT {limit}")
    lines.append("EXCHANGE END\n")
    return "\n".join(lines)


def _sequence_line(
    path: List[Move],
    taken: List[str],
    by: List[Color],
    promoted: List[int],
    length: int,
    cut: bool,
) -> str:
    path_str = " ".join(m.uci for m in path)
    took = {WHITE: 0, BLACK: 0}
    promotion_gains = {WHITE: 0, BLACK: 0}
    white_took = []
    black_took = []
    for i in range(length):
        took[by[i]] += piece_value(taken[i]) + promoted[i]
        promotion_gains[by[i]] += promoted[i]
        if by[i] == WHITE:
            white_took.append(taken[i])
        else:
            black_took.append(taken[i])
    w_str = f"WHITE-TOOK {' '.join(white_took) if white_took else '-'}"
    b_str = f"BLACK-TOOK {' '.join(black_took) if black_took else '-'}"
    cut_str = " LIMIT" if cut else ""
    promotion_str = (
        f" PROMOTION-GAIN White {promotion_gains[WHITE]} Black {promotion_gains[BLACK]}"
        if any(promotion_gains.values())
        else ""
    )
    return (
        f"SEQUENCE {path_str} {w_str} {b_str} "
        f"MATERIAL White {took[WHITE]} Black {took[BLACK]}"
        f"{promotion_str}{cut_str}"
    )
