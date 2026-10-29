"""Draw the board and highlight your selected piece and legal destinations.

Selection markers are informational only — no piece moves until you preview
and type F in the command layer.
"""

import os
from typing import List, Tuple

from .constants import (
    BOARD_SIZE,
    RESET,
    LIGHT_SQUARE_BG, DARK_SQUARE_BG, LIGHT_TEXT_FG, DARK_TEXT_FG,
    COMPARE_WIDTH,
    in_bounds, color_name, row_col_text,
)
from .board import Board
from .movegen import generate_moves, legal_destination_map


def enable_windows_colors() -> None:
    """Turn on ANSI color codes in the Windows console, if possible."""
    if os.name != "nt":
        return
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
        kernel32.GetStdHandle.restype = wintypes.HANDLE
        kernel32.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetConsoleMode.restype = wintypes.BOOL
        kernel32.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel32.SetConsoleMode.restype = wintypes.BOOL
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = wintypes.DWORD()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):\
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def selected_destinations(board: Board, row: int, col: int) -> List[List[bool]]:
    """Returns destination map for selected piece, verifying ownership."""
    if not in_bounds(row, col) or board.grid[row][col].color != board.turn:
        return [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    return legal_destination_map(board, row, col, board.turn)


def print_selection_near_prompt(board: Board, row: int, col: int) -> None:
    """One-line hint of legal destinations right after you pick a start square."""
    if not in_bounds(row, col):
        return

    destinations = selected_destinations(board, row, col)
    from_sq = row_col_text(row, col)
    dest_list = []
    # List destinations rank 8 -> 1, file a -> h (easy to scan).
    for r in range(BOARD_SIZE - 1, -1, -1):
        for c in range(BOARD_SIZE):
            if destinations[r][c]:
                dest_list.append(row_col_text(r, c))

    if dest_list:
        print(f"Selected {from_sq} -> {' '.join(dest_list)}")
    else:
        print(f"Selected {from_sq} -> (no legal moves)")


def display(board: Board, selected_row: int = -1, selected_col: int = -1) -> None:
    """Show ASCII then colored board; optional [piece], *, (capture) highlights."""
    # Plain grid first (works even if colors fail).
    print("\n  a b c d e f g h")
    for row in range(BOARD_SIZE):
        symbols = ["." if piece.is_empty else piece.symbol for piece in board.grid[row]]
        print(f"{BOARD_SIZE - row} {' '.join(symbols)}")

    destinations = selected_destinations(board, selected_row, selected_col)

    # Colored board with selection / destination markers.
    print("\n    a   b   c   d   e   f   g   h")
    print("  +---+---+---+---+---+---+---+---+")

    for row in range(BOARD_SIZE):
        line_parts = [f"{8 - row} |"]
        for col in range(BOARD_SIZE):
            piece = board.grid[row][col]
            light_square = ((row + col) % 2 == 0)

            background = LIGHT_SQUARE_BG if light_square else DARK_SQUARE_BG
            foreground = DARK_TEXT_FG if light_square else LIGHT_TEXT_FG

            symbol = piece.symbol
            left = ' '
            right = ' '

            if row == selected_row and col == selected_col:
                left = '['
                right = ']'
            elif destinations[row][col]:
                if piece.is_empty:
                    symbol = '*'
                else:
                    left = '('
                    right = ')'

            line_parts.append(f"{background}{foreground}{left}{symbol}{right}{RESET}|")

        line_parts.append(f" {8 - row}")
        print("".join(line_parts))
        print("  +---+---+---+---+---+---+---+---+")

    print("    a   b   c   d   e   f   g   h\n")

    if in_bounds(selected_row, selected_col):
        piece = board.grid[selected_row][selected_col]
        dest_sqs = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if destinations[r][c]:
                    dest_sqs.append(row_col_text(r, c))

        at = row_col_text(selected_row, selected_col)
        print(f"SELECTED: {color_name(piece.color)} {piece.type} at {at}")
        if dest_sqs:
            print(f"LEGAL DESTINATIONS: {' '.join(dest_sqs)}")
        else:
            print("LEGAL DESTINATIONS: (none)")
        print(f"TOTAL: {len(dest_sqs)} square(s)")
        print("LEGEND: [P]=selected piece, *=empty legal destination, (p)=legal capture")
        print("Selection is informational: no piece has moved.\n")


def list_piece_moves(position: Board, row: int, col: int) -> str:
    """Returns the legal destinations for a piece as a space-separated string."""
    if not in_bounds(row, col):
        return ""
    piece = position.grid[row][col]
    if piece.is_empty:
        return ""

    view = position.clone()
    view.turn = piece.color
    moves = generate_moves(view)

    seen = set()
    result = []
    for m in moves:
        if m.sr == row and m.sc == col and (m.er, m.ec) not in seen:
            seen.add((m.er, m.ec))
            result.append(row_col_text(m.er, m.ec))

    return " ".join(result) if result else "(none)"


def next_chunk(source: str, at: int, width: int = COMPARE_WIDTH) -> Tuple[str, int]:
    """Extracts the next word-wrapped chunk of text up to width characters."""
    length = len(source)
    if width <= 0:
        return "", length
    if at < 0:
        at = 0

    while at < length and source[at] == ' ':
        at += 1

    if at >= length:
        return "", at

    words = []
    curr_len = 0
    curr_at = at

    while curr_at < length:
        # Find next space
        space_idx = source.find(' ', curr_at)
        word = source[curr_at:] if space_idx == -1 else source[curr_at:space_idx]
        word_len = len(word)
        sep_len = 1 if words else 0

        if curr_len + sep_len + word_len > width:
            if not words:
                # Word itself exceeds width, take substring
                chunk = word[:width]
                return chunk, curr_at + width
            break

        words.append(word)
        curr_len += sep_len + word_len
        curr_at += word_len
        while curr_at < length and source[curr_at] == ' ':
            curr_at += 1

    return " ".join(words), curr_at


def print_side_by_side(before: str, after: str, width: int = COMPARE_WIDTH) -> None:
    """Prints two strings side-by-side in aligned columns."""
    left_offset = 0
    right_offset = 0
    before_len = len(before)
    after_len = len(after)

    while left_offset < before_len or right_offset < after_len:
        left_chunk, left_offset = next_chunk(before, left_offset, width)
        right_chunk, right_offset = next_chunk(after, right_offset, width)
        print(f"{left_chunk:<{width}} | {right_chunk}")
