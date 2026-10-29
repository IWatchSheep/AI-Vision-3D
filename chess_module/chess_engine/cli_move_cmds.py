"""Commands that actually move pieces or control the game.

Square names drive select → preview; F finalizes. FEN loading is capped by
FEN_TEXT_MAX so pasted positions cannot blow memory.
"""

from __future__ import annotations

from typing import Optional

from .constants import (
    FEN_TEXT_MAX,
    opposite, color_name, parse_square, in_bounds,
)
from .move import Move
from .movegen import destination_is_legal, legal_move, make_move
from .ui import print_selection_near_prompt
from .analysis import goal_marks_selection, distance_selection
from .cli_session import GameSession, err, move_label


def handle_cancel(session: GameSession, cmd: str) -> bool:
    """N / NEW / select none / cancel -> clear selection."""
    lower = cmd.lower()
    is_new = lower in ("new", "select none", "cancel")
    is_n = lower == "n" and not session.promotion_pending
    if not (is_new or is_n):
        return False
    session.clear_selection()
    print("Selection cleared. Enter a new start square.")
    return True


def handle_fen(session: GameSession, cmd: str) -> bool:
    """fen  -> print position;  fen <text>  -> load a practice position."""
    lower = cmd.lower()
    if lower == "fen":
        print(f"FEN: {session.board.to_fen()}")
        return True
    if not lower.startswith("fen "):
        return False

    fen_str = cmd[4:].strip()
    # Reject oversized FEN strings before parsing (same idea as MAX_COMMAND_CHARS).
    if len(fen_str) > FEN_TEXT_MAX:
        err("FEN rejected: text is too long. The position is unchanged.")
        return True
    ok, reason = session.board.load_fen(fen_str)
    if ok:
        session.clear_selection()
        session.clear_analysis_options()
        session.memory.clear()
        session.tracker.init_from_board(session.board)
        print("FEN loaded: practice position set up.")
    else:
        err(f"FEN rejected: {reason}. The position is unchanged.")
    return True


def handle_promotion_choice(session: GameSession, cmd: str) -> bool:
    """If a promotion piece is required, accept Q/R/B/N (or keep waiting)."""
    if not session.promotion_pending:
        return False

    # Game-control commands are handled later by handle_game_control.
    if cmd.lower() in ("quit", "exit", "restart", "resign", "claim") or cmd.lower().startswith("claim "):
        return False

    if len(cmd) == 1 and cmd.upper() in "QRBN":
        pending = session.pending_promotion
        if not (in_bounds(pending.sr, pending.sc) and in_bounds(pending.er, pending.ec)):
            err("Promotion state is invalid. Type NEW to cancel and start over.")
            session.clear_selection()
            return True
        move = Move(
            pending.sr, pending.sc, pending.er, pending.ec,
            promotion=cmd.upper(),
        )
        # Re-check with the chosen letter (destination was only pre-checked).
        if not legal_move(session.board, move):
            err("That promotion is not legal. Type NEW to cancel and start over.")
            session.clear_selection()
            return True
        session.set_preview(move)
        return True

    err("Choose Q, R, B or N; or type NEW to cancel.")
    return True


def handle_finalize(session: GameSession, cmd: str) -> bool:
    """F -> play the previewed move for real."""
    if cmd.lower() != "f":
        return False

    if not session.preview_shown or not session.has_selection():
        err("No preview to finalize. Select a piece and preview a destination first.")
        return True

    if not legal_move(session.board, session.preview_move):
        err("Preview is no longer legal. Start a new selection.")
        session.invalidate_preview()
        return True

    # Step 3: apply the previewed move on the real board.
    print(f"FINALIZED: {move_label(session.preview_move)}")
    session.memory.record_finalized()
    session.tracker.commit(session.board, session.preview_move)
    make_move(session.board, session.preview_move)
    session.board.record_position()
    session.clear_selection()
    return True


def handle_discard_preview(session: GameSession, cmd: str) -> bool:
    """P -> keep the selected piece, clear only the destination preview."""
    if cmd.lower() != "p":
        return False
    if not session.has_selection():
        err("Select a piece first.")
    else:
        session.clear_preview_keep_piece()
        print("Preview cleared. Enter another destination for the selected piece.")
    return True


def handle_square_entry(session: GameSession, cmd: str) -> bool:
    """Two-character input: pick a start square, or a destination."""
    if len(cmd) != 2:
        return False

    parsed = parse_square(cmd)
    if not parsed:
        return False

    if session.preview_shown:
        err("Preview already shown. Press F, P or N, then Enter.")
        return True

    row, col = parsed

    # Step 1: pick your own piece on a legal start square.
    if not session.has_selection():
        piece = session.board.grid[row][col]
        if piece.color != session.board.turn:
            err("Choose a square containing your own piece.")
            return True
        session.select_piece(row, col)
        print_selection_near_prompt(session.board, row, col)
        print("Piece selected. BEFORE/AFTER lists will appear after you enter a destination.")
        if session.goal.active:
            print(goal_marks_selection(session.board, session.goal, row, col), end="")
        if session.distance_view:
            print(distance_selection(session.board, row, col), end="")
        return True

    # Step 2: destination → preview (or promotion prompt), not played until F.
    sr = session.selected_row
    sc = session.selected_col
    # Pawn-to-last-rank is legal as a destination before the player names
    # Q/R/B/N; legal_move itself requires the letter once the move is complete.
    if not destination_is_legal(session.board, sr, sc, row, col):
        err("Not a legal destination. Press N then Enter to select a different piece.")
        return True

    chosen = Move(sr=sr, sc=sc, er=row, ec=col)
    piece = session.board.grid[sr][sc]
    if piece.type == "P" and row in (0, 7):
        session.begin_promotion(chosen)
        print("PROMOTION: choose Q (Queen), R (Rook), B (Bishop), or N (Knight).")
        print("Type NEW to cancel and choose a different starting piece.")
        return True

    session.set_preview(chosen)
    return True


def handle_game_control(session: GameSession, cmd: str) -> Optional[str]:
    """quit / restart / resign / claim.

    Returns 'quit', 'handled', or None if not a game-control command.
    """
    lower = cmd.lower()

    # End session or reset position without changing move-flow rules elsewhere.
    if lower in ("quit", "exit"):
        return "quit"

    if lower == "restart":
        session.restart()
        print("Game restarted.")
        return "handled"

    if lower == "resign":
        winner = opposite(session.board.turn)
        if session.board.insufficient_mating_material(winner):
            print(f"{color_name(session.board.turn)} resigns. Draw: {color_name(winner)} cannot checkmate.")
        else:
            print(f"{color_name(session.board.turn)} resigns. {color_name(winner)} wins.")
        return "quit"

    if lower == "claim" or lower.startswith("claim "):
        # FIDE allows claiming that the move about to be played creates
        # threefold / 50-move; use the current preview when one is ready.
        intended = (
            session.preview_move
            if session.preview_shown and session.preview_move is not None and getattr(session.preview_move, "sr", -1) >= 0
            else None
        )
        can_claim, draw_reason = session.board.claimable_draw(intended)
        if can_claim:
            print(f"Game Over! Draw claimed by {draw_reason}.")
            return "quit"
        err("No draw claim is currently available.")
        return "handled"

    return None
