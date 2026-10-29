"""Project entry point: start the chess game when chess_module is present.

PyCharm "Run" on this file delegates to chess_module.main. If the chess
subpackage is missing (wrong branch), prints a short hint instead of crashing.
"""

from pathlib import Path


def main() -> None:
    chess_folder = Path(__file__).resolve().parent / "chess_module"
    if not (chess_folder / "main.py").is_file():
        print("Chess game is not in this checkout. Open the feature/chess-integration branch.")
        return

    from chess_module.main import main as chess_main

    chess_main()


if __name__ == "__main__":
    main()
