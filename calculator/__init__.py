"""
Calculator package.

Layout for beginners
--------------------
  strategies_data.py  -> raw 20 doll records (ASCII boards)
  strategies.py       -> Strategy type, load/validate/print dolls
  pattern.py          -> chess doll compare / rank / fill
  shape.py            -> 5x5 shape compare / rank / fill / imagine
  window.py           -> shared past/current/accept notepad
  interface.py        -> generic Action / Observation messages

Import tip
----------
  Chess:  from calculator.pattern import compare, print_chess_fill
  Shapes: from calculator.shape import compare, print_shape_fill

Both modules define compare / rank / print_fill. Import from the submodule
you mean so you do not grab the wrong one.
"""

from calculator.pattern import (
    CompareResult,
    PatternWindow,
    print_doll_on_record,
    print_strategy_forming_list,
)
from calculator.strategies import (
    BOARD_SIZE,
    STRATEGIES,
    Strategy,
    board_to_fen_pieces,
    fen_piece_field,
    get_strategy,
    print_joints,
    print_strategy,
    require_board,
)

__all__ = [
    "BOARD_SIZE",
    "CompareResult",
    "PatternWindow",
    "STRATEGIES",
    "Strategy",
    "board_to_fen_pieces",
    "fen_piece_field",
    "get_strategy",
    "print_doll_on_record",
    "print_joints",
    "print_strategy",
    "print_strategy_forming_list",
    "require_board",
]
