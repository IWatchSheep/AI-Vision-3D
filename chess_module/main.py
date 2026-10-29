"""Start the two-player chess game in the terminal.

This file runs the main loop: show the board, read your command, and repeat until
checkmate, draw, quit, or an invalid position. All typing rules live in cli_commands;
this file only wires display + input together.

Move flow (every time):
  1. Start square (e2)
  2. Destination (e4) — preview only; the board does not change yet
  3. F — play the move for real

N cancels selection; help lists commands.
"""

if __package__:
    from .chess_engine.constants import WHITE, BLACK, CYAN, RESET
    from .chess_engine.movegen import is_in_check, has_king, game_over
    from .chess_engine.ui import display, print_selection_near_prompt, enable_windows_colors
    from .chess_engine.cli_session import GameSession, err, sanitize_display_text
    from .chess_engine.cli_commands import print_instructions, build_prompt, process_command
else:
    from chess_engine.constants import WHITE, BLACK, CYAN, RESET
    from chess_engine.movegen import is_in_check, has_king, game_over
    from chess_engine.ui import display, print_selection_near_prompt, enable_windows_colors
    from chess_engine.cli_session import GameSession, err, sanitize_display_text
    from chess_engine.cli_commands import print_instructions, build_prompt, process_command


def main() -> None:
    """Run one hotseat game until checkmate, draw, quit, or an invalid board."""
    enable_windows_colors()
    print("=== Simple 2-Player Chess ===")

    session = GameSession()

    while True:
        board = session.board

        # Sanity check after FEN load or bugs — both kings must be on the board.
        if not has_king(board, WHITE) or not has_king(board, BLACK):
            print("Invalid position: both kings must be on the board.")
            break

        display(board, session.selected_row, session.selected_col)

        is_over, is_stalemate, draw_reason = game_over(board)
        if is_over:
            if is_stalemate:
                print("Game Over! Stalemate.")
            elif draw_reason:
                print(f"Game Over! Draw by {draw_reason}.")
            else:
                # Side to move cannot move and is in check -> the other side won.
                winner = "Black" if board.turn == WHITE else "White"
                print(f"Checkmate! {winner} wins!")
            break

        if is_in_check(board, board.turn):
            print(f"{CYAN}Your king is in check!{RESET}")

        print_instructions(session)
        print_selection_near_prompt(board, session.selected_row, session.selected_col)

        # Read one line; empty input just redisplays the board.
        try:
            line = input(build_prompt(session)).strip()
        except (EOFError, KeyboardInterrupt):
            print("")
            break

        if not line:
            continue

        try:
            result = process_command(session, line)
        except Exception as exc:
            # process_command already catches most errors; keep the loop alive.
            # Sanitize so exception text cannot inject terminal control codes.
            err(f"Unexpected error: {sanitize_display_text(str(exc), 120)}")
            continue

        if result == "quit":
            break
        if result == "unknown":
            err(
                "Unknown command. Enter a square, or use F, P, N, "
                "restart, quit, claim or resign."
            )


if __name__ == "__main__":
    main()
