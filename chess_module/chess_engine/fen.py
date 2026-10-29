"""Load and save board positions as FEN strings.

FEN is the standard text format (piece placement, turn, castling, EP, clocks).
Parsing is strict: bad material, illegal EP, or oversized text is rejected.
"""

from typing import Optional, Tuple, TYPE_CHECKING

from .constants import (
    BOARD_SIZE, Color, EMPTY, WHITE, BLACK,
    FEN_NUMBER_MAX_DIGITS, FEN_TEXT_MAX,
    in_bounds, opposite, parse_square, parse_nonneg_int,
)
from .piece import Piece

if TYPE_CHECKING:
    from .board import Board


def board_to_fen(board: "Board") -> str:
    """Serializes board state into FEN notation."""
    parts = []
    # 1. Piece placement
    placement = []
    for r in range(BOARD_SIZE):
        empty_count = 0
        row_chars = []
        for c in range(BOARD_SIZE):
            p = board.grid[r][c]
            if p.is_empty:
                empty_count += 1
            else:
                if empty_count > 0:
                    row_chars.append(str(empty_count))
                    empty_count = 0
                row_chars.append(p.symbol)
        if empty_count > 0:
            row_chars.append(str(empty_count))
        placement.append("".join(row_chars))
    parts.append("/".join(placement))

    # 2. Side to move
    parts.append("w" if board.turn == WHITE else "b")

    # 3. Castling rights
    castling = []
    if not board.white_king_moved and not board.white_rook_h_moved:
        castling.append("K")
    if not board.white_king_moved and not board.white_rook_a_moved:
        castling.append("Q")
    if not board.black_king_moved and not board.black_rook_h_moved:
        castling.append("k")
    if not board.black_king_moved and not board.black_rook_a_moved:
        castling.append("q")
    parts.append("".join(castling) if castling else "-")

    # 4. En passant target square
    if in_bounds(board.ep_row, board.ep_col):
        parts.append(f"{chr(ord('a') + board.ep_col)}{8 - board.ep_row}")
    else:
        parts.append("-")

    # 5. Halfmove clock
    parts.append(str(board.halfmove_clock))

    # 6. Fullmove number
    parts.append(str(board.fullmove_number))

    return " ".join(parts)


def load_fen_into(board: "Board", fen: str) -> Tuple[bool, Optional[str]]:
    """Parses, validates, and loads a chess position from a FEN string into board."""
    from .attacks import find_king, is_in_check, count_attackers
    from .board import Board

    if not fen:
        return False, "FEN text is missing"
    if not isinstance(fen, str):
        return False, "FEN text is missing"
    # Reject oversized input before any heavy parsing (DoS guard).
    if len(fen) > FEN_TEXT_MAX:
        return False, "FEN text is too long"

    fields = fen.strip().split()
    if len(fields) not in (4, 6):
        return False, "a FEN has 6 fields (or 4) separated by single spaces"

    # Parse into a temporary board first — reject bad FEN before touching `board`.
    new_b = Board()

    # Field 1: Piece placement
    ranks = fields[0].split('/')
    if len(ranks) != 8:
        return False, "the board must have exactly 8 ranks of 8 squares"

    for r, rank_str in enumerate(ranks):
        col = 0
        previous_digit = False
        for ch in rank_str:
            # Require ASCII '1'..'8' only — Python's str.isdigit() also
            # accepts Unicode decimal digits, which are not valid FEN.
            if ch.isascii() and ch.isdigit():
                if previous_digit:
                    return False, "consecutive empty-square digits in a rank"
                previous_digit = True
                digit = int(ch)
                if digit < 1 or digit > 8:
                    return False, "a rank does not have exactly 8 squares"
                col += digit
                if col > 8:
                    return False, "a rank does not have exactly 8 squares"
            elif ch.isascii() and ch.isalpha():
                previous_digit = False
                upper = ch.upper()
                if upper not in "PNBRQK":
                    return False, "unknown piece letter"
                if col >= 8:
                    return False, "a rank does not have exactly 8 squares"
                piece_color = WHITE if ch.isupper() else BLACK
                new_b.grid[r][col] = Piece(type=upper, color=piece_color)
                col += 1
            else:
                return False, "unknown piece letter"
        if col != 8:
            return False, "a rank does not have exactly 8 squares"

    # Field 2: Side to move
    if fields[1] not in ("w", "b"):
        return False, "side to move must be w or b"
    new_b.turn = WHITE if fields[1] == "w" else BLACK

    # Validate piece material counts
    for side in (WHITE, BLACK):
        counts = {p: 0 for p in "PNBRQK"}
        bishop_shades = [0, 0]
        total = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = new_b.grid[r][c]
                if p.color == side:
                    counts[p.type] += 1
                    if p.type == 'B':
                        bishop_shades[(r + c) % 2] += 1
                    total += 1
                    if p.type == 'P' and (r == 0 or r == 7):
                        return False, "a pawn is on the first or last rank"

        if counts['K'] != 1:
            return False, "White must have exactly one king" if side == WHITE else "Black must have exactly one king"

        promoted = (
            max(0, counts['Q'] - 1) +
            max(0, counts['R'] - 2) +
            sum(max(0, count - 1) for count in bishop_shades) +
            max(0, counts['N'] - 2)
        )
        if counts['P'] > 8 or total > 16 or promoted > (8 - counts['P']):
            return False, "White has more pieces than a game allows" if side == WHITE else "Black has more pieces than a game allows"

    # Field 3: Castling rights
    castling_field = fields[2]
    wk = wq = bk = bq = False
    if castling_field != "-":
        order = "KQkq"
        curr_idx = 0
        for ch in castling_field:
            pos = order.find(ch, curr_idx)
            if pos == -1:
                return False, "castling field must be - or letters from KQkq in that order"
            curr_idx = pos + 1
            if ch == 'K': wk = True
            elif ch == 'Q': wq = True
            elif ch == 'k': bk = True
            elif ch == 'q': bq = True

    def piece_at(r, c, t, colr):
        return new_b.grid[r][c].type == t and new_b.grid[r][c].color == colr

    if (wk or wq) and not piece_at(7, 4, 'K', WHITE):
        return False, "White castling right without the king on e1"
    if (bk or bq) and not piece_at(0, 4, 'K', BLACK):
        return False, "Black castling right without the king on e8"
    if (wk and not piece_at(7, 7, 'R', WHITE)) or (wq and not piece_at(7, 0, 'R', WHITE)) or \
       (bk and not piece_at(0, 7, 'R', BLACK)) or (bq and not piece_at(0, 0, 'R', BLACK)):
        return False, "castling right without the rook on its starting square"

    new_b.white_king_moved = not (wk or wq)
    new_b.black_king_moved = not (bk or bq)
    new_b.white_rook_h_moved = not wk
    new_b.white_rook_a_moved = not wq
    new_b.black_rook_h_moved = not bk
    new_b.black_rook_a_moved = not bq

    # Field 4: En passant
    ep_field = fields[3]
    if ep_field != "-":
        parsed = parse_square(ep_field)
        if not parsed or len(ep_field) != 2:
            return False, "en passant field must be - or a square"
        r, c = parsed
        expected_row = 2 if new_b.turn == WHITE else 5
        pawn_row = 3 if new_b.turn == WHITE else 4
        start_row = 1 if new_b.turn == WHITE else 6
        mover = opposite(new_b.turn)
        if r != expected_row:
            return False, "en passant square is on the wrong rank for the side to move"
        if not piece_at(pawn_row, c, 'P', mover) or \
           new_b.grid[r][c].color != EMPTY or \
           new_b.grid[start_row][c].color != EMPTY:
            return False, "en passant square does not match a pawn that just moved two squares"
        new_b.ep_row = r
        new_b.ep_col = c
    else:
        new_b.ep_row = -1
        new_b.ep_col = -1

    # Fields 5 & 6 (digit-length capped — avoids huge-int DoS from bad FEN)
    if len(fields) == 6:
        halfmove = parse_nonneg_int(fields[4], FEN_NUMBER_MAX_DIGITS)
        fullmove = parse_nonneg_int(fields[5], FEN_NUMBER_MAX_DIGITS)
        if halfmove is None or fullmove is None or fullmove < 1:
            return False, (
                "halfmove clock and move number must be whole numbers "
                "(move number at least 1)"
            )
        new_b.halfmove_clock = halfmove
        new_b.fullmove_number = fullmove
        if ep_field != "-" and halfmove != 0:
            return False, "en passant requires a zero halfmove clock"

    # Verify king presence and legality
    if is_in_check(new_b, opposite(new_b.turn)):
        return False, "the side that is not to move is in check"

    king_pos = find_king(new_b, new_b.turn)
    if not king_pos:
        return False, "the side to move has no king"

    if count_attackers(new_b, king_pos[0], king_pos[1], opposite(new_b.turn)) > 2:
        return False, "the king to move is attacked by more than two pieces"

    # Transfer loaded state to self
    board.grid = new_b.grid
    board.turn = new_b.turn
    board.white_king_moved = new_b.white_king_moved
    board.black_king_moved = new_b.black_king_moved
    board.white_rook_a_moved = new_b.white_rook_a_moved
    board.white_rook_h_moved = new_b.white_rook_h_moved
    board.black_rook_a_moved = new_b.black_rook_a_moved
    board.black_rook_h_moved = new_b.black_rook_h_moved
    board.ep_row = new_b.ep_row
    board.ep_col = new_b.ep_col
    board.halfmove_clock = new_b.halfmove_clock
    board.fullmove_number = new_b.fullmove_number
    board.history = []
    board.record_position()
    return True, None
