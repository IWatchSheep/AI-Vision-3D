"""Interactive strategy building. The real board changes only when a move is legal.

Run from the project folder:

    python show_play.py

Type a move such as e2e4 to accept it. Type imagine to look four moves ahead
on a copy. The plain chess game is still python main.py. python show_build.py
still prints the fixed four-move demonstration.
"""

from calculator.play_build import HELP, PlaySession, format_position, handle_command


def main() -> None:
    session = PlaySession()
    print(format_position(session))
    print()
    print(HELP)
    while True:
        try:
            typed = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        output = handle_command(session, typed)
        if output is None:
            return
        if output:
            print(output)


if __name__ == "__main__":
    main()
