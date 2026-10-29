"""One candidate move: start square, end square, optional promotion letter.

Used everywhere moves are parsed, sorted, compared, or sent to the legality checker.
"""

from dataclasses import dataclass
from typing import Optional

from .constants import PROMOTION_PIECES, parse_square, in_bounds, row_col_text


def promotion_rank(promotion: str) -> int:
    """Sort order for promotions: Q, R, B, N, then none."""
    if not isinstance(promotion, str):
        return 0
    order = {"Q": 1, "R": 2, "B": 3, "N": 4}
    return order.get(promotion, 0)


@dataclass(frozen=True, slots=True)
class Move:
    sr: int  # start row
    sc: int  # start col
    er: int  # end row
    ec: int  # end col
    promotion: str = "\0"  # 'Q','R','B','N' or '\0'

    @property
    def is_kingside_castle(self) -> bool:
        """King moved two files toward h (used only for king castling moves)."""
        return self.ec > self.sc

    @property
    def uci(self) -> str:
        """UCI text like 'e2e4' or 'e7e8q'. Uses '????' if coords are invalid."""
        if not (in_bounds(self.sr, self.sc) and in_bounds(self.er, self.ec)):
            return "????"
        promo = ""
        if isinstance(self.promotion, str) and self.promotion and self.promotion != "\0":
            promo = self.promotion.lower()
        return f"{row_col_text(self.sr, self.sc)}{row_col_text(self.er, self.ec)}{promo}"

    def sort_key(self) -> tuple:
        """Stable order matching the C compare_moves rules."""
        return (self.sr, self.sc, self.er, self.ec, promotion_rank(self.promotion))

    def __lt__(self, other: "Move") -> bool:
        """Enables sorted(moves) to use the same order as the C engine."""
        return self.sort_key() < other.sort_key()


def parse_move_text(text: str) -> Optional[Move]:
    """Parse 'e2e4' or 'e7e8q'. Returns None if the text is not a move."""
    # Reject non-ASCII or wrong length so junk input cannot become a Move.
    if not isinstance(text, str) or not text.isascii() or len(text) not in (4, 5):
        return None

    start = parse_square(text[0:2])
    end = parse_square(text[2:4])
    if not start or not end:
        return None

    promo = "\0"
    if len(text) == 5:
        letter = text[4].upper()
        if letter not in PROMOTION_PIECES:
            return None
        promo = letter

    sr, sc = start
    er, ec = end
    return Move(sr=sr, sc=sc, er=er, ec=ec, promotion=promo)
