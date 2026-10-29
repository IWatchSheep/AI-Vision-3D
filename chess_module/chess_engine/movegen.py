"""How pieces move: attacks, legal moves, and applying a move to the board.

Beginner map:
  piece_attacks / path_clear  — can this piece hit that square?
  pseudo_legal / legal_move   — is this Move allowed right now?
  generate_moves              — every legal move for the side to play
  make_move                   — actually play it (updates clocks, EP, turn)

Implementation is split across attacks.py, move_legality.py, move_apply.py,
and move_gen.py (move_rules.py bundles legality + apply). This file
re-exports the public API so older imports from movegen still work.
"""

from .attacks import (
    pawn_direction,
    is_knight_move,
    is_diagonal_move,
    is_straight_move,
    is_queen_move,
    path_clear,
    piece_attacks,
    square_attacked,
    count_attackers,
    find_king,
    has_king,
    is_in_check,
)
from .move_rules import (
    can_castle,
    move_is_en_passant,
    pawn_move_is_pseudo_legal,
    king_move_is_pseudo_legal,
    promotion_is_valid,
    pseudo_legal,
    apply_move_to_board,
    legal_move,
    destination_is_legal,
    mark_rook_at_home_square,
    update_castle_state,
    make_move,
    consider_move,
)
from .move_gen import (
    generate_sliding_moves,
    generate_pawn_moves,
    generate_knight_moves,
    generate_king_moves,
    generate_piece_moves,
    generate_moves,
    sorted_moves,
    legal_destination_map,
    game_over,
)

__all__ = [
    "pawn_direction",
    "is_knight_move",
    "is_diagonal_move",
    "is_straight_move",
    "is_queen_move",
    "path_clear",
    "piece_attacks",
    "square_attacked",
    "count_attackers",
    "find_king",
    "has_king",
    "is_in_check",
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
    "generate_sliding_moves",
    "generate_pawn_moves",
    "generate_knight_moves",
    "generate_king_moves",
    "generate_piece_moves",
    "generate_moves",
    "sorted_moves",
    "legal_destination_map",
    "game_over",
]
