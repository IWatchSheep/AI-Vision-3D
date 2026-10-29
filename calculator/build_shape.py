"""Fill a fixed chess blueprint by playing engine-approved moves on copies.

BoardRows presents eight strings to the existing doll comparator, and keeps
a private engine snapshot for turn, castling, en passant, clocks and history.
Use render_board(live_board) to begin from any live chess_module position.
Plain row lists are accepted as move inputs only for the standard initial
position: arbitrary placement alone cannot tell us whose turn it is or which
castling/en passant rights remain. Never reconstruct rules from a picture.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
from typing import Iterable

from calculator.pattern import cell_name, compare
from calculator.strategies import BOARD_SIZE, Strategy, require_board
from chess_module.chess_engine.board import Board
from chess_module.chess_engine.constants import HISTORY_MAX_LEN
from chess_module.chess_engine.move import parse_move_text
from chess_module.chess_engine.movegen import game_over, legal_move, make_move
from chess_module.chess_engine.tracker import FollowCase, follow_piece

IMAGINE_STEP_LIMIT = 4


def imaginary_moves(moves: Iterable[str], limit: int = IMAGINE_STEP_LIMIT) -> tuple[str, ...]:
    """Validate a supplied line without exhausting an unbounded iterable."""
    if (not isinstance(limit, int) or isinstance(limit, bool)
            or not 0 <= limit <= HISTORY_MAX_LEN):
        raise ValueError(f"Move limit must be an integer from zero to {HISTORY_MAX_LEN}")
    if isinstance(moves, (str, bytes)):
        raise ValueError("Supply a sequence of moves")
    texts = tuple(islice(moves, limit + 1))
    if len(texts) > limit:
        raise ValueError(f"An imaginary line is limited to {limit} moves")
    if any(not isinstance(text, str) for text in texts):
        raise ValueError("Imaginary moves must be text")
    return texts


def _rows(board: Board) -> list[str]:
    return [
        "".join("." if piece.is_empty else piece.symbol for piece in row)
        for row in board.grid
    ]


class BoardRows(list[str]):
    """Eight rendered rows backed by a private, complete engine position.

    Changing the strings by hand is rejected when a move is requested. Copy
    through copy() or render_board() to retain the complete chess state.
    """

    def __init__(self, board: Board) -> None:
        self.__position = board.clone()
        super().__init__(_rows(self.__position))

    def engine_copy(self) -> Board:
        if list(self) != _rows(self.__position):
            raise ValueError("Board rows were edited; render a live engine board instead")
        return self.__position.clone()

    def copy(self) -> BoardRows:
        return BoardRows(self.engine_copy())


def render_board(board: Board) -> BoardRows:
    """Render a live engine board without changing it or sharing mutable state."""
    return BoardRows(board)


def starting_board() -> BoardRows:
    board = Board()
    board.reset_board()
    return render_board(board)


def _engine_copy(board_rows: list[str]) -> Board:
    require_board(board_rows, label="real board")
    if isinstance(board_rows, BoardRows):
        return board_rows.engine_copy()
    board = Board()
    board.reset_board()
    if board_rows != _rows(board):
        raise ValueError("Render the live engine board to preserve turn and special-move rights")
    return board


@dataclass(frozen=True)
class BuildTarget:
    square: str
    expected: str
    seen: str
    mark: str


@dataclass(frozen=True)
class BuildView:
    marks: tuple[str, ...]
    filled: int
    empty: int
    wrong: int
    filled_squares: tuple[str, ...]
    targets: tuple[BuildTarget, ...]

    @property
    def total_matched(self) -> int:
        return self.filled

    @property
    def required(self) -> int:
        return self.filled + self.empty + self.wrong


def build_view(doll: Strategy, board_rows: list[str]) -> BuildView:
    """Compare required squares, keeping matched piece letters in the fill."""
    compared = compare(doll, board_rows)
    marks = []
    filled_squares = []
    targets = []
    for r in range(BOARD_SIZE):
        row = []
        for c in range(BOARD_SIZE):
            mark = compared.fill[r][c]
            if mark == "#":
                row.append(compared.strategy.board[r][c])
                filled_squares.append(cell_name(r, c))
            else:
                row.append(mark)
                if mark in ("+", "X"):
                    targets.append(BuildTarget(
                        cell_name(r, c), compared.strategy.board[r][c], board_rows[r][c], mark
                    ))
        marks.append("".join(row))
    return BuildView(tuple(marks), compared.hash_count, compared.plus_count,
                     compared.x_count, tuple(filled_squares), tuple(targets))


def print_build_view(view: BuildView) -> None:
    print("Blueprint fill")
    for row in view.marks:
        print(row)
    print(f"Filled {view.filled}, empty {view.empty}, wrong {view.wrong}")
    print(f"Total blueprint positions matched: {view.total_matched}")
    print("IDENTITY CLAIMED: no")


@dataclass(frozen=True)
class MoveResult:
    board_rows: list[str]
    legal: bool
    enters: tuple[str, ...]
    leaves: tuple[str, ...]
    message: str
    view: BuildView

    @property
    def enter_line(self) -> str:
        return f"ENTERS: {', '.join(self.enters) or 'none'}"

    @property
    def leave_line(self) -> str:
        return f"LEAVES: {', '.join(self.leaves) or 'none'}"


def apply_legal_move(board_rows: list[str], move_text: str, doll: Strategy) -> MoveResult:
    """Ask the chess engine to validate a move, then apply it to a clone.

    Arrivals/departures describe moving pieces on required squares, including
    both the king and rook in castling. They do not imply a correct match:
    a wrong piece arriving is X. An illegal move returns the original rows.
    """
    before = _engine_copy(board_rows)
    view = build_view(doll, board_rows)
    move = parse_move_text(move_text)
    if move is None or not legal_move(before, move) or game_over(before)[0]:
        return MoveResult(board_rows, False, (), (), f"Move refused: {move_text!r}", view)

    enters = []
    leaves = []
    moving_cases = {FollowCase.FOLLOW_MOVED, FollowCase.FOLLOW_PROMOTED,
                    FollowCase.FOLLOW_CASTLING_ROOK}
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = before.grid[r][c]
            if piece.is_empty or piece.color != before.turn:
                continue
            er, ec, _, outcome = follow_piece(before, move, r, c)
            if outcome not in moving_cases:
                continue
            if doll.board[r][c] != ".":
                leaves.append(cell_name(r, c))
            if doll.board[er][ec] != ".":
                enters.append(cell_name(er, ec))

    after = before.clone()
    make_move(after, move, record_history=True)
    new_rows = render_board(after)
    piece = before.grid[move.sr][move.sc].symbol
    message = (f"{piece} {cell_name(move.sr, move.sc)} -> {cell_name(move.er, move.ec)} "
               f"enters {', '.join(enters) or 'none'}, leaves {', '.join(leaves) or 'none'}")
    return MoveResult(new_rows, True, tuple(enters), tuple(leaves), message,
                      build_view(doll, new_rows))


@dataclass(frozen=True)
class StrategyFormingList:
    doll_id: str
    filled: int
    empty: int
    wrong: int
    total_matched: int


@dataclass(frozen=True)
class ImagineStep:
    move_text: str
    result: MoveResult
    strategy_forming_list: StrategyFormingList
    greatest_target_list: tuple[BuildTarget, ...]
    new_targets_filled: int
    new_targets_total: int


@dataclass(frozen=True)
class ImagineLine:
    steps: tuple[ImagineStep, ...]
    board_rows: BoardRows
    real_before: tuple[str, ...]
    real_after: tuple[str, ...]
    real_unchanged: bool


def imagine_line(doll: Strategy, board_rows: list[str], moves: Iterable[str]) -> ImagineLine:
    """Play the supplied line on copies, storing both theoretical lists.

    New targets are initially unfilled squares that become matched anywhere
    in this supplied line. Each step counts how many are still matched then,
    so progress can fall again. The denominator counts distinct such squares
    across the whole line, rather than all missing squares of the blueprint.
    A refused move is stored with unchanged counts and does not advance turn.
    """
    # This lower-level replay supports longer rule demonstrations, while the
    # interactive calculator limits imagination to four plies.
    texts = imaginary_moves(moves, HISTORY_MAX_LEN)
    blueprint = doll.copy()
    source = _engine_copy(board_rows)
    original_rows = tuple(board_rows)
    original_fen = source.to_fen()
    original_history = list(source.history)
    current = render_board(source)
    initial_filled = set(build_view(blueprint, current).filled_squares)
    # --- Pass 1: play the line on copies; track new blueprint squares filled ---
    records = []
    line_targets = set()
    for text in texts:
        result = apply_legal_move(current, text, blueprint)
        current = result.board_rows
        new_filled = set(result.view.filled_squares) - initial_filled
        line_targets.update(new_filled)
        records.append((text, result, len(new_filled)))

    # --- Pass 2: attach Strategy Forming / Greatest Target lists per step ---
    steps = []
    for text, result, new_count in records:
        view = result.view
        forming = StrategyFormingList(blueprint.id, view.filled, view.empty,
                                     view.wrong, view.total_matched)
        steps.append(ImagineStep(text, result, forming, view.targets,
                                 new_count, len(line_targets)))
    real_after = tuple(board_rows)
    real_position = _engine_copy(board_rows)
    unchanged = (original_rows == real_after and real_position.to_fen() == original_fen
                 and real_position.history == original_history)
    return ImagineLine(tuple(steps), current, original_rows, real_after, unchanged)
