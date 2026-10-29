"""Public report budgets, bounded imagination, and full terminal game flows."""

import contextlib
import io
from itertools import repeat
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from calculator.build_shape import BuildView, MoveResult, imagine_line, starting_board
from calculator.play_build import PlaySession, auto_moves, handle_command, spoken_move, _mark_at
from calculator.strategies import get_strategy
from chess_module.chess_engine.board import Board
from chess_module.chess_engine.constants import BLACK, WHITE
from chess_module.chess_engine.move import Move, parse_move_text
from chess_module.chess_engine.movegen import generate_moves, legal_destination_map
from chess_module.chess_engine.search_budget import SearchBudget, SearchLimitExceeded
from chess_module.chess_engine.study.calc import calc_report
from chess_module.chess_engine.study.exchange_compare import compare_report
from chess_module.chess_engine.study.exchange_core import exchange_report, first_capture_class, order_report
from chess_module.chess_engine.study.common import MaterialResult
from chess_module.chess_engine.study.goal_basics import parse_goal
from chess_module.chess_engine.study.goal_marks import goal_marks_selection
from chess_module.chess_engine.study.replies import replies_report
from chess_module.chess_engine.study.search import trace_report, mate_forced
from chess_module.chess_engine.tracker import Tracker
from chess_module.chess_engine.cli_session import (
    GameSession, Step, parse_bounded_int, sanitize_display_text,
)


class TestReviewRegressions(unittest.TestCase):
    def test_capture_promotions_count_material_created_for_both_sides(self):
        for fen, move, sq, totals in (
            ("7r/6Pk/8/8/8/8/8/K7 w - - 0 1", "g7h8q", 7,
             "MATERIAL White 13 Black 9 PROMOTION-GAIN White 8 Black 0"),
            ("k7/8/8/8/8/8/6pK/7R b - - 0 1", "g2h1q", 63,
             "MATERIAL White 9 Black 13 PROMOTION-GAIN White 0 Black 8"),
        ):
            with self.subTest(move=move):
                board = Board()
                self.assertTrue(board.load_fen(fen)[0])
                before = (board.to_fen(), list(board.history))
                self.assertEqual(first_capture_class(board, parse_move_text(move), 2),
                                 (MaterialResult.MATERIAL_FORCED, False))
                report = exchange_report(board, sq, 2)
                self.assertIn(totals, report)
                self.assertIn(f"FIRST {move} TAKES R VALUE 5 MATERIAL FORCED NONNEGATIVE", report)
                self.assertEqual((board.to_fen(), board.history), before)

    def test_bad_blueprint_commands_preserve_state_and_allow_quit(self):
        session = PlaySession()
        before = session.state_key()
        for command in ("doll ²", "doll " + "9" * 5000, None, 42,
                        "imagine e2e4 e7e5 g1f3 b8c6 f1c4"):
            with self.subTest(command=str(command)[:40]):
                answer = handle_command(session, command)
                self.assertIsInstance(answer, str)
                self.assertEqual(session.state_key(), before)
        self.assertIsNone(handle_command(session, "quit"))

    def test_imagination_rejects_infinite_input_after_five_items(self):
        session = PlaySession()
        before = session.state_key()
        consumed = []

        def endless():
            while True:
                consumed.append("e2e4")
                yield "e2e4"

        with self.assertRaises(ValueError):
            session.imagine(endless())
        self.assertEqual(len(consumed), 5)
        self.assertEqual(session.state_key(), before)
        with self.assertRaises(ValueError):
            imagine_line(session.doll, session.rows, repeat("e2e4"))

    def test_imagination_validates_move_sequences_and_ply_limits(self):
        session = PlaySession()
        for moves in ("e2e4", (None,), (42,)):
            with self.subTest(moves=moves), self.assertRaises(ValueError):
                session.imagine(moves)
        for plies in (-1, 5, 1.5, True, "4"):
            with self.subTest(plies=plies), self.assertRaises(ValueError):
                auto_moves(session.doll, session.rows, plies)
        self.assertEqual(auto_moves(session.doll, session.rows, 0), ())

    def test_long_rule_replay_remains_supported(self):
        line = imagine_line(get_strategy("develop-to-the-center"), starting_board(),
                            ("e2e4", "a7a6", "e4e5", "d7d5", "e5d6"))
        self.assertEqual(len(line.steps), 5)
        self.assertTrue(all(step.result.legal for step in line.steps))
        self.assertTrue(line.real_unchanged)

    def test_blueprint_game_stops_at_automatic_draw(self):
        board = Board()
        board.reset_board()
        board.halfmove_clock = 150
        session = PlaySession(board=board)
        before = session.state_key()
        self.assertFalse(session.accept("g1f3").legal)
        self.assertEqual(session.imagine().steps, ())
        self.assertEqual(session.state_key(), before)

    def test_direct_reports_share_one_budget_across_all_subreports(self):
        board = Board()
        board.reset_board()
        tracker = Tracker(board)
        first, second = map(parse_move_text, ("e2e4", "d2d4"))
        goal = parse_goal("d4 1")
        calls = (
            lambda: calc_report(board, tracker, first),
            lambda: replies_report(board, tracker, first),
            lambda: compare_report(board, tracker, None, 1, [first, second]),
            lambda: trace_report(board, tracker, "e2e4 e7e5"),
            lambda: goal_marks_selection(board, goal, 6, 3),
            lambda: order_report(board, 1),
        )
        before = (board.to_fen(), list(board.history), tracker.clone().__dict__)
        for index, call in enumerate(calls):
            with self.subTest(report=index):
                with patch("chess_module.chess_engine.search_budget.SearchBudget",
                           side_effect=lambda: SearchBudget(seconds=60)) as factory:
                    call()
                self.assertEqual(factory.call_count, 1)
                self.assertEqual((board.to_fen(), board.history, tracker.__dict__), before)

    def test_direct_report_timeout_preserves_board_and_tracker(self):
        board = Board()
        board.reset_board()
        tracker = Tracker(board)
        before = (board.to_fen(), list(board.history), tracker.clone().__dict__)
        with patch("chess_module.chess_engine.search_budget.SearchBudget",
                   return_value=SearchBudget(seconds=1, started=0)):
            with patch("chess_module.chess_engine.search_budget.monotonic",
                       side_effect=[0, 2]):
                with self.assertRaises(SearchLimitExceeded):
                    calc_report(board, tracker, parse_move_text("e2e4"))
        self.assertEqual((board.to_fen(), board.history, tracker.__dict__), before)

    def test_trace_rejects_bad_types_and_oversized_input_before_parsing(self):
        board = Board()
        board.reset_board()
        for text in (None, 42, "e2e4 " * 10000):
            self.assertEqual(trace_report(board, Tracker(board), text), (False, "", 1))

    def test_piece_destination_maps_match_full_generation_for_both_sides(self):
        for fen in (
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "4k3/P7/8/2Pp4/8/8/8/4K3 w - d6 0 2",
        ):
            board = Board()
            self.assertTrue(board.load_fen(fen)[0])
            before = (board.to_fen(), list(board.history))
            for side in (WHITE, BLACK):
                view = board.clone()
                view.turn = side
                moves = generate_moves(view)
                for row in range(8):
                    for col in range(8):
                        if board.grid[row][col].color != side:
                            continue
                        expected = {(m.er, m.ec) for m in moves if (m.sr, m.sc) == (row, col)}
                        actual = legal_destination_map(board, row, col, side)
                        self.assertEqual({(r, c) for r in range(8) for c in range(8)
                                          if actual[r][c]}, expected)
            self.assertEqual((board.to_fen(), board.history), before)

    def test_all_launch_modes_play_a_full_game_to_checkmate(self):
        root = Path(__file__).resolve().parent
        commands = (['main.py'], ['-m', 'chess_module.main'], ['chess_module/main.py'])
        moves = "f2\nf3\nf\ne7\ne5\nf\ng2\ng4\nf\nd8\nh4\nf\n"
        for command in commands:
            with self.subTest(command=command):
                result = subprocess.run([sys.executable, *command], cwd=root, input=moves,
                                        text=True, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertIn("Checkmate! Black wins!", result.stdout)
                self.assertEqual(result.stdout.count("FINALIZED:"), 4)

    def test_blueprint_cli_recovers_from_invalid_strategy_and_interrupt(self):
        from show_play import main
        with patch("builtins.input", side_effect=["doll ²", "e2e4", KeyboardInterrupt]):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                main()
        self.assertIn("No strategy matching", output.getvalue())
        self.assertIn("Accepted real move", output.getvalue())

    def test_spoken_move_and_mark_at_robustness(self):
        dummy_view = BuildView(tuple(["." * 8] * 8), 0, 0, 0, (), ())
        refused = MoveResult([], False, (), (), "Move refused: 'invalid'", dummy_view)
        self.assertIn("refused or invalid", spoken_move(refused, "invalid"))

        empty_msg = MoveResult([], True, (), (), "", dummy_view)
        self.assertIn("refused or invalid", spoken_move(empty_msg, "e2e4"))

        short_msg = MoveResult([], True, (), (), "P e2", dummy_view)
        self.assertEqual(spoken_move(short_msg, "e2e4"), "P e2")

        for bad in ("z9", "e9", "a0", "e22", "", 123, None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                _mark_at(dummy_view, bad)

        self.assertEqual(_mark_at(dummy_view, "e4"), ".")

    def test_cli_session_defensive_bounds_and_state_clearing(self):
        self.assertIsNone(parse_bounded_int("5", lo=True, hi=10))
        self.assertIsNone(parse_bounded_int("5", lo=1, hi=False))
        self.assertIsNone(parse_bounded_int("5", lo=10, hi=1))
        self.assertEqual(parse_bounded_int("5", lo=1, hi=10), 5)

        self.assertEqual(sanitize_display_text("hello", max_len=-5), "...")
        self.assertEqual(sanitize_display_text("hello", max_len=True), "...")
        self.assertEqual(sanitize_display_text(123), "")

        session = GameSession()
        with self.assertRaises(ValueError):
            session.select_piece(-1, 0)
        with self.assertRaises(ValueError):
            session.select_piece(8, 0)

        session.select_piece(6, 4)
        session.preview_move = Move(6, 4, 4, 4)
        session.pending_promotion = Move(1, 0, 0, 0, "q")
        session.clear_selection()
        self.assertEqual(session.selected_row, -1)
        self.assertEqual(session.selected_col, -1)
        self.assertEqual(session.preview_move.sr, -1)
        self.assertEqual(session.pending_promotion.sr, -1)
        self.assertEqual(session.step, Step.PICK_PIECE)

        session.select_piece(6, 4)
        session.preview_move = Move(6, 4, 4, 4)
        session.pending_promotion = Move(1, 0, 0, 0, "q")
        session.clear_preview_keep_piece()
        self.assertEqual(session.preview_move.sr, -1)
        self.assertEqual(session.pending_promotion.sr, -1)
        self.assertEqual(session.step, Step.PICK_DESTINATION)

        session.preview_move = Move(6, 4, 4, 4)
        session.pending_promotion = Move(1, 0, 0, 0, "q")
        session.invalidate_preview()
        self.assertEqual(session.preview_move.sr, -1)
        self.assertEqual(session.pending_promotion.sr, -1)

    def test_mate_forced_obeys_search_budget(self):
        board = Board()
        board.reset_board()
        with patch("chess_module.chess_engine.search_budget.SearchBudget",
                   return_value=SearchBudget(seconds=1, started=0)):
            with patch("chess_module.chess_engine.search_budget.monotonic",
                       side_effect=[0, 2]):
                with self.assertRaises(SearchLimitExceeded):
                    mate_forced(board, 3)


if __name__ == "__main__":
    unittest.main()
