"""Forced-mate helpers used by LOOP and other reports."""

from ..search_budget import bounded_search, search_checkpoint
from ..constants import LOOP_MAX_DEPTH
from ..board import Board
from ..movegen import generate_moves, make_move, is_in_check


def require_mate_depth(depth: int) -> None:
    if (
        not isinstance(depth, int)
        or isinstance(depth, bool)
        or not 0 <= depth <= LOOP_MAX_DEPTH
    ):
        raise ValueError(f"depth must be between 0 and {LOOP_MAX_DEPTH}")


@bounded_search
def mate_forced(board: Board, n: int) -> bool:
    """True if side to move can force checkmate in n plies."""
    require_mate_depth(n)
    if n < 1 or board.automatic_draw()[0]:
        return False

    for m in generate_moves(board):
        search_checkpoint()
        next_b = board.clone()
        make_move(next_b, m, record_history=True)
        replies = generate_moves(next_b)
        if len(replies) == 0:
            if is_in_check(next_b, next_b.turn):
                return True
        elif n >= 3 and not next_b.automatic_draw()[0] and not next_b.claimable_draw()[0]:
            all_forced = True
            for rep in replies:
                search_checkpoint()
                if next_b.claimable_draw(rep)[0]:
                    all_forced = False
                    break
                after_rep = next_b.clone()
                make_move(after_rep, rep, record_history=True)
                if not mate_forced(after_rep, n - 2):
                    all_forced = False
                    break
            if all_forced:
                return True
    return False


@bounded_search
def first_move_forces(after_board: Board, n: int) -> bool:
    """True if the position after the first move forces mate in n plies."""
    require_mate_depth(n)
    if n < 1:
        return False
    replies = generate_moves(after_board)
    if not replies:
        return is_in_check(after_board, after_board.turn)
    if after_board.automatic_draw()[0] or after_board.claimable_draw()[0]:
        return False
    if n < 3:
        return False
    for rep in replies:
        search_checkpoint()
        if after_board.claimable_draw(rep)[0]:
            return False
        after_rep = after_board.clone()
        make_move(after_rep, rep, record_history=True)
        if not mate_forced(after_rep, n - 2):
            return False
    return True
