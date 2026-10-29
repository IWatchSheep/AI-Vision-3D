#!/usr/bin/env python3
"""Console program: show the 20 strategy dolls and how they fill against seen boards.

Display only. Does not accept a compare into PatternWindow past.
"""

from calculator.pattern import (
    compare,
    print_doll_on_record,
    print_fill,
    print_greatest_target_list,
    print_strategy_forming_list,
)
from calculator.strategies import STRATEGIES, get_strategy, print_strategy


def main() -> None:
    # 1. All 20 dolls
    print("=== Strategy dolls on record ===")
    print()
    for strategy in STRATEGIES:
        print_strategy(strategy)
        print()

    starting = get_strategy("starting-array")
    develop = get_strategy("develop-to-the-center")
    kings_pawn = get_strategy("kings-pawn-promotion")

    # 2. Seen board: starting array
    print("=== What the calculator sees at the beginning. ===")
    for row in starting.board:
        print(row)
    print()
    print_doll_on_record(kings_pawn, starting.board)
    print()
    print_doll_on_record(develop, starting.board)
    print()
    print_strategy_forming_list(starting.board)
    print()

    # 3. Seen board: develop-to-the-center
    print("=== What the calculator sees at the formed end. ===")
    for row in develop.board:
        print(row)
    print()
    print("Doll on record: develop-to-the-center")
    result_dev = compare(develop, develop.board)
    print_fill(result_dev)
    print_greatest_target_list(result_dev, develop.board)
    print()
    print("Doll on record: kings-pawn-promotion")
    result_kp = compare(kings_pawn, develop.board)
    print_fill(result_kp)
    print_greatest_target_list(result_kp, develop.board)
    print()
    print_strategy_forming_list(develop.board)


if __name__ == "__main__":
    main()
