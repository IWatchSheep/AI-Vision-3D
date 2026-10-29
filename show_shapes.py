#!/usr/bin/env python3
"""
Console program: show shape pictures, fills, lists, and imaginary looks.

Display only. Does not accept an observation into ShapeWindow.past.
"""

from calculator.shape import (
    PERSON_DOLL,
    WHEEL,
    Observation,
    compare,
    print_fill,
    print_greatest_target_list,
    print_imagine,
    print_picture,
    print_strategy_forming_list,
    reveal,
)


def main() -> None:
    # 1) Show the two hardcoded pictures.
    print("=== Shape pictures ===")
    print()
    print_picture("wheel", WHEEL)
    print()
    print_picture("person-doll", PERSON_DOLL)
    print()

    # 2) Partial real look: only the top rim of a hidden wheel.
    obs = Observation.blank()
    for row, col in ((0, 1), (0, 2), (0, 3)):
        obs = reveal(obs, row, col, WHEEL)

    print("=== Partial observation (hidden wheel: 0,1  0,2  0,3) ===")
    print()
    print("Fill: wheel")
    print_fill(compare(WHEEL, obs, "wheel"))
    print()
    print("Fill: person-doll")
    print_fill(compare(PERSON_DOLL, obs, "person-doll"))
    print()
    print_strategy_forming_list(obs)
    print()
    print_greatest_target_list(obs)
    print()

    # 3) Imaginary looks from a fully unlooked observation (copy only).
    blank = Observation.blank()
    print("=== Imagine from a fully unlooked observation ===")
    print()
    print_imagine(blank, WHEEL)


if __name__ == "__main__":
    main()
