"""REAL routes report for goals (Stage 3D).

REAL = normal turn order: after your move the opponent may play any legal reply.
Search depth is in full plies. Results are FORCED (works vs all replies),
POSSIBLE (works vs some), or ELSE.
"""

from ..search_budget import bounded_search

from typing import List

from ..constants import (
    LOOP_MAX_DEPTH,
    opposite, color_name, square_text,
)
from ..move import Move
from ..board import Board
from ..movegen import (
    generate_moves, sorted_moves, make_move, is_in_check, game_over,
)
from .common import Goal, GoalCondition, RealResult
from .goal_basics import goal_squares, goal_text, goal_holds


@bounded_search
def routes_real_report(board: Board, goal: Goal, depth: int) -> str:
    """Generates Stage 3D real goal report."""
    if (not isinstance(depth, int) or isinstance(depth, bool)
            or not 1 <= depth <= LOOP_MAX_DEPTH):
        raise ValueError(f"depth must be between 1 and {LOOP_MAX_DEPTH}")
    side = board.turn
    enemy = opposite(side)
    squares = goal_squares(goal, board, side)
    lines = [
        f"ROUTES BEGIN {color_name(side)} GOAL {goal_text(goal)} DEPTH {depth} REAL",
        f"NOTE REAL: {color_name(enemy)} answers with every legal move; FORCED = reached whatever {color_name(enemy)} does"
    ]

    all_moves = generate_moves(board)
    if not all_moves:
        lines.append(f"NO MOVES {'checkmate' if is_in_check(board, side) else 'stalemate'}")
        lines.append("ROUTES END\n")
        return "\n".join(lines)

    drawn, reason = board.automatic_draw()
    if drawn:
        lines.extend([f"DRAW {reason}", "ROUTES END\n"])
        return "\n".join(lines)

    # --- REAL search helpers (minimax-style over generate_moves) ---
    @bounded_search
    def goal_forced_real(b: Board, sq: int, cond: GoalCondition, n: int) -> bool:
        """True if side can force the goal in n plies against every reply."""
        if goal_holds(b, side, sq, cond):
            return True
        if n < 1 or game_over(b)[0]:
            return False
        moves = generate_moves(b)
        for m in moves:
            next_b = b.clone()
            make_move(next_b, m, record_history=True)
            if goal_holds(next_b, side, sq, cond):
                return True
            if n < 2 or game_over(next_b)[0] or next_b.claimable_draw()[0]:
                continue
            replies = generate_moves(next_b)
            if not replies:
                continue
            # Each reply needs its own clone — do not reuse one board.
            if all(
                not next_b.claimable_draw(rep)[0]
                and goal_forced_real(_after_reply(next_b, rep), sq, cond, n - 2)
                for rep in replies
            ):
                return True
        return False

    def _after_reply(position: Board, rep: Move) -> Board:
        after = position.clone()
        make_move(after, rep, record_history=True)
        return after

    @bounded_search
    def goal_possible_real(b: Board, sq: int, cond: GoalCondition, n: int) -> bool:
        if goal_holds(b, side, sq, cond):
            return True
        if n < 1 or game_over(b)[0]: return False
        moves = generate_moves(b)
        for m in moves:
            next_b = b.clone()
            make_move(next_b, m, record_history=True)
            if goal_holds(next_b, side, sq, cond):
                return True
            if n >= 2 and not game_over(next_b)[0]:
                replies = generate_moves(next_b)
                for rep in replies:
                    after_rep = next_b.clone()
                    make_move(after_rep, rep, record_history=True)
                    if goal_possible_real(after_rep, sq, cond, n - 2):
                        return True
        return False

    def real_text(r: RealResult) -> str:
        if r == RealResult.REAL_FORCED: return "CONDITION IF FORCED"
        elif r == RealResult.REAL_POSSIBLE: return "CONDITION IF POSSIBLE"
        return "CONDITION ELSE"

    # --- For each goal square: score REACH and PROTECTED at REAL depth ---
    first_moves = sorted_moves(board)
    results: List[List[RealResult]] = []
    all_forced = True

    for sq in squares:
        sq_str = square_text(sq)
        sq_results = []
        for cond_idx, (cond, cond_name) in enumerate(((GoalCondition.COND_REACH, "REACH"),
                                                      (GoalCondition.COND_PROTECTED, "PROTECTED"))):
            lines.append(f"GOAL {sq_str} {cond_name}")
            best = RealResult.REAL_ELSE
            for m in first_moves:
                next_b = board.clone()
                make_move(next_b, m, record_history=True)
                if goal_holds(next_b, side, sq, cond):
                    lines.append(f"FIRST {m.uci} CONDITION IF FORCED MOVES 1")
                    best = RealResult.REAL_FORCED
                    continue

                replies = [] if depth < 2 or game_over(next_b)[0] else generate_moves(next_b)
                forced = (depth >= 2 and len(replies) > 0 and not next_b.claimable_draw()[0])
                k = 0
                for rep in replies:
                    after_rep = next_b.clone()
                    make_move(after_rep, rep, record_history=True)
                    can = goal_possible_real(after_rep, sq, cond, depth - 2)
                    if can: k += 1
                    if forced and (next_b.claimable_draw(rep)[0] or not can
                                   or not goal_forced_real(after_rep, sq, cond, depth - 2)):
                        forced = False

                if forced:
                    lines.append(f"FIRST {m.uci} CONDITION IF FORCED")
                    best = RealResult.REAL_FORCED
                elif k > 0:
                    lines.append(f"FIRST {m.uci} CONDITION IF POSSIBLE {k} OF {len(replies)}")
                    if best == RealResult.REAL_ELSE:
                        best = RealResult.REAL_POSSIBLE
                else:
                    lines.append(f"FIRST {m.uci} CONDITION ELSE")

            sq_results.append(best)
            lines.append(f"RESULT {sq_str} {cond_name} {real_text(best)}")
            if best != RealResult.REAL_FORCED:
                all_forced = False
        results.append(sq_results)

    if not squares:
        lines.append("NO SQUARES")

    for k, sq in enumerate(squares):
        sq_str = square_text(sq)
        lines.append(f"SQUARE {sq_str} REACH {real_text(results[k][0])} PROTECTED {real_text(results[k][1])}")

    for cond_idx, cond_name in enumerate(("REACH", "PROTECTED")):
        first_idx = next((k for k in range(len(squares)) if results[k][cond_idx] != RealResult.REAL_ELSE), -1)
        if first_idx >= 0:
            res_word = "FORCED" if results[first_idx][cond_idx] == RealResult.REAL_FORCED else "POSSIBLE"
            lines.append(f"FIRST-IF {cond_name} {square_text(squares[first_idx])} {res_word}")
        else:
            lines.append(f"FIRST-IF {cond_name} none (ELSE)")

    if not all_forced or not squares:
        lines.append(f"LIMIT {depth}")
    lines.append("ROUTES END\n")
    return "\n".join(lines)
