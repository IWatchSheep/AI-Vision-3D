"""LOOP report: exhaustive game-tree walk up to a ply limit."""

from typing import List

from ..search_budget import bounded_search
from ..constants import WHITE, BLACK, color_name, LOOP_MAX_DEPTH
from ..move import Move
from ..board import Board
from ..movegen import generate_moves, sorted_moves, make_move, is_in_check
from .mate_search import first_move_forces


def zero_move_pieces(board: Board, moves: List[Move]) -> int:
    """Counts pieces of side to move that have 0 legal moves."""
    from ..constants import BOARD_SIZE
    moves_from = {m.sr * BOARD_SIZE + m.sc for m in moves}
    zero = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board.grid[r][c].color == board.turn and (r * BOARD_SIZE + c) not in moves_from:
                zero += 1
    return zero


@bounded_search
def loop_report(board: Board, depth: int, zero_k: int = 0) -> str:
    """Exhaustive game tree search up to `depth` plies."""
    lines: List[str] = []
    mover = board.turn
    if (not isinstance(depth, int) or isinstance(depth, bool)
            or depth < 1 or depth > LOOP_MAX_DEPTH):
        raise ValueError(f"depth must be an integer from 1 to {LOOP_MAX_DEPTH}")
    if not isinstance(zero_k, int) or isinstance(zero_k, bool) or zero_k < 0:
        raise ValueError("zero_k must be a non-negative integer")

    first = sorted_moves(board)

    hdr = f"LOOP BEGIN {color_name(mover)} DEPTH {depth}"
    if zero_k > 0:
        hdr += f" ZERO {zero_k}"
    lines.append(hdr)

    if not first:
        lines.append(f"NO MOVES {'checkmate' if is_in_check(board, mover) else 'stalemate'}")
        lines.append("LOOP END\n")
        return "\n".join(lines)

    drawn, reason = board.automatic_draw()
    if drawn:
        lines.extend([f"DRAW {reason}", "LOOP END\n"])
        return "\n".join(lines)

    positions = [0] * (depth + 1)
    mated = {WHITE: [0] * (depth + 1), BLACK: [0] * (depth + 1)}
    stalemates = [0] * (depth + 1)
    zero_counts = [0] * (depth + 1)
    first_mated = [{WHITE: 0, BLACK: 0} for _ in range(len(first))]
    replies_with_mate = [0] * len(first)
    # One slot per ply index 0..depth-1; never share Move objects across slots.
    current_line: List[Move] = [Move(0, 0, 0, 0) for _ in range(depth)]
    reply_reaches_mate = [False]

    # --- Depth-first walk: record mates, draws, and optional ZERO counts ---
    @bounded_search
    def loop_walk(b: Board, ply: int, first_idx: int) -> None:
        moves = sorted_moves(b)
        positions[ply] += 1
        if zero_k > 0 and zero_move_pieces(b, moves) >= zero_k:
            zero_counts[ply] += 1

        if not moves:
            if is_in_check(b, b.turn):
                mated[b.turn][ply] += 1
                first_mated[first_idx][b.turn] += 1
                if b.turn != mover and ply >= 3:
                    reply_reaches_mate[0] = True
                path_str = " ".join(current_line[i].uci for i in range(ply))
                lines.append(f"MATE {ply} {path_str} MATED {color_name(b.turn)}")
            else:
                stalemates[ply] += 1
        elif b.automatic_draw()[0]:
            lines.append(f"DRAW {ply} {b.automatic_draw()[1]}")
        elif ply < depth:
            for m in moves:
                next_b = b.clone()
                make_move(next_b, m, record_history=True)
                current_line[ply] = m
                if ply == 1:
                    reply_reaches_mate[0] = False
                loop_walk(next_b, ply + 1, first_idx)
                if ply == 1 and reply_reaches_mate[0]:
                    replies_with_mate[first_idx] += 1

    for idx, m in enumerate(first):
        next_b = board.clone()
        make_move(next_b, m, record_history=True)
        current_line[0] = m
        loop_walk(next_b, 1, idx)

    for p in range(1, depth + 1):
        line = f"PLY {p} POSITIONS {positions[p]} MATED White {mated[WHITE][p]} Black {mated[BLACK][p]} STALEMATES {stalemates[p]}"
        if zero_k > 0:
            line += f" ZERO {zero_counts[p]}"
        lines.append(line)

    any_forced = False
    any_possible = False
    for idx, m in enumerate(first):
        next_b = board.clone()
        make_move(next_b, m, record_history=True)
        replies = generate_moves(next_b)
        prefix = f"FIRST {m.uci} "
        if first_move_forces(next_b, depth):
            status = "FORCED"
            any_forced = True
        elif replies_with_mate[idx] > 0:
            status = f"POSSIBLE {replies_with_mate[idx]} OF {len(replies)}"
            any_possible = True
        else:
            status = "NOT-FOUND"
        lines.append(f"{prefix}{status} MATED White {first_mated[idx][WHITE]} Black {first_mated[idx][BLACK]}")

    result_str = "FORCED" if any_forced else ("POSSIBLE" if any_possible else "NOT-FOUND")
    lines.append(f"RESULT {color_name(mover)} {result_str}")
    if not any_forced:
        lines.append(f"LIMIT {depth}")
    lines.append("LOOP END\n")
    return "\n".join(lines)

