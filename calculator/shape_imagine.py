"""Imaginary reveals on a copy of an observation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from calculator.shape_compare import (
    ShapeObservation,
    disagreeing_unlooked_cells,
    greatest_target_list_lines,
    require_observation,
    reveal,
    strategy_forming_list_lines,
)
from calculator.shape_grid import IMAGINE_STEP_LIMIT, require_picture


@dataclass(frozen=True)
class ImagineStep:
    """One imaginary reveal and the theoretical lists after it."""

    cell: tuple[int, int]
    observation: ShapeObservation
    forming_list: tuple[str, ...]
    target_list: tuple[str, ...]


@dataclass(frozen=True)
class ImagineResult:
    """Steps from imagine, plus proof the real observation was not changed."""

    steps: tuple[ImagineStep, ...]
    real_before_forming: tuple[str, ...]
    real_before_targets: tuple[str, ...]
    real_after_forming: tuple[str, ...]
    real_after_targets: tuple[str, ...]
    real_unchanged: bool


def imagine(
    observation: ShapeObservation,
    hidden: Sequence[str],
) -> ImagineResult:
    """
    Copy the observation and reveal up to IMAGINE_STEP_LIMIT target cells
    on the COPY only.

    Stop early when no disagreeing unlooked cell remains.
    The real observation must still match the before-imagine snapshot.
    """
    require_observation(observation)
    require_picture(hidden, label="hidden")

    snapshot = ShapeObservation(
        tuple(tuple(row) for row in observation.cells)
    )
    real_before_forming = tuple(strategy_forming_list_lines(observation))
    real_before_targets = tuple(greatest_target_list_lines(observation))

    copy = ShapeObservation(observation.cells)
    steps: list[ImagineStep] = []

    # --- Imaginary reveals: copy only, stop when templates agree or limit hit ---
    for _ in range(IMAGINE_STEP_LIMIT):
        targets = disagreeing_unlooked_cells(copy)
        # Do not read targets[0] when the list is empty.
        if len(targets) == 0:
            break
        r, c = targets[0]
        copy = reveal(copy, r, c, hidden)
        steps.append(
            ImagineStep(
                cell=(r, c),
                observation=copy,
                forming_list=tuple(strategy_forming_list_lines(copy)),
                target_list=tuple(greatest_target_list_lines(copy)),
            )
        )

    real_after_forming = tuple(strategy_forming_list_lines(observation))
    real_after_targets = tuple(greatest_target_list_lines(observation))
    real_unchanged = (
        observation.matches(snapshot)
        and real_before_forming == real_after_forming
        and real_before_targets == real_after_targets
    )

    return ImagineResult(
        steps=tuple(steps),
        real_before_forming=real_before_forming,
        real_before_targets=real_before_targets,
        real_after_forming=real_after_forming,
        real_after_targets=real_after_targets,
        real_unchanged=real_unchanged,
    )


def _print_lines_after_title(lines: list[str]) -> None:
    """Print every line after the title. Safe when the list is short."""
    if len(lines) <= 1:
        return
    for line in lines[1:]:
        print(line)


def print_imagine(
    observation: ShapeObservation,
    hidden: Sequence[str],
) -> ImagineResult:
    """Run imagine, print each theoretical step, then reprint the real lists."""
    result = imagine(observation, hidden)

    print("Real lists before imagine:")
    for line in result.real_before_forming:
        print(line)
    print("IDENTITY CLAIMED: no")
    for line in result.real_before_targets:
        print(line)
    print()

    for i, step in enumerate(result.steps, start=1):
        r, c = step.cell
        print(f"Imaginary step {i}: reveal cell-{r}-{c}")
        print("Theoretical Strategy Forming List")
        _print_lines_after_title(list(step.forming_list))
        print("IDENTITY CLAIMED: no")
        print("Theoretical Greatest Target List")
        _print_lines_after_title(list(step.target_list))
        print()

    print("Real lists after imagine (must match before):")
    for line in result.real_after_forming:
        print(line)
    print("IDENTITY CLAIMED: no")
    for line in result.real_after_targets:
        print(line)

    lists_match = (
        result.real_before_forming == result.real_after_forming
        and result.real_before_targets == result.real_after_targets
    )
    if result.real_unchanged and lists_match:
        print("REAL OBSERVATION UNCHANGED: yes")
    else:
        print("REAL OBSERVATION UNCHANGED: no")

    return result
