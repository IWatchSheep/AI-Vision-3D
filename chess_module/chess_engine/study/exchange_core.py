"""Stage 3E: capture exchanges and move ordering.

EXCHANGE enumerates capture sequences on one square. ORDER ranks all legal
moves by material class first, then by distance — a fixed fact list, not advice.
"""

from ..search_budget import bounded_search

from typing import List, Tuple

from ..constants import (
    BOARD_SIZE, TOTAL_SQUARES, Color, WHITE, BLACK,
    color_name, square_index, square_text, in_bounds, EXCHANGE_MAX,
)
from ..move import Move
from ..board import Board
from ..movegen import sorted_moves, make_move, is_in_check, move_is_en_passant, legal_move
from .common import MaterialResult, move_distance, order_label, piece_value


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
    # En passant: diagonal pawn move onto an empty square.
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
    return [m for m in all_moves if (m.er * BOARD_SIZE + m.ec == sq) and captured_type(board, m)]


@bounded_search
def exchange_value(
    board: Board, mover: Color, sq: int, m: int, left: int
) -> Tuple[bool, bool, bool]:
    """Minimax exchange value evaluation: returns (forced, possible, bounded)."""
    if (not isinstance(left, int) or isinstance(left, bool)
            or not 0 <= left <= EXCHANGE_MAX):
        raise ValueError(f"remaining captures must be between 0 and {EXCHANGE_MAX}")
    bounded = False
    caps = captures_on(board, sq) if left > 0 else []
    if left == 0 and len(captures_on(board, sq)) > 0:
        bounded = True

    stop_ok = (m >= 0)
    any_forced = False
    all_forced = True
    any_possible = stop_ok

    for c in caps:
        next_b = board.clone()
        v = piece_value(captured_type(board, c))
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
    """Classify the capture tree after playing ``c`` (forced/possible/else + bounded)."""
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= EXCHANGE_MAX:
        raise ValueError(f"exchange limit must be between 1 and {EXCHANGE_MAX}")
    if not legal_move(board, c) or not captured_type(board, c):
        raise ValueError("Expected a legal capture")
    next_b = board.clone()
    v = piece_value(captured_type(board, c))
    make_move(next_b, c)
    sq = square_index(c.er, c.ec)
    forced, possible, bounded = exchange_value(next_b, board.turn, sq, v, limit - 1)
    if forced:
        return MaterialResult.MATERIAL_FORCED, bounded
    elif possible:
        return MaterialResult.MATERIAL_POSSIBLE, bounded
    return MaterialResult.MATERIAL_ELSE, bounded


def material_text(r: MaterialResult) -> str:
    if r == MaterialResult.MATERIAL_FORCED:
        return "MATERIAL FORCED NONNEGATIVE"
    elif r == MaterialResult.MATERIAL_POSSIBLE:
        return "MATERIAL POSSIBLE NONNEGATIVE"
    return "MATERIAL ELSE"


@bounded_search
def exchange_report(board: Board, sq: int, limit: int) -> str:
    """Generates Stage 3E exchange report for square sq."""
    if not isinstance(sq, int) or isinstance(sq, bool) or not 0 <= sq < TOTAL_SQUARES:
        raise ValueError(f"invalid square index: {sq}")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= EXCHANGE_MAX:
        raise ValueError(f"exchange limit must be between 1 and {EXCHANGE_MAX}")
    lines: List[str] = [
        f"EXCHANGE BEGIN {color_name(board.turn)} {square_text(sq)} LIMIT {limit}",
        "NOTE values P 1, N 3, B 3, R 5, Q 9 are logged only, not a score; a nonnegative material result is not proof that a move is good"
    ]
    first_caps = captures_on(board, sq)
    if not first_caps:
        lines.append("NO CAPTURES")
        lines.append("EXCHANGE END\n")
        return "\n".join(lines)

    sequences_count = 0
    was_cut = False

    @bounded_search
    def exchange_walk(b: Board, path: List[Move], taken: List[str], by: List[Color], length: int) -> None:
        nonlocal sequences_count, was_cut
        caps = captures_on(b, sq)
        cut = (length == limit and len(caps) > 0)
        if length > 0:
            path_str = " ".join(m.uci for m in path)
            took = {WHITE: 0, BLACK: 0}
            white_took = []
            black_took = []
            for i in range(length):
                took[by[i]] += piece_value(taken[i])
                if by[i] == WHITE:
                    white_took.append(taken[i])
                else:
                    black_took.append(taken[i])
            w_str = f"WHITE-TOOK {' '.join(white_took) if white_took else '-'}"
            b_str = f"BLACK-TOOK {' '.join(black_took) if black_took else '-'}"
            cut_str = " LIMIT" if cut else ""
            lines.append(f"SEQUENCE {path_str} {w_str} {b_str} MATERIAL White {took[WHITE]} Black {took[BLACK]}{cut_str}")
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
                exchange_walk(next_b, path, taken, by, length + 1)
                path.pop()
                taken.pop()
                by.pop()

    exchange_walk(board, [], [], [], 0)
    values = [piece_value(captured_type(board, c)) for c in first_caps]

    for idx, c in enumerate(first_caps):
        mat_res, bounded = first_capture_class(board, c, limit)
        bnd_str = " BOUNDED" if bounded else ""
        lines.append(f"FIRST {c.uci} TAKES {captured_type(board, c)} VALUE {values[idx]} {material_text(mat_res)} ORDER {order_label(values, values[idx])}{bnd_str}")

    lines.append(f"SUMMARY SEQUENCES {sequences_count}")
    if was_cut:
        lines.append(f"LIMIT {limit}")
    lines.append("EXCHANGE END\n")
    return "\n".join(lines)


def order_report(board: Board, limit: int) -> str:
    """Generates Stage 3E combined move ordering report."""
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= EXCHANGE_MAX:
        raise ValueError(f"exchange limit must be between 1 and {EXCHANGE_MAX}")
    lines: List[str] = [
        f"ORDER BEGIN {color_name(board.turn)} EXCHANGE LIMIT {limit}",
        "NOTE an order of listed facts (ideas 7 and 8), rebuilt in every position; not a choice of move"
    ]
    all_moves = sorted_moves(board)
    if not all_moves:
        lines.append(f"NO MOVES {'checkmate' if is_in_check(board, board.turn) else 'stalemate'}")
        lines.append("ORDER END\n")
        return "\n".join(lines)

    entries = []
    has_group1 = False
    for m in all_moves:
        taken = captured_type(board, m)
        val = piece_value(taken)
        dist = move_distance(m)
        bounded = False
        if taken:
            mat, bounded = first_capture_class(board, m, limit)
        else:
            mat = MaterialResult.MATERIAL_ELSE
        if taken and mat != MaterialResult.MATERIAL_ELSE:
            has_group1 = True
        entries.append({
            'move': m, 'taken': taken, 'value': val,
            'squares': dist, 'material': mat, 'bounded': bounded
        })

    lines.append(f"HEADS {'CAPTURE' if has_group1 else 'DISTANCE'}")

    # Group 1: FORCED then POSSIBLE
    for cls in (MaterialResult.MATERIAL_FORCED, MaterialResult.MATERIAL_POSSIBLE):
        vals = [9 - e['value'] for e in entries if e['taken'] and e['material'] == cls]
        for v in range(9, 0, -1):
            for d in range(1, 8):
                for e in entries:
                    if not e['taken'] or e['material'] != cls or e['value'] != v or e['squares'] != d:
                        continue
                    bnd_str = " BOUNDED" if e['bounded'] else ""
                    lines.append(f"GROUP 1 CAPTURE {e['move'].uci} TAKES {e['taken']} VALUE {e['value']} SQUARES {e['squares']} {material_text(e['material'])} ORDER {order_label(vals, 9 - v)}{bnd_str}")

    # Group 2: Everything else by distance
    distances = [e['squares'] for e in entries if not (e['taken'] and e['material'] != MaterialResult.MATERIAL_ELSE)]
    for d in range(1, 8):
        for e in entries:
            if (e['taken'] and e['material'] != MaterialResult.MATERIAL_ELSE) or e['squares'] != d:
                continue
            line = f"GROUP 2 DISTANCE {e['move'].uci} SQUARES {d} ORDER {order_label(distances, d)}"
            if e['taken']:
                bnd_str = " BOUNDED" if e['bounded'] else ""
                line += f" TAKES {e['taken']} VALUE {e['value']} {material_text(e['material'])}{bnd_str}"
            lines.append(line)

    lines.append("ORDER END\n")
    return "\n".join(lines)
