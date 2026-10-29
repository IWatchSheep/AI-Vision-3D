"""ORDER report: captures first, then other moves by distance."""

from typing import List

from ..search_budget import bounded_search
from ..constants import color_name, EXCHANGE_MAX
from ..board import Board
from ..movegen import sorted_moves, is_in_check
from .common import MaterialResult, move_distance, order_label, piece_value
from .exchange_gain import captured_type, first_capture_class, material_text


@bounded_search
def order_report(board: Board, limit: int) -> str:
    """Generates Stage 3E combined move ordering report."""
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= EXCHANGE_MAX
    ):
        raise ValueError(f"exchange limit must be between 1 and {EXCHANGE_MAX}")
    lines: List[str] = [
        f"ORDER BEGIN {color_name(board.turn)} EXCHANGE LIMIT {limit}",
        "NOTE an order of listed facts (ideas 7 and 8), rebuilt in every position; "
        "not a choice of move",
    ]
    all_moves = sorted_moves(board)
    if not all_moves:
        outcome = "checkmate" if is_in_check(board, board.turn) else "stalemate"
        lines.append(f"NO MOVES {outcome}")
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
        entries.append(
            {
                "move": m,
                "taken": taken,
                "value": val,
                "squares": dist,
                "material": mat,
                "bounded": bounded,
            }
        )

    lines.append(f"HEADS {'CAPTURE' if has_group1 else 'DISTANCE'}")
    lines.extend(_group1_lines(entries))
    lines.extend(_group2_lines(entries))
    lines.append("ORDER END\n")
    return "\n".join(lines)


def _group1_lines(entries: list) -> List[str]:
    lines: List[str] = []
    for cls in (MaterialResult.MATERIAL_FORCED, MaterialResult.MATERIAL_POSSIBLE):
        vals = [9 - e["value"] for e in entries if e["taken"] and e["material"] == cls]
        for v in range(9, 0, -1):
            for d in range(1, 8):
                for e in entries:
                    if (
                        not e["taken"]
                        or e["material"] != cls
                        or e["value"] != v
                        or e["squares"] != d
                    ):
                        continue
                    bnd_str = " BOUNDED" if e["bounded"] else ""
                    lines.append(
                        f"GROUP 1 CAPTURE {e['move'].uci} TAKES {e['taken']} "
                        f"VALUE {e['value']} SQUARES {e['squares']} "
                        f"{material_text(e['material'])} "
                        f"ORDER {order_label(vals, 9 - v)}{bnd_str}"
                    )
    return lines


def _group2_lines(entries: list) -> List[str]:
    lines: List[str] = []
    distances = [
        e["squares"]
        for e in entries
        if not (e["taken"] and e["material"] != MaterialResult.MATERIAL_ELSE)
    ]
    for d in range(1, 8):
        for e in entries:
            if (
                e["taken"] and e["material"] != MaterialResult.MATERIAL_ELSE
            ) or e["squares"] != d:
                continue
            line = (
                f"GROUP 2 DISTANCE {e['move'].uci} SQUARES {d} "
                f"ORDER {order_label(distances, d)}"
            )
            if e["taken"]:
                bnd_str = " BOUNDED" if e["bounded"] else ""
                line += (
                    f" TAKES {e['taken']} VALUE {e['value']} "
                    f"{material_text(e['material'])}{bnd_str}"
                )
            lines.append(line)
    return lines
