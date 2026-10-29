"""Typed commands for the blueprint play loop."""

from __future__ import annotations

from calculator.build_shape import IMAGINE_STEP_LIMIT
from calculator.play_format import format_accept, format_imagine, format_position
from calculator.play_session import PlaySession
from chess_module.chess_engine.constants import MAX_COMMAND_CHARS

HELP = """
Commands
  e2e4                         accept that move on the real board
  imagine                      look four legal moves ahead on a copy
  imagine e2e4 e7e5 g1f3 b8c6  look at that line on a copy
  doll develop-to-the-center   hold a different blueprint against this game
  doll 2                       same thing, by strategy number
  board                        show the real board and the real lists again
  help                         show these commands
  quit                         leave
""".strip()


def handle_command(session: PlaySession, text: str) -> str | None:
    """Run one typed command. None means the player asked to leave."""
    if not isinstance(text, str):
        return "Command must be text."
    if len(text) > MAX_COMMAND_CHARS:
        return f"Command too long (max {MAX_COMMAND_CHARS} characters)."
    command = text.strip()
    if not command:
        return ""
    lowered = command.lower()
    if lowered in {"quit", "exit"}:
        return None
    if lowered == "help":
        return HELP
    if lowered == "board":
        return format_position(session)
    if lowered == "doll" or lowered.startswith("doll "):
        return _handle_doll(session, lowered)
    if lowered == "imagine" or lowered.startswith("imagine "):
        return _handle_imagine(session, command)
    before = session.view().total_matched
    return format_accept(session, session.accept(command), before)


def _handle_doll(session: PlaySession, lowered: str) -> str:
    parts = lowered.split(maxsplit=1)
    if len(parts) == 1:
        return "Type doll and an id, for example: doll develop-to-the-center"
    try:
        session.select(parts[1])
    except KeyError as exc:
        return str(exc)
    return format_position(session)


def _handle_imagine(session: PlaySession, command: str) -> str:
    parts = command.split()
    moves = tuple(parts[1:]) if len(parts) > 1 else None
    if moves is not None and len(moves) > IMAGINE_STEP_LIMIT:
        return "An imaginary line is limited to four moves."
    return format_imagine(session, session.imagine(moves))
