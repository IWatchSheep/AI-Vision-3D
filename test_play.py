"""Accept real chess moves into a fixed blueprint, and imagine on a copy."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from calculator.play_build import PlaySession, handle_command
from chess_module.chess_engine.board import Board
from show_play import main as show_play


def _load(fen: str) -> Board:
    board = Board()
    ok, reason = board.load_fen(fen)
    if not ok:
        raise AssertionError(reason)
    return board


class TestPlay(unittest.TestCase):
    def test_two_real_moves_fill_center_and_keep_full_state(self):
        session = PlaySession()
        start_fen = session.fen()
        start_history = session.history()
        first = session.accept("e2e4")
        self.assertTrue(first.legal)
        self.assertEqual(first.enters, ("e4",))
        self.assertEqual(first.leaves, ())
        self.assertEqual(first.view.total_matched, 23)
        self.assertEqual(
            session.fen(),
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        )
        self.assertNotEqual(session.history(), start_history)
        second = session.accept("e7e5")
        self.assertTrue(second.legal)
        self.assertEqual(second.view.total_matched, 24)
        self.assertEqual(
            session.fen(),
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
        )
        self.assertNotEqual(session.fen(), start_fen)
        self.assertEqual(session.rows[4][4], "P")
        self.assertEqual(session.rows[3][4], "p")
        self.assertEqual(session.accepted, ["e2e4", "e7e5"])

    def test_forming_list_changes_only_after_accepted_move(self):
        session = PlaySession()

        def filled(doll_id: str) -> int:
            return next(item.filled for item in session.forming() if item.id == doll_id)

        self.assertEqual(len(session.forming()), 20)
        self.assertEqual(filled("develop-to-the-center"), 22)
        self.assertEqual(filled("starting-array"), 32)
        before = session.forming()
        refused = session.accept("e2e5")
        self.assertFalse(refused.legal)
        self.assertEqual(session.forming(), before)
        session.accept("e2e4")
        self.assertEqual(filled("develop-to-the-center"), 23)
        self.assertEqual(filled("starting-array"), 31)
        after_one = session.forming()
        imagined = session.imagine(("e7e5", "g1f3", "b8c6", "d2d3"))
        self.assertTrue(imagined.real_unchanged)
        self.assertEqual(session.forming(), after_one)
        session.accept("e7e5")
        self.assertEqual(filled("develop-to-the-center"), 24)

    def test_imaginary_classic_line_ranks_all_twenty_without_touching_real_state(self):
        session = PlaySession()
        before = session.state_key()
        line = session.imagine(("e2e4", "e7e5", "g1f3", "b8c6"))
        self.assertTrue(line.real_unchanged)
        self.assertEqual(session.state_key(), before)
        self.assertEqual(
            [step.matched_after for step in line.steps],
            [23, 24, 25, 26],
        )
        for step in line.steps:
            self.assertEqual(len(step.forming), 20)
            self.assertEqual(len({item.id for item in step.forming}), 20)
            center = next(item for item in step.forming if item.id == "develop-to-the-center")
            self.assertEqual(center.filled, step.matched_after)
        real_center = next(item.filled for item in session.forming()
                           if item.id == "develop-to-the-center")
        self.assertEqual(real_center, 22)
        text = handle_command(session, "imagine e2e4 e7e5 g1f3 b8c6")
        self.assertIsNotNone(text)
        assert text is not None
        self.assertEqual(text.count("Theoretical Strategy Forming List"), 4)
        self.assertEqual(text.count("Theoretical Greatest Target List"), 4)
        self.assertIn("REAL BOARD UNCHANGED: yes", text)
        self.assertIn("26 of 32 positions matched.", text)
        self.assertIn("Doubled rooks", text)
        self.assertEqual(session.state_key(), before)

    def test_auto_imagine_prefers_a_legal_fill_and_stays_on_a_copy(self):
        session = PlaySession()
        before = session.state_key()
        line = session.imagine()
        self.assertEqual(len(line.steps), 4)
        self.assertTrue(all(step.result.legal for step in line.steps))
        self.assertEqual(line.steps[0].result.message.split()[1], "d2")
        self.assertGreater(line.steps[0].matched_after, line.steps[0].matched_before)
        self.assertTrue(line.real_unchanged)
        self.assertEqual(session.state_key(), before)

    def test_departure_reduces_completion_and_the_display_says_so(self):
        session = PlaySession()
        result = session.accept("a2a3")
        self.assertTrue(result.legal)
        self.assertEqual(result.leaves, ("a2",))
        self.assertEqual(result.view.total_matched, 21)
        self.assertEqual(result.view.marks[6][0], "+")
        text = handle_command(PlaySession(), "a2a3")
        assert text is not None
        self.assertIn("This move left a matching position. The count fell from 22 to 21.", text)
        self.assertIn("a2 is unfilled", text)
        self.assertIn("21 of 32 positions matched.", text)

    def test_illegal_move_and_same_side_twice_are_rejected(self):
        session = PlaySession()
        before = session.state_key()
        text = handle_command(session, "e2e5")
        assert text is not None
        self.assertIn("Move refused: 'e2e5'", text)
        self.assertIn("The real chessboard is unchanged.", text)
        self.assertIn("Real Strategy Forming List unchanged.", text)
        self.assertEqual(session.state_key(), before)
        session.accept("e2e4")
        after = session.state_key()
        refused = session.accept("g1f3")
        self.assertFalse(refused.legal)
        self.assertEqual(session.state_key(), after)
        self.assertNotIn(" g1f3", " " + " ".join(session.accepted))

    def test_castling_updates_rights_history_and_marks_a_mismatch(self):
        session = PlaySession(
            "starting-array",
            _load("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1"),
        )
        before_history = session.history()
        before_matched = session.view().total_matched
        blocked = PlaySession()
        self.assertFalse(blocked.accept("e1g1").legal)
        result = session.accept("e1g1")
        self.assertTrue(result.legal)
        self.assertEqual(set(result.enters), {"f1", "g1"})
        self.assertEqual(set(result.leaves), {"e1", "h1"})
        self.assertEqual(session.rows[7], "R....RK.")
        self.assertNotIn("K", session.fen().split()[2])
        self.assertNotIn("Q", session.fen().split()[2])
        self.assertGreater(len(session.history()), len(before_history))
        self.assertNotEqual(session.history(), before_history)
        self.assertLess(session.view().total_matched, before_matched)
        self.assertEqual(result.view.marks[7][5], "X")
        self.assertEqual(result.view.marks[7][4], "+")
        shown = handle_command(
            PlaySession("starting-array", _load("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1")),
            "e1g1",
        )
        assert shown is not None
        self.assertIn("f1 is mismatch", shown)
        self.assertIn("e1 is unfilled", shown)
        self.assertIn("White king e1 to g1", shown)

    def test_en_passant_right_is_kept_until_the_capture(self):
        session = PlaySession()
        for move in ("e2e4", "a7a6", "e4e5", "d7d5"):
            result = session.accept(move)
            self.assertTrue(result.legal, result.message)
        self.assertIn(" d6 ", f" {session.fen()} ")
        stripped = session.fen().split()
        stripped[3] = "-"
        bare = _load(" ".join(stripped))
        from calculator.build_shape import apply_legal_move, render_board
        self.assertFalse(apply_legal_move(render_board(bare), "e5d6", session.doll).legal)
        capture = session.accept("e5d6")
        self.assertTrue(capture.legal, capture.message)
        self.assertEqual(session.rows[3][3], ".")
        self.assertEqual(session.rows[2][3], "P")
        self.assertEqual(session.fen().split()[1], "b")
        self.assertEqual(session.fen().split()[3], "-")
        self.assertNotEqual(session.history(), [])

    def test_promotion_requires_a_piece_and_can_reduce_the_blueprint(self):
        session = PlaySession(
            "kings-pawn-promotion",
            _load("7k/4P3/8/8/8/8/8/4K3 w - - 0 1"),
        )
        self.assertEqual(session.view().total_matched, 3)
        before = session.state_key()
        refused = session.accept("e7e8")
        self.assertFalse(refused.legal)
        self.assertEqual(session.state_key(), before)
        result = session.accept("e7e8q")
        self.assertTrue(result.legal, result.message)
        self.assertEqual(session.rows[0][4], "Q")
        self.assertEqual(session.rows[1][4], ".")
        self.assertEqual(result.leaves, ("e7",))
        self.assertEqual(session.view().total_matched, 2)
        self.assertEqual(session.fen().split()[1], "b")
        self.assertIn("Q", session.fen().split()[0])
        self.assertNotEqual(session.history(), before[1])
        text = handle_command(
            PlaySession("kings-pawn-promotion", _load("7k/4P3/8/8/8/8/8/4K3 w - - 0 1")),
            "e7e8q",
        )
        assert text is not None
        self.assertIn("promoting to a queen", text)
        self.assertIn("The count fell from 3 to 2.", text)
        self.assertIn("e7 is unfilled", text)

    def test_display_shows_pieces_blueprint_and_unfilled_squares(self):
        session = PlaySession()
        text = handle_command(session, "board")
        assert text is not None
        self.assertIn("rnbqkbnr", text)
        self.assertIn("r.bqk..r", text)
        self.assertIn("+", text)
        self.assertIn("22 of 32 positions matched.", text)
        self.assertIn("Real Strategy Forming List", text)
        self.assertIn("Real Greatest Target List", text)
        self.assertIn("e4 + wants P, seen empty, legal move e2e4", text)
        self.assertIn("no legal move this turn", text)
        self.assertIn("IDENTITY CLAIMED: no", text)
        self.assertIn("Chess state: " + session.fen(), text)
        moved = handle_command(session, "e2e4")
        assert moved is not None
        self.assertIn("..+.P...", moved)
        self.assertIn("23 of 32 positions matched.", moved)
        self.assertIn("e4 is filled", moved)
        self.assertIn("White pawn e2 to e4", moved)

    def test_classic_line_story_reaches_twenty_six_and_keeps_history(self):
        session = PlaySession()
        histories = [session.history()]
        for move in ("e2e4", "e7e5", "g1f3", "b8c6"):
            self.assertTrue(session.accept(move).legal)
            histories.append(session.history())
        self.assertEqual(len(histories[1]), 1)
        self.assertEqual(len(histories[2]), 1)
        self.assertNotEqual(histories[1], histories[2])
        self.assertEqual(len(histories[3]), 2)
        self.assertEqual(len(histories[4]), 3)
        self.assertEqual(
            session.fen(),
            "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        )
        record = "\n".join(session.development_lines())
        self.assertIn("Starting board: 22 of 32 positions matched.", record)
        self.assertIn("White pawn e2 to e4: 23 of 32 positions matched.", record)
        self.assertIn("Black pawn e7 to e5: 24 of 32 positions matched.", record)
        self.assertIn("White knight g1 to f3: 25 of 32 positions matched.", record)
        self.assertIn("Black knight b8 to c6: 26 of 32 positions matched.", record)
        self.assertNotIn("The count fell", record)

    def test_switching_doll_does_not_move_the_real_board(self):
        session = PlaySession()
        session.accept("e2e4")
        before = session.fen(), tuple(session.history()), tuple(session.accepted)
        text = handle_command(session, "doll starting-array")
        assert text is not None
        self.assertEqual((session.fen(), tuple(session.history()), tuple(session.accepted)), before)
        self.assertEqual(session.view().total_matched, 31)
        self.assertIn("Starting array", text)
        missing = handle_command(session, "doll not-a-strategy")
        self.assertEqual(session.doll.id, "starting-array")
        self.assertIn("No strategy matching", missing or "")

    def test_knight_on_the_pawn_square_is_a_mismatch(self):
        session = PlaySession()
        self.assertTrue(session.accept("b1c3").legal)
        self.assertTrue(session.accept("a7a6").legal)
        result = session.accept("c3e4")
        self.assertTrue(result.legal)
        self.assertEqual(result.enters, ("e4",))
        self.assertEqual(result.leaves, ("c3",))
        self.assertEqual(result.view.marks[4][4], "X")
        text = handle_command(session, "board")
        assert text is not None
        self.assertIn("X", text)
        self.assertIn("e4 X wants P", text)

    def test_show_play_accepts_a_typed_move_then_quits(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["e2e4", "quit"]), redirect_stdout(output):
            show_play()
        text = output.getvalue()
        self.assertIn("22 of 32 positions matched.", text)
        self.assertIn("23 of 32 positions matched.", text)
        self.assertIn("rnbqkbnr", text)
        self.assertIn("IDENTITY CLAIMED: no", text)


if __name__ == "__main__":
    unittest.main()