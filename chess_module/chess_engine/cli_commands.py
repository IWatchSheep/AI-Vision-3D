"""CLI commands: how the player types moves and analysis tools.

Read this file top-down:
  1. Help text
  2. Move flow (select square, preview, F / P / N, fen, promotion)
  3. Analysis handlers (r, replies, loop, goal, memory, ...)
  4. Command tables used by process_command

Play always goes: start square -> destination preview -> F to finalize.
Analysis commands only print facts; they never choose a move for you.
"""

from __future__ import annotations

from typing import Callable, Optional, Sequence

from .move import parse_move_text
from .search_budget import bounded_search
from .cli_session import (
    GameSession, Step, err, move_label,
    MAX_COMMAND_CHARS, sanitize_display_text,
)
from .cli_help import CommandSpec, handle_help, print_help
from .cli_move_cmds import (
    handle_cancel,
    handle_fen,
    handle_promotion_choice,
    handle_finalize,
    handle_discard_preview,
    handle_square_entry,
    handle_game_control,
)
from .cli_goal_cmds import (
    handle_goal,
    handle_goal2,
    handle_distance,
    handle_routes,
    handle_support,
)
from .cli_analysis_cmds import (
    handle_calc_report,
    handle_replies,
    handle_loop,
    handle_exchange,
    handle_order,
    handle_compare,
    handle_risk,
    handle_trace,
    handle_memory,
)

Handler = Callable[[GameSession, str], bool]

# Re-export for tests and callers that import handlers from cli_commands.
__all__ = [
    "CommandSpec",
    "print_help",
    "handle_help",
    "process_command",
    "process_promotion_command",
    "dispatch_named_command",
    "print_instructions",
    "build_prompt",
    "ANALYSIS_COMMANDS",
    "PLAY_HANDLERS",
    "ALL_HELP_SPECS",
    "handle_cancel",
    "handle_fen",
    "handle_promotion_choice",
    "handle_finalize",
    "handle_discard_preview",
    "handle_square_entry",
    "handle_game_control",
    "handle_calc_report",
    "handle_replies",
    "handle_loop",
    "handle_goal",
    "handle_goal2",
    "handle_distance",
    "handle_routes",
    "handle_support",
    "handle_exchange",
    "handle_order",
    "handle_compare",
    "handle_risk",
    "handle_trace",
    "handle_memory",
    "move_label",
]

# ---------------------------------------------------------------------------
# Command tables (dispatch order + help)
# ---------------------------------------------------------------------------

ANALYSIS_COMMANDS: Sequence[CommandSpec] = (
    CommandSpec("r", "calculator report for the current preview", handle_calc_report,
                usage="Preview a move, then type R."),
    CommandSpec("replies", "list or inspect opponent replies to the preview", handle_replies,
                usage="replies   or   replies e7e5"),
    CommandSpec("loop", "count positions to a given depth", handle_loop,
                usage="loop 3   or   loop 3 6"),
    CommandSpec("goal", "set / show / clear the primary goal", handle_goal,
                usage="goal f7 2 | goal off"),
    CommandSpec("distance", "show or set distance-order view", handle_distance,
                usage="distance | distance on | distance off"),
    CommandSpec("goal2", "set / show / clear the second goal", handle_goal2,
                usage="goal2 d5 2 | goal2 off"),
    CommandSpec("routes", "PASS routes for the active goal", handle_routes,
                usage="routes   or   routes real 3"),
    CommandSpec("support", "support report for the current preview", handle_support,
                usage="Preview a move, then type support."),
    CommandSpec("exchange", "exchange analysis on a square", handle_exchange,
                usage="exchange e5 4"),
    CommandSpec("order", "order report for exchange limit", handle_order,
                usage="order 4"),
    CommandSpec("compare", "compare several legal moves at a depth", handle_compare,
                usage="compare 3 d1h5 d1f3 g1f3"),
    CommandSpec("risk", "show or set AT-RISK display", handle_risk,
                usage="risk | risk on | risk off"),
    CommandSpec("trace", "step through a move sequence", handle_trace,
                usage="trace e2e4 e7e5"),
    CommandSpec("memory", "show the five-move window (past + current preview)", handle_memory,
                usage="memory"),
)

# Play / session commands (checked before analysis table in dispatch).
PLAY_HANDLERS: Sequence[Handler] = (
    handle_help,
    handle_cancel,
    handle_fen,
    handle_promotion_choice,
    handle_finalize,
    handle_discard_preview,
)

ALL_HELP_SPECS: Sequence[CommandSpec] = (
    CommandSpec("help", "show this help", handle_help, topic="move",
                usage="help   or   help goal"),
    CommandSpec("f", "finalize the previewed move", handle_finalize, topic="move"),
    CommandSpec("p", "clear preview, keep selected piece", handle_discard_preview, topic="move"),
    CommandSpec("n", "cancel selection / pick a new piece", handle_cancel, topic="move"),
    CommandSpec("fen", "print or load a FEN position", handle_fen, topic="move",
                usage="fen   or   fen <fen-text>"),
    *ANALYSIS_COMMANDS,
)


@bounded_search
def dispatch_named_command(session: GameSession, cmd: str) -> bool:
    """Run the first matching play or analysis handler. True if handled."""
    for handler in PLAY_HANDLERS:
        if handler(session, cmd):
            return True
    for spec in ANALYSIS_COMMANDS:
        if spec.handler(session, cmd):
            return True
    return False


# ---------------------------------------------------------------------------
# Screen text (used by main)
# ---------------------------------------------------------------------------

def print_instructions(session: GameSession) -> None:
    """Tell the player what to type next."""
    print("How to move: select a piece, preview a destination, then type F to play it.")

    if session.step == Step.CHOOSE_PROMOTION:
        print("PROMOTION: choose the new piece")
        print("  Q = Queen   R = Rook   B = Bishop   N = Knight")
        print("  Type NEW to cancel and pick a different piece.")
    elif session.step == Step.PICK_PIECE:
        print("Step 1: enter a start square (example: e2), then press Enter.")
    elif session.step == Step.PICK_DESTINATION:
        print("Step 2: enter a destination (example: e4), then press Enter.")
        print("  BEFORE/AFTER lists will appear. The move is NOT played yet.")
        print("  Type N then Enter to pick a different piece.")
    else:
        print(f"PREVIEW READY: {move_label(session.preview_move)} (NOT played yet).")
        print("  F = Finalize (play the move)")
        print("  P = Pick a different destination for the same piece")
        print("  N = Pick a different piece")

    if session.step not in (Step.CONFIRM_PREVIEW, Step.CHOOSE_PROMOTION):
        print("Every move needs a preview, then F + Enter.")
        print("Other commands: restart, quit, claim, resign, help")


def build_prompt(session: GameSession) -> str:
    """Build the input prompt for the current step."""
    from .constants import color_name

    turn = color_name(session.board.turn)
    if session.step == Step.CHOOSE_PROMOTION:
        return f"{turn} - choose promotion (Q/R/B/N): "
    if session.step == Step.CONFIRM_PREVIEW:
        return f"{turn} - Enter command (F/P/N): "
    if session.step == Step.PICK_DESTINATION:
        return f"{turn} - enter destination square: "
    return f"{turn} - enter START square: "


def process_promotion_command(session: GameSession, cmd: str) -> Optional[str]:
    """Restrict input while a promotion piece must be chosen.

    Only Q/R/B/N, NEW/select none, and quit/exit/restart/resign/claim are allowed.
    This prevents help/fen/analysis/F/P from running mid-promotion.
    """
    lower = cmd.lower()

    if lower in ("new", "select none", "cancel"):
        session.clear_selection()
        print("Selection cleared. Enter a new start square.")
        return None

    if lower in ("quit", "exit", "restart", "resign", "claim") or lower.startswith("claim "):
        control = handle_game_control(session, cmd)
        if control == "quit":
            return "quit"
        return None

    # Q/R/B/N or a rejection message for anything else.
    handle_promotion_choice(session, cmd)
    return None


def process_command(session: GameSession, cmd: str) -> Optional[str]:
    """Handle one user command.

    Order: length check → promotion gate → named commands → square entry →
    game control → reject old-style one-line moves.

    Returns None (continue), 'quit', or 'unknown'.
    """
    if not isinstance(cmd, str):
        err("Command must be text.")
        return None
    if len(cmd) > MAX_COMMAND_CHARS:
        err(f"Command too long (max {MAX_COMMAND_CHARS} characters).")
        return None
    cmd = cmd.strip()
    if not cmd:
        return None

    # While choosing Q/R/B/N, only promotion + quit/restart/etc. are allowed.
    if session.promotion_pending:
        return process_promotion_command(session, cmd)

    try:
        if dispatch_named_command(session, cmd):
            return None

        if handle_square_entry(session, cmd):
            return None

        control = handle_game_control(session, cmd)
        if control == "quit":
            return "quit"
        if control == "handled":
            return None

        if parse_move_text(cmd) is not None:
            err(
                "Direct moves are disabled. Enter the START square, then the destination, "
                "review BEFORE/AFTER, and press F + Enter."
            )
            return None

        if cmd.lower() in ("offer", "offer draw") or cmd.lower().startswith("offer "):
            err(
                "Draw offers are not supported in hotseat play. Players may agree to quit, "
                "claim a rule-based draw, or resign."
            )
            return None

        return "unknown"
    except Exception as exc:
        # Analysis helpers can be heavy; never let an unexpected error kill the game loop.
        err(f"Command failed: {sanitize_display_text(str(exc), 120)}")
        return None
