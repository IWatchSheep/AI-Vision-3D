"""Watch legal chess moves fill a fixed strategy blueprint.

Split across small modules so each file stays easy to read:

  play_types.py      data classes and spoken-move text
  play_rank.py       ranking dolls and fill moves
  play_session.py    the live game + blueprint session
  play_format.py     printed reports
  play_commands.py   typed command handling

This file re-exports the public names used by show_play and the tests.
"""

from calculator.play_commands import HELP, handle_command
from calculator.play_format import (
    format_accept,
    format_imagine,
    format_position,
    mark_at,
)
from calculator.play_rank import (
    as_engine_rows,
    auto_moves,
    legal_fill_moves,
    next_imaginary_move,
    rank_strategies,
    target_choices,
)
from calculator.play_session import PlaySession
from calculator.play_types import (
    PIECE_NAMES,
    RankedStrategy,
    TargetChoice,
    TheoreticalLine,
    TheoreticalStep,
    piece_phrase,
    spoken_move,
)

# Older private names kept for existing tests.
_as_rows = as_engine_rows
_mark_at = mark_at

__all__ = [
    "HELP",
    "PIECE_NAMES",
    "PlaySession",
    "RankedStrategy",
    "TargetChoice",
    "TheoreticalLine",
    "TheoreticalStep",
    "auto_moves",
    "format_accept",
    "format_imagine",
    "format_position",
    "handle_command",
    "legal_fill_moves",
    "next_imaginary_move",
    "piece_phrase",
    "rank_strategies",
    "spoken_move",
    "target_choices",
    "_as_rows",
    "_mark_at",
]
