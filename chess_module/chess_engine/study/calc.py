"""Stage 3A: the fact calculator (CALC report).

calc_report describes everything that changes when one move is played.
Section builders live in calc_header, calc_mobility, and calc_ending.
"""

from ..search_budget import bounded_search
from ..move import Move
from ..board import Board
from ..movegen import make_move, legal_move
from ..tracker import Tracker
from .calc_helpers import (
    count_mate_in_one,
    linked,
    report_mates,
    zero_move_cause,
)
from .calc_header import header_lines, zero_lines
from .calc_mobility import mobility_change_lines, reach_change_lines
from .calc_ending import ending_lines, link_lines

__all__ = [
    "zero_move_cause",
    "linked",
    "report_mates",
    "count_mate_in_one",
    "calc_report",
]


@bounded_search
def calc_report(board: Board, tracker: Tracker, move: Move) -> str:
    """Generates the complete Stage 3A Calculator report for `move`."""
    if not legal_move(board, move):
        raise ValueError("Cannot report an illegal move")

    after_board = board.clone()
    make_move(after_board, move, record_history=True)
    after_id, captured = tracker.ids_after_move(board, move)
    s0 = tracker.take_snapshot(board)

    temp_t = Tracker()
    temp_t.grid = after_id
    temp_t.color = list(tracker.color)
    s1 = temp_t.take_snapshot(after_board)
    names = tracker.make_names(board)

    lines = []
    lines.extend(header_lines(board, tracker, move, captured))
    lines.extend(zero_lines(board, after_board, tracker, s0, s1))

    mob_lines, lost, gained, restored = mobility_change_lines(
        board, tracker, names, s0, s1
    )
    lines.extend(mob_lines)

    reach_lines, denied, opened = reach_change_lines(
        board, tracker, s0, s1, captured
    )
    lines.extend(reach_lines)
    lines.extend(link_lines(board, after_board, tracker, after_id, names, s0, s1))
    lines.extend(
        ending_lines(
            after_board, tracker, s1, lost, gained, restored, denied, opened
        )
    )
    return "\n".join(lines)
