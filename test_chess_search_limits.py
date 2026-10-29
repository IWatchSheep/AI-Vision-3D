"""Work limits and end-to-end checks for the maintained chess engine."""

import contextlib
import io
import unittest
from unittest.mock import patch

from chess_module.chess_engine.board import Board
from chess_module.chess_engine.cli_commands import process_command
from chess_module.chess_engine.cli_session import GameSession
from chess_module.chess_engine.movegen import generate_moves, game_over, make_move
from chess_module.chess_engine.search_budget import (
    SearchBudget, SearchLimitExceeded, bounded_search,
)
from chess_module.chess_engine.study.search import loop_report


class TestSearchLimits(unittest.TestCase):
    def test_nested_calls_share_budget_and_failure_resets_context(self):
        @bounded_search
        def walk(left):
            if left:
                walk(left - 1)

        with patch("chess_module.chess_engine.search_budget.SearchBudget",
                   side_effect=lambda: SearchBudget(max_nodes=3)):
            with self.assertRaises(SearchLimitExceeded):
                walk(3)
            walk(2)

    def test_elapsed_time_limit(self):
        with patch("chess_module.chess_engine.search_budget.monotonic", return_value=11):
            with self.assertRaises(SearchLimitExceeded):
                SearchBudget(seconds=10, started=0).consume()

    def test_loop_limit_preserves_entire_board_and_cli_recovers(self):
        session = GameSession()
        before = (session.board.to_fen(), list(session.board.history))
        with patch("chess_module.chess_engine.search_budget.SearchBudget",
                   side_effect=lambda: SearchBudget(max_nodes=3)):
            with self.assertRaises(SearchLimitExceeded):
                loop_report(session.board, 3)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                process_command(session, "loop 3")
            self.assertIn("Analysis work limit reached", output.getvalue())
        self.assertEqual((session.board.to_fen(), session.board.history), before)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(process_command(session, "quit"), "quit")

    def test_bad_command_types_and_whitespace(self):
        session = GameSession()
        before = session.board.to_fen()
        with contextlib.redirect_stdout(io.StringIO()):
            for command in (None, 42, [], "   "):
                self.assertIsNone(process_command(session, command))
            self.assertEqual(process_command(session, "  quit  "), "quit")
        self.assertEqual(session.board.to_fen(), before)

    def test_fools_mate_through_preview_and_finalize(self):
        session = GameSession()
        with contextlib.redirect_stdout(io.StringIO()):
            for start, end in (("f2", "f3"), ("e7", "e5"),
                               ("g2", "g4"), ("d8", "h4")):
                before = session.board.to_fen()
                process_command(session, start)
                process_command(session, end)
                self.assertEqual(session.board.to_fen(), before)
                process_command(session, "f")
                self.assertNotEqual(session.board.to_fen(), before)
        self.assertEqual(game_over(session.board), (True, False, None))
        self.assertEqual(generate_moves(session.board), [])

    def test_kiwipete_castling_perft(self):
        board = Board()
        ok, reason = board.load_fen(
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
        )
        self.assertTrue(ok, reason)
        first = generate_moves(board)
        self.assertEqual(len(first), 48)
        nodes = 0
        for move in first:
            child = board.clone()
            make_move(child, move)
            nodes += len(generate_moves(child))
        self.assertEqual(nodes, 2039)


if __name__ == "__main__":
    unittest.main()
