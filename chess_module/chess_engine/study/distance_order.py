"""DISTANCE ORDER reports for one piece or the whole board after a move."""

from typing import List

from ..constants import (
    BOARD_SIZE, TOTAL_SQUARES,
    WHITE, BLACK,
    in_bounds, color_name, square_index, square_text,
)
from ..move import Move
from ..board import Board
from ..movegen import sorted_moves, make_move, legal_move
from .common import move_distance, order_label


def distance_lines(board: Board, r: int, c: int, label: str) -> List[str]:
    """Generates distance order lines for piece on (r, c)."""
    if not in_bounds(r, c) or board.grid[r][c].is_empty:
        return []
    view = board.clone()
    view.turn = board.grid[r][c].color
    piece_moves = [m for m in sorted_moves(view) if m.sr == r and m.sc == c]
    if not piece_moves:
        return [f"NO-MOVES{label[4:]}"]

    distances = [move_distance(m) for m in piece_moves]
    lines = []
    for d in range(1, 8):
        for idx, m in enumerate(piece_moves):
            if distances[idx] != d:
                continue
            line = f"{label} {m.uci} DISTANCE {d} ORDER {order_label(distances, d)}"
            ptype = board.grid[r][c].type
            if ptype == "N":
                line += " JUMP"
            elif ptype == "K" and m.sr == m.er and abs(m.ec - m.sc) == 2:
                is_ks = m.ec > m.sc
                rf = square_text(square_index(r, 7 if is_ks else 0))
                rt = square_text(square_index(r, 5 if is_ks else 3))
                line += f" CASTLE {rf}{rt}"
            lines.append(line)
    return lines


def distance_selection(board: Board, r: int, c: int) -> str:
    """DISTANCE ORDER report for one selected piece."""
    if not in_bounds(r, c) or board.grid[r][c].is_empty:
        return "DISTANCE ORDER END\n"
    at = square_text(square_index(r, c))
    lines = [f"DISTANCE ORDER {board.grid[r][c].type} {at}"]
    lines.extend(distance_lines(board, r, c, "MOVE"))
    lines.append("DISTANCE ORDER END\n")
    return "\n".join(lines)


def distance_after(board: Board, move: Move) -> str:
    """DISTANCE ORDER for every piece after a legal move is applied."""
    if not legal_move(board, move):
        raise ValueError("Cannot report an illegal move")
    after = board.clone()
    make_move(after, move)
    lines = [f"DISTANCE ORDER AFTER {move.uci} REAL"]
    for side in (WHITE, BLACK):
        for i in range(TOTAL_SQUARES):
            r, c = i // BOARD_SIZE, i % BOARD_SIZE
            if after.grid[r][c].color == side:
                at = square_text(i)
                label = f"MOVE {color_name(side)} {after.grid[r][c].type} {at}"
                lines.extend(distance_lines(after, r, c, label))
    lines.append("DISTANCE ORDER END\n")
    return "\n".join(lines)
