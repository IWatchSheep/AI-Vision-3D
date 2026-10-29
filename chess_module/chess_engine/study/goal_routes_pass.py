"""PASS routes reports for goals (Stage 3D).

PASS = only the side to move moves; the opponent always passes. Reports list
shortest distances, enumerate example paths, mark dominated routes, and can
chain a optional second goal after the first square is reached.
"""

from ..search_budget import bounded_search

from typing import List, Optional

from ..constants import (
    BOARD_SIZE,
    WHITE, BLACK,
    GOAL_MAX_ROUTES,
    opposite, color_name, square_text,
)
from ..move import Move
from ..board import Board
from .common import (
    Goal, GoalCondition, RouteVector,
    get_goal_show_risk, order_label,
    pass_moves, pass_play, pieces_on_square, piece_value,
)
from .goal_basics import (
    goal_squares, goal_text, goal_holds, piece_distance, side_distance,
)


def mark_dominated(routes: List[RouteVector]) -> None:
    """Marks routes as dominated if another route is strictly better or equal in all metrics."""
    for i, a in enumerate(routes):
        for j, b in enumerate(routes):
            if i == j:
                continue
            no_worse = (b.own <= a.own and b.protectors >= a.protectors and b.attackers <= a.attackers)
            better = (b.own < a.own or b.protectors > a.protectors or b.attackers < a.attackers)
            if no_worse and better:
                a.dominated = True
                break


@bounded_search
def routes_report_with(
    board: Board, goal: Goal, second_goal: Optional[Goal] = None, show_risk: bool = False
) -> str:
    """Generates the Stage 3D routes report."""
    lines: List[str] = []
    side = board.turn
    enemy = opposite(side)
    squares = goal_squares(goal, board, side)

    lines.append(f"ROUTES BEGIN {color_name(side)} GOAL {goal_text(goal)} LIMIT {goal.limit} PASS")
    lines.append(f"NOTE PASS is hypothetical: only {color_name(side)} moves, {color_name(enemy)} passes; not a real sequence of turns")

    reach: List[int] = []
    prot: List[int] = []
    first_reach = -1
    saved_routes: List[RouteVector] = []

    for sq in squares:
        sq_str = square_text(sq)
        lines.append(f"GOAL {sq_str} NOW White {pieces_on_square(board, sq, WHITE)} Black {pieces_on_square(board, sq, BLACK)}")

        # PIECE routes
        distances: List[int] = [-2] * 64
        for i in range(64):
            r, c = i // BOARD_SIZE, i % BOARD_SIZE
            if board.grid[r][c].color == side:
                distances[i] = piece_distance(board, r, c, side, sq, goal.limit)

        for i in range(64):
            if distances[i] == -2:
                continue
            r, c = i // BOARD_SIZE, i % BOARD_SIZE
            at = square_text(i)
            ptype = board.grid[r][c].type
            if distances[i] >= 0:
                lines.append(f"PIECE {ptype} {at} CONDITION IF MOVES {distances[i]} ORDER {order_label(distances, distances[i])}")
            else:
                lines.append(f"PIECE {ptype} {at} CONDITION ELSE ORDER NONE")

        route_list: List[RouteVector] = []
        extra_count = 0

        # --- PIECE routes: DFS along pass_moves for exactly distance[i] plies ---
        @bounded_search
        def find_piece_routes(b: Board, r: int, c: int, path: List[Move], length: int, kind: str) -> None:
            nonlocal extra_count
            if len(path) == length:
                if r * BOARD_SIZE + c == sq:
                    if len(route_list) >= GOAL_MAX_ROUTES:
                        extra_count += 1
                        return
                    end_b = b
                    rv = RouteVector(
                        own=length,
                        length=length,
                        path=list(path),
                        protectors=pieces_on_square(end_b, sq, side),
                        attackers=pieces_on_square(end_b, sq, enemy)
                    )
                    path_str = " ".join(m.uci for m in path)
                    raw = f"ROUTE {kind} {path_str} OWN {length} PROTECTORS {rv.protectors} ATTACKERS {rv.attackers}"
                    if show_risk or get_goal_show_risk():
                        at_risk_val = piece_value(end_b.grid[sq // 8][sq % 8].type) if rv.attackers > 0 else 0
                        raw += f" AT-RISK {at_risk_val}"
                    rv.raw_text = raw
                    route_list.append(rv)
                return
            if r * BOARD_SIZE + c == sq:
                return

            moves = pass_moves(b, side)
            for m in moves:
                if m.sr == r and m.sc == c:
                    next_b = b.clone()
                    pass_play(next_b, m, side)
                    path.append(m)
                    find_piece_routes(next_b, m.er, m.ec, path, length, kind)
                    path.pop()

        for i in range(64):
            if distances[i] >= 1:
                r, c = i // BOARD_SIZE, i % BOARD_SIZE
                at = square_text(i)
                kind_str = f"PIECE {board.grid[r][c].type} {at}"
                find_piece_routes(board, r, c, [], distances[i], kind_str)

        # --- SIDE routes: team reach/protect distances and protected-path DFS ---
        r_dist = side_distance(board, side, sq, GoalCondition.COND_REACH, goal.limit)
        p_dist = side_distance(board, side, sq, GoalCondition.COND_PROTECTED, goal.limit)
        reach.append(r_dist)
        prot.append(p_dist)

        lines.append(f"SIDE REACH CONDITION {'IF MOVES ' + str(r_dist) if r_dist >= 0 else 'ELSE'}")
        if p_dist >= 0:
            lines.append(f"SIDE PROTECTED CONDITION IF MOVES {p_dist}")
            if p_dist >= 1:
                @bounded_search
                def find_side_routes(b: Board, path: List[Move], length: int) -> None:
                    nonlocal extra_count
                    holds = goal_holds(b, side, sq, GoalCondition.COND_PROTECTED)
                    if len(path) == length:
                        if holds:
                            if len(route_list) >= GOAL_MAX_ROUTES:
                                extra_count += 1
                                return
                            rv = RouteVector(
                                own=length,
                                length=length,
                                path=list(path),
                                protectors=pieces_on_square(b, sq, side),
                                attackers=pieces_on_square(b, sq, enemy)
                            )
                            path_str = " ".join(m.uci for m in path)
                            raw = f"ROUTE SIDE PROTECTED {path_str} OWN {length} PROTECTORS {rv.protectors} ATTACKERS {rv.attackers}"
                            if show_risk or get_goal_show_risk():
                                at_risk_val = piece_value(b.grid[sq // 8][sq % 8].type) if rv.attackers > 0 else 0
                                raw += f" AT-RISK {at_risk_val}"
                            rv.raw_text = raw
                            route_list.append(rv)
                        return
                    if holds:
                        return
                    moves = pass_moves(b, side)
                    for m in moves:
                        next_b = b.clone()
                        pass_play(next_b, m, side)
                        path.append(m)
                        find_side_routes(next_b, path, length)
                        path.pop()

                find_side_routes(board, [], p_dist)
        else:
            lines.append("SIDE PROTECTED CONDITION ELSE")

        mark_dominated(route_list)
        for rv in route_list:
            if rv.dominated:
                lines.append(f"{rv.raw_text} DOMINATED")
            else:
                lines.append(rv.raw_text)

        if r_dist >= 0 and first_reach < 0:
            first_reach = sq
            saved_routes = list(route_list)

        if extra_count > 0:
            lines.append(f"MORE ROUTES {extra_count} not listed")

    if not squares:
        lines.append("NO SQUARES")

    for k, sq in enumerate(squares):
        lines.append(f"SQUARE {square_text(sq)} REACH CONDITION {'IF' if reach[k] >= 0 else 'ELSE'} PROTECTED CONDITION {'IF' if prot[k] >= 0 else 'ELSE'}")

    for cond_name, dist_arr in (("REACH", reach), ("PROTECTED", prot)):
        first_idx = next((k for k, d in enumerate(dist_arr) if d >= 0), -1)
        if first_idx >= 0:
            lines.append(f"FIRST-IF {cond_name} {square_text(squares[first_idx])}")
        else:
            lines.append(f"FIRST-IF {cond_name} none (ELSE)")

    if second_goal and second_goal.active:
        lines.append(second_goal_report(board, second_goal, first_reach if first_reach >= 0 else None, saved_routes).rstrip())

    lines.append("ROUTES END\n")
    return "\n".join(lines)


def second_from(board: Board, second: Goal, label: str) -> List[str]:
    """PASS distances for the follow-up goal from a labeled board state."""
    squares = goal_squares(second, board, board.turn)
    lines = []
    for sq in squares:
        r_dist = side_distance(board, board.turn, sq, GoalCondition.COND_REACH, second.limit)
        p_dist = side_distance(board, board.turn, sq, GoalCondition.COND_PROTECTED, second.limit)
        r_str = f"CONDITION IF MOVES {r_dist}" if r_dist >= 0 else "CONDITION ELSE"
        p_str = f"CONDITION IF MOVES {p_dist}" if p_dist >= 0 else "CONDITION ELSE"
        lines.append(f"FROM {label} SQUARE {square_text(sq)} REACH {r_str} PROTECTED {p_str}")
    return lines


@bounded_search
def second_goal_report(
    board: Board, second: Goal, first_square: Optional[int], routes: List[RouteVector]
) -> str:
    """After the first REACH square, replay each non-dominated route and re-score."""
    lines = [f"SECOND GOAL {goal_text(second)} LIMIT {second.limit} PASS AFTER {square_text(first_square) if first_square is not None else 'none (ELSE)'}"]
    lines.extend(second_from(board, second, "START"))

    if first_square is not None:
        seen_paths = set()
        for rv in routes:
            if rv.dominated:
                continue
            path_tuple = tuple((m.sr, m.sc, m.er, m.ec, m.promotion) for m in rv.path)
            if path_tuple in seen_paths:
                continue
            seen_paths.add(path_tuple)

            end_b = board.clone()
            for m in rv.path:
                pass_play(end_b, m, board.turn)
            label = " ".join(m.uci for m in rv.path)
            lines.extend(second_from(end_b, second, label))

    lines.append("SECOND END")
    return "\n".join(lines)
