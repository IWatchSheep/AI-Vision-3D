"""CALC closing sections: protect/attack links, check, mate-in-one, counts."""

from typing import Dict, List

from ..constants import CALC_MAX_ID, Color, WHITE, BLACK, color_name
from ..board import Board
from ..movegen import is_in_check, game_over
from ..tracker import Tracker
from .calc_helpers import append_link_changes, report_mates


def link_lines(
    board: Board,
    after_board: Board,
    tracker: Tracker,
    after_id: List[List[int]],
    names: Dict[int, str],
    s0,
    s1,
) -> List[str]:
    """PROTECT+/PROTECT-/ATTACK+/ATTACK- lines."""
    lines: List[str] = []
    append_link_changes(
        lines, "PROTECT+", True,
        after_board, after_id, board, s0.present, s0.row, s0.col, names,
    )
    append_link_changes(
        lines, "PROTECT-", True,
        board, tracker.grid, after_board, s1.present, s1.row, s1.col, names,
    )
    append_link_changes(
        lines, "ATTACK+", False,
        after_board, after_id, board, s0.present, s0.row, s0.col, names,
    )
    append_link_changes(
        lines, "ATTACK-", False,
        board, tracker.grid, after_board, s1.present, s1.row, s1.col, names,
    )
    return lines


def ending_lines(
    after_board: Board,
    tracker: Tracker,
    s1,
    lost_counts: Dict[Color, int],
    gained_counts: Dict[Color, int],
    restored_counts: Dict[Color, int],
    denied_counts: Dict[Color, int],
    opened_counts: Dict[Color, int],
) -> List[str]:
    """CHECK, MATE1, COUNT, and CALC END."""
    lines: List[str] = []
    for side in (WHITE, BLACK):
        if is_in_check(after_board, side):
            lines.append(f"CHECK {color_name(side)}")

    if not game_over(after_board)[0]:
        for side in (WHITE, BLACK):
            mates = report_mates(after_board, side)
            if mates:
                lines.append(f"MATE1 {color_name(side)} {' '.join(mates)}")

    for side in (WHITE, BLACK):
        u1 = sum(
            1
            for pid in range(1, CALC_MAX_ID)
            if (
                s1.present[pid]
                and tracker.color[pid] == side
                and s1.legal_count[pid] == 0
            )
        )
        lines.append(
            f"COUNT {color_name(side)} "
            f"U1 {u1} U2 {lost_counts[side]} U3 {denied_counts[side]} "
            f"GAINED {gained_counts[side]} RESTORED {restored_counts[side]} "
            f"OPENED {opened_counts[side]}"
        )
    lines.append("CALC END\n")
    return lines
