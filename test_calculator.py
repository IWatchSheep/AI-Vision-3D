"""Tests for the chess strategy calculator dolls and fill."""

from __future__ import annotations

import io
import pathlib
import unittest
from contextlib import redirect_stdout

from calculator.pattern import compare, print_fill
from calculator.strategies import (
    STRATEGIES,
    board_to_fen_pieces,
    fen_piece_field,
    get_strategy,
    print_joints,
)

PIECE_CHARS = set("KQRBNPkqrbnp.")


class TestStrategies(unittest.TestCase):
    def test_exactly_twenty_strategies_numbered_1_to_20(self) -> None:
        self.assertEqual(len(STRATEGIES), 20)
        numbers = [s.number for s in STRATEGIES]
        self.assertEqual(numbers, list(range(1, 21)))

    def test_unique_ids(self) -> None:
        ids = [s.id for s in STRATEGIES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_board_shape_and_chars(self) -> None:
        for s in STRATEGIES:
            self.assertEqual(len(s.board), 8, msg=s.id)
            for row in s.board:
                self.assertEqual(len(row), 8, msg=s.id)
                self.assertTrue(set(row) <= PIECE_CHARS, msg=f"{s.id}: {row}")

    def test_both_kings_on_every_board(self) -> None:
        for s in STRATEGIES:
            flat = "".join(s.board)
            self.assertIn("K", flat, msg=s.id)
            self.assertIn("k", flat, msg=s.id)

    def test_fen_piece_field_matches_ascii(self) -> None:
        for s in STRATEGIES:
            from_ascii = board_to_fen_pieces(s.board)
            from_fen = fen_piece_field(s.fen)
            self.assertEqual(
                from_ascii,
                from_fen,
                msg=f"{s.id}: ASCII FEN {from_ascii!r} != stored {from_fen!r}",
            )


class TestFill(unittest.TestCase):
    def test_kings_pawn_promotion_on_starting_array(self) -> None:
        starting = get_strategy("starting-array")
        doll = get_strategy("kings-pawn-promotion")
        result = compare(doll, starting.board)
        # e1 is rank 1 = row 7, file e = col 4
        self.assertEqual(result.fill[7][4], "#")
        # e7 is rank 7 = row 1, file e = col 4
        self.assertEqual(result.fill[1][4], "X")

    def test_develop_fill_perfect_against_itself(self) -> None:
        develop = get_strategy("develop-to-the-center")
        result = compare(develop, develop.board)
        self.assertEqual(result.plus_count, 0)
        self.assertEqual(result.x_count, 0)
        for row in result.fill:
            self.assertNotIn("+", row)
            self.assertNotIn("X", row)

    def test_perfect_fill_still_prints_identity_claimed_no(self) -> None:
        develop = get_strategy("develop-to-the-center")
        result = compare(develop, develop.board)
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_fill(result)
        self.assertIn("IDENTITY CLAIMED: no", buf.getvalue())

    def test_print_joints_leaves_board_unchanged(self) -> None:
        for s in STRATEGIES:
            before = list(s.board)
            buf = io.StringIO()
            with redirect_stdout(buf):
                print_joints(s)
            self.assertEqual(s.board, before, msg=s.id)


class TestNoForbiddenMentions(unittest.TestCase):
    def test_pattern_and_strategies_clean(self) -> None:
        root = pathlib.Path(__file__).resolve().parent / "calculator"
        for name in ("pattern.py", "strategies.py"):
            text = (root / name).read_text(encoding="utf-8").lower()
            self.assertNotIn("unity", text, msg=name)
            self.assertNotIn("camera", text, msg=name)
            self.assertNotIn("chess_module", text, msg=name)
            self.assertNotIn("import chess", text, msg=name)


if __name__ == "__main__":
    unittest.main()
