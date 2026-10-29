# Chess review and fixes

Reviewed the maintained Python engine, command flow, study reports, piece
tracking, move memory, calculator code, strategy records, and their tests.
The Unity scripts were also inspected. Generated Unity files, virtual-environment
dependencies, binary assets, and editor caches are outside this source review.
The ignored `chess_source` checkout and archived upstream repositories remain
reference material; fixes are in this repository's `chess_module` copy.
Existing uncommitted work was preserved.

## Verified defects corrected

| Area | Defect and corrected behavior |
| --- | --- |
| Repetition | A bishop, queen, or king able to move onto an en passant target could incorrectly make it part of the repetition key. Only a legal pawn en passant capture now counts. |
| Draw claims | Previewing a pawn move or capture could hide a draw already claimable in the current position. Current-position claims are checked first. Completed games cannot be replaced by a claim. |
| Checkmate | Direct automatic-draw checks could report the 75-move rule instead of checkmate. Checkmate takes precedence. |
| Applying moves | Direct calls could move through blockers, expose the mover's king, or silently promote without a choice. Illegal moves now leave all state unchanged. |
| Castling and en passant helpers | Direct castling validation now checks that the king exists and is not in check. En passant recognition also checks pawn movement and rank. |
| Search | LOOP, forced-mate search, TRACE, REAL routes, and reply reports could continue past automatic draws and lose repetition history. Real simulations now record history and stop at terminal positions. Forced results account for the defender claiming a draw. |
| Reports and tracking | Invalid moves could produce facts about moves that never occurred or corrupt piece IDs. CALC, reply reports, tracker commits, and memory entries reject illegal moves. |
| Captures in memory | Captured pieces' formerly available destinations were omitted from LOST. They are now included. |
| Resignation | A resignation always awarded a win, even to a bare king. Proven insufficient-mating-material cases now produce a draw. Opponent material is considered when assessing lone minors. |
| FEN | Consecutive empty-square digits, a nonzero clock with an en passant target, and unaccounted same-color bishop promotions are rejected atomically. |
| Public inputs | Wrong-type move/square inputs and promotion values are rejected. Public LOOP, REAL-route, and exchange-report limits are checked before allocation or recursive search. |
| Strategy references | Corrected castling rights after White castled, the side to move in the open-file check, and the extra bishop and blocking pawn in the pin example. All 20 reference FENs load successfully; the pin actually prevents the knight leaving its line. |
| Shared memory | A memory window now owns a copy of supplied history, trims in one operation, and rejects a subsequently invalid limit before consuming a pending item. Shape observations freeze supplied rows so outside list edits cannot change saved observations. |

Rules reference: [FIDE Laws of Chess](https://handbook.fide.com/chapter/E012023),
particularly articles 5.1.2, 9.2, 9.3, and 9.6.

## Validation

From the repository root, using the configured project interpreter:

```sh
python -m unittest discover -s chess_module -p 'test_*.py'
python -m unittest test_calculator test_shape
```

- Chess: 78 tests, including 23 added regression tests.
- Calculator and shapes: 38 tests, including 3 added regressions.
- Move generation matches starting-position counts 20, 400, and 8,902;
  Kiwipete counts 48 and 2,039; and rook-endgame counts 14, 191, and 2,812.
- Tests cover input rejection without mutation, checkmate/draw precedence,
  repetition through simulated moves, draw claims, pins, castling, en passant,
  promotions, resignation, captured-piece memory, and saved-state isolation.

## Limits of this review

Passing these checks is not proof of the absence of all bugs or security issues.
The maintained Python application has no network server, shell execution,
dynamic evaluation of commands, or untrusted pickle loading in the reviewed
code. The input and search-limit checks are defensive hardening, not a claim
that a remote exploit was demonstrated. Installed dependencies and Unity
runtime behavior were not audited or executed.

Dead-position and resignation adjudication use conservative material proofs.
They do not solve every possible blocked position in which no legal sequence
can ever produce mate. FEN validation checks structural and common legality
conditions, not complete reachability from the starting position. Exhaustive
analysis at allowed depths can still be expensive. PASS reports intentionally
let one side move repeatedly and are hypothetical, as labeled in their output.

`make_move` keeps its default convention of not appending history. Callers
simulating actual turns should pass `record_history=True`, or explicitly call
`record_position()` after each finalized move as the CLI does. Geometric move
generation remains separate from game-end adjudication so mobility reports
and move-count tests can examine positions independently of game results.
