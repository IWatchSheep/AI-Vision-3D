"""Text reports for the real board, accepted moves, and imaginary lines."""

from __future__ import annotations

from calculator.build_shape import BoardRows, BuildView, MoveResult
from calculator.play_rank import as_engine_rows
from calculator.play_session import PlaySession
from calculator.play_types import RankedStrategy, TargetChoice, TheoreticalLine, spoken_move


def score_lines(phrase: str, before: int, after: int, required: int) -> list[str]:
    lines = [f"{phrase}: {after} of {required} positions matched."]
    if after < before:
        lines.append(
            f"This move left a matching position. The count fell from {before} to {after}."
        )
    elif after == before:
        lines.append(f"The count stayed {after}.")
    return lines


def fill_word(mark: str) -> str:
    if mark == "+":
        return "unfilled"
    if mark == "X":
        return "mismatch"
    if mark == ".":
        return "not required"
    return "filled"


def mark_at(view: BuildView, square: str) -> str:
    if (
        not isinstance(square, str)
        or len(square) != 2
        or square[0] not in "abcdefgh"
        or square[1] not in "12345678"
    ):
        raise ValueError(f"Invalid square: {square!r}")
    column = "abcdefgh".index(square[0])
    row = 8 - int(square[1])
    return view.marks[row][column]


def seen_word(piece: str) -> str:
    return "empty" if piece == "." else piece


def state_lines(rows: BoardRows) -> list[str]:
    board = rows.engine_copy()
    fen = board.to_fen()
    side = "White" if fen.split()[1] == "w" else "Black"
    return [
        f"Side to move: {side}",
        f"Chess state: {fen}",
        f"Position history: {len(board.history)} recorded keys",
    ]


def paired_board(
    real: list[str], blueprint: list[str], fill: tuple[str, ...] | list[str]
) -> list[str]:
    lines = ["        real board  blueprint   fill"]
    for index, (real_row, doll_row, fill_row) in enumerate(zip(real, blueprint, fill)):
        lines.append(f"rank {8 - index}  {real_row}    {doll_row}    {fill_row}")
    return lines


def forming_lines(title: str, ranked: tuple[RankedStrategy, ...]) -> list[str]:
    lines = [title]
    for index, item in enumerate(ranked, start=1):
        lines.append(
            f"{index}. {item.name}  score={item.score}  "
            f"#={item.filled}  +={item.empty}  X={item.wrong}"
        )
        lines.append(f"   {item.sentence}")
    lines.append("IDENTITY CLAIMED: no")
    return lines


def target_lines(title: str, targets: tuple[TargetChoice, ...]) -> list[str]:
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
            f"seen {seen_word(target.seen)}, {legal}"
        )
    return lines


def arrival_lines(result: MoveResult) -> list[str]:
    lines = [result.enter_line, result.leave_line]
    for square in result.enters:
        lines.append(f"{square} is {fill_word(mark_at(result.view, square))}")
    for square in result.leaves:
        lines.append(f"{square} is {fill_word(mark_at(result.view, square))}")
    return lines


def format_position(session: PlaySession) -> str:
    """Real pieces, the fixed blueprint, its fill, and both real lists."""
    view = session.view()
    lines = [
        f"Blueprint: {session.doll.name} ({session.doll.id})",
        "The blueprint stays fixed. Chess pieces arrive only by legal moves.",
        "",
        "Real board and blueprint",
        *paired_board(session.rows, session.doll.board, view.marks),
        "",
        f"Matched: {view.total_matched} of {view.required} positions matched.",
        f"Filled {view.filled}, empty {view.empty}, wrong {view.wrong}",
        *state_lines(session.rows),
        "",
        "Move record",
        *session.development_lines(),
        "",
        *forming_lines("Real Strategy Forming List", session.forming()),
        "",
        *target_lines("Real Greatest Target List", session.targets()),
    ]
    return "\n".join(lines)


def format_accept(
    session: PlaySession, result: MoveResult, before_matched: int
) -> str:
    """What the latest typed move did, then the real board when it was accepted."""
    if not result.legal:
        view = session.view()
        lines = [
            result.message,
            "The real chessboard is unchanged.",
            f"Matched: {view.total_matched} of {view.required} positions matched.",
            *state_lines(session.rows),
            "Real Strategy Forming List unchanged.",
        ]
        return "\n".join(lines)

    lines = [
        "Accepted real move",
        spoken_move(result, session.accepted[-1]),
        *arrival_lines(result),
        *score_lines(
            "Matched", before_matched, result.view.total_matched, result.view.required
        ),
        "",
        format_position(session),
    ]
    return "\n".join(lines)


def format_imagine(session: PlaySession, line: TheoreticalLine) -> str:
    """Move-by-move copy. The real board is printed again only as confirmation."""
    lines = ["Imaginary line on a copy. The real chessboard is not changed.", ""]
    if not line.steps:
        lines.append("No legal move is available on the copy.")
    for number, step in enumerate(line.steps, start=1):
        if step.result.legal:
            heading = (
                f"Imaginary move {number}: {spoken_move(step.result, step.move_text)}"
            )
        else:
            heading = (
                f"Imaginary move {number}: refused {step.move_text!r}. "
                "The copy did not advance."
            )
        lines.append(heading)
        lines.extend(arrival_lines(step.result))
        lines.extend(
            score_lines(
                "Matched", step.matched_before, step.matched_after, step.required
            )
        )
        position = as_engine_rows(step.result.board_rows)
        lines.append("")
        lines.append("Theoretical board and blueprint")
        lines.extend(paired_board(position, session.doll.board, step.result.view.marks))
        lines.extend(state_lines(position))
        lines.append("")
        lines.extend(forming_lines("Theoretical Strategy Forming List", step.forming))
        lines.append("")
        lines.extend(target_lines("Theoretical Greatest Target List", step.targets))
        lines.append("")
    lines.append(f"REAL BOARD UNCHANGED: {'yes' if line.real_unchanged else 'no'}")
    lines.append(f"Real chess state: {session.fen()}")
    real = session.view()
    lines.append(
        f"Real matched: {real.total_matched} of {real.required} positions matched."
    )
    lines.append("IDENTITY CLAIMED: no")
    return "\n".join(lines)
