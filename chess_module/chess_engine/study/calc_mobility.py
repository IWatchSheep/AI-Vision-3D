"""CALC mobility sections: LOST/GAINED/RESTORED and DENIED/OPENED."""

from typing import Dict, List, Tuple

from ..constants import (
    BOARD_SIZE, TOTAL_SQUARES, CALC_MAX_ID,
    Color, WHITE, BLACK,
    color_name, square_index, square_text,
)
from ..board import Board
from ..tracker import Tracker


def mobility_change_lines(
    board: Board, tracker: Tracker, names: Dict[int, str], s0, s1
) -> Tuple[List[str], Dict[Color, int], Dict[Color, int], Dict[Color, int]]:
    """LOST / GAINED / RESTORED destination lines and their counts."""
    lines: List[str] = []
    lost_counts: Dict[Color, int] = {WHITE: 0, BLACK: 0}
    gained_counts: Dict[Color, int] = {WHITE: 0, BLACK: 0}
    restored_counts: Dict[Color, int] = {WHITE: 0, BLACK: 0}

    for keyword, target_dict in (
        ("LOST", lost_counts),
        ("GAINED", gained_counts),
        ("RESTORED", restored_counts),
    ):
        for side in (WHITE, BLACK):
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    pid = tracker.grid[r][c]
                    if pid <= 0 or pid >= CALC_MAX_ID or tracker.color[pid] != side:
                        continue
                    sq_list = _wanted_squares(keyword, tracker, s0, s1, pid)
                    target_dict[side] += len(sq_list)
                    if sq_list:
                        p_name = names.get(
                            pid,
                            f"{board.grid[r][c].type} {square_text(square_index(r, c))}",
                        )
                        lines.append(
                            f"{keyword} {color_name(side)} {p_name} {' '.join(sq_list)}"
                        )
    return lines, lost_counts, gained_counts, restored_counts


def _wanted_squares(keyword: str, tracker: Tracker, s0, s1, pid: int) -> List[str]:
    sq_list = []
    for i in range(TOTAL_SQUARES):
        is_lost = s0.legal[pid][i] and not s1.legal[pid][i]
        is_new = not s0.legal[pid][i] and s1.legal[pid][i]
        wanted = False
        if keyword == "LOST" and is_lost:
            wanted = True
        elif keyword == "GAINED" and is_new and not tracker.lost[pid][i]:
            wanted = True
        elif keyword == "RESTORED" and is_new and tracker.lost[pid][i]:
            wanted = True
        if wanted:
            sq_list.append(square_text(i))
    return sq_list


def reach_change_lines(
    board: Board, tracker: Tracker, s0, s1, captured: List[bool]
) -> Tuple[List[str], Dict[Color, int], Dict[Color, int]]:
    """DENIED and OPENED square lines with counts."""
    lines: List[str] = []
    denied_counts: Dict[Color, int] = {WHITE: 0, BLACK: 0}
    opened_counts: Dict[Color, int] = {WHITE: 0, BLACK: 0}

    for denied_mode, target_dict in ((True, denied_counts), (False, opened_counts)):
        kw = "DENIED" if denied_mode else "OPENED"
        for side in (WHITE, BLACK):
            for i in range(TOTAL_SQUARES):
                chg = (
                    (s0.reach[side][i] and not s1.reach[side][i])
                    if denied_mode
                    else (not s0.reach[side][i] and s1.reach[side][i])
                )
                if not chg:
                    continue
                only_captured = (
                    _denied_only_by_capture(board, tracker, s0, captured, side, i)
                    if denied_mode
                    else False
                )
                cap_suffix = " by-capture" if only_captured else ""
                lines.append(f"{kw} {color_name(side)} {square_text(i)}{cap_suffix}")
                target_dict[side] += 1
    return lines, denied_counts, opened_counts


def _denied_only_by_capture(
    board: Board, tracker: Tracker, s0, captured: List[bool], side: Color, i: int
) -> bool:
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            pid = tracker.grid[r][c]
            if (
                0 < pid < CALC_MAX_ID
                and board.grid[r][c].color == side
                and s0.legal[pid][i]
                and not captured[pid]
            ):
                return False
    return True
