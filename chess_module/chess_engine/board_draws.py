"""Draw adjudication helpers used by Board."""

from typing import TYPE_CHECKING, Optional, Tuple

from .constants import BOARD_SIZE, Color

if TYPE_CHECKING:
    from .board import Board
    from .move import Move


def dead_position(board: "Board") -> bool:
    """True when material cannot deliver checkmate under common FIDE cases."""
    minors = 0
    bishops = 0
    bishop_color = -1
    bishops_same_color = True

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board.grid[r][c]
            if p.is_empty or p.type == "K":
                continue
            if p.type not in ("B", "N"):
                return False
            minors += 1
            if p.type == "B":
                bishops += 1
                sq_color = (r + c) % 2
                if bishop_color == -1:
                    bishop_color = sq_color
                elif bishop_color != sq_color:
                    bishops_same_color = False

    if minors <= 1:
        return True
    if bishops == minors and bishops_same_color:
        return True
    return False


def automatic_draw(board: "Board") -> Tuple[bool, Optional[str]]:
    """Mandatory draws: 75-move, fivefold repetition, dead position."""
    from .movegen import is_in_check, generate_moves
    from .board_key import repetition_count

    reason = None
    if board.halfmove_clock >= 150:
        reason = "75-move rule"
    elif repetition_count(board) >= 5:
        reason = "fivefold repetition"
    elif dead_position(board):
        reason = "dead position"
    if reason:
        if is_in_check(board, board.turn) and not generate_moves(board):
            return False, None
        return True, reason
    return False, None


def insufficient_mating_material(board: "Board", side: Color) -> bool:
    """True when this side cannot force mate with the material on the board."""
    own = [p for row in board.grid for p in row if p.color == side]
    all_pieces = [p for row in board.grid for p in row if not p.is_empty]
    enemy_helpers = [p for p in all_pieces if p.color != side and p.type != "K"]

    if any(p.type in ("P", "R", "Q") for p in own):
        return False

    if any(p.type == "N" for p in own):
        return len(own) <= 2 and not enemy_helpers

    if any(p.type == "B" for p in own):
        shades = {
            (r + c) % 2
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            if board.grid[r][c].type == "B"
        }
        if len(shades) != 1:
            return False
        if any(p.type in ("P", "N", "R", "Q") for p in all_pieces):
            return False
        return True

    return True


def claimable_draw(
    board: "Board", intended_move: Optional["Move"] = None
) -> Tuple[bool, Optional[str]]:
    """Claimable draws: 50-move rule or threefold repetition."""
    from .movegen import legal_move, make_move, game_over, generate_moves
    from .board_key import repetition_count

    if game_over(board)[0]:
        return False, None

    if board.halfmove_clock >= 100:
        return True, "50-move rule"
    if repetition_count(board) >= 3:
        return True, "threefold repetition"

    pos = board
    has_intended = intended_move is not None
    if has_intended:
        if not legal_move(board, intended_move):
            return False, None
        after_move = board.clone()
        make_move(after_move, intended_move)
        pos = after_move
        if not generate_moves(pos):
            return False, None

    if pos.halfmove_clock >= 100:
        return True, "50-move rule"

    needed = 2 if has_intended else 3
    if repetition_count(pos) >= needed:
        return True, "threefold repetition"

    return False, None
