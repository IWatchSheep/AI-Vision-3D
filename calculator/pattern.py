"""
Compare a seen chess board with strategy dolls and show how they fill in.

Worked example
--------------
Doll square e1 has King "K", seen board also has "K" -> mark "#"
Doll square e7 has pawn "P", seen board has black pawn "p" -> mark "X"
Doll empty squares are not scored -> mark "."

Marks cheat sheet (doll squares only)
-------------------------------------
  "#"  same piece on the seen board (filling in)
  "+"  doll has a piece; seen square is empty (predicted)
  "X"  doll has a piece; seen has a different piece
  "."  doll has no piece here (skipped)

Pieces are never moved to force a better match.
Joints are only written down; this file does not slide them.
This file does not import a chess engine.

Memory notepad (PatternWindow) uses calculator.window.MemoryWindow:
  past / current / accept(), with PAST_LIMIT accepted compares.

Tip: this module's compare() is for chess dolls.
Shape grids use calculator.shape.compare instead.
"""

from __future__ import annotations

from dataclasses import dataclass

from calculator.strategies import BOARD_SIZE, STRATEGIES, Strategy, require_board
from calculator.window import DEFAULT_PAST_LIMIT, MemoryWindow

# File letters a..h for names like "e7". Must match BOARD_SIZE.
FILES = "abcdefgh"
if len(FILES) != BOARD_SIZE:
    raise RuntimeError("FILES length must equal BOARD_SIZE")

PAST_LIMIT = DEFAULT_PAST_LIMIT

# Allowed marks on a chess fill board.
FILL_MARKS = frozenset({"#", "+", "X", "."})


def _is_whole_number(value: object) -> bool:
    """True for real ints. Rejects bool (True/False) and floats."""
    return isinstance(value, int) and not isinstance(value, bool)


@dataclass(frozen=True)
class CompareResult:
    """One doll held up against a seen board."""

    strategy: Strategy
    fill: tuple[str, ...]  # 8 mark-strings, rank 8 first
    hash_count: int
    plus_count: int
    x_count: int

    @property
    def score(self) -> int:
        """score = number of '#' minus number of 'X'."""
        return self.hash_count - self.x_count


class PatternWindow:
    """
    Short memory of chess compares.

    Same public names as before (past, current, set_current, accept).
    Storage is the shared MemoryWindow helper.
    """

    def __init__(self) -> None:
        self._memory: MemoryWindow[CompareResult] = MemoryWindow(limit=PAST_LIMIT)

    @property
    def past(self) -> list[CompareResult]:
        return self._memory.past

    @past.setter
    def past(self, value: list[CompareResult]) -> None:
        # replace_past enforces the size limit (direct assign could bypass it).
        self._memory.replace_past(value)

    @property
    def current(self) -> CompareResult | None:
        return self._memory.current

    @current.setter
    def current(self, value: CompareResult | None) -> None:
        self._memory.current = value

    def set_current(self, result: CompareResult) -> None:
        """Put a compare on screen without accepting it."""
        self._memory.set_current(result)

    def accept(self) -> None:
        """Move current into past; keep at most PAST_LIMIT items."""
        self._memory.accept()


def in_bounds(row: object, col: object) -> bool:
    """True when row and col are whole numbers inside 0..7."""
    if not _is_whole_number(row) or not _is_whole_number(col):
        return False
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def require_in_bounds(row: object, col: object) -> None:
    """Raise ValueError if (row, col) is not a safe board index."""
    if not in_bounds(row, col):
        raise ValueError(
            f"square ({row!r}, {col!r}) is outside the "
            f"{BOARD_SIZE}x{BOARD_SIZE} board or is not a whole number"
        )


def cell_name(row: int, col: int) -> str:
    """
    Chess square name like e7.

    row 0 is rank 8, row 7 is rank 1.
    col 0 is file a, col 7 is file h.
    """
    require_in_bounds(row, col)
    return f"{FILES[col]}{BOARD_SIZE - row}"


def compare(doll: Strategy, seen_board: list[str]) -> CompareResult:
    """
    Hold one doll up against a seen board and mark how it is filling in.

    Both boards are size-checked first so we never index off the ends.
    """
    require_board(doll.board, label=f"doll {doll.id}")
    require_board(seen_board, label="seen board")

    # Score against a private copy so later edits to result.strategy cannot
    # change the doll stored in STRATEGIES.
    doll_snapshot = doll.copy()

    fill_rows: list[str] = []
    hash_count = 0
    plus_count = 0
    x_count = 0

    for r in range(BOARD_SIZE):
        marks: list[str] = []
        for c in range(BOARD_SIZE):
            doll_piece = doll_snapshot.board[r][c]
            seen_piece = seen_board[r][c]

            if doll_piece == ".":
                marks.append(".")
            elif doll_piece == seen_piece:
                marks.append("#")
                hash_count += 1
            elif seen_piece == ".":
                marks.append("+")
                plus_count += 1
            else:
                marks.append("X")
                x_count += 1
        fill_rows.append("".join(marks))

    return CompareResult(
        strategy=doll_snapshot,
        fill=tuple(fill_rows),
        hash_count=hash_count,
        plus_count=plus_count,
        x_count=x_count,
    )


def rank(seen_board: list[str]) -> list[CompareResult]:
    """
    Rank every doll against the seen board.

    Highest score first. Ties break by strategy number (lower first).
    """
    require_board(seen_board, label="seen board")
    results = [compare(doll, seen_board) for doll in STRATEGIES]
    results.sort(key=lambda item: (-item.score, item.strategy.number))
    return results


def print_fill(result: CompareResult) -> None:
    """Print the fill board. Fill alone never claims an identity."""
    for row in result.fill:
        print(row)
    print("IDENTITY CLAIMED: no")


# Clearer alias for beginners (same function, same output).
print_chess_fill = print_fill


def print_greatest_target_list(result: CompareResult, seen_board: list[str]) -> None:
    """
    List each "+" or "X" square for this doll: parts not filled yet.

    Format: cell-<file><rank>, doll piece, and seen piece (or empty).
    These are not captures.
    """
    require_board(seen_board, label="seen board")
    require_board(result.strategy.board, label=f"doll {result.strategy.id}")

    if len(result.fill) != BOARD_SIZE:
        raise ValueError("fill board has the wrong number of rows")

    print("Greatest Target List")
    any_target = False

    for r in range(BOARD_SIZE):
        if len(result.fill[r]) != BOARD_SIZE:
            raise ValueError(f"fill row {r} has the wrong length")
        for c in range(BOARD_SIZE):
            mark = result.fill[r][c]
            if mark not in ("+", "X"):
                continue
            any_target = True
            doll_piece = result.strategy.board[r][c]
            seen_piece = seen_board[r][c]
            seen_label = "empty" if seen_piece == "." else seen_piece
            print(
                f"cell-{cell_name(r, c)}: doll {doll_piece}, seen {seen_label}"
            )

    if not any_target:
        print("(none)")


def print_strategy_forming_list(seen_board: list[str]) -> None:
    """Print the ranked Strategy Forming List for a seen board."""
    print("Strategy Forming List")
    ranked = rank(seen_board)
    for i, result in enumerate(ranked, start=1):
        s = result.strategy
        print(
            f"{i}. {s.name}  score={result.score}  "
            f"#={result.hash_count}  +={result.plus_count}  X={result.x_count}"
        )
        print(f"   {s.sentence}")
    print("IDENTITY CLAIMED: no")


def print_doll_on_record(doll: Strategy, seen_board: list[str]) -> None:
    """Print one doll's fill against the seen board, plus greatest targets."""
    print(f"Doll on record: {doll.id}")
    result = compare(doll, seen_board)
    print_fill(result)
    print_greatest_target_list(result, seen_board)
