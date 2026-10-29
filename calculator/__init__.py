"""Chess strategy calculator: hardcoded dolls and fill comparison."""

from calculator.pattern import (
    CompareResult,
    PatternWindow,
    compare,
    print_doll_on_record,
    print_fill,
    print_greatest_target_list,
    print_strategy_forming_list,
    rank,
)
from calculator.strategies import (
    STRATEGIES,
    Strategy,
    board_to_fen_pieces,
    fen_piece_field,
    get_strategy,
    print_joints,
    print_strategy,
)

__all__ = [
    "CompareResult",
    "PatternWindow",
    "STRATEGIES",
    "Strategy",
    "board_to_fen_pieces",
    "compare",
    "fen_piece_field",
    "get_strategy",
    "print_doll_on_record",
    "print_fill",
    "print_greatest_target_list",
    "print_joints",
    "print_strategy",
    "print_strategy_forming_list",
    "rank",
]
