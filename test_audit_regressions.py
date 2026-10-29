"""Regression checks for package entry points and defensive public APIs."""

import contextlib
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from calculator.pattern import PatternWindow, CompareResult
from calculator.strategies import STRATEGIES
from calculator.window import MemoryWindow
from chess_module.chess_engine.board import Board
from chess_module.chess_engine.cli_session import (
    GameSession, Step, parse_bounded_int, sanitize_display_text,
)
from chess_module.chess_engine.constants import WHITE
from chess_module.chess_engine.move import Move, parse_move_text, promotion_rank
from chess_module.chess_engine.study.common import (
    Goal, GoalCondition, pass_play, pieces_on_square, move_distance, piece_value,
)
from chess_module.chess_engine.study.exchange import compare_report, exchange_value, first_capture_class
from chess_module.chess_engine.study.exchange_core import captured_type
from chess_module.chess_engine.study.goals import (
    distance_after, goal_marks_after, piece_distance, routes_report_with,
    side_distance, support_report, parse_goal, routes_real_report,
)
from chess_module.chess_engine.study.search import first_move_forces, mate_forced
from chess_module.chess_engine.tracker import Tracker
from chess_module.chess_engine.study.calc import calc_report
from chess_module.chess_engine.move_gen import generate_sliding_moves
from chess_module.chess_engine.ui import is_en_passant_capture, show_step2_after


class TestAuditRegressions(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board.reset_board()

    def test_all_launch_modes_use_the_maintained_engine(self):
        root = Path(__file__).resolve().parent
        for args in (("main.py",), ("-m", "chess_module.main"), ("chess_module/main.py",)):
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, *args], input="quit\n", text=True,
                    capture_output=True, cwd=root, timeout=15,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Simple 2-Player Chess", result.stdout)

    def test_package_import_does_not_load_a_second_engine(self):
        import chess_module.main as entry
        self.assertIs(entry.GameSession, GameSession)

    def test_failed_history_replacement_preserves_existing_state(self):
        window = MemoryWindow(limit=2, past=["original"], current="preview")
        history = window.past
        window.limit = 0
        with self.assertRaises(ValueError):
            window.replace_past(["replacement"])
        self.assertIs(window.past, history)
        self.assertEqual(window.past, ["original"])
        self.assertEqual(window.current, "preview")

    def test_illegal_reports_and_preview_are_rejected_without_output_or_mutation(self):
        session = GameSession()
        before = (session.board.to_fen(), list(session.board.history), session.step)
        move = parse_move_text("e2e5")
        calls = (
            lambda: show_step2_after(session.board, move),
            lambda: session.set_preview(move),
            lambda: goal_marks_after(session.board, Goal(), move),
            lambda: distance_after(session.board, move),
            lambda: support_report(session.board, move),
        )
        output = io.StringIO()
        for call in calls:
            with self.subTest(call=call), contextlib.redirect_stdout(output):
                with self.assertRaises(ValueError):
                    call()
            self.assertEqual((session.board.to_fen(), session.board.history, session.step), before)
            self.assertIsNone(session.memory.current)
        self.assertEqual(output.getvalue(), "")

    def test_en_passant_display_checks_geometry_and_victim(self):
        self.board.ep_row, self.board.ep_col = 4, 4
        # e2-e4 is a straight push, even with a corrupt EP target at e4.
        self.assertFalse(is_en_passant_capture(self.board, Move(6, 4, 4, 4), 6, 4))
        self.assertTrue(self.board.load_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2")[0])
        self.assertTrue(is_en_passant_capture(self.board, parse_move_text("e5d6"), 3, 3))

    def test_illegal_pass_move_preserves_turn_and_special_rights(self):
        from chess_module.chess_engine.constants import BLACK
        before = (self.board.to_fen(), list(self.board.history))
        with self.assertRaises(ValueError):
            pass_play(self.board, parse_move_text("e7e4"), BLACK)
        self.assertEqual((self.board.to_fen(), self.board.history), before)

    def test_one_ply_goal_search_does_not_count_opponent_reply(self):
        # Moving the c2 rook can uncover Bd1's protection of a4, but that
        # would be a second ply and is outside a depth-one report.
        ok, reason = self.board.load_fen("7k/8/8/8/P7/8/2r5/3B3K w - - 0 1")
        self.assertTrue(ok, reason)
        report = routes_real_report(self.board, parse_goal("a4 1"), 1)
        protected = report.split("GOAL a4 PROTECTED\n", 1)[1]
        self.assertIn("FIRST h1g1 CONDITION ELSE", protected)

    def test_two_ply_goal_search_counts_protection_uncovered_by_reply(self):
        ok, reason = self.board.load_fen("7k/8/8/8/P7/8/2r5/3B3K w - - 0 1")
        self.assertTrue(ok, reason)
        before = (self.board.to_fen(), list(self.board.history))
        report = routes_real_report(self.board, parse_goal("a4 1"), 2)
        protected = report.split("GOAL a4 PROTECTED\n", 1)[1]
        self.assertIn("FIRST h1g1 CONDITION IF POSSIBLE", protected)
        self.assertEqual((self.board.to_fen(), self.board.history), before)

    def test_calc_counts_captured_piece_destinations_as_lost(self):
        for fen, text, name, destination in (
            ("r6k/8/8/8/8/8/8/R6K w - - 0 1", "a1a8", "R a8", "b8"),
            ("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2", "e5d6", "P d5", "d4"),
        ):
            with self.subTest(move=text):
                self.assertTrue(self.board.load_fen(fen)[0])
                tracker = Tracker(self.board)
                report = calc_report(self.board, tracker, parse_move_text(text))
                lost = next(line for line in report.splitlines()
                            if line.startswith(f"LOST Black {name} "))
                self.assertIn(destination, lost.split())
                count = next(line for line in report.splitlines()
                             if line.startswith("COUNT Black ")).split()
                self.assertGreater(int(count[count.index("U2") + 1]), 0)

    def test_two_ply_goal_can_be_forced_by_opponents_only_reply(self):
        # Rh1+ leaves Black only ...Rc1, uncovering Bd1's defense of a4.
        ok, reason = self.board.load_fen("8/8/8/8/P7/K7/2r4R/1k1B4 w - - 0 1")
        self.assertTrue(ok, reason)
        report = routes_real_report(self.board, parse_goal("a4 1"), 2)
        protected = report.split("GOAL a4 PROTECTED\n", 1)[1]
        self.assertIn("FIRST h2h1 CONDITION IF FORCED", protected)

    def test_sliding_generator_rejects_invalid_vectors(self):
        for vector in ((0, 0), (0, 0.5), (True, 0), (2, 1)):
            with self.subTest(vector=vector), self.assertRaises(ValueError):
                generate_sliding_moves(self.board, [], 4, 4, [vector])

    def test_public_search_limits_are_checked_before_search(self):
        goal = Goal(active=True, count=1, squares=[36], limit=1000000)
        calls = (
            lambda: routes_report_with(self.board, goal),
            lambda: piece_distance(self.board, 6, 4, WHITE, 36, 1000000),
            lambda: side_distance(self.board, WHITE, 36, GoalCondition.COND_REACH, 1000000),
            lambda: mate_forced(self.board, 1000000),
            lambda: first_move_forces(self.board, 1000000),
            lambda: exchange_value(self.board, WHITE, 36, 0, 1000000),
        )
        for call in calls:
            with self.subTest(call=call), self.assertRaises(ValueError):
                call()

    def test_capture_classifier_rejects_non_capture_and_bad_limit(self):
        move = parse_move_text("e2e4")
        for limit in (1, 0, 1000000, True):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                first_capture_class(self.board, move, limit)

    def test_compare_validates_candidates_before_starting_expensive_search(self):
        move = parse_move_text("e2e4")
        with patch("chess_module.chess_engine.study.exchange.loop_report") as search:
            for moves in ([move], [move, move], [move, parse_move_text("e2e5")]):
                with self.subTest(moves=moves), self.assertRaises(ValueError):
                    compare_report(self.board, Tracker(self.board), None, 1, moves)
            search.assert_not_called()

    def test_move_generation_and_consider_move_negative_coordinates_underflow(self):
        from chess_module.chess_engine.move_rules import consider_move
        from chess_module.chess_engine.move_gen import (
            generate_piece_moves, generate_pawn_moves, generate_knight_moves,
            generate_king_moves, generate_sliding_moves
        )
        moves = []
        # consider_move with negative starting row/col or target row/col
        consider_move(self.board, moves, -1, 0, 0, 0)
        consider_move(self.board, moves, 0, -1, 0, 0)
        consider_move(self.board, moves, 0, 0, -1, 0)
        consider_move(self.board, moves, 0, 0, 0, -1)
        consider_move(self.board, moves, 8, 0, 0, 0)
        self.assertEqual(moves, [])

        # piece move generators with negative or out-of-bounds coords
        generate_piece_moves(self.board, moves, -1, 0)
        generate_pawn_moves(self.board, moves, -1, 0)
        generate_knight_moves(self.board, moves, -1, 0)
        generate_king_moves(self.board, moves, -1, 0)
        generate_sliding_moves(self.board, moves, -1, 0, [(-1, 0)])
        self.assertEqual(moves, [])

    def test_next_chunk_negative_index_underflow(self):
        from chess_module.chess_engine.ui_board import next_chunk
        chunk, next_at = next_chunk("test chunk", -5, 10)
        self.assertEqual(chunk, "test chunk")
        self.assertEqual(next_at, 10)

    def test_exchange_report_validates_square_bounds(self):
        from chess_module.chess_engine.study.exchange import exchange_report
        for bad_sq in (-1, 64, 100, True, "e4"):
            with self.subTest(bad_sq=bad_sq), self.assertRaises(ValueError):
                exchange_report(self.board, bad_sq, 2)

    def test_study_distance_handles_out_of_bounds_squares(self):
        from chess_module.chess_engine.study.goal_basics import side_within
        for bad_sq in (-1, 64, 100, True):
            self.assertEqual(piece_distance(self.board, 6, 4, WHITE, bad_sq, 2), -1)
            self.assertFalse(side_within(self.board, WHITE, bad_sq, GoalCondition.COND_REACH, 2))
            self.assertEqual(side_distance(self.board, WHITE, bad_sq, GoalCondition.COND_REACH, 2), -1)

    def test_loop_report_validates_zero_k_bounds(self):
        from chess_module.chess_engine.study.search import loop_report
        for bad_zero_k in (-1, -10, True, "5"):
            with self.subTest(bad_zero_k=bad_zero_k), self.assertRaises(ValueError):
                loop_report(self.board, 2, bad_zero_k)

    def test_cli_analysis_handles_stale_or_illegal_preview(self):
        from chess_module.chess_engine.cli_analysis_cmds import handle_calc_report, handle_replies
        from chess_module.chess_engine.cli_goal_cmds import handle_support
        session = GameSession()
        session.step = Step.CONFIRM_PREVIEW
        session.preview_move = parse_move_text("e2e5")  # Illegal move
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(handle_calc_report(session, "R"))
            self.assertFalse(session.preview_shown)

            session.step = Step.CONFIRM_PREVIEW
            session.preview_move = parse_move_text("e2e5")
            self.assertTrue(handle_replies(session, "replies"))
            self.assertFalse(session.preview_shown)

            session.step = Step.CONFIRM_PREVIEW
            session.preview_move = parse_move_text("e2e5")
            self.assertTrue(handle_support(session, "support"))
            self.assertFalse(session.preview_shown)

    def test_cli_commands_at_game_start_preserve_pick_piece_step(self):
        from chess_module.chess_engine.cli_analysis_cmds import handle_calc_report, handle_replies
        from chess_module.chess_engine.cli_goal_cmds import handle_support
        session = GameSession()
        self.assertEqual(session.step, Step.PICK_PIECE)
        self.assertFalse(session.has_selection())

        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(handle_calc_report(session, "r"))
            self.assertEqual(session.step, Step.PICK_PIECE)

            self.assertTrue(handle_replies(session, "replies"))
            self.assertEqual(session.step, Step.PICK_PIECE)

            self.assertTrue(handle_support(session, "support"))
            self.assertEqual(session.step, Step.PICK_PIECE)

            # Invalidate directly when no selection is held
            session.invalidate_preview()
            self.assertEqual(session.step, Step.PICK_PIECE)

    def test_study_common_defensive_checks(self):
        for bad_sq in (True, False, -1, 64, 100, "e4"):
            self.assertEqual(pieces_on_square(self.board, bad_sq, WHITE), 0)

        for bad_move in (None, "e2e4", Move(-1, 0, 0, 0), Move(0, 0, 8, 8)):
            self.assertEqual(move_distance(bad_move), 0)

        for bad_val in (None, 123, True, "invalid"):
            self.assertEqual(piece_value(bad_val), 0)

    def test_exchange_core_captured_type_defensive_checks(self):
        for bad_move in (None, "e2e4", Move(-1, 0, 0, 0), Move(0, 0, 8, 8)):
            self.assertEqual(captured_type(self.board, bad_move), "")

    def test_parse_bounded_int_and_parse_goal_reject_non_strings(self):
        self.assertIsNone(parse_bounded_int(123, 1, 10))
        self.assertIsNone(parse_bounded_int(None, 1, 10))
        self.assertEqual(sanitize_display_text(None), "")
        self.assertEqual(sanitize_display_text(123), "")
        self.assertIsNone(parse_goal(None))
        self.assertIsNone(parse_goal(123))

    def test_move_uci_and_promotion_rank_type_safety(self):
        self.assertEqual(promotion_rank(None), 0)
        self.assertEqual(promotion_rank(123), 0)
        self.assertEqual(promotion_rank(True), 0)

        # Move with invalid coordinates returns "????"
        self.assertEqual(Move(-1, -1, -1, -1).uci, "????")

        # Move with non-string promotion does not raise AttributeError
        m = Move(6, 4, 4, 4, promotion=None)
        self.assertEqual(m.uci, "e2e4")
        m2 = Move(6, 4, 4, 4, promotion=123)
        self.assertEqual(m2.uci, "e2e4")

    def test_pattern_window_type_validation_and_clear_current(self):
        window = PatternWindow()
        self.assertIsNone(window.current)
        self.assertEqual(window.past, [])

        window.clear_current()
        self.assertIsNone(window.current)

        comp = CompareResult(
            strategy=STRATEGIES[0],
            fill=tuple(["." * 8] * 8),
            hash_count=0,
            plus_count=0,
            x_count=0,
        )
        window.set_current(comp)
        self.assertIs(window.current, comp)

        window.clear_current()
        self.assertIsNone(window.current)

        window.current = comp
        self.assertIs(window.current, comp)
        window.current = None
        self.assertIsNone(window.current)

        with self.assertRaises(ValueError):
            window.current = "not a CompareResult"
        with self.assertRaises(ValueError):
            window.set_current("not a CompareResult")
        with self.assertRaises(ValueError):
            window.past = "not a list"
        with self.assertRaises(ValueError):
            window.past = ["not a CompareResult"]

    def test_distance_selection_empty_and_out_of_bounds(self):
        from chess_module.chess_engine.study.distance_order import distance_selection, distance_lines
        # Empty square e4
        self.assertEqual(distance_selection(self.board, 4, 4), "DISTANCE ORDER END\n")
        self.assertEqual(distance_lines(self.board, 4, 4, "MOVE"), [])

        # Out of bounds
        for r, c in ((-1, 0), (0, -1), (8, 0), (0, 8), (-1, -1)):
            self.assertEqual(distance_selection(self.board, r, c), "DISTANCE ORDER END\n")
            self.assertEqual(distance_lines(self.board, r, c, "MOVE"), [])

    def test_claim_with_none_or_malformed_preview(self):
        from chess_module.chess_engine.cli_move_cmds import handle_game_control
        session = GameSession()
        session.preview_move = None
        session.step = Step.CONFIRM_PREVIEW
        with contextlib.redirect_stdout(io.StringIO()):
            res = handle_game_control(session, "claim")
            self.assertEqual(res, "handled")

    def test_python_source_files_no_bom(self):
        root = Path(__file__).resolve().parent
        for path in root.glob("**/*.py"):
            if ".venv" in path.parts or "chess_source" in path.parts:
                continue
            with open(path, "rb") as f:
                header = f.read(3)
                self.assertNotEqual(header, b"\xef\xbb\xbf", f"File contains UTF-8 BOM: {path}")


if __name__ == "__main__":
    unittest.main()
