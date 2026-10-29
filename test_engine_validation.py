"""Engine invariants across reproducible games and special-move positions."""

import random
import unittest

from chess_module.chess_engine.board import Board
from chess_module.chess_engine.constants import opposite
from chess_module.chess_engine.movegen import generate_moves, game_over, is_in_check, make_move


class TestEngineValidation(unittest.TestCase):
    def test_seeded_games_preserve_legal_positions_and_fen_roundtrips(self):
        for seed in range(4):
            rng = random.Random(seed)
            board = Board()
            board.reset_board()
            for ply in range(60):
                with self.subTest(seed=seed, ply=ply):
                    before = (board.to_fen(), list(board.history))
                    moves = generate_moves(board)
                    self.assertEqual(len(moves), len(set(moves)))
                    self.assertEqual((board.to_fen(), board.history), before)
                    if game_over(board)[0]:
                        break
                    move = rng.choice(moves)
                    child = board.clone()
                    make_move(child, move, record_history=True)
                    self.assertFalse(is_in_check(child, board.turn))
                    self.assertEqual(child.turn, opposite(board.turn))
                    self.assertEqual(child.history[-1], child.position_key())
                    self.assertEqual((board.to_fen(), board.history), before)
                    restored = Board()
                    ok, reason = restored.load_fen(child.to_fen())
                    self.assertTrue(ok, reason)
                    self.assertEqual(restored.to_fen(), child.to_fen())
                    self.assertEqual(set(generate_moves(restored)), set(generate_moves(child)))
                    board = child


if __name__ == "__main__":
    unittest.main()
