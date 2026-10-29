"""Console list and print helpers for shape compare.

Builds Strategy Forming List and Greatest Target List as text lines or
stdout output. Fill printing always ends with IDENTITY CLAIMED: no.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from calculator.shape_grid import require_picture

if TYPE_CHECKING:
    from calculator.shape_compare import ShapeCompare, ShapeObservation


def strategy_forming_list_lines(observation: ShapeObservation) -> list[str]:
    """Build the Strategy Forming List as text lines (no identity line)."""
    from calculator.shape_compare import rank

    lines = ["Strategy Forming List"]
    for i, result in enumerate(rank(observation), start=1):
        lines.append(
            f"{i}. {result.name}  score={result.score}  "
            f"#={result.confirmed}  +={result.predicted}  "
            f"X={result.contradictions}  ?={result.unknown}  "
            f"-={result.confirmed_empty}  unexpected={result.unexpected}"
        )
        lines.append(f"   {result.coverage}")
    return lines


def greatest_target_list_lines(observation: ShapeObservation) -> list[str]:
    """Build the Greatest Target List as text lines."""
    from calculator.shape_compare import disagreeing_unlooked_cells

    lines = ["Greatest Target List"]
    targets = disagreeing_unlooked_cells(observation)
    if len(targets) == 0:
        lines.append("(none)")
    else:
        for r, c in targets:
            lines.append(f"cell-{r}-{c}")
    return lines


def print_fill(result: ShapeCompare) -> None:
    """Print fill grid, coverage, agree line, and identity line."""
    for row in result.fill:
        print(row)
    print(result.coverage)
    if result.measurements_agree:
        print("MEASUREMENTS AGREE: yes")
    else:
        print("MEASUREMENTS AGREE: no")
    # Agreeing measurements still do not name the shape.
    print("IDENTITY CLAIMED: no")


# Clearer alias for beginners (same function, same output).
print_shape_fill = print_fill


def print_strategy_forming_list(observation: ShapeObservation) -> None:
    for line in strategy_forming_list_lines(observation):
        print(line)
    print("IDENTITY CLAIMED: no")


def print_greatest_target_list(observation: ShapeObservation) -> None:
    for line in greatest_target_list_lines(observation):
        print(line)


def print_picture(name: str, picture: Sequence[str]) -> None:
    require_picture(picture, label=name)
    print(f"{name}:")
    for row in picture:
        print(row)
