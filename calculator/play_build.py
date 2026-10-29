"""Watch legal chess moves fill a fixed strategy blueprint.

The chess engine accepts or refuses every move and keeps the real position:
side to move, castling, en passant, clocks, and position history. The
blueprint is a doll from calculator.strategies and does not change to fit
the pieces. This file only connects the two.

Four lists:

  Real Strategy Forming List
      All 20 dolls ranked on the real board. It changes only after a real
      move is accepted.
  Real Greatest Target List
      Missing (+) and mismatched (X) squares of the selected doll, plus a
      legal move that would fill that square on this turn, when one exists.
  Theoretical Strategy Forming List
      All 20 dolls ranked on a copy after each imaginary move.
  Theoretical Greatest Target List
      The same target report for that copied position.

Imaginary lines call the engine on copies. They do not replace the real
board or the real lists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from calculator.build_shape import (
    BoardRows,
    BuildView,
    MoveResult,
    apply_legal_move,
    build_view,
    render_board,
    starting_board,
)
from calculator.pattern import rank
from calculator.strategies import Strategy, get_strategy
from chess_module.chess_engine.board import Board
from chess_module.chess_engine.movegen import generate_moves

PIECE_NAMES = {
    "K": "king",
    "Q": "queen",
    "R": "rook",
    "B": "bishop",
    "N": "knight",
    "P": "pawn",
}

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
    parts = result.message.split()
    phrase = f"{piece_phrase(parts[0])} {parts[1]} to {parts[3]}"
    typed = move_text.strip()
    if len(typed) >= 5 and typed[4].isalpha():
        name = PIECE_NAMES.get(typed[4].upper(), "piece")
        phrase += f", promoting to a {name}"
    return phrase


def _as_rows(board_rows: list[str]) -> BoardRows:
    if isinstance(board_rows, BoardRows):
        return board_rows
    raise TypeError("strategy building needs a live engine position, not a bare picture")


def rank_strategies(board_rows: list[str]) -> tuple[RankedStrategy, ...]:
    """Rank all 20 dolls. The board itself is not changed."""
    return tuple(
        RankedStrategy(
            item.strategy.number,
            item.strategy.id,
            item.strategy.name,
            item.strategy.sentence,
            item.score,
            item.hash_count,
            item.plus_count,
            item.x_count,
        )
        for item in rank(board_rows)
    )


def legal_fill_moves(doll: Strategy, board_rows: BoardRows) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Every legal move, in engine order, and the blueprint squares it newly matches.

    A move can fill one required square while leaving another. Only the newly
    matched squares are listed. The real position is not changed.
    """
    board = board_rows.engine_copy()
    already = set(build_view(doll, board_rows).filled_squares)
    found = []
    for move in generate_moves(board):
        result = apply_legal_move(board_rows, move.uci, doll)
        if not result.legal:
            continue
        gained = tuple(square for square in result.view.filled_squares if square not in already)
        found.append((move.uci, gained))
    return tuple(found)


def target_choices(doll: Strategy, board_rows: BoardRows) -> tuple[TargetChoice, ...]:
    """Missing and mismatched squares, each with the legal moves that fill it now."""
    view = build_view(doll, board_rows)
    by_square: dict[str, list[str]] = {}
    for uci, gained in legal_fill_moves(doll, board_rows):
        for square in gained:
            by_square.setdefault(square, []).append(uci)
    return tuple(
        TargetChoice(target.square, target.expected, target.seen, target.mark,
                     tuple(by_square.get(target.square, ())))
        for target in view.targets
    )


def next_imaginary_move(doll: Strategy, board_rows: BoardRows) -> str | None:
    """First legal move that fills a required square, or the first legal move."""
    choices = legal_fill_moves(doll, board_rows)
    for uci, gained in choices:
        if gained:
            return uci
    if choices:
        return choices[0][0]
    return None


def auto_moves(doll: Strategy, board_rows: BoardRows, plies: int = 4) -> tuple[str, ...]:
    """Up to four legal plies on a copy, preferring a move that fills the blueprint."""
    current = board_rows.copy()
    chosen = []
    for _ in range(plies):
        text = next_imaginary_move(doll, current)
        if text is None:
            break
        result = apply_legal_move(current, text, doll)
        if not result.legal:
            break
        chosen.append(text)
        current = _as_rows(result.board_rows)
    return tuple(chosen)


class PlaySession:
    """One real chess game held up against one selected blueprint."""

    def __init__(self, doll_id: str | int = "develop-to-the-center", board: Board | None = None) -> None:
        self.doll = get_strategy(doll_id)
        self.rows = starting_board() if board is None else render_board(board)
        self.initial = self.rows.copy()
        self.accepted: list[str] = []

    def select(self, id_or_number: str) -> None:
        """Hold a different blueprint against the same real game."""
        token: str | int = int(id_or_number) if id_or_number.isdigit() else id_or_number
        self.doll = get_strategy(token)

    def view(self) -> BuildView:
        return build_view(self.doll, self.rows)

    def forming(self) -> tuple[RankedStrategy, ...]:
        return rank_strategies(self.rows)

    def targets(self) -> tuple[TargetChoice, ...]:
        return target_choices(self.doll, self.rows)

    def fen(self) -> str:
        return self.rows.engine_copy().to_fen()

    def history(self) -> list[str]:
        return list(self.rows.engine_copy().history)

    def state_key(self) -> tuple:
        """Everything a real move is allowed to change, and an imaginary move is not."""
        return (self.fen(), tuple(self.history()), tuple(self.rows), self.forming(),
                tuple(self.accepted), self.doll.id)

    def accept(self, move_text: str) -> MoveResult:
        """Validate one move with the chess engine. Only a legal move replaces the real board."""
        text = move_text.strip()
        result = apply_legal_move(self.rows, text, self.doll)
        if result.legal:
            self.rows = _as_rows(result.board_rows)
            self.accepted.append(text)
        return result

    def imagine(self, moves: Iterable[str] | None = None) -> TheoreticalLine:
        """Play a line on a copy. The default line is four legal filling tries."""
        before = self.state_key()
        texts = auto_moves(self.doll, self.rows) if moves is None else tuple(moves)
        current = self.rows.copy()
        steps = []
        for text in texts:
            before_matched = build_view(self.doll, current).total_matched
            result = apply_legal_move(current, text, self.doll)
            position = _as_rows(result.board_rows)
            steps.append(TheoreticalStep(
                text,
                result,
                before_matched,
                result.view.total_matched,
                result.view.required,
                rank_strategies(position),
                target_choices(self.doll, position),
            ))
            if result.legal:
                current = position
        return TheoreticalLine(tuple(steps), self.state_key() == before)

    def development_lines(self) -> list[str]:
        """Replay the accepted moves against the selected blueprint."""
        current = self.initial.copy()
        view = build_view(self.doll, current)
        lines = [f"Starting board: {view.total_matched} of {view.required} positions matched."]
        for text in self.accepted:
            result = apply_legal_move(current, text, self.doll)
            if not result.legal:
                lines.append(f"Replay refused {text!r}. The record stopped here.")
                break
            lines.extend(_score_lines(
                spoken_move(result, text), view.total_matched,
                result.view.total_matched, result.view.required,
            ))
            current = _as_rows(result.board_rows)
            view = result.view
        return lines


def _score_lines(phrase: str, before: int, after: int, required: int) -> list[str]:
    lines = [f"{phrase}: {after} of {required} positions matched."]
    if after < before:
        lines.append(f"This move left a matching position. The count fell from {before} to {after}.")
    elif after == before:
        lines.append(f"The count stayed {after}.")
    return lines


def _fill_word(mark: str) -> str:
    if mark == "+":
        return "unfilled"
    if mark == "X":
        return "mismatch"
    if mark == ".":
        return "not required"
    return "filled"


def _mark_at(view: BuildView, square: str) -> str:
    column = "abcdefgh".index(square[0])
    row = 8 - int(square[1])
    return view.marks[row][column]


def _seen_word(piece: str) -> str:
    return "empty" if piece == "." else piece


def _state_lines(rows: BoardRows) -> list[str]:
    board = rows.engine_copy()
    fen = board.to_fen()
    side = "White" if fen.split()[1] == "w" else "Black"
    return [
        f"Side to move: {side}",
        f"Chess state: {fen}",
        f"Position history: {len(board.history)} recorded keys",
    ]


def _paired_board(real: list[str], blueprint: list[str], fill: tuple[str, ...] | list[str]) -> list[str]:
    lines = ["        real board  blueprint   fill"]
    for index, (real_row, doll_row, fill_row) in enumerate(zip(real, blueprint, fill)):
        lines.append(f"rank {8 - index}  {real_row}    {doll_row}    {fill_row}")
    return lines


def _forming_lines(title: str, ranked: tuple[RankedStrategy, ...]) -> list[str]:
    lines = [title]
    for index, item in enumerate(ranked, start=1):
        lines.append(
            f"{index}. {item.name}  score={item.score}  "
            f"#={item.filled}  +={item.empty}  X={item.wrong}"
        )
        lines.append(f"   {item.sentence}")
    lines.append("IDENTITY CLAIMED: no")
    return lines


def _target_lines(title: str, targets: tuple[TargetChoice, ...]) -> list[str]:
    lines = [title]
    if not targets:
        lines.append("(none)")
        return lines
    for target in targets:
        if target.moves:
            legal = "legal move " + " or ".join(target.moves)
        else:
            legal = "no legal move this turn"
        lines.append(
            f"{target.square} {target.mark} wants {target.expected}, "
            f"seen {_seen_word(target.seen)}, {legal}"
        )
    return lines


def _arrival_lines(result: MoveResult) -> list[str]:
    lines = [result.enter_line, result.leave_line]
    for square in result.enters:
        lines.append(f"{square} is {_fill_word(_mark_at(result.view, square))}")
    for square in result.leaves:
        lines.append(f"{square} is {_fill_word(_mark_at(result.view, square))}")
    return lines


def format_position(session: PlaySession) -> str:
    """Real pieces, the fixed blueprint, its fill, and both real lists."""
    view = session.view()
    lines = [
        f"Blueprint: {session.doll.name} ({session.doll.id})",
        "The blueprint stays fixed. Chess pieces arrive only by legal moves.",
        "",
        "Real board and blueprint",
        *_paired_board(session.rows, session.doll.board, view.marks),
        "",
        f"Matched: {view.total_matched} of {view.required} positions matched.",
        f"Filled {view.filled}, empty {view.empty}, wrong {view.wrong}",
        *_state_lines(session.rows),
        "",
        "Move record",
        *session.development_lines(),
        "",
        *_forming_lines("Real Strategy Forming List", session.forming()),
        "",
        *_target_lines("Real Greatest Target List", session.targets()),
    ]
    return "\n".join(lines)


def format_accept(session: PlaySession, result: MoveResult, before_matched: int) -> str:
    """What the latest typed move did, then the real board when it was accepted."""
    if not result.legal:
        view = session.view()
        lines = [
            result.message,
            "The real chessboard is unchanged.",
            f"Matched: {view.total_matched} of {view.required} positions matched.",
            *_state_lines(session.rows),
            "Real Strategy Forming List unchanged.",
        ]
        return "\n".join(lines)

    lines = [
        "Accepted real move",
        spoken_move(result, session.accepted[-1]),
        *_arrival_lines(result),
        *_score_lines("Matched", before_matched, result.view.total_matched, result.view.required),
        "",
        format_position(session),
    ]
    return "\n".join(lines)


def format_imagine(session: PlaySession, line: TheoreticalLine) -> str:
    """Move-by-move copy. The real board is printed again only as a confirmation."""
    lines = ["Imaginary line on a copy. The real chessboard is not changed.", ""]
    if not line.steps:
        lines.append("No legal move is available on the copy.")
    for number, step in enumerate(line.steps, start=1):
        if step.result.legal:
            heading = f"Imaginary move {number}: {spoken_move(step.result, step.move_text)}"
        else:
            heading = f"Imaginary move {number}: refused {step.move_text!r}. The copy did not advance."
        lines.append(heading)
        lines.extend(_arrival_lines(step.result))
        lines.extend(_score_lines(
            "Matched", step.matched_before, step.matched_after, step.required,
        ))
        position = _as_rows(step.result.board_rows)
        lines.append("")
        lines.append("Theoretical board and blueprint")
        lines.extend(_paired_board(position, session.doll.board, step.result.view.marks))
        lines.extend(_state_lines(position))
        lines.append("")
        lines.extend(_forming_lines("Theoretical Strategy Forming List", step.forming))
        lines.append("")
        lines.extend(_target_lines("Theoretical Greatest Target List", step.targets))
        lines.append("")
    lines.append(f"REAL BOARD UNCHANGED: {'yes' if line.real_unchanged else 'no'}")
    lines.append(f"Real chess state: {session.fen()}")
    real = session.view()
    lines.append(f"Real matched: {real.total_matched} of {real.required} positions matched.")
    lines.append("IDENTITY CLAIMED: no")
    return "\n".join(lines)


def handle_command(session: PlaySession, text: str) -> str | None:
    """Run one typed command. None means the player asked to leave."""
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
        parts = lowered.split(maxsplit=1)
        if len(parts) == 1:
            return "Type doll and an id, for example: doll develop-to-the-center"
        try:
            session.select(parts[1])
        except KeyError as exc:
            return str(exc)
        return format_position(session)
    if lowered == "imagine" or lowered.startswith("imagine "):
        parts = command.split()
        moves = tuple(parts[1:]) if len(parts) > 1 else None
        return format_imagine(session, session.imagine(moves))
    before = session.view().total_matched
    return format_accept(session, session.accept(command), before)