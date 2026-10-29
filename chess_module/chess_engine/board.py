"""Board state: pieces, turn, castling, en passant, clocks, history.

Think of Board as the whole game position — not just the 8x8 grid.
Draw rules live in board_draws.py; position keys live in board_key.py.
"""

from typing import List, Optional, Tuple, TYPE_CHECKING

from .constants import (
    BOARD_SIZE, Color, WHITE, BLACK,
    HISTORY_MAX_LEN,
)
from .piece import Piece, empty_piece
from . import board_draws
from . import board_key

if TYPE_CHECKING:
    from .move import Move


class Board:
    """Full game position: grid, side to move, castling, EP, clocks, history.

    grid[row][col] uses the same layout as constants.py (row 0 = Black's rank 8).
    """

    def __init__(self):
        self.grid: List[List[Piece]] = [
            [empty_piece() for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
        ]
        self.turn: Color = WHITE
        self.white_king_moved: bool = False
        self.black_king_moved: bool = False
        self.white_rook_a_moved: bool = False
        self.white_rook_h_moved: bool = False
        self.black_rook_a_moved: bool = False
        self.black_rook_h_moved: bool = False
        self.ep_row: int = -1
        self.ep_col: int = -1
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1
        self.history: List[str] = []

    def clone(self) -> "Board":
        """Creates a deep copy of the board."""
        new_b = Board()
        new_b.grid = [
            [self.grid[r][c] for c in range(BOARD_SIZE)] for r in range(BOARD_SIZE)
        ]
        new_b.turn = self.turn
        new_b.white_king_moved = self.white_king_moved
        new_b.black_king_moved = self.black_king_moved
        new_b.white_rook_a_moved = self.white_rook_a_moved
        new_b.white_rook_h_moved = self.white_rook_h_moved
        new_b.black_rook_a_moved = self.black_rook_a_moved
        new_b.black_rook_h_moved = self.black_rook_h_moved
        new_b.ep_row = self.ep_row
        new_b.ep_col = self.ep_col
        new_b.halfmove_clock = self.halfmove_clock
        new_b.fullmove_number = self.fullmove_number
        new_b.history = list(self.history)
        return new_b

    def reset_board(self) -> None:
        """Resets the board to the standard starting chess position."""
        back_row = "RNBQKBNR"
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                self.grid[r][c] = empty_piece()

        for c in range(BOARD_SIZE):
            self.grid[0][c] = Piece(type=back_row[c], color=BLACK)
            self.grid[1][c] = Piece(type="P", color=BLACK)
            self.grid[6][c] = Piece(type="P", color=WHITE)
            self.grid[7][c] = Piece(type=back_row[c], color=WHITE)

        self.turn = WHITE
        self.white_king_moved = False
        self.black_king_moved = False
        self.white_rook_a_moved = False
        self.white_rook_h_moved = False
        self.black_rook_a_moved = False
        self.black_rook_h_moved = False
        self.ep_row = -1
        self.ep_col = -1
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.history = []
        self.record_position()

    def record_position(self) -> None:
        """Remember this position for repetition draws (oldest dropped if full)."""
        self.history.append(self.position_key())
        if len(self.history) > HISTORY_MAX_LEN:
            overflow = len(self.history) - HISTORY_MAX_LEN
            del self.history[:overflow]

    def position_key(self) -> str:
        return board_key.position_key(self)

    def repetition_count(self, key: Optional[str] = None) -> int:
        return board_key.repetition_count(self, key)

    def dead_position(self) -> bool:
        return board_draws.dead_position(self)

    def automatic_draw(self) -> Tuple[bool, Optional[str]]:
        return board_draws.automatic_draw(self)

    def insufficient_mating_material(self, side: Color) -> bool:
        return board_draws.insufficient_mating_material(self, side)

    def claimable_draw(
        self, intended_move: Optional["Move"] = None
    ) -> Tuple[bool, Optional[str]]:
        return board_draws.claimable_draw(self, intended_move)

    def to_fen(self) -> str:
        from .fen import board_to_fen
        return board_to_fen(self)

    def load_fen(self, fen: str) -> Tuple[bool, Optional[str]]:
        from .fen import load_fen_into
        return load_fen_into(self, fen)
