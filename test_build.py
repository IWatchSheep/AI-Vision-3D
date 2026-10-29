"""Blueprint filling uses real chess turns, legal moves, and isolated copies."""

import contextlib
import io
import unittest

from calculator.build_shape import (
    apply_legal_move, build_view, imagine_line, print_build_view, render_board, starting_board,
)
from calculator.strategies import get_strategy
from chess_module.chess_engine.board import Board
from show_build import main as show_build


class TestBuild(unittest.TestCase):
    def setUp(self):
        self.doll = get_strategy("develop-to-the-center")
        self.rows = starting_board()
        self.moves = ("e2e4", "e7e5", "g1f3", "b8c6")

    def test_starting_array_has_twenty_two_filled_required_squares(self):
        view = build_view(self.doll, self.rows)
        self.assertEqual(view.filled, 22)
        self.assertEqual(view.total_matched, 22)
        self.assertEqual(view.required, 32)
        self.assertEqual(view.marks[7][4], "K")
        self.assertEqual(view.marks[4][4], "+")
        self.assertEqual(view.empty, 10)
        self.assertEqual(view.wrong, 0)
        self.assertEqual(view.marks[1][3], ".")
        self.assertEqual(view.marks[6][4], ".")

    def test_e2e4_arrives_without_departing_required_square(self):
        original = list(self.rows)
        result = apply_legal_move(self.rows, "e2e4", self.doll)
        self.assertTrue(result.legal)
        self.assertEqual(result.enters, ("e4",))
        self.assertEqual(result.leaves, ())
        self.assertEqual(result.view.total_matched, 23)
        self.assertEqual(result.message, "P e2 -> e4 enters e4, leaves none")
        self.assertEqual(self.rows, original)
        self.assertIsNot(result.board_rows, self.rows)

    def test_four_arrivals_follow_real_turns_and_total_twenty_six(self):
        rows = self.rows
        arrivals = []
        for index, move in enumerate(self.moves, 1):
            original = list(rows)
            result = apply_legal_move(rows, move, self.doll)
            self.assertTrue(result.legal, result.message)
            self.assertEqual(result.leaves, ())
            arrivals.extend(result.enters)
            self.assertEqual(result.view.filled, 22 + index)
            self.assertEqual(rows, original)
            rows = result.board_rows
        self.assertEqual(arrivals, ["e4", "e5", "f3", "c6"])

    def test_legal_departure_can_reduce_filled_count(self):
        result = apply_legal_move(self.rows, "a2a3", self.doll)
        self.assertTrue(result.legal)
        self.assertEqual(result.enters, ())
        self.assertEqual(result.leaves, ("a2",))
        self.assertEqual(result.view.filled, 21)
        self.assertEqual(result.view.marks[6][0], "+")

    def test_illegal_move_returns_original_board_without_advancing_turn(self):
        before_fen = self.rows.engine_copy().to_fen()
        before_history = self.rows.engine_copy().history
        refused = apply_legal_move(self.rows, "e2e5", self.doll)
        self.assertFalse(refused.legal)
        self.assertIn("refused", refused.message)
        self.assertIs(refused.board_rows, self.rows)
        self.assertEqual(self.rows.engine_copy().to_fen(), before_fen)
        self.assertEqual(self.rows.engine_copy().history, before_history)
        self.assertTrue(apply_legal_move(refused.board_rows, "e2e4", self.doll).legal)

    def test_same_side_cannot_move_twice(self):
        first = apply_legal_move(self.rows, "e2e4", self.doll)
        refused = apply_legal_move(first.board_rows, "g1f3", self.doll)
        self.assertFalse(refused.legal)
        self.assertIs(refused.board_rows, first.board_rows)

    def test_imagine_line_stores_both_lists_and_preserves_live_board(self):
        live = Board()
        live.reset_board()
        rows = render_board(live)
        before_rows = tuple(rows)
        before_fen = live.to_fen()
        before_history = list(live.history)
        result = imagine_line(self.doll, rows, self.moves)
        self.assertEqual([s.new_targets_filled for s in result.steps], [1, 2, 3, 4])
        self.assertEqual([s.new_targets_total for s in result.steps], [4, 4, 4, 4])
        for index, step in enumerate(result.steps, 1):
            forming = step.strategy_forming_list
            self.assertEqual(forming.total_matched, 22 + index)
            self.assertEqual(forming.filled + forming.empty + forming.wrong, 32)
            self.assertEqual(len(step.greatest_target_list), 10 - index)
            self.assertTrue(all(t.mark in ("+", "X") for t in step.greatest_target_list))
        self.assertTrue(result.real_unchanged)
        self.assertEqual(result.real_before, result.real_after)
        self.assertEqual(tuple(rows), before_rows)
        self.assertEqual(live.to_fen(), before_fen)
        self.assertEqual(live.history, before_history)

    def test_move_can_both_enter_and_leave_required_squares(self):
        result = apply_legal_move(self.rows, "b1c3", self.doll)
        self.assertTrue(result.legal)
        self.assertEqual(result.leaves, ())
        self.assertEqual(result.enters, ("c3",))
        # In the develop blueprint, c3 and e4 are both required. Once the
        # knight is on c3, its move to e4 enters a wrong-piece square too.
        rows = apply_legal_move(result.board_rows, "a7a6", self.doll).board_rows
        both = apply_legal_move(rows, "c3e4", self.doll)
        self.assertTrue(both.legal)
        self.assertEqual(both.enters, ("e4",))
        self.assertEqual(both.leaves, ("c3",))
        self.assertEqual(both.view.marks[4][4], "X")

    def test_new_target_progress_can_fall_again(self):
        line = imagine_line(self.doll, self.rows, ("g1f3", "a7a6", "f3g1"))
        self.assertEqual([s.new_targets_filled for s in line.steps], [1, 1, 0])
        self.assertEqual([s.new_targets_total for s in line.steps], [1, 1, 1])
        self.assertEqual(line.steps[-1].strategy_forming_list.total_matched, 21)

    def test_en_passant_state_survives_rendered_rows(self):
        line = imagine_line(self.doll, self.rows, ("e2e4", "a7a6", "e4e5", "d7d5", "e5d6"))
        self.assertTrue(all(step.result.legal for step in line.steps))
        self.assertEqual(line.board_rows[3][3], ".")
        self.assertEqual(line.board_rows[2][3], "P")

    def test_castling_reports_both_pieces_and_keeps_real_position(self):
        live = Board()
        ok, reason = live.load_fen("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1")
        self.assertTrue(ok, reason)
        rows = render_board(live)
        before = live.to_fen()
        doll = get_strategy("starting-array")
        result = apply_legal_move(rows, "e1g1", doll)
        self.assertTrue(result.legal)
        self.assertEqual(set(result.enters), {"f1", "g1"})
        self.assertEqual(set(result.leaves), {"e1", "h1"})
        self.assertEqual(result.board_rows[7], "R....RK.")
        self.assertEqual(live.to_fen(), before)

    def test_plain_initial_rows_supported_but_edited_live_rows_rejected(self):
        plain = list(self.rows)
        self.assertTrue(apply_legal_move(plain, "e2e4", self.doll).legal)
        self.rows[0] = "........"
        with self.assertRaises(ValueError):
            apply_legal_move(self.rows, "e2e4", self.doll)

    def test_castling_rights_stay_lost_after_king_returns(self):
        live = Board()
        ok, reason = live.load_fen("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1")
        self.assertTrue(ok, reason)
        line = imagine_line(self.doll, render_board(live),
                            ("e1f1", "e8f8", "f1e1", "f8e8", "e1g1"))
        self.assertTrue(all(s.result.legal for s in line.steps[:-1]))
        self.assertFalse(line.steps[-1].result.legal)
        self.assertEqual(line.board_rows, render_board(live))
        self.assertNotEqual(line.board_rows.engine_copy().to_fen(), live.to_fen())

    def test_refused_imaginary_move_preserves_state_for_next_move(self):
        line = imagine_line(self.doll, self.rows, ("e2e5", "e2e4", "e7e5"))
        self.assertEqual([s.result.legal for s in line.steps], [False, True, True])
        self.assertEqual([s.strategy_forming_list.filled for s in line.steps], [22, 23, 24])
        self.assertTrue(line.real_unchanged)

    def test_fully_matched_set_does_not_claim_identity(self):
        doll = get_strategy("starting-array")
        view = build_view(doll, self.rows)
        self.assertEqual(view.filled, view.required)
        self.assertEqual(view.targets, ())
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            print_build_view(view)
        self.assertIn("IDENTITY CLAIMED: no", output.getvalue())

    def test_demo_prints_line_progress_and_no_identity_claim(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            show_build()
        text = output.getvalue()
        self.assertIn("Known blueprint", text)
        self.assertIn("Real board", text)
        self.assertIn("Blueprint fill", text)
        for number in range(1, 5):
            self.assertIn(f"New target positions filled on this line: {number} of 4", text)
            self.assertIn(f"Total blueprint positions matched: {22 + number}", text)
        self.assertEqual(text.count("LEAVES: none"), 4)
        self.assertIn("REAL BOARD UNCHANGED: yes", text)
        self.assertTrue(text.rstrip().endswith("IDENTITY CLAIMED: no"))


if __name__ == "__main__":
    unittest.main()
