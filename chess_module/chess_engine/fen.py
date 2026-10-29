"""Load and save board positions as FEN strings.

Split across fen_write.py (board -> text) and fen_load.py (text -> board).
"""

from .fen_load import load_fen_into
from .fen_write import board_to_fen

__all__ = ["board_to_fen", "load_fen_into"]
