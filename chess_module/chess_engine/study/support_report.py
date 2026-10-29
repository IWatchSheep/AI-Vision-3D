"""SUPPORT report: follow-up PASS moves that newly protect the landing square."""

from ..search_budget import bounded_search
from ..constants import opposite, color_name, square_index, square_text
from ..move import Move
from ..board import Board
from ..movegen import legal_move, piece_attacks
from .common import pass_moves, pass_play, pieces_on_square


@bounded_search
def support_report(board: Board, move: Move) -> str:
    """Generates Stage 3D SUPPORT report."""
    if not legal_move(board, move):
        raise ValueError("Cannot report an illegal move")
    side = board.turn
    enemy = opposite(side)
    after = board.clone()
    pass_play(after, move, side)
    sq = square_index(move.er, move.ec)
    ptype = after.grid[move.er][move.ec].type
    at = square_text(sq)

    lines = [
        f"SUPPORT BEGIN {move.uci} PASS",
        f"NOTE PASS is hypothetical: {color_name(side)} moves again, "
        f"{color_name(enemy)} passes",
        f"SUPPORT NOW {ptype} {at} PROTECTORS {pieces_on_square(after, sq, side)}",
    ]

    follows = 0
    for f in pass_moves(after, side):
        if f.sr == move.er and f.sc == move.ec:
            continue
        next_b = after.clone()
        pass_play(next_b, f, side)
        if next_b.grid[move.er][move.ec].color != side:
            continue

        before_att = piece_attacks(after, f.sr, f.sc, move.er, move.ec)
        now_att = piece_attacks(next_b, f.er, f.ec, move.er, move.ec)
        if now_att and not before_att:
            from_sq = square_text(square_index(f.sr, f.sc))
            ftype = after.grid[f.sr][f.sc].type
            prots = pieces_on_square(next_b, sq, side)
            lines.append(
                f"FOLLOW {f.uci} {ftype} {from_sq} PROTECTS {ptype} {at} "
                f"PROTECTORS {prots}"
            )
            follows += 1

    lines.append(f"SUMMARY FOLLOWS {follows}")
    lines.append("SUPPORT END\n")
    return "\n".join(lines)
