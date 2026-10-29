"""Demo: fill the develop-to-the-center doll by playing four moves on a copy.

The live chess_module board stays unchanged; imagine_line() only mutates
BoardRows copies. Run with: python show_build.py
"""

from calculator.build_shape import build_view, imagine_line, render_board
from calculator.strategies import get_strategy
from chess_module.chess_engine.board import Board


def main() -> None:
    doll = get_strategy("develop-to-the-center")
    live_board = Board()
    live_board.reset_board()
    before_fen = live_board.to_fen()
    real_rows = render_board(live_board)

    print(f"Known blueprint: {doll.name}")
    for row in doll.board:
        print(row)
    print("\nReal board")
    for row in real_rows:
        print(row)
    print("\nBlueprint fill")
    initial = build_view(doll, real_rows)
    for row in initial.marks:
        print(row)
    print(f"Total blueprint positions matched: {initial.total_matched}")

    line = imagine_line(doll, real_rows, ("e2e4", "e7e5", "g1f3", "b8c6"))
    for number, step in enumerate(line.steps, 1):
        print(f"\nImaginary move {number}: {step.result.message}")
        print(step.result.enter_line)
        print(step.result.leave_line)
        print(f"New target positions filled on this line: {step.new_targets_filled} of {step.new_targets_total}")
        print("Theoretical Strategy Forming List")
        forming = step.strategy_forming_list
        print(f"{doll.id}: filled {forming.filled}, empty {forming.empty}, wrong {forming.wrong}")
        print(f"Total blueprint positions matched: {forming.total_matched}")
        print("Theoretical Greatest Target List")
        for target in step.greatest_target_list:
            print(f"{target.square} {target.mark} wants {target.expected}, seen {target.seen}")
        if not step.greatest_target_list:
            print("(none)")

    unchanged = line.real_unchanged and live_board.to_fen() == before_fen
    print(f"\nREAL BOARD UNCHANGED: {'yes' if unchanged else 'no'}")
    print("IDENTITY CLAIMED: no")


if __name__ == "__main__":
    main()
