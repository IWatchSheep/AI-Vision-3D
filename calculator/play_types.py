"""Small data types and spoken-move helpers for blueprint play."""

from __future__ import annotations

from dataclasses import dataclass

from calculator.build_shape import MoveResult

PIECE_NAMES = {
    "K": "king",
    "Q": "queen",
    "R": "rook",
    "B": "bishop",
    "N": "knight",
    "P": "pawn",
}


@dataclass(frozen=True)
class RankedStrategy:
    """One doll in a Strategy Forming List."""

    number: int
    id: str
    name: str
    sentence: str
    score: int
    filled: int
    empty: int
    wrong: int


@dataclass(frozen=True)
class TargetChoice:
    """One required square that is not filled, and moves that would fill it."""

    square: str
    expected: str
    seen: str
    mark: str
    moves: tuple[str, ...]


@dataclass(frozen=True)
class TheoreticalStep:
    """One imaginary ply and both theoretical lists after that ply."""

    move_text: str
    result: MoveResult
    matched_before: int
    matched_after: int
    required: int
    forming: tuple[RankedStrategy, ...]
    targets: tuple[TargetChoice, ...]


@dataclass(frozen=True)
class TheoreticalLine:
    steps: tuple[TheoreticalStep, ...]
    real_unchanged: bool


def piece_phrase(symbol: str) -> str:
    """'P' -> 'White pawn', 'n' -> 'Black knight'."""
    side = "White" if symbol.isupper() else "Black"
    return f"{side} {PIECE_NAMES.get(symbol.upper(), 'piece')}"


def spoken_move(result: MoveResult, move_text: str) -> str:
    """Read the engine's move message as a sentence a person can follow."""
    if not result.legal or not result.message:
        return f"Move {move_text.strip() or '?'}: refused or invalid"
    parts = result.message.split()
    if len(parts) < 4:
        return result.message
    phrase = f"{piece_phrase(parts[0])} {parts[1]} to {parts[3]}"
    typed = move_text.strip()
    if len(typed) >= 5 and typed[4].isalpha():
        name = PIECE_NAMES.get(typed[4].upper(), "piece")
        phrase += f", promoting to a {name}"
    return phrase
