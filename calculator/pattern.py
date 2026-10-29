"""Compare a seen board with strategy dolls and rank how they fill in.

Memory shape (PatternWindow)
----------------------------
past:    at most 4 accepted compares (oldest first)
current: the compare on screen right now
accept(): move current into past; a 5th accept drops the oldest

This update only shows dolls and fill. Accepting a compare into past,
and trying a joint on a copy, belong to a later update after a person asks.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from calculator.strategies import STRATEGIES, Strategy

FILES = "abcdefgh"


@dataclass
class CompareResult:
    """One doll held up against a seen board."""

    strategy: Strategy
    fill: list[str]
    hash_count: int
    plus_count: int
    x_count: int

    @property
    def score(self) -> int:
        return self.hash_count - self.x_count


@dataclass
class PatternWindow:
    """
    Short memory of compares.

    past holds at most 4 accepted compares.
    current holds the compare on screen.
    accept() moves current into past; a 5th accept drops the oldest.
    """

    past: list[CompareResult] = field(default_factory=list)
    current: CompareResult | None = None

    def set_current(self, result: CompareResult) -> None:
        self.current = result

    def accept(self) -> None:
        """Move current into past. Drop the oldest if past would exceed 4."""
        if self.current is None:
            return
        self.past.append(self.current)
        self.current = None
        if len(self.past) > 4:
            self.past.pop(0)


def _cell_name(row: int, col: int) -> str:
    """Square name like e7 (row 0 is rank 8, col 0 is file a)."""
    return f"{FILES[col]}{8 - row}"


def compare(doll: Strategy, seen_board: list[str]) -> CompareResult:
    """
    Hold one doll up against a seen board and mark how it is filling in.

    Only squares where the doll has a piece are compared. Other squares
    stay ".". Marks:
      "#" — seen board has the same piece (the doll is filling in)
      "+" — doll has a piece there; seen square is empty (predicted, not seen)
      "X" — doll has a piece there; seen square has a different piece
    Pieces are never moved to force a better match.
    """
    fill: list[str] = []
    hash_count = 0
    plus_count = 0
    x_count = 0
    for r in range(8):
        marks: list[str] = []
        for c in range(8):
            doll_piece = doll.board[r][c]
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
        fill.append("".join(marks))
    return CompareResult(
        strategy=doll,
        fill=fill,
        hash_count=hash_count,
        plus_count=plus_count,
        x_count=x_count,
    )


def rank(seen_board: list[str]) -> list[CompareResult]:
    """
    Rank every doll against the seen board.

    score = number of "#" minus number of "X".
    Highest score first. Ties break by strategy number (lower first).
    """
    results = [compare(doll, seen_board) for doll in STRATEGIES]
    results.sort(key=lambda r: (-r.score, r.strategy.number))
    return results


def print_fill(result: CompareResult) -> None:
    """Print the fill board and the identity line (never claimed from fill alone)."""
    for row in result.fill:
        print(row)
    print("IDENTITY CLAIMED: no")


def print_greatest_target_list(result: CompareResult, seen_board: list[str]) -> None:
    """
    List each "+" or "X" square for this doll: parts not filled yet.

    Format: cell-<file><rank>, doll piece, and seen piece (or empty).
    These are not captures.
    """
    print("Greatest Target List")
    any_target = False
    for r in range(8):
        for c in range(8):
            mark = result.fill[r][c]
            if mark not in ("+", "X"):
                continue
            any_target = True
            doll_piece = result.strategy.board[r][c]
            seen_piece = seen_board[r][c]
            seen_label = "empty" if seen_piece == "." else seen_piece
            print(
                f"cell-{_cell_name(r, c)}: doll {doll_piece}, seen {seen_label}"
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
