"""What you see in the terminal: colored board, legal squares, move preview.

Re-exports ui_board (drawing) and ui_changes (BEFORE/AFTER preview text).
Playing still requires F in the CLI after you preview a destination.
"""

from .ui_board import (
    enable_windows_colors,
    selected_destinations,
    print_selection_near_prompt,
    display,
    list_piece_moves,
    next_chunk,
    print_side_by_side,
)
from .ui_changes import (
    is_en_passant_capture,
    resolve_piece_after_move,
    print_piece_changes,
    compare_all_other_pieces,
    show_step2_after,
)

__all__ = [
    "enable_windows_colors",
    "selected_destinations",
    "print_selection_near_prompt",
    "display",
    "list_piece_moves",
    "next_chunk",
    "print_side_by_side",
    "is_en_passant_capture",
    "resolve_piece_after_move",
    "print_piece_changes",
    "compare_all_other_pieces",
    "show_step2_after",
]
