"""Tests for the chess strategy calculator dolls and fill.

These 10 checks must keep passing when the dolls and fill logic are edited.
"""

from __future__ import annotations

import io
import pathlib
import unittest
from contextlib import redirect_stdout

from calculator.pattern import FILL_MARKS, PatternWindow, compare, print_chess_fill, print_fill
from calculator.strategies import (
    BOARD_SIZE,
    PIECE_CHARS,
    STRATEGIES,
    board_to_fen_pieces,
    fen_piece_field,
    get_strategy,
    print_joints,
)
from calculator.strategies_data import RAW_DOLLS
from calculator.window import DEFAULT_PAST_LIMIT, MemoryWindow


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
            self.assertEqual(len(s.board), BOARD_SIZE, msg=s.id)
            for row in s.board:
                self.assertEqual(len(row), BOARD_SIZE, msg=s.id)
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


class TestFillInvariants(unittest.TestCase):
    """Additive checks: marks, counts, and score stay consistent."""

    def test_fill_marks_counts_and_score(self) -> None:
        starting = get_strategy("starting-array")
        for doll in STRATEGIES:
            result = compare(doll, starting.board)
            flat = "".join(result.fill)
            self.assertTrue(set(flat) <= FILL_MARKS, msg=doll.id)
            self.assertEqual(result.hash_count, flat.count("#"), msg=doll.id)
            self.assertEqual(result.plus_count, flat.count("+"), msg=doll.id)
            self.assertEqual(result.x_count, flat.count("X"), msg=doll.id)
            self.assertEqual(
                result.score,
                result.hash_count - result.x_count,
                msg=doll.id,
            )

    def test_compare_does_not_mutate_inputs(self) -> None:
        doll = get_strategy("starting-array")
        seen = list(doll.board)
        before_doll = list(doll.board)
        before_seen = list(seen)
        compare(doll, seen)
        self.assertEqual(doll.board, before_doll)
        self.assertEqual(seen, before_seen)

    def test_print_chess_fill_alias_matches_print_fill(self) -> None:
        develop = get_strategy("develop-to-the-center")
        result = compare(develop, develop.board)
        buf_a = io.StringIO()
        buf_b = io.StringIO()
        with redirect_stdout(buf_a):
            print_fill(result)
        with redirect_stdout(buf_b):
            print_chess_fill(result)
        self.assertEqual(buf_a.getvalue(), buf_b.getvalue())

    def test_strategy_copy_is_independent(self) -> None:
        original = get_strategy("starting-array")
        copied = original.copy()
        copied.board[0] = "X" * BOARD_SIZE
        self.assertNotEqual(original.board[0], copied.board[0])

    def test_raw_dolls_match_loaded_strategies(self) -> None:
        self.assertEqual(len(RAW_DOLLS), len(STRATEGIES))
        for raw, loaded in zip(RAW_DOLLS, STRATEGIES):
            self.assertEqual(raw["id"], loaded.id)
            self.assertEqual(raw["number"], loaded.number)

    def test_pattern_window_uses_shared_limit(self) -> None:
        window = PatternWindow()
        memory = MemoryWindow(limit=DEFAULT_PAST_LIMIT)
        for i in range(DEFAULT_PAST_LIMIT + 1):
            doll = STRATEGIES[i]
            result = compare(doll, doll.board)
            window.set_current(result)
            window.accept()
            memory.set_current(result)
            memory.accept()
        self.assertEqual(len(window.past), DEFAULT_PAST_LIMIT)
        self.assertEqual(len(memory.past), DEFAULT_PAST_LIMIT)

    def test_compare_result_does_not_alias_live_doll(self) -> None:
        # Mutating result.strategy must not change the doll on record.
        doll = get_strategy("starting-array")
        before = list(doll.board)
        result = compare(doll, doll.board)
        result.strategy.board[0] = "X" * BOARD_SIZE
        self.assertEqual(doll.board, before)
        self.assertEqual(get_strategy("starting-array").board, before)

    def test_memory_window_rejects_bad_limits(self) -> None:
        with self.assertRaises(ValueError):
            MemoryWindow(limit=0)
        with self.assertRaises(ValueError):
            MemoryWindow(limit=-1)
        with self.assertRaises(ValueError):
            MemoryWindow(limit=True)

    def test_memory_window_trim_on_replace_past(self) -> None:
        memory = MemoryWindow(limit=2)
        memory.replace_past(["a", "b", "c", "d"])
        self.assertEqual(memory.past, ["c", "d"])

    def test_memory_window_does_not_mutate_or_alias_supplied_history(self) -> None:
        history = ["a", "b", "c"]
        memory = MemoryWindow(limit=2, past=history)
        self.assertEqual(history, ["a", "b", "c"])
        history.append("d")
        self.assertEqual(memory.past, ["b", "c"])

    def test_invalid_changed_limit_preserves_pending_item(self) -> None:
        memory = MemoryWindow(limit=2, past=["a"], current="b")
        memory.limit = -1
        with self.assertRaises(ValueError):
            memory.accept()
        self.assertEqual(memory.current, "b")
        self.assertEqual(memory.past, ["a"])


if __name__ == "__main__":
    unittest.main()
