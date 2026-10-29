"""TRACE report: replay a UCI line with one CALC block per ply."""

from typing import Tuple

from ..search_budget import bounded_search, search_checkpoint
from ..constants import HISTORY_MAX_LEN
from ..move import parse_move_text
from ..board import Board
from ..movegen import generate_moves, legal_move, make_move
from ..tracker import Tracker
from .calc import calc_report


@bounded_search
def trace_report(
    board: Board, tracker: Tracker, moves_text: str
) -> Tuple[bool, str, int]:
    """Replays a series of moves and prints CALC reports."""
    if not isinstance(moves_text, str) or len(moves_text) > HISTORY_MAX_LEN * 6:
        return False, "", 1
    tokens = moves_text.strip().split()
    if not tokens:
        return False, "", 0
    if len(tokens) > HISTORY_MAX_LEN:
        return False, "", 1

    sim_b = board.clone()
    parsed_moves = []
    for idx, tok in enumerate(tokens):
        search_checkpoint()
        m = parse_move_text(tok)
        if (not m or not legal_move(sim_b, m)
                or not generate_moves(sim_b) or sim_b.automatic_draw()[0]):
            return False, "", idx + 1
        make_move(sim_b, m, record_history=True)
        parsed_moves.append(m)

    lines: List[str] = [f"TRACE BEGIN {len(parsed_moves)}"]
    cur_b = board.clone()
    cur_t = tracker.clone()

    # --- Replay from the start position; one CALC block per parsed move ---
    for idx, m in enumerate(parsed_moves):
        lines.append(f"TRACE PLY {idx + 1} {m.uci}")
        lines.append(calc_report(cur_b, cur_t, m).rstrip())
        cur_t.commit(cur_b, m)
        make_move(cur_b, m, record_history=True)

    lines.append("TRACE END\n")
    return True, "\n".join(lines), 0
