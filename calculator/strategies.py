"""
Chess strategy dolls: types, validation, lookup, and printing.

The 20 hardcoded doll records live in calculator.strategies_data (ASCII boards
are the source of truth). This file turns each record into a Strategy, checks
size/characters, and checks that each stored FEN piece field matches ASCII.

Joints are written down for a later update. Printing joints must NOT change
any board string, and this file never moves a piece.

Board legend
------------
  Uppercase = White pieces (K Q R B N P)
  Lowercase = Black pieces (k q r b n p)
  "."       = empty
  board[0]  = rank 8 ... board[7] = rank 1
  each string = files a..h
"""

from __future__ import annotations

from dataclasses import dataclass, field

from calculator.strategies_data import RAW_DOLLS

# Chess boards are always 8x8. Checking this size stops reads past the end.
BOARD_SIZE = 8

# Characters allowed on a doll board (frozenset so the rule set cannot be edited).
PIECE_CHARS = frozenset("KQRBNPkqrbnp.")

# Keys every raw doll record must provide.
_REQUIRED_DOLL_KEYS = frozenset(
    {"number", "id", "name", "stage", "sentence", "board", "fen", "joints"}
)


@dataclass
class Strategy:
    """One strategy doll: a posed picture held up against a seen board."""

    number: int
    id: str
    name: str
    stage: str
    sentence: str
    board: list[str]
    fen: str
    joints: list[str] = field(default_factory=list)

    def copy(self) -> Strategy:
        """
        Return a new Strategy with copied board and joints lists.

        Use this when you need a private copy so later edits cannot change
        the doll on record. Runtime scoring still uses the shared STRATEGIES
        entries and does not require calling copy().
        """
        return Strategy(
            number=self.number,
            id=self.id,
            name=self.name,
            stage=self.stage,
            sentence=self.sentence,
            board=[str(row) for row in self.board],
            fen=self.fen,
            joints=[str(joint) for joint in self.joints],
        )


def require_board(board: list[str], label: str = "board") -> None:
    """
    Raise ValueError if board is not 8 strings of length 8 with legal chars.

    This stops later code from reading past the end of a short or jagged board.
    """
    if not isinstance(board, list):
        raise ValueError(f"{label} must be a list of strings")
    if len(board) != BOARD_SIZE:
        raise ValueError(f"{label} must have {BOARD_SIZE} rows, got {len(board)}")
    for i, row in enumerate(board):
        if not isinstance(row, str):
            raise ValueError(f"{label} row {i} must be a string")
        if len(row) != BOARD_SIZE:
            raise ValueError(
                f"{label} row {i} must have {BOARD_SIZE} columns, got {len(row)}"
            )
        bad = set(row) - PIECE_CHARS
        if bad:
            raise ValueError(f"{label} row {i} has illegal characters: {sorted(bad)}")


def make_strategy(
    number: int,
    id_: str,
    name: str,
    stage: str,
    sentence: str,
    board: list[str],
    fen: str,
    joints: list[str],
) -> Strategy:
    """
    Build one Strategy and copy board/joints so callers do not share lists.

    Each board line is copied as a new string so outside code cannot reach
    back into the hardcoded doll text through a shared object.
    """
    if not isinstance(number, int) or isinstance(number, bool):
        raise ValueError("strategy number must be a whole number")
    if not isinstance(id_, str) or id_ == "":
        raise ValueError("strategy id must be a non-empty string")
    if not isinstance(fen, str) or fen.strip() == "":
        raise ValueError(f"strategy {id_!r} FEN must be a non-empty string")
    if not isinstance(joints, list):
        raise ValueError(f"strategy {id_!r} joints must be a list of strings")
    for j, joint in enumerate(joints):
        if not isinstance(joint, str):
            raise ValueError(f"strategy {id_!r} joint {j} must be a string")

    require_board(board, label=id_)

    return Strategy(
        number=number,
        id=id_,
        name=str(name),
        stage=str(stage),
        sentence=str(sentence),
        board=[str(row) for row in board],
        fen=str(fen),
        joints=[str(joint) for joint in joints],
    )


def _load_strategies() -> list[Strategy]:
    """Turn RAW_DOLLS records into Strategy objects (same order as the data file)."""
    if not isinstance(RAW_DOLLS, list):
        raise TypeError("RAW_DOLLS must be a list")

    loaded: list[Strategy] = []
    seen_ids: set[str] = set()
    seen_numbers: set[int] = set()

    for index, record in enumerate(RAW_DOLLS):
        if not isinstance(record, dict):
            raise TypeError(f"RAW_DOLLS[{index}] must be a dict")
        missing = _REQUIRED_DOLL_KEYS - set(record.keys())
        if missing:
            raise ValueError(
                f"RAW_DOLLS[{index}] missing keys: {sorted(missing)}"
            )

        strategy = make_strategy(
            record["number"],
            record["id"],
            record["name"],
            record["stage"],
            record["sentence"],
            list(record["board"]),
            record["fen"],
            list(record["joints"]),
        )

        if strategy.id in seen_ids:
            raise ValueError(f"duplicate strategy id: {strategy.id!r}")
        if strategy.number in seen_numbers:
            raise ValueError(f"duplicate strategy number: {strategy.number}")
        seen_ids.add(strategy.id)
        seen_numbers.add(strategy.number)

        flat = "".join(strategy.board)
        if "K" not in flat or "k" not in flat:
            raise ValueError(
                f"strategy {strategy.id!r} must include both kings (K and k)"
            )

        loaded.append(strategy)

    return loaded


# The 20 dolls on record. Tuple so callers cannot append/remove entries.
STRATEGIES: tuple[Strategy, ...] = tuple(_load_strategies())


def get_strategy(id_or_number: str | int) -> Strategy:
    """Return a strategy by id string or by number (1..20)."""
    for strategy in STRATEGIES:
        if strategy.id == id_or_number or strategy.number == id_or_number:
            return strategy
    raise KeyError(f"No strategy matching {id_or_number!r}")


def board_to_fen_pieces(board: list[str]) -> str:
    """
    Build the FEN piece-placement field from an ASCII board.

    Example: "....K..." becomes "4K3". Rank 8 is the first string.
    """
    require_board(board)
    ranks: list[str] = []
    for row in board:
        empty = 0
        parts: list[str] = []
        for ch in row:
            if ch == ".":
                empty += 1
            else:
                if empty > 0:
                    parts.append(str(empty))
                    empty = 0
                parts.append(ch)
        if empty > 0:
            parts.append(str(empty))
        ranks.append("".join(parts))
    return "/".join(ranks)


def fen_piece_field(fen: str) -> str:
    """
    Return the piece-placement field of a FEN string (text before the first space).

    Empty input must not use split()[0] (that would be an underflow-style error).
    """
    if not isinstance(fen, str):
        raise ValueError("FEN must be a string")
    parts = fen.split()
    if len(parts) == 0:
        raise ValueError("FEN string is empty")
    return parts[0]


def print_joints(strategy: Strategy) -> None:
    """Print joint sentences. Must not change any board string."""
    for joint in strategy.joints:
        print(joint)


def print_strategy(strategy: Strategy) -> None:
    """Print one doll: number, name, stage, sentence, board, FEN, joints."""
    print(f"{strategy.number}. {strategy.name}")
    print(f"Stage: {strategy.stage}")
    print(strategy.sentence)
    for row in strategy.board:
        print(row)
    print(f"FEN: {strategy.fen}")
    print_joints(strategy)
    print("Joints were not moved.")


# Startup check: every stored FEN piece field must match its ASCII board.
for _strategy in STRATEGIES:
    _from_ascii = board_to_fen_pieces(_strategy.board)
    _from_fen = fen_piece_field(_strategy.fen)
    if _from_ascii != _from_fen:
        raise RuntimeError(
            f"{_strategy.id}: ASCII FEN {_from_ascii!r} != stored {_from_fen!r}"
        )
