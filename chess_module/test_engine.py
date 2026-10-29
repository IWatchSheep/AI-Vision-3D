"""Comprehensive unit tests for chess_engine."""

import unittest
from chess_engine.constants import (
    WHITE, BLACK, EMPTY,
    square_index, parse_square, square_text
)
from chess_engine.piece import Piece
from chess_engine.move import Move, parse_move_text
from chess_engine.board import Board
from chess_engine.movegen import (
    generate_moves, sorted_moves, legal_move, make_move,
    is_in_check, game_over
)
from chess_engine.tracker import Tracker
from chess_engine.analysis import (
    Goal, parse_goal, calc_report, replies_report, loop_report,
    exchange_report, order_report, routes_report_with
)


class TestChessEngine(unittest.TestCase):

    def setUp(self):
        self.board = Board()
        self.board.reset_board()

    def test_initial_position(self):
        self.assertEqual(len(sorted_moves(self.board)), 20)
        self.assertEqual(self.board.to_fen(), "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        self.assertFalse(is_in_check(self.board, WHITE))
        self.assertFalse(is_in_check(self.board, BLACK))

    def test_fools_mate(self):
        # 1. f3 e5 2. g4 Qh4#
        m1 = parse_move_text("f2f3")
        m2 = parse_move_text("e7e5")
        m3 = parse_move_text("g2g4")
        m4 = parse_move_text("d8h4")

        self.assertTrue(legal_move(self.board, m1))
        make_move(self.board, m1)
        self.assertTrue(legal_move(self.board, m2))
        make_move(self.board, m2)
        self.assertTrue(legal_move(self.board, m3))
        make_move(self.board, m3)
        self.assertTrue(legal_move(self.board, m4))
        make_move(self.board, m4)

        self.assertTrue(is_in_check(self.board, WHITE))
        is_over, is_stalemate, reason = game_over(self.board)
        self.assertTrue(is_over)
        self.assertFalse(is_stalemate)
        self.assertIsNone(reason)  # Checkmate

    def test_scholar_mate(self):
        # 1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#
        moves = ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"]
        for uci in moves:
            m = parse_move_text(uci)
            self.assertTrue(legal_move(self.board, m), f"Move {uci} was expected to be legal")
            make_move(self.board, m)

        is_over, is_stalemate, _ = game_over(self.board)
        self.assertTrue(is_over)
        self.assertFalse(is_stalemate)
        self.assertTrue(is_in_check(self.board, BLACK))

    def test_castling(self):
        # 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O
        for uci in ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"]:
            make_move(self.board, parse_move_text(uci))

        # White kingside castle: e1g1
        castle_ks = parse_move_text("e1g1")
        self.assertTrue(legal_move(self.board, castle_ks))
        make_move(self.board, castle_ks)

        # King should be on g1 (row 7, col 6) and Rook on f1 (row 7, col 5)
        self.assertEqual(self.board.grid[7][6].type, 'K')
        self.assertEqual(self.board.grid[7][5].type, 'R')
        self.assertTrue(self.board.white_king_moved)
        self.assertTrue(self.board.white_rook_h_moved)

    def test_en_passant(self):
        # 1. e4 a6 2. e5 d5 3. exd6
        make_move(self.board, parse_move_text("e2e4"))
        make_move(self.board, parse_move_text("a7a6"))
        make_move(self.board, parse_move_text("e4e5"))
        make_move(self.board, parse_move_text("d7d5"))

        # En passant target square should be d6 (row 2, col 3)
        self.assertEqual((self.board.ep_row, self.board.ep_col), (2, 3))
        ep_move = parse_move_text("e5d6")
        self.assertTrue(legal_move(self.board, ep_move))
        make_move(self.board, ep_move)

        # Captured pawn on d5 (row 3, col 3) should be empty
        self.assertTrue(self.board.grid[3][3].is_empty)
        # White pawn should be on d6 (row 2, col 3)
        self.assertEqual(self.board.grid[2][3].type, 'P')
        self.assertEqual(self.board.grid[2][3].color, WHITE)

    def test_fen_roundtrip(self):
        fen_start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        ok, reason = self.board.load_fen(fen_start)
        self.assertTrue(ok)
        self.assertEqual(self.board.to_fen(), fen_start)

        # Custom FEN
        fen_custom = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 4 5"
        ok, reason = self.board.load_fen(fen_custom)
        self.assertTrue(ok, f"Failed loading valid FEN: {reason}")
        self.assertEqual(self.board.to_fen(), fen_custom)

    def test_repetition_threefold(self):
        # 1. Nf3 Nf6 2. Ng1 Ng8 3. Nf3 Nf6 4. Ng1 Ng8
        moves = ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"]
        for uci in moves:
            make_move(self.board, parse_move_text(uci))
            self.board.record_position()

        can_claim, reason = self.board.claimable_draw()
        self.assertTrue(can_claim)
        self.assertEqual(reason, "threefold repetition")

    def test_analysis_reports(self):
        tracker = Tracker(self.board)
        e2e4 = parse_move_text("e2e4")

        # Stage 3A Calc report
        calc_out = calc_report(self.board, tracker, e2e4)
        self.assertIn("CALC BEGIN e2e4", calc_out)
        self.assertIn("MOVED White P e2 e4", calc_out)
        self.assertIn("CALC END", calc_out)

        # Stage 3B Replies report
        rep_out = replies_report(self.board, tracker, e2e4)
        self.assertIn("REPLIES BEGIN e2e4", rep_out)
        self.assertIn("SUMMARY REPLIES 20", rep_out)
        self.assertIn("REPLIES END", rep_out)

        # Stage 3C Loop report
        loop_out = loop_report(self.board, depth=1)
        self.assertIn("LOOP BEGIN White DEPTH 1", loop_out)
        self.assertIn("PLY 1 POSITIONS 20", loop_out)
        self.assertIn("LOOP END", loop_out)

        # Stage 3D Goal & PASS routes
        goal = parse_goal("e4 1")
        self.assertIsNotNone(goal)
        routes_out = routes_report_with(self.board, goal)
        self.assertIn("ROUTES BEGIN White GOAL e4 LIMIT 1 PASS", routes_out)

        # Stage 3E Exchange & Order
        order_out = order_report(self.board, limit=2)
        self.assertIn("ORDER BEGIN White EXCHANGE LIMIT 2", order_out)

    def test_cannot_castle_while_in_check(self):
        ok, reason = self.board.load_fen("4r1k1/8/8/8/8/8/8/R3K2R w KQ - 0 1")
        self.assertTrue(ok, reason)
        self.assertTrue(is_in_check(self.board, WHITE))
        self.assertFalse(legal_move(self.board, parse_move_text("e1g1")))
        self.assertFalse(legal_move(self.board, parse_move_text("e1c1")))

    def test_absolute_pin_blocks_leaving_the_line(self):
        ok, reason = self.board.load_fen("4r1k1/8/8/8/8/8/4N3/4K3 w - - 0 1")
        self.assertTrue(ok, reason)
        self.assertFalse(legal_move(self.board, parse_move_text("e2f4")))
        self.assertFalse(legal_move(self.board, parse_move_text("e2c3")))

    def test_promotion_requires_piece_letter(self):
        ok, reason = self.board.load_fen("8/4P3/8/8/8/8/8/4K1k1 w - - 0 1")
        self.assertTrue(ok, reason)
        self.assertFalse(legal_move(self.board, parse_move_text("e7e8")))
        self.assertTrue(legal_move(self.board, parse_move_text("e7e8q")))
        self.assertTrue(legal_move(self.board, parse_move_text("e7e8n")))
        make_move(self.board, parse_move_text("e7e8n"))
        self.assertEqual(self.board.grid[0][4].type, "N")
        self.assertEqual(self.board.grid[0][4].color, WHITE)

    def test_en_passant_expires_after_one_move(self):
        for uci in ("e2e4", "a7a6", "e4e5", "d7d5"):
            make_move(self.board, parse_move_text(uci))
        self.assertTrue(legal_move(self.board, parse_move_text("e5d6")))
        make_move(self.board, parse_move_text("h2h3"))
        self.assertEqual((self.board.ep_row, self.board.ep_col), (-1, -1))
        self.assertFalse(legal_move(self.board, parse_move_text("e5d6")))

    def test_stalemate_and_dead_position(self):
        ok, reason = self.board.load_fen("k7/2Q5/8/8/8/8/8/4K3 b - - 0 1")
        self.assertTrue(ok, reason)
        over, stalemate, draw_reason = game_over(self.board)
        self.assertTrue(over)
        self.assertTrue(stalemate)
        self.assertIsNone(draw_reason)

        ok, reason = self.board.load_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
        self.assertTrue(ok, reason)
        auto, why = self.board.automatic_draw()
        self.assertTrue(auto)
        self.assertEqual(why, "dead position")

    def test_in_bounds_rejects_bool_and_float(self):
        from chess_engine.constants import in_bounds
        self.assertFalse(in_bounds(True, 0))
        self.assertFalse(in_bounds(0, False))
        self.assertFalse(in_bounds(1.0, 0))
        self.assertTrue(in_bounds(0, 0))

    def test_load_fen_rejects_oversized_text(self):
        ok, reason = self.board.load_fen("x" * 300)
        self.assertFalse(ok)
        self.assertIn("too long", reason or "")

    def test_ep_that_exposes_king_is_illegal(self):
        # Black pawn c4; EP target d3; capturing would open the a-file rook check.
        ok, reason = self.board.load_fen("8/8/8/8/k1pP3R/8/8/4K3 b - d3 0 1")
        self.assertTrue(ok, reason)
        self.assertFalse(legal_move(self.board, parse_move_text("c4d3")))

    def test_apply_move_from_empty_does_not_wipe_destination(self):
        from chess_engine.movegen import apply_move_to_board
        before = self.board.to_fen()
        # Empty e4 -> occupied e2 must not clear the white pawn.
        apply_move_to_board(self.board, Move(4, 4, 6, 4))
        self.assertEqual(self.board.to_fen(), before)
        self.assertEqual(self.board.grid[6][4].type, "P")

    def test_make_move_ignores_wrong_side_piece(self):
        before = self.board.to_fen()
        # Black pawn on white's turn must not move.
        make_move(self.board, Move(1, 4, 3, 4))
        self.assertEqual(self.board.to_fen(), before)

    def test_make_move_ignores_own_piece_capture(self):
        before = self.board.to_fen()
        # White knight b1 onto white pawn d2 must not wipe the pawn.
        make_move(self.board, Move(7, 1, 6, 3))
        self.assertEqual(self.board.to_fen(), before)

    def test_index_to_row_col_rejects_bool(self):
        from chess_engine.constants import index_to_row_col
        self.assertIsNone(index_to_row_col(True))
        self.assertIsNone(index_to_row_col(False))
        self.assertEqual(index_to_row_col(1), (0, 1))

    def test_promotion_moves_are_generated(self):
        ok, reason = self.board.load_fen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
        self.assertTrue(ok, reason)
        promos = {
            m.uci for m in sorted_moves(self.board) if m.promotion != "\0"
        }
        self.assertEqual(promos, {"a7a8q", "a7a8r", "a7a8b", "a7a8n"})
        make_move(self.board, parse_move_text("a7a8n"))
        self.assertEqual(self.board.grid[0][0].type, "N")
        self.assertEqual(self.board.grid[0][0].color, WHITE)

    def test_make_move_refuses_castling_without_rook(self):
        ok, reason = self.board.load_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
        self.assertTrue(ok, reason)
        before = self.board.to_fen()
        make_move(self.board, parse_move_text("e1g1"))
        self.assertEqual(self.board.to_fen(), before)
        self.assertEqual(self.board.grid[7][4].type, "K")
        self.assertTrue(self.board.grid[7][6].is_empty)

    def test_load_fen_rejects_unicode_digits(self):
        # Arabic-Indic digit for an empty rank must not be treated as FEN.
        ok, reason = self.board.load_fen(
            "rnbqkbnr/pppppppp/\u0668/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )
        self.assertFalse(ok)
        self.assertIsNotNone(reason)

    def test_claimable_draw_with_intended_move(self):
        # After returning twice toward the start, Ng8 would create threefold.
        moves = ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1"]
        for uci in moves:
            make_move(self.board, parse_move_text(uci))
            self.board.record_position()
        intended = parse_move_text("f6g8")
        self.assertFalse(self.board.claimable_draw()[0])
        can_claim, reason = self.board.claimable_draw(intended)
        self.assertTrue(can_claim)
        self.assertEqual(reason, "threefold repetition")

    def test_cannot_castle_through_or_into_check(self):
        ok, reason = self.board.load_fen("5rk1/8/8/8/8/8/8/4K2R w K - 0 1")
        self.assertTrue(ok, reason)
        self.assertFalse(legal_move(self.board, parse_move_text("e1g1")))
        # Rook on g8 attacks g1; king would castle into check.
        ok, reason = self.board.load_fen("4k1r1/8/8/8/8/8/8/4K2R w K - 0 1")
        self.assertTrue(ok, reason)
        self.assertFalse(legal_move(self.board, parse_move_text("e1g1")))
        # b-file attack does not block queenside castling (king never crosses b1).
        ok, reason = self.board.load_fen("1r2k3/8/8/8/8/8/8/R3K3 w Q - 0 1")
        self.assertTrue(ok, reason)
        self.assertTrue(legal_move(self.board, parse_move_text("e1c1")))

    def test_zero_move_cause_pawn_promotion(self):
        from chess_engine.study.calc import zero_move_cause
        # White pawn on a7 with a8 empty: promotion is possible, not BLOCKED
        ok, reason = self.board.load_fen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
        self.assertTrue(ok, reason)
        cause = zero_move_cause(self.board, 1, 0)
        self.assertNotEqual(cause, "BLOCKED")

    def test_captured_type_non_ep(self):
        from chess_engine.study.exchange import captured_type
        # White pawn on e4, d5 is empty and not ep target. Diagonal move e4d5 should return ""
        self.board.reset_board()
        make_move(self.board, parse_move_text("e2e4"))
        self.assertEqual(captured_type(self.board, Move(4, 4, 3, 3)), "")

    def test_trace_report_history_limit(self):
        from chess_engine.study.search import trace_report
        from chess_engine.constants import HISTORY_MAX_LEN
        tracker = Tracker(self.board)
        oversized = " ".join(["e2e4"] * (HISTORY_MAX_LEN + 1))
        ok, out, idx = trace_report(self.board, tracker, oversized)
        self.assertFalse(ok)
        self.assertEqual(idx, 1)

    def test_diagonal_king_move_is_not_castle(self):
        from chess_engine.study.goals import distance_lines
        from chess_engine.ui import resolve_piece_after_move
        # Diagonal move with delta_col 2 must not be treated as castling
        diag_move = Move(7, 4, 5, 6)
        after_row, after_col, captured = resolve_piece_after_move(self.board, diag_move, 7, 7)
        self.assertEqual(after_col, 7)  # rook didn't castle

        # In distance_lines, a king moving diagonally 2 squares doesn't get CASTLE tag
        lines = distance_lines(self.board, 7, 4, "MOVE")
        for line in lines:
            if "CASTLE" in line:
                self.assertIn("e1", line)


if __name__ == "__main__":
    unittest.main()
