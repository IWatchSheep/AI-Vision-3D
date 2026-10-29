"""Prints help when you type help or help <command>.

Does not change the board; only explains move flow (square → preview → F) and
optional analysis commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .cli_session import GameSession, sanitize_display_text

Handler = Callable[[GameSession, str], bool]


@dataclass(frozen=True)
class CommandSpec:
    """Links a command name to its handler and the text shown in help."""

    name: str
    summary: str
    handler: Handler
    topic: str = "analysis"  # "move" or "analysis"
    usage: str = ""


def print_help(topic: str = "") -> None:
    """Print command help. topic may be empty, 'goal', or another command name."""
    from .cli_commands import ANALYSIS_COMMANDS, ALL_HELP_SPECS

    topic = topic.strip().lower()

    if not topic:
        print("=== Help: how to move ===")
        print("  1. Enter a start square (e2)")
        print("  2. Enter a destination (e4)  -> preview only, nothing is played")
        print("  3. Type F to finalize / play the move")
        print("  N / NEW  cancel selection     P  clear preview, keep piece")
        print("  restart  quit  claim  resign  fen  fen <text>")
        print("")
        print("=== Help: analysis (optional) ===")
        for spec in ANALYSIS_COMMANDS:
            print(f"  {spec.name:<14} {spec.summary}")
        print("")
        print("Type help <name> for details, for example: help goal")
        print("Note: typing distance or risk alone shows status;")
        print("      use distance on/off and risk on/off to change them.")
        return

    if topic in ("goal", "goal2"):
        print("goal / goal2: set target squares and a limit of own moves (1 to 4).")
        print("  Examples: goal f7 2 | goal f7 g7 h7 3 | goal king 2 | goal off")
        print("  goal2 d5 2 | goal2 off")
        print("  Then: routes   or   routes real 3")
        return

    for spec in ALL_HELP_SPECS:
        if spec.name == topic or topic in spec.name.split():
            print(f"{spec.name}: {spec.summary}")
            if spec.usage:
                print(f"  {spec.usage}")
            return

    safe = sanitize_display_text(topic)
    print(f"No help topic named '{safe}'. Type help for the full list.")


def handle_help(_session: GameSession, cmd: str) -> bool:
    """Handle help and help <topic>; return False if the line is not help."""
    lower = cmd.lower()
    if lower != "help" and not lower.startswith("help "):
        return False
    topic = cmd[5:].strip() if lower.startswith("help ") else ""
    print_help(topic)
    return True
