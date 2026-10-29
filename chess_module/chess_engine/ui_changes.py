"""Build the BEFORE/AFTER preview when you enter a destination (step 2).

Clones the board, simulates the move for display only, then reminds you to
press F to finalize or P/N to change your choice.
"""

from typing import Tuple

from .constants import (
    BOARD_SIZE, WHITE, BLACK,
    COMPARE_WIDTH,
    in_bounds, row_col_text,
    CASTLE_KINGSIDE_KING_DEST_COL, CASTLE_QUEENSIDE_KING_DEST_COL,
    ROOK_KINGSIDE_START_COL, ROOK_QUEENSIDE_START_COL,
    CASTLE_KINGSIDE_ROOK_DEST_COL, CASTLE_QUEENSIDE_ROOK_DEST_COL,
)
from .move import Move
from .board import Board
from .movegen import legal_destination_map, make_move, legal_move, move_is_en_passant
from .ui_board import list_piece_moves, print_side_by_side


def is_en_passant_capture(before: Board, proposed: Move, row: int, col: int) -> bool:
    """Checks if the piece on (row, col) is captured by en passant during proposed move."""
    if not in_bounds(proposed.sr, proposed.sc):
        return False
    moving_piece = before.grid[proposed.sr][proposed.sc]
    return (
        move_is_en_passant(before, proposed, moving_piece)
        and row == proposed.sr
        and col == proposed.ec
    )


def resolve_piece_after_move(
    before: Board, proposed: Move, row: int, col: int
) -> Tuple[int, int, bool]:
    """Where the piece on (row, col) ends up after `proposed`, plus captured flag.

    Returns (after_row, after_col, captured). Captured pieces keep their old
    square coords; callers should ignore destination maps for them.
    """
    if not in_bounds(row, col):
        return row, col, False
    if not (in_bounds(proposed.sr, proposed.sc) and in_bounds(proposed.er, proposed.ec)):
        return row, col, False

    after_row = row
    after_col = col
    captured = False

    if row == proposed.er and col == proposed.ec:
        captured = True

    if is_en_passant_capture(before, proposed, row, col):
        captured = True

    moving_piece = before.grid[proposed.sr][proposed.sc]
    is_castling = (
        moving_piece.type == "K"
        and proposed.sr == proposed.er
        and abs(proposed.ec - proposed.sc) == 2
        and row == proposed.sr
    )
    if is_castling:
        if (
            proposed.ec == CASTLE_KINGSIDE_KING_DEST_COL
            and col == ROOK_KINGSIDE_START_COL
            and before.grid[row][col].type == "R"
            and before.grid[row][col].color == moving_piece.color
        ):
            after_col = CASTLE_KINGSIDE_ROOK_DEST_COL
        if (
            proposed.ec == CASTLE_QUEENSIDE_KING_DEST_COL
            and col == ROOK_QUEENSIDE_START_COL
            and before.grid[row][col].type == "R"
            and before.grid[row][col].color == moving_piece.color
        ):
            after_col = CASTLE_QUEENSIDE_ROOK_DEST_COL

    return after_row, after_col, captured


def print_piece_changes(
    before: Board, after: Board,
    before_row: int, before_col: int,
    after_row: int, after_col: int,
    captured: bool
) -> None:
    """Compares destinations before and after move, reporting GAINED, LOST, UNCHANGED."""
    if captured:
        print("    CHANGE: CAPTURED - this piece has no AFTER moves.")
        return
    if not (in_bounds(before_row, before_col) and in_bounds(after_row, after_col)):
        return

    side = before.grid[before_row][before_col].color
    old_dest = legal_destination_map(before, before_row, before_col, side)
    new_dest = legal_destination_map(after, after_row, after_col, side)

    gained = []
    lost = []
    unchanged = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            in_new = new_dest[r][c]
            in_old = old_dest[r][c]
            sq = row_col_text(r, c)
            if in_new and not in_old:
                gained.append(sq)
            elif in_old and not in_new:
                lost.append(sq)
            elif in_old and in_new:
                unchanged.append(sq)

    if not gained and not lost:
        print("    CHANGE: UNCHANGED - no destinations gained or lost.")
    else:
        print("    CHANGE: destinations changed.")

    print(f"    GAINED: {' '.join(gained) if gained else '(none)'}")
    print(f"    LOST: {' '.join(lost) if lost else '(none)'}")
    print(f"    UNCHANGED: {' '.join(unchanged) if unchanged else '(none)'}")


def compare_all_other_pieces(before: Board, after: Board, proposed: Move) -> None:
    """Generates the complete side-by-side comparative report for every other piece."""
    # Walk both colors; skip the piece the player is moving.
    for side in (WHITE, BLACK):
        side_name = "WHITE" if side == WHITE else "BLACK"
        print("")
        print(f"{side_name} PIECES (excluding selected piece)")
        print_side_by_side(
            "BEFORE: square piece -> legal destinations",
            "AFTER: square piece -> legal destinations"
        )
        print("-" * COMPARE_WIDTH + "+" + "-" * COMPARE_WIDTH)

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = before.grid[row][col]
                if piece.color != side or (row == proposed.sr and col == proposed.sc):
                    continue

                after_row, after_col, captured = resolve_piece_after_move(before, proposed, row, col)

                before_moves = list_piece_moves(before, row, col)
                before_desc = f"{row_col_text(row, col)} {piece.symbol}: {before_moves}"

                if captured:
                    after_desc = f"(captured at {row_col_text(row, col)})"
                else:
                    after_piece = after.grid[after_row][after_col]
                    after_moves = list_piece_moves(after, after_row, after_col)
                    after_desc = (
                        f"{row_col_text(after_row, after_col)} "
                        f"{after_piece.symbol}: {after_moves}"
                    )

                print_side_by_side(before_desc, after_desc)
                print_piece_changes(before, after, row, col, after_row, after_col, captured)


def show_step2_after(board: Board, proposed: Move) -> None:
    """Preview a move: print BEFORE/AFTER for every other piece. Board is not changed."""
    if not legal_move(board, proposed):
        raise ValueError("Cannot preview an illegal move")
    # Simulate on a copy — real board and turn stay until F in cli_move_cmds.
    simulated = board.clone()
    start = row_col_text(proposed.sr, proposed.sc)
    end = row_col_text(proposed.er, proposed.ec)
    print(f"\nPREVIEW ONLY: {start} -> {end} (NOT PLAYED)")
    make_move(simulated, proposed)

    print("Widen your console to about 140 columns for the two-column report.")
    print("CHANGE shows gained, lost, and unchanged destinations for each other piece.")
    print("LEGAL MOVE LIST NOTE: Each side is evaluated as if it were that side's turn.")
    print("Black and White possibilities are shown for comparison; only the actual")
    print("side to move can play immediately. Check restrictions still apply.")

    compare_all_other_pieces(board, simulated, proposed)

    print("\nThe real board and player turn have NOT changed.")
    print("Press F then Enter to FINALIZE this previewed move.")
    print("Press P then Enter to preview another destination, or N for a new piece.")
