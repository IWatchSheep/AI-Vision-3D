"""Regression positions for rule adjudication and safe engine entry points."""

import contextlib
import io
from pathlib import Path
import runpy
import unittest

from chess_engine.board import Board
from chess_engine.constants import WHITE, BLACK, parse_square
from chess_engine.move import Move, parse_move_text
from chess_engine.movegen import generate_moves, legal_move, make_move, game_over
from chess_engine.tracker import Tracker
from chess_engine.cli_session import GameSession, Step
from chess_engine.cli_commands import process_command
from chess_engine.study.calc import report_mates
from chess_engine.study.replies import replies_report, reply_detail
from chess_engine.study.search import loop_report, first_move_forces, trace_report


def position(fen):
    board = Board()
    ok, reason = board.load_fen(fen)
    if not ok:
        raise AssertionError(reason)
    return board


class TestRulesRegressions(unittest.TestCase):
    def test_repetition_key_ignores_nonpawn_moves_to_ep_square(self):
        board = position("4k3/8/8/2Bp4/8/8/8/4K3 w - d6 0 2")
        key = board.position_key()
        board.ep_row = board.ep_col = -1
        self.assertEqual(key, board.position_key())

    def test_repetition_key_distinguishes_legal_ep_but_ignores_pinned_ep(self):
        for fen, different in [
            ("4k3/8/8/2Pp4/8/8/8/4K3 w - d6 0 2", True),
            ("8/8/8/8/k1pP3R/8/8/4K3 b - d3 0 2", False),
        ]:
            with self.subTest(fen=fen):
                board = position(fen)
                key = board.position_key()
                board.ep_row = board.ep_col = -1
                self.assertEqual(key != board.position_key(), different)

    def test_current_draw_claim_survives_irreversible_preview(self):
        board = Board()
        board.reset_board()
        board.halfmove_clock = 100
        self.assertEqual(board.claimable_draw(parse_move_text("e2e4")),
                         (True, "50-move rule"))
        board.halfmove_clock = 0
        board.history = [board.position_key()] * 3
        self.assertEqual(board.claimable_draw(parse_move_text("e2e4")),
                         (True, "threefold repetition"))

    def test_checkmate_has_priority_over_clock_draws_and_claims(self):
        for clock in (99, 149):
            board = position(f"7k/8/5KQ1/8/8/8/8/8 w - - {clock} 1")
            mate = parse_move_text("g6g7")
            self.assertEqual(board.claimable_draw(mate)[0], clock >= 100)
            make_move(board, mate, record_history=True)
            self.assertEqual(game_over(board), (True, False, None))
            self.assertFalse(board.automatic_draw()[0])
            self.assertFalse(board.claimable_draw()[0])
            self.assertTrue(first_move_forces(board, 1))

    def test_make_move_rejects_illegal_moves_atomically(self):
        board = Board()
        board.reset_board()
        for move in (parse_move_text("e2e5"), parse_move_text("a1a4"),
                     parse_move_text("e1g1"), Move(6, 4, 4, 4, []), None):
            with self.subTest(move=move):
                before = (board.to_fen(), list(board.history))
                make_move(board, move, record_history=True)
                self.assertEqual((board.to_fen(), board.history), before)
        board = position("4r1k1/8/8/8/8/8/4N3/4K3 w - - 0 1")
        before = board.to_fen()
        make_move(board, parse_move_text("e2f4"))
        self.assertEqual(board.to_fen(), before)

    def test_bad_promotions_do_not_change_board(self):
        board = position("8/P7/8/8/8/8/8/4K2k w - - 0 1")
        before = board.to_fen()
        for move in (parse_move_text("a7a8"), Move(1, 0, 0, 0, "K")):
            make_move(board, move)
            self.assertEqual(board.to_fen(), before)

    def test_rejects_invalid_fen_without_mutation(self):
        board = Board()
        board.reset_board()
        before = (board.to_fen(), list(board.history))
        for fen in (
            "4k3/8/8/8/8/8/8/4K111 w - - 0 1",
            "4k3/8/8/3pP3/8/8/8/4K3 w - d6 1 2",
            "4k3/8/8/8/8/8/PPPPPPPP/2B1K1B1 w - - 0 1",
        ):
            with self.subTest(fen=fen):
                self.assertFalse(board.load_fen(fen)[0])
                self.assertEqual((board.to_fen(), board.history), before)

    def test_loop_stops_at_automatic_draw_and_tracks_repetition(self):
        board = position("7k/8/5KQ1/8/8/8/8/8 w - - 150 1")
        self.assertIn("DRAW 75-move rule", loop_report(board, 3))
        self.assertNotIn("MATE ", loop_report(board, 3))
        self.assertEqual(report_mates(board, WHITE), [])
        board = Board()
        board.reset_board()
        move = parse_move_text("g1f3")
        after = board.clone()
        make_move(after, move)
        board.history = [after.position_key()] * 4 + [board.position_key()]
        report = loop_report(board, 2)
        self.assertIn("DRAW 1 fivefold repetition", report)
        self.assertIn("PLY 2 POSITIONS 380", report)

    def test_forced_mate_search_respects_defenders_draw_claim(self):
        board = position("7k/8/5KQ1/8/8/8/8/8 b - - 100 1")
        self.assertFalse(first_move_forces(board, 3))

    def test_replies_stop_at_draw_and_trace_cannot_play_past_it(self):
        board = position("7k/8/5KQ1/8/8/8/8/8 w - - 149 1")
        move = parse_move_text("g6g5")
        tracker = Tracker(board)
        report = replies_report(board, tracker, move)
        self.assertIn("NO REPLIES 75-move rule", report)
        self.assertIn("SUMMARY REPLIES 0", report)
        self.assertIsNone(reply_detail(board, tracker, move, parse_move_text("h8h7")))
        ok, _, ply = trace_report(board, tracker, "g6g5 h8h7")
        self.assertFalse(ok)
        self.assertEqual(ply, 2)

    def test_history_recording_is_optional_and_isolated(self):
        board = Board()
        board.reset_board()
        after = board.clone()
        make_move(after, parse_move_text("g1f3"), record_history=True)
        self.assertEqual(len(board.history), 1)
        self.assertEqual(len(after.history), 2)

    def test_input_parsers_reject_wrong_types(self):
        for value in (None, 123, [], b"e2"):
            self.assertIsNone(parse_square(value))
            self.assertIsNone(parse_move_text(value))

    def test_loop_rejects_unbounded_depth(self):
        board = Board()
        board.reset_board()
        with self.assertRaises(ValueError):
            loop_report(board, 1000000)

    def test_real_routes_stop_at_automatic_draw(self):
        from chess_engine.study.goals import parse_goal, routes_real_report
        board = position("7k/8/5KQ1/8/8/8/8/8 w - - 150 1")
        report = routes_real_report(board, parse_goal("g7 1"), 3)
        self.assertIn("DRAW 75-move rule", report)
        self.assertNotIn("FIRST ", report)
        with self.assertRaises(ValueError):
            routes_real_report(board, parse_goal("g7 1"), 1000000)

    def test_capture_memory_includes_captured_pieces_lost_destinations(self):
        from chess_engine.move_memory import build_entry
        board = position("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1")
        entry = build_entry(board, parse_move_text("e4d5"))
        self.assertIn("d4", entry.lost)

    def test_illegal_reports_leave_tracker_unchanged(self):
        from chess_engine.study.calc import calc_report
        from chess_engine.move_memory import build_entry
        board = Board()
        board.reset_board()
        tracker = Tracker(board)
        before_grid = [list(row) for row in tracker.grid]
        before_fen = board.to_fen()
        move = parse_move_text("e2e5")
        for call in (lambda: tracker.commit(board, move),
                     lambda: calc_report(board, tracker, move),
                     lambda: replies_report(board, tracker, move),
                     lambda: build_entry(board, move)):
            with self.assertRaises(ValueError):
                call()
            self.assertEqual(tracker.grid, before_grid)
            self.assertEqual(board.to_fen(), before_fen)

    def test_resignation_draws_when_opponent_cannot_mate(self):
        for black_piece in ("", "b", "n"):
            # A bare king, bishop, or knight cannot mate a king and queen.
            last_rank = "7k" if not black_piece else f"5{black_piece}1k"
            session = GameSession()
            session.board = position(f"{last_rank}/8/8/8/8/8/8/3QK3 w - - 0 1")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(process_command(session, "resign"), "quit")
            self.assertIn("Draw:", output.getvalue())

    def test_opponents_material_can_enable_lone_knight_mate(self):
        board = position("5n1k/8/8/8/8/8/8/3RK3 w - - 0 1")
        self.assertFalse(board.insufficient_mating_material(BLACK))

    def test_all_strategy_reference_fens_are_valid_positions(self):
        data_path = Path(__file__).resolve().parents[1] / "calculator" / "strategies_data.py"
        records = runpy.run_path(str(data_path))["RAW_DOLLS"]
        for record in records:
            with self.subTest(strategy=record["id"]):
                board = position(record["fen"])
                if record["id"] == "pin-against-the-king":
                    board.turn = BLACK
                    self.assertFalse(legal_move(board, parse_move_text("c6a5")))

    def test_cli_claim_works_with_preview_and_preserves_board(self):
        session = GameSession()
        session.board.halfmove_clock = 100
        session.select_piece(6, 4)
        session.preview_move = parse_move_text("e2e4")
        session.step = Step.CONFIRM_PREVIEW
        before = session.board.to_fen()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(process_command(session, "claim"), "quit")
        self.assertEqual(session.board.to_fen(), before)


class TestMoveGenerationCounts(unittest.TestCase):
    @staticmethod
    def perft(board, depth):
        if depth == 0:
            return 1
        moves = generate_moves(board)
        if depth == 1:
            return len(moves)
        total = 0
        for move in moves:
            child = board.clone()
            make_move(child, move)
            total += TestMoveGenerationCounts.perft(child, depth - 1)
        return total

    def test_starting_position(self):
        board = Board()
        board.reset_board()
        self.assertEqual([self.perft(board, d) for d in (1, 2, 3)], [20, 400, 8902])

    def test_castling_pins_and_captures(self):
        board = position("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
        self.assertEqual(self.perft(board, 1), 48)
        self.assertEqual(self.perft(board, 2), 2039)

    def test_rook_endgame_with_en_passant(self):
        board = position("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1")
        self.assertEqual([self.perft(board, d) for d in (1, 2, 3)], [14, 191, 2812])


if __name__ == "__main__":
    unittest.main()
