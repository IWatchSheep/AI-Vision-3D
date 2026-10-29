"""Small helpers used while building a CALC report."""

from typing import Dict, List

from ..search_budget import bounded_search, search_checkpoint
from ..constants import (
    BOARD_SIZE, CALC_MAX_ID,
    Color, WHITE, BLACK,
    color_name, square_index, square_text, in_bounds,
)
from ..move import Move
from ..board import Board
from ..movegen import (
    generate_moves, make_move, is_in_check, piece_attacks, pseudo_legal, game_over,
)


def zero_move_cause(board: Board, row: int, col: int) -> str:
    """Diagnoses why a piece has 0 legal moves: BLOCKED, CHECK, or PIN."""
    if not in_bounds(row, col) or board.grid[row][col].is_empty:
        return "BLOCKED"

    piece = board.grid[row][col]
    view = board.clone()
    view.turn = piece.color
    pseudo_count = 0
    for er in range(BOARD_SIZE):
        for ec in range(BOARD_SIZE):
            if piece.type == "P" and er in (0, 7):
                m = Move(sr=row, sc=col, er=er, ec=ec, promotion="Q")
            else:
                m = Move(sr=row, sc=col, er=er, ec=ec)
            if pseudo_legal(view, m):
                pseudo_count += 1

    if pseudo_count == 0:
        return "BLOCKED"
    return "CHECK" if is_in_check(view, view.turn) else "PIN"


def linked(board: Board, pr: int, pc: int, qr: int, qc: int, protect: bool) -> bool:
    """True when (pr,pc) protects (friendly) or attacks (enemy) the piece on (qr,qc)."""
    if not (in_bounds(pr, pc) and in_bounds(qr, qc)):
        return False
    p = board.grid[pr][pc]
    q = board.grid[qr][qc]
    if p.is_empty or q.is_empty or q.type == "K" or (pr == qr and pc == qc):
        return False
    same_color = p.color == q.color
    if same_color != protect:
        return False
    return piece_attacks(board, pr, pc, qr, qc)


@bounded_search
def report_mates(board: Board, side: Color) -> List[str]:
    """Finds all immediate checkmate moves available for `side`."""
    if game_over(board)[0]:
        return []
    view = board.clone()
    view.turn = side
    mates = []
    for m in generate_moves(view):
        search_checkpoint()
        next_b = view.clone()
        make_move(next_b, m)
        replies = generate_moves(next_b)
        if len(replies) == 0 and is_in_check(next_b, next_b.turn):
            mates.append(m.uci)
    return mates


def count_mate_in_one(board: Board, side: Color) -> int:
    """Number of distinct checkmate moves available for ``side`` right now."""
    return len(report_mates(board, side))


def append_link_changes(
    lines: List[str],
    keyword: str,
    protect: bool,
    scan_board: Board,
    scan_ids: List[List[int]],
    other_board: Board,
    other_present: List[bool],
    other_row: List[int],
    other_col: List[int],
    names: Dict[int, str],
) -> None:
    """Add PROTECT+/PROTECT-/ATTACK+/ATTACK- lines for one before/after view."""
    for side in (WHITE, BLACK):
        for pr in range(BOARD_SIZE):
            for pc in range(BOARD_SIZE):
                p = scan_ids[pr][pc]
                if not (0 < p < CALC_MAX_ID) or scan_board.grid[pr][pc].color != side:
                    continue
                for qr in range(BOARD_SIZE):
                    for qc in range(BOARD_SIZE):
                        q = scan_ids[qr][qc]
                        if not (0 < q < CALC_MAX_ID):
                            continue
                        if not linked(scan_board, pr, pc, qr, qc, protect):
                            continue
                        in_other = (
                            other_present[p]
                            and other_present[q]
                            and linked(
                                other_board,
                                other_row[p],
                                other_col[p],
                                other_row[q],
                                other_col[q],
                                protect,
                            )
                        )
                        if in_other:
                            continue
                        p_name = names.get(
                            p,
                            f"{scan_board.grid[pr][pc].type} "
                            f"{square_text(square_index(pr, pc))}",
                        )
                        q_name = names.get(
                            q,
                            f"{scan_board.grid[qr][qc].type} "
                            f"{square_text(square_index(qr, qc))}",
                        )
                        lines.append(f"{keyword} {color_name(side)} {p_name} {q_name}")
