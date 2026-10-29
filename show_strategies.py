#!/usr/bin/env python3
"""
Console program: show the 20 strategy dolls and how they fill against seen boards.

Display only. Does not accept a compare into PatternWindow.past.
Does not move joints.
"""

from calculator.pattern import (
    print_doll_on_record,
    print_strategy_forming_list,
)
from calculator.strategies import STRATEGIES, get_strategy, print_strategy


def _print_board(board: list[str]) -> None:
    """Print eight board lines."""
    for row in board:
        print(row)


def main() -> None:
    # 1) Print every doll on record.
    print("=== Strategy dolls on record ===")
    print()
    for strategy in STRATEGIES:
        print_strategy(strategy)
        print()

    starting = get_strategy("starting-array")
    develop = get_strategy("develop-to-the-center")
    kings_pawn = get_strategy("kings-pawn-promotion")

    # 2) Seen board = starting array (beginning of a game).
    print("=== What the calculator sees at the beginning. ===")
    _print_board(starting.board)
    print()
    print_doll_on_record(kings_pawn, starting.board)
    print()
    print_doll_on_record(develop, starting.board)
    print()
    print_strategy_forming_list(starting.board)
    print()

    # 3) Seen board = develop-to-the-center (formed end doll itself).
    print("=== What the calculator sees at the formed end. ===")
    _print_board(develop.board)
    print()
    print_doll_on_record(develop, develop.board)
    print()
    print_doll_on_record(kings_pawn, develop.board)
    print()
    print_strategy_forming_list(develop.board)


if __name__ == "__main__":
    main()
