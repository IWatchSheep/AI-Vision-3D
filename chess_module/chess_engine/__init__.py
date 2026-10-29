"""Chess engine package converted from C99 implementation.

Beginner map (open the small file that matches your question):
  main.py               — run the game loop
  cli_commands.py       — routes every typed command
  cli_move_cmds.py      — squares, F finalize, FEN, quit/restart
  ui.py / ui_changes.py — board display and preview (before F)
  board.py / fen.py     — position, draws, load/save FEN
  attacks.py            — can a piece hit a square? is the king in check?
  move_legality.py      — is this Move allowed right now?
  move_apply.py         — play a move on the board
  move_gen.py           — list every legal move
  cli_*.py              — other typed commands (help, goals, analysis)
  study/                — fact reports (calc, replies, goals, exchange)

Playing: start square → destination (preview) → F to play.
"""

from .constants import (
    Color, EMPTY, WHITE, BLACK,
    opposite, color_name,
    in_bounds, square_index, index_to_row_col, square_text, row_col_text,
    parse_square,
)
from .piece import Piece, empty_piece
from .move import Move, parse_move_text
from .board import Board
from .movegen import (
    generate_moves, sorted_moves, legal_move, make_move,
    is_in_check, has_king, game_over
)
from .ui import display, show_step2_after, print_selection_near_prompt
from .tracker import Tracker, position_after
from .analysis import (
    Goal, parse_goal,
    calc_report, replies_report, reply_detail,
    loop_report, trace_report,
    routes_report_with, routes_real_report, support_report,
    exchange_report, order_report, compare_report
)

__all__ = [
    'Color', 'EMPTY', 'WHITE', 'BLACK',
    'opposite', 'color_name',
    'in_bounds', 'square_index', 'index_to_row_col', 'square_text', 'row_col_text',
    'parse_square',
    'Piece', 'empty_piece',
    'Move', 'parse_move_text',
    'Board',
    'generate_moves', 'sorted_moves', 'legal_move', 'make_move',
    'is_in_check', 'has_king', 'game_over',
    'display', 'show_step2_after', 'print_selection_near_prompt',
    'Tracker', 'position_after',
    'Goal', 'parse_goal',
    'calc_report', 'replies_report', 'reply_detail',
    'loop_report', 'trace_report',
    'routes_report_with', 'routes_real_report', 'support_report',
    'exchange_report', 'order_report', 'compare_report'
]
