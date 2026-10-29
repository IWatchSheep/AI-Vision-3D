"""Holds everything for one game: board, turn, and move-entry step.

The session remembers whether you are picking a piece, a destination, choosing
promotion, or confirming a preview. Playing a move always ends with F after a
preview; this module does not read keyboard input itself.
"""

from enum import Enum
from typing import Optional

from .constants import (
    in_bounds, row_col_text, RED, RESET, MAX_COMMAND_CHARS,
)
from .move import Move
from .board import Board
from .tracker import Tracker
from .analysis import (
    Goal,
    goal_marks_after,
    distance_after,
    set_goal_show_risk,
)
from .ui import show_step2_after
from .move_memory import MoveMemory
from .movegen import legal_move

# MAX_COMMAND_CHARS (from constants) limits raw input length in process_command.

# Re-export for tests / callers that imported it from this module.
__all__ = [
    "Step", "err", "move_label", "warn_slow_search",
    "parse_bounded_int", "sanitize_display_text",
    "GameSession", "MAX_COMMAND_CHARS",
]


class Step(Enum):
    """Where the player is in the select -> preview -> finalize flow."""

    PICK_PIECE = "pick_piece"
    PICK_DESTINATION = "pick_destination"
    CHOOSE_PROMOTION = "choose_promotion"
    CONFIRM_PREVIEW = "confirm_preview"


def err(message: str) -> None:
    """Print an error in red so it stands out from normal board output."""
    print(f"{RED}{message}{RESET}")


def move_label(move: Move) -> str:
    """Turn a Move into text like 'e2 -> e4'."""
    if not (in_bounds(move.sr, move.sc) and in_bounds(move.er, move.ec)) :
        return "?? -> ??"
    return f"{row_col_text(move.sr, move.sc)} -> {row_col_text(move.er, move.ec)}"


def warn_slow_search(depth: int) -> None:
    """Warn the user when a deep search may take a long time."""
    if depth >= 5:
        print(f"Searching {depth} plies. Analysis stops at its work limit.")


def parse_bounded_int(text: str, lo: int, hi: int) -> Optional[int]:
    """Parse an ASCII decimal integer in [lo, hi], or return None.

    Rejects signs, spaces, non-ASCII digits, and very long digit strings
    so int() cannot be fed a huge number.
    """
    if (not isinstance(lo, int) or isinstance(lo, bool)
            or not isinstance(hi, int) or isinstance(hi, bool)
            or lo > hi):
        return None
    if not isinstance(text, str) or not text or not text.isascii() or not text.isdigit():
        return None
    if len(text) > 18:
        return None
    try:
        value = int(text, 10)
    except ValueError:
        return None
    if value < lo or value > hi:
        return None
    return value


def sanitize_display_text(text: str, max_len: int = 64) -> str:
    """Make untrusted text safe to print (no escape codes); trim long strings."""
    if not isinstance(text, str):
        return ""
    if not isinstance(max_len, int) or isinstance(max_len, bool) or max_len < 0:
        max_len = 0
    cleaned = "".join(ch for ch in text if ch.isprintable())
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len] + "..."
    return cleaned


class GameSession:
    """Tracks the board, move-entry step, and analysis options for one game."""

    def __init__(self) -> None:
        self.board = Board()
        self.board.reset_board()
        self.tracker = Tracker(self.board)

        self.step = Step.PICK_PIECE
        self.selected_row = -1
        self.selected_col = -1
        self.preview_move = Move(-1, -1, -1, -1)
        self.pending_promotion = Move(-1, -1, -1, -1)

        self.distance_view = False
        self.goal = Goal()
        self.second_goal = Goal()
        self.memory = MoveMemory()

    # -- derived flags (same meaning as the old boolean fields) --------------

    @property
    def preview_shown(self) -> bool:
        return self.step == Step.CONFIRM_PREVIEW

    @property
    def promotion_pending(self) -> bool:
        return self.step == Step.CHOOSE_PROMOTION

    def has_selection(self) -> bool:
        """True after step 1 (start square) until N or F clears the flow."""
        return in_bounds(self.selected_row, self.selected_col)

    def clear_selection(self) -> None:
        """Reset to step 1: no piece selected, no preview."""
        self.selected_row = -1
        self.selected_col = -1
        self.preview_move = Move(-1, -1, -1, -1)
        self.pending_promotion = Move(-1, -1, -1, -1)
        self.step = Step.PICK_PIECE
        self.memory.clear_current()

    def select_piece(self, row: int, col: int) -> None:
        """Step 1 done — next two-character input will be treated as destination."""
        if not in_bounds(row, col):
            raise ValueError(f"Out of bounds piece selection: ({row}, {col})")
        self.selected_row = row
        self.selected_col = col
        self.step = Step.PICK_DESTINATION

    def begin_promotion(self, move: Move) -> None:
        """Pawn reached the back rank; wait for Q/R/B/N before showing preview."""
        self.pending_promotion = move
        self.step = Step.CHOOSE_PROMOTION

    def clear_preview_keep_piece(self) -> None:
        """P command: stay on the selected piece, drop only the preview."""
        self.preview_move = Move(-1, -1, -1, -1)
        self.pending_promotion = Move(-1, -1, -1, -1)
        self.step = Step.PICK_DESTINATION
        self.memory.clear_current()

    def invalidate_preview(self) -> None:
        """Preview became illegal; keep selection if any, ask for a new destination."""
        self.preview_move = Move(-1, -1, -1, -1)
        self.pending_promotion = Move(-1, -1, -1, -1)
        if self.has_selection():
            self.step = Step.PICK_DESTINATION
        else:
            self.step = Step.PICK_PIECE
        self.memory.clear_current()

    def clear_analysis_options(self) -> None:
        """Reset goals / distance / risk (used on restart and FEN load)."""
        self.distance_view = False
        self.goal = Goal()
        self.second_goal = Goal()
        set_goal_show_risk(False)

    def restart(self) -> None:
        self.board.reset_board()
        self.tracker = Tracker(self.board)
        self.clear_selection()
        self.clear_analysis_options()
        self.memory.clear()

    def show_preview_extras(self, move: Move) -> None:
        """Print optional goal / distance notes after a preview.

        Goal marks use PASS (same side may move again). Distance uses REAL
        rules (turn flips). When both are on, say so once so the two reports
        are not read as one shared after-position.
        """
        if self.goal.active and self.distance_view:
            print(
                "NOTE goal marks use PASS; distance order uses REAL "
                "(opponent answers)."
            )
        if self.goal.active:
            print(goal_marks_after(self.board, self.goal, move), end="")
        if self.distance_view:
            print(distance_after(self.board, move), end="")

    def set_preview(self, move: Move) -> None:
        """Show BEFORE/AFTER for a legal destination and mark preview ready."""
        if not legal_move(self.board, move):
            raise ValueError("Cannot preview an illegal move")
        show_step2_after(self.board, move)
        self.show_preview_extras(move)
        self.memory.set_current(self.board, move)
        self.preview_move = move
        self.pending_promotion = Move(-1, -1, -1, -1)
        self.step = Step.CONFIRM_PREVIEW
