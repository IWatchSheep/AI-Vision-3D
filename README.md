# AI-Vision-3D

One See–Think–Do calculator for three applications. It reads a situation, matches patterns, ranks strategies, ranks targets, and tries four imaginary next actions on a copy. The real situation stays as it is until a person accepts a change.

The three applications supply their own facts. They share the calculator.

| Application | What it supplies | Status |
|---|---|---|
| Chess | Positions, legal moves, and measurements from the finished Python chess engine | Engine finished and archived. Adapter not started. |
| AI Vision | An observed shape and an adjustable 3D model | Not started. This repository has a Unity motion scene only. |
| Grid board | Movement, obstacles, observations, and predictions from the existing grid project | Not started. The repository location is not recorded yet. |

## What already exists

Current runnable code: `python main.py` launches chess. The package launch
`python -m chess_module.main` and direct `python chess_module/main.py` also work.
`python show_strategies.py`, `python show_shapes.py`, and `python show_build.py`
run the calculator demonstrations. The milestone checklist below is the
original roadmap; see [AUDIT.md](AUDIT.md) for the current review and checks.

- [x] [chess-c99](https://github.com/IWatchSheep/chess-c99) version 16 is archived. Leave it unchanged.
- [x] [chess-python](https://github.com/IWatchSheep/chess-python) at commit `c5730c0` is archived. Leave it unchanged. It plays a full game, prints fact reports, and keeps the five-move `memory` window.
- [x] This repository is the active project. `main.py` launches chess. `unity/AI-Vision-Motion` is a Unity 6 scene where one character slides from left to right and back.
- [ ] The shared calculator.
- [ ] The 20 chess strategies.
- [ ] The four lists.
- [ ] The four imaginary actions.
- [ ] The vision adapter and the grid adapter.

The chess engine already measures gained, lost, and unchanged squares, replies, future lines, goals, routes, and candidate comparisons. It does not choose a move. Choosing belongs to the calculator.

## Rules that stay fixed

1. One calculator. Chess, vision, and the grid each connect through the same interface.
2. Each application supplies its own state, legal actions, observations, patterns, targets, and the way a copy changes.
3. Four lists, under the names below. An application may show a clearer label on screen. The ranking code stays the same.
4. See–Think–Do selects up to four imaginary actions. In chess, one action is one half-move, and the side to move alternates.
5. Imaginary actions are applied to a copy. The real position, the real model, and the real grid stay unchanged.
6. A shared improvement is a change to the calculator, then the same tests on every connected application. A chess rule does not become a vision rule or a grid rule.
7. The first version does not train. A match score is a ranking number. Calling a score a probability waits until it has been checked against known examples.
8. Build one milestone at a time. Leave a milestone when its completion line is true.

## See, think, do

- **See.** Record the current state and the measurements the application supplies.
- **Think.** Match patterns, rank strategies, rank targets, and compare what each legal action would change.
- **Do.** For an imaginary step, apply the chosen action to the copy and look again. For a real step, apply an action only when it is accepted.

## The four lists

| List | When it is calculated | Chess label |
|---|---|---|
| Strategy Forming List | From the real situation | Same name |
| Greatest Target List | From the real situation | Greatest Target Pieces List |
| Theoretical Strategy Forming List | After each imaginary action | Same name |
| Theoretical Greatest Target List | After each imaginary action | Theoretical Greatest Target Pieces List |

During imagination, the two real lists stay fixed. The two theoretical lists are stored once per imaginary step.

In chess, a target is a piece of the side that is not about to move. A high rank means the piece matters to the matched strategies. It is not a recommendation to capture it.

## What every application gives the calculator

| Input | Meaning |
|---|---|
| State | What is true now, plus a way to copy it |
| Actions | What can legally or physically happen next |
| Observations | What has actually been seen |
| Patterns | The arrangements to match, with a score from 0 to complete |
| Targets | The things whose importance should be ranked |
| Measurements | Facts used for the scores |
| Result of an action | The copied state after one legal action |
| Done | How to tell that no further action is possible |

The calculator returns one result shape for every application: the two real lists, up to four imaginary steps, the two theoretical lists at each step, the action chosen at each step, and a plain-language reason for every score.

## Decisions to write down before the milestone that needs them

These are unresolved. The milestone that depends on one of them waits until the decision is written in this README.

1. **Imaginary opponent.** In chess, the other side needs its own choice on its turns. The working rule is: each side uses the same scoring rules for its own strategies and targets. Change this rule only by writing a new one here.
2. **Strategy equivalence.** A strategy matches written conditions, such as which pieces control an area or support a target. The reference board is the picture for people. A strategy that also matches a rotated or mirrored board says so in its definition.
3. **Imaginary memory.** The real five-move window records played moves only. An imaginary line keeps a temporary window on the copy. Ending the imagination leaves the real window as it was.
4. **Search limits.** The four-action search has a maximum number of candidates per step, a time limit, and a memory limit. Those three numbers are written down before Milestone 7, and tests use them.
5. **Grid repository.** Record the grid project's URL, commit, and test command before Milestone 12. It is not one of the three public repositories above.
6. **The 20 strategies.** Their names and conditions are Milestone 4. Scoring code waits until those definitions exist.

## Milestone 1 — Keep the finished projects fixed

- [x] Leave chess-c99 archived.
- [x] Leave chess-python archived at `c5730c0`.
- [x] Develop the calculator in this repository.
- [ ] Record the grid repository and commit when that project is identified.
- [ ] Run the chess-python tests from a local checkout and save the result: `python3 -m unittest test_engine.py test_main.py`
- [ ] Run the grid project's existing tests once that checkout exists, and save the result.

**Done when:** the archived chess commits above are still the ones this plan uses, and the baseline test results are written down.

## Milestone 2 — The calculator and a tiny test application

The calculator lives in its own Python package. The tiny application is a few numbered squares and a few legal steps. It is the proof that the calculator runs with no chess, no Unity, and no grid code.

- [ ] Represent state, actions, observations, patterns, targets, measurements, and a copied result.
- [ ] Keep the real state and the imaginary copy separate.
- [ ] Rank patterns and targets with an explainable score.
- [ ] Run up to four imaginary actions on the copy.
- [ ] Stop early when no legal action remains.
- [ ] Return the standard result, including a reason for each score.
- [ ] Log each score from the measurements that produced it.
- [ ] Repeat the same input and settings and get the same result.

**Done when:** the tiny application produces all four lists and four imaginary steps, and the test imports neither chess, Unity, nor the grid.

## Milestone 3 — Chess adapter

Copy the needed chess-python files into this repository, or import a local checkout of commit `c5730c0`. Do not commit changes back to the archived repository, and do not reimplement the chess rules.

Call the engine in process. Read `MoveMemory` entries directly. Use the engine's report functions for facts that are already returned as text. Drive the interactive prompt only if a fact has no function.

- [ ] Read the FEN, the side to move, and every piece square.
- [ ] List legal moves and count destinations for a selected piece.
- [ ] Preview a move on a copy: gained, lost, and unchanged squares.
- [ ] Read protection, attacks, replies, limited future lines, goals, routes, and candidate comparisons.
- [ ] Read the five-move window.
- [ ] Cover check, checkmate, stalemate, castling, en passant, and promotion by calling the engine.
- [ ] Compare adapter results with the archived engine on the same positions.

**Done when:** a chess position can be read and previewed through the adapter, and the adapter tests agree with chess-python.

## Milestone 4 — Twenty chess strategies

Write 20 strategies and keep them in a versioned data file, outside the calculator code. Each strategy needs an id, a plain-language explanation, a reference FEN, the conditions that must hold, the conditions that help, the conditions that contradict it, the important squares, and the pieces that support it. A position may match part of a strategy.

- [ ] Approve the list of 20 before any scoring code depends on it.
- [ ] Add a known matching position and a known non-matching position for each strategy.
- [ ] Score how complete the match is, which conditions hold, and which are missing.

**Done when:** all 20 definitions and their matching tests are in the repository.

## Milestone 5 — Real Strategy Forming List

- [ ] Match the real position to all 20 strategies.
- [ ] Rank them from the strongest match to the weakest.
- [ ] Allow more than one strategy to match at the same time.
- [ ] Use the five-move window to say whether a match is growing, shrinking, or holding.
- [ ] Explain each rank in plain language.
- [ ] Show the reference board and the real board together.

**Done when:** one chess position produces a full ranked Strategy Forming List.

## Milestone 6 — Real Greatest Target List

- [ ] Score every piece of the side that is not about to move.
- [ ] Use its moves, attacks, protection, important squares, and role in the matched strategies.
- [ ] Explain each rank.
- [ ] Recalculate after each real move.
- [ ] Keep this list beside the Strategy Forming List.

**Done when:** the same position produces both real lists, and a high target rank is described as importance rather than as a capture.

## Milestone 7 — Four imaginary chess actions

- [ ] Copy the real board and record its FEN.
- [ ] From the side to move, score legal candidates on further copies.
- [ ] Apply the chosen half-move to the imaginary board only.
- [ ] Give the other side its turn under the opponent rule above.
- [ ] Repeat until four half-moves are stored, or the game has ended.
- [ ] Keep every imaginary position and the reason for its chosen move.
- [ ] Step backward and forward through those four positions.
- [ ] Compare more than one four-move line when asked.
- [ ] Restore the real position when imagination ends.
- [ ] Repeat the run with the same settings and get the same moves.

**Done when:** four imaginary half-moves are stored and the real game FEN is unchanged.

## Milestone 8 — The two theoretical lists

After each imaginary half-move:

- [ ] Rank all 20 strategies again and store that Theoretical Strategy Forming List.
- [ ] Rank targets again and store that Theoretical Greatest Target List.
- [ ] Record which scores rose, fell, appeared, or disappeared, including captures.
- [ ] Compare each step with the previous imaginary step and with the real lists.

**Done when:** a person can inspect all four steps and see both theoretical lists change while both real lists stay fixed.

## Milestone 9 — A simple chess view

Use text first. A 3D chessboard can wait.

- [ ] Show the real board, the reference strategy, and the imaginary board with different labels.
- [ ] Show all four lists, the five-move window, and gained, lost, and unchanged squares.
- [ ] Show which of the four imaginary steps is on screen, and why that move was chosen.
- [ ] Switch among saved imaginary lines.
- [ ] Leave the real position unchanged while browsing.

**Done when:** the chess reasoning path can be read from this view without guessing which board is real.

## Milestone 10 — Remove chess and put it back

- [ ] Keep chess rules, strategy files, and piece names inside the chess adapter.
- [ ] Start the calculator with no chess adapter and run the tiny application.
- [ ] Connect chess, run Milestones 5 through 8, disconnect chess, and run the tiny application again.
- [ ] Clear calculator state when the application changes.

**Done when:** disconnecting chess leaves the tiny application working, with no chess state left behind.

## Milestone 11 — AI Vision, starting with a simple shape

The first vision target is a measured test shape, not a person. Person matching waits until the simple shape meets the completion line.

- [ ] Define the observation as measurements the calculator can read.
- [ ] Represent the model with position, orientation, and the adjustments that are allowed.
- [ ] Measure the difference between the observation and the model. Keep that error separate from the match score.
- [ ] Rank visual patterns on the Strategy Forming List.
- [ ] Rank the model parts that most affect the match on the Greatest Target List.
- [ ] Copy the model, try four imaginary adjustments, and refresh the two theoretical lists after each one.
- [ ] Change the real model only after an adjustment is accepted.
- [ ] Show the model in Unity after the text result is correct.

**Done when:** chess can be disconnected, the vision adapter can be connected, and the same calculator produces the four lists and four imaginary adjustments for a simple shape.

## Milestone 12 — Grid board

Use the existing grid project. Record its repository before writing adapter code. Preserve its rules, its tests, and the split between what an agent has seen and what it has not seen.

- [ ] Supply agent locations, known obstacles, legal steps, observations, predictions, and the belief map as separate inputs.
- [ ] Define grid patterns and grid targets, such as a destination, a safe step, or a blocking obstacle.
- [ ] Rank strategies and targets, then simulate four legal steps on a copy.
- [ ] Refresh both theoretical lists after each step.
- [ ] When an observation disagrees with a prediction, update the belief from the observation and choose again.
- [ ] Give the prediction path only information that agent has observed.
- [ ] Treat an obstacle that has not appeared yet as unknown.
- [ ] Compare adapter results with the grid project's own baseline and run its existing tests.

**Done when:** vision can be disconnected, the grid adapter can be connected, and the calculator core is unchanged.

## Milestone 13 — One improvement, three applications

- [ ] Change one generic part of the calculator, such as how tied scores are ordered.
- [ ] Run the tiny application, chess, vision, and grid tests.
- [ ] Record whether each result got better, stayed the same, or got worse.
- [ ] Keep the change only when no application regresses.
- [ ] Leave chess knowledge, vision measurements, and grid rules in their own adapters.

**Done when:** the recorded results show the same calculator change was tested on every connected application.

## Milestone 14 — One program, then a release

The program offers Chess, AI Vision, and Grid Board. Each screen shows the application name, the real view, the reference pattern, both real lists, the imaginary view, both theoretical lists, the four imagined actions, and the reasons.

- [ ] Document how to run the calculator and how to connect each application.
- [ ] Document See–Think–Do, the four lists, the four imaginary actions, and the difference between a measurement, a prediction, and a chosen action.
- [ ] Document the score limit: a score is not yet a probability.
- [ ] Keep the links to the two archived chess repositories and the pinned commit `c5730c0`.
- [ ] Mark each milestone complete or experimental.
- [ ] Run the full test set and tag the release.

**Done when:** the three demonstrations below pass on that tag.

## Acceptance

**Chess.** Connect chess. Show the real board, one reference strategy, and both real lists. Imagine four legal half-moves. Show both theoretical lists after each half-move. The real game is unchanged.

**Vision.** Disconnect chess and connect vision. Compare a simple test shape with the model. Produce the same four lists and four imaginary adjustments. The real model changes only after an adjustment is accepted.

**Grid.** Disconnect vision and connect the grid. Rank strategies and targets, imagine four legal steps, and update the theoretical lists. A prediction that disagrees with an observation causes a new choice. Hidden obstacles stay hidden from an agent that has not seen them.

**Shared calculator.** One generic change is tested on all three. Application rules stay in their adapters. A change that breaks an existing test is reverted.
