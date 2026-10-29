"""One real chess game held up against one selected blueprint."""

from __future__ import annotations

from typing import Iterable

from calculator.build_shape import (
    MoveResult,
    apply_legal_move,
    build_view,
    imaginary_moves,
    render_board,
    starting_board,
)
from calculator.play_rank import (
    as_engine_rows,
    auto_moves,
    rank_strategies,
    target_choices,
)
from calculator.play_types import (
    RankedStrategy,
    TargetChoice,
    TheoreticalLine,
    TheoreticalStep,
    spoken_move,
)
from calculator.strategies import get_strategy
from chess_module.chess_engine.board import Board


class PlaySession:
    """One real chess game held up against one selected blueprint."""

    def __init__(
        self, doll_id: str | int = "develop-to-the-center", board: Board | None = None
    ) -> None:
        self.doll = get_strategy(doll_id)
        self.rows = starting_board() if board is None else render_board(board)
        self.initial = self.rows.copy()
        self.accepted: list[str] = []

    def select(self, id_or_number: str) -> None:
        """Hold a different blueprint against the same real game."""
        token: str | int = (
            int(id_or_number)
            if (
                id_or_number.isascii()
                and id_or_number.isdigit()
                and len(id_or_number) <= 2
            )
            else id_or_number
        )
        self.doll = get_strategy(token)

    def view(self):
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
        """Everything a real move may change, and an imaginary move must not."""
        return (
            self.fen(),
            tuple(self.history()),
            tuple(self.rows),
            self.forming(),
            tuple(self.accepted),
            self.doll.id,
        )

    def accept(self, move_text: str) -> MoveResult:
        """Validate one move. Only a legal move replaces the real board."""
        text = move_text.strip()
        result = apply_legal_move(self.rows, text, self.doll)
        if result.legal:
            self.rows = as_engine_rows(result.board_rows)
            self.accepted.append(text)
        return result

    def imagine(self, moves: Iterable[str] | None = None) -> TheoreticalLine:
        """Play a line on a copy. Default is four legal filling tries."""
        texts = None if moves is None else imaginary_moves(moves)
        before = self.state_key()
        if texts is None:
            texts = auto_moves(self.doll, self.rows)
        current = self.rows.copy()
        steps = []
        for text in texts:
            before_matched = build_view(self.doll, current).total_matched
            result = apply_legal_move(current, text, self.doll)
            position = as_engine_rows(result.board_rows)
            steps.append(
                TheoreticalStep(
                    text,
                    result,
                    before_matched,
                    result.view.total_matched,
                    result.view.required,
                    rank_strategies(position),
                    target_choices(self.doll, position),
                )
            )
            if result.legal:
                current = position
        return TheoreticalLine(tuple(steps), self.state_key() == before)

    def development_lines(self) -> list[str]:
        """Replay the accepted moves against the selected blueprint."""
        from calculator.play_format import score_lines

        current = self.initial.copy()
        view = build_view(self.doll, current)
        lines = [
            f"Starting board: {view.total_matched} of {view.required} positions matched."
        ]
        for text in self.accepted:
            result = apply_legal_move(current, text, self.doll)
            if not result.legal:
                lines.append(f"Replay refused {text!r}. The record stopped here.")
                break
            lines.extend(
                score_lines(
                    spoken_move(result, text),
                    view.total_matched,
                    result.view.total_matched,
                    result.view.required,
                )
            )
            current = as_engine_rows(result.board_rows)
            view = result.view
        return lines
