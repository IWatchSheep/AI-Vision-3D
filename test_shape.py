"""Tests for shape filling beside the chess dolls."""

from __future__ import annotations

import io
import pathlib
import unittest
from contextlib import redirect_stdout

from calculator.shape import (
    COLS,
    FILL_MARKS,
    ROWS,
    WHEEL,
    Observation,
    ShapeObservation,
    ShapeWindow,
    compare,
    disagreeing_unlooked_cells,
    imagine,
    print_fill,
    print_shape_fill,
    rank,
    reveal,
)
from calculator.window import DEFAULT_PAST_LIMIT


class TestUnlookedFill(unittest.TestCase):
    def test_blank_observation_wheel_marks(self) -> None:
        # Before any reveal: object cells are "+", empty cells are "?".
        obs = Observation.blank()
        result = compare(WHEEL, obs, "wheel")
        for r in range(ROWS):
            for c in range(COLS):
                mark = result.fill[r][c]
                if WHEEL[r][c] == "#":
                    self.assertEqual(mark, "+", msg=f"({r},{c})")
                else:
                    self.assertEqual(mark, "?", msg=f"({r},{c})")
                self.assertNotEqual(mark, "-")
                self.assertNotEqual(mark, "X")


class TestPartialReveal(unittest.TestCase):
    def test_top_rim_confirmed_rest_predicted(self) -> None:
        obs = Observation.blank()
        for cell in ((0, 1), (0, 2), (0, 3)):
            obs = reveal(obs, *cell, WHEEL)
        result = compare(WHEEL, obs, "wheel")
        for c in (1, 2, 3):
            self.assertEqual(result.fill[0][c], "#")
        for r in range(ROWS):
            for c in range(COLS):
                if WHEEL[r][c] != "#":
                    continue
                if (r, c) in ((0, 1), (0, 2), (0, 3)):
                    continue
                self.assertEqual(result.fill[r][c], "+", msg=f"({r},{c})")

    def test_reveal_empty_picture_cell_is_dash(self) -> None:
        # Wheel picture is empty at (2,2); looking there on a real wheel is "-".
        obs = reveal(Observation.blank(), 2, 2, WHEEL)
        result = compare(WHEEL, obs, "wheel")
        self.assertEqual(result.fill[2][2], "-")

    def test_looked_object_on_empty_picture_is_unexpected_x(self) -> None:
        # Build a hidden grid that has an object where the wheel is empty.
        hidden_rows = []
        for r, row in enumerate(WHEEL):
            if r == 2:
                chars = list(row)
                chars[2] = "#"
                hidden_rows.append("".join(chars))
            else:
                hidden_rows.append(row)
        obs = reveal(Observation.blank(), 2, 2, hidden_rows)
        result = compare(WHEEL, obs, "wheel")
        self.assertEqual(result.fill[2][2], "X")
        self.assertEqual(result.unexpected, 1)

    def test_reveal_out_of_bounds_raises(self) -> None:
        # Overflow / underflow guard: bad indices must not silently wrap.
        with self.assertRaises(ValueError):
            reveal(Observation.blank(), -1, 0, WHEEL)
        with self.assertRaises(ValueError):
            reveal(Observation.blank(), 0, 5, WHEEL)
        # bool and float must not be treated as board indices (True == 1).
        with self.assertRaises(ValueError):
            reveal(Observation.blank(), True, 0, WHEEL)
        with self.assertRaises(ValueError):
            reveal(Observation.blank(), 0, 1.0, WHEEL)


class TestFullReveal(unittest.TestCase):
    def test_full_wheel_agree_no_identity(self) -> None:
        obs = Observation.blank()
        for r in range(ROWS):
            for c in range(COLS):
                obs = reveal(obs, r, c, WHEEL)
        result = compare(WHEEL, obs, "wheel")
        self.assertEqual(result.predicted, 0)
        self.assertEqual(result.contradictions, 0)
        for row in result.fill:
            self.assertNotIn("+", row)
            self.assertNotIn("X", row)
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_fill(result)
        out = buf.getvalue()
        self.assertIn("MEASUREMENTS AGREE: yes", out)
        self.assertIn("IDENTITY CLAIMED: no", out)


class TestRanking(unittest.TestCase):
    def test_after_one_rim_cell_wheel_ranks_above_person(self) -> None:
        obs = reveal(Observation.blank(), 0, 1, WHEEL)
        ranked = rank(obs)
        self.assertEqual(ranked[0].name, "wheel")
        self.assertEqual(ranked[1].name, "person-doll")
        self.assertGreater(ranked[0].score, ranked[1].score)


class TestImagine(unittest.TestCase):
    def test_imagine_four_steps_first_cell_and_unchanged(self) -> None:
        obs = Observation.blank()
        before_targets = disagreeing_unlooked_cells(obs)
        result = imagine(obs, WHEEL)
        self.assertEqual(len(result.steps), 4)
        self.assertEqual(result.steps[0].cell, (0, 1))
        for r in range(ROWS):
            for c in range(COLS):
                self.assertIsNone(obs.get(r, c), msg=f"({r},{c})")
        self.assertTrue(result.real_unchanged)
        self.assertEqual(result.real_before_forming, result.real_after_forming)
        self.assertEqual(result.real_before_targets, result.real_after_targets)
        self.assertEqual(before_targets, disagreeing_unlooked_cells(obs))

    def test_imagine_deterministic(self) -> None:
        obs = Observation.blank()
        a = imagine(obs, WHEEL)
        b = imagine(obs, WHEEL)
        self.assertEqual([s.cell for s in a.steps], [s.cell for s in b.steps])
        ranked_a = [(r.name, r.score) for r in rank(obs)]
        ranked_b = [(r.name, r.score) for r in rank(Observation.blank())]
        self.assertEqual(ranked_a, ranked_b)
        self.assertEqual(len(a.steps), 4)
        self.assertEqual(len(b.steps), 4)


class TestShapeWindow(unittest.TestCase):
    def test_accept_five_leaves_four(self) -> None:
        window = ShapeWindow()
        # Accept five different one-cell looks; past must keep only the last four.
        for col in range(5):
            obs = reveal(Observation.blank(), 0, col, WHEEL)
            window.set_current(obs)
            window.accept()
        self.assertEqual(len(window.past), DEFAULT_PAST_LIMIT)
        self.assertIsNone(window.current)
        # Oldest (col 0) was dropped; past starts at col 1.
        self.assertTrue(window.past[0].is_looked(0, 1))
        self.assertFalse(window.past[0].is_looked(0, 0))


class TestSourceConstraints(unittest.TestCase):
    def test_shape_source_clean(self) -> None:
        path = pathlib.Path(__file__).resolve().parent / "calculator" / "shape.py"
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertNotIn("unity", lower)
        self.assertNotIn("camera", lower)
        self.assertNotIn("KQRBNP", text)
        self.assertNotIn("kqrbnp", text)
        self.assertNotIn('"K"', text)
        self.assertNotIn("'K'", text)


class TestShapeInvariants(unittest.TestCase):
    """Additive checks: marks, counts, score, and no input mutation."""

    def test_fill_marks_counts_and_score(self) -> None:
        obs = reveal(Observation.blank(), 0, 1, WHEEL)
        result = compare(WHEEL, obs, "wheel")
        flat = "".join(result.fill)
        self.assertTrue(set(flat) <= FILL_MARKS)
        self.assertEqual(result.confirmed, flat.count("#"))
        self.assertEqual(result.predicted, flat.count("+"))
        self.assertEqual(result.contradictions, flat.count("X"))
        self.assertEqual(result.unknown, flat.count("?"))
        self.assertEqual(result.confirmed_empty, flat.count("-"))
        self.assertEqual(result.score, result.confirmed - result.contradictions)

    def test_reveal_and_imagine_do_not_mutate_real_observation(self) -> None:
        obs = Observation.blank()
        before = obs.cells
        reveal(obs, 0, 1, WHEEL)
        self.assertIs(obs.cells, before)
        self.assertEqual(obs.cells, before)
        imagine(obs, WHEEL)
        self.assertEqual(obs.cells, before)

    def test_print_shape_fill_alias_matches_print_fill(self) -> None:
        obs = Observation.blank()
        result = compare(WHEEL, obs, "wheel")
        buf_a = io.StringIO()
        buf_b = io.StringIO()
        with redirect_stdout(buf_a):
            print_fill(result)
        with redirect_stdout(buf_b):
            print_shape_fill(result)
        self.assertEqual(buf_a.getvalue(), buf_b.getvalue())

    def test_observation_alias_is_shape_observation(self) -> None:
        self.assertIs(Observation, ShapeObservation)

    def test_observation_freezes_caller_owned_rows_before_storing(self) -> None:
        cells = [[None] * COLS for _ in range(ROWS)]
        observation = ShapeObservation(cells)
        window = ShapeWindow()
        window.set_current(observation)
        window.accept()
        cells[0][0] = "#"
        self.assertIsNone(window.past[0].get(0, 0))

    def test_shape_window_past_setter_enforces_limit(self) -> None:
        window = ShapeWindow()
        # Six looks on valid cells; past must keep only the last four.
        looks = [
            reveal(Observation.blank(), 0, i % COLS, WHEEL)
            for i in range(DEFAULT_PAST_LIMIT + 2)
        ]
        window.past = looks
        self.assertEqual(len(window.past), DEFAULT_PAST_LIMIT)
        # Dropped i=0 (col 0) and i=1 (col 1); first kept is i=2 (col 2).
        self.assertTrue(window.past[0].is_looked(0, 2))
        self.assertFalse(window.past[0].is_looked(0, 0))


if __name__ == "__main__":
    unittest.main()
