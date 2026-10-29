"""Re-export of move legality + apply helpers (for older imports).

Beginners: prefer reading move_legality.py and move_apply.py instead of this file.
"""

from .move_legality import (
    can_castle,
    move_is_en_passant,
    pawn_move_is_pseudo_legal,
    king_move_is_pseudo_legal,
    promotion_is_valid,
    pseudo_legal,
    legal_move,
    destination_is_legal,
)
from .move_apply import (
    apply_move_to_board,
    mark_rook_at_home_square,
    update_castle_state,
    make_move,
    consider_move,
)

__all__ = [
    "can_castle",
    "move_is_en_passant",
    "pawn_move_is_pseudo_legal",
    "king_move_is_pseudo_legal",
    "promotion_is_valid",
    "pseudo_legal",
    "apply_move_to_board",
    "legal_move",
    "destination_is_legal",
    "mark_rook_at_home_square",
    "update_castle_state",
    "make_move",
    "consider_move",
]
