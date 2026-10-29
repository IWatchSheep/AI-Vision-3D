# Source review — 2026-10-29

Reviewed every maintained Python source and test file in the project root,
`calculator/`, and `chess_module/`, including the existing untracked blueprint
files. Reviewed all C# sources in the Unity project, its motion scene, package
configuration, and relevant project settings. Existing workspace edits were
preserved.

The ignored `chess_source/` checkout is the archived reference described in
the README. Its differences were inspected; it was not changed or certified.
The archived C listing, installed dependencies, Unity Library/PackageCache,
editor caches, Git internals, and binary assets are outside this source audit.
This is not a claim that every file on disk was audited or that no bugs remain.

## Issues fixed in this review

| Area | Finding and fix |
| --- | --- |
| Package launch | `python -m chess_module.main` failed to resolve `chess_engine`. The root launcher also loaded the engine under a second module name by modifying `sys.path`. Package imports now use the maintained package; direct script launch remains supported. |
| Misleading previews and reports | Several public preview, support, distance, and goal functions reported illegal moves even though `make_move` refused to play them. They now reject the move before printing or changing preview state. |
| PASS state mutation | An illegal PASS move could still change the live turn and clear en passant rights. The hypothetical move is validated on a copy before any state changes. |
| Goal search depth | A depth-one REAL goal report could count protection uncovered by the opponent's reply, outside the requested horizon. Replies are now excluded at that depth. |
| Search input hardening | Public recursive mate, PASS-distance, and exchange helpers could bypass the CLI's limits. They now enforce bounded integer depths. Goal square counts/indices and candidate comparisons are validated before expensive work. These are local defensive checks; no remote exploit was demonstrated. |
| Memory atomicity | `replace_past` replaced history before rejecting an invalid changed limit. A rejected replacement now preserves existing history and the pending preview. |
| En passant display | The UI capture helper matched only the EP target, without validating pawn geometry or the victim. It now reuses the engine's en passant recognition. |
| Windows console | ctypes defaulted Win32 console handles to a 32-bit integer. Explicit handle and argument types prevent truncation on 64-bit Windows. |
| Motion timing | Every movement/rest boundary discarded leftover elapsed time and zero rest time inserted an extra stopped frame. A complete-cycle clock preserves time across transitions and long frames. |
| Documentation | The root README still described `main.py` as a status message. It now documents the working launch modes and demonstrations. |

The earlier chess-rule audit is preserved in [chess_module/AUDIT.md](chess_module/AUDIT.md).

## Verification

Using PyCharm's configured Python interpreter:

```powershell
python -m unittest discover -q
python -m unittest discover -s chess_module -q
```

- Root suite: **81 passed**, including 22 regression tests.
- Chess suite: **79 passed**, including existing move-generation count checks.
- Total test suite: **160 tests passing cleanly**.
- Regression tests exercise all three launch modes in fresh processes.
- Unity **6000.6.7f1** completed a headless import/compile and then executed
  **six passing timing checks** against the actual CharacterMotion component.
- `git diff --check` passed.

Repeat the Unity timing checks with your installed editor executable:

```powershell
& 'C:\Program Files\Unity\Hub\Editor\6000.6.7f1\Editor\Unity.exe' `
  -batchmode -nographics -quit -projectPath "$PWD/unity/AI-Vision-Motion" `
  -executeMethod CharacterMotionChecks.Run -logFile -
```

The editor-only checks cover endpoint rest, leftover time, crossing a complete
cycle in one frame, uneven frame intervals, zero rest, and zero travel duration.
Rendering and interactive play were not manually exercised. Dependency
vulnerabilities and complete chess-position reachability were not audited.
Allowed exhaustive search depths can still take substantial time.

## Follow-up review — 2026-10-29

Preserved the existing workspace changes and checked the maintained calculator,
engine, command, report, and Unity source paths again. This follow-up corrected:

- CALC skipped captured pieces when computing LOST destinations and U2 counts.
  Their before-move mobility now contributes to the loss, including en passant.
- REAL goal search could label a goal POSSIBLE when it was forced on the
  opponent's last permitted reply. Both the first-move classifier and recursive
  search now include even-ply horizons while respecting the requested depth.
- The exported sliding-move generator accepted zero/fractional direction vectors,
  which could loop indefinitely on an empty square. It now validates unit ray
  directions and bounds each ray to seven steps. This is defensive hardening of
  a local helper; the normal generator supplied valid directions already.
- Coordinate underflow and unvalidated start squares in `consider_move`:
  `consider_move` checked only `in_bounds(er, ec)` but accessed `board.grid[sr][sc]`,
  which allowed negative index wrapping (Python underflow) or out-of-bounds `IndexError`.
  It now explicitly requires `in_bounds(sr, sc) and in_bounds(er, ec)`.
- Starting coordinate bounds guards across piece move generators:
  `generate_piece_moves`, `generate_pawn_moves`, `generate_knight_moves`,
  `generate_king_moves`, and `generate_sliding_moves` now guard `in_bounds(row, col)`.
- UI text formatting underflow:
  `next_chunk` in `ui_board.py` clamped negative starting index `at < 0` to 0, preventing
  negative indexing wrapping from the end of the text.
- Exchange report square bounds validation:
  `exchange_report` in `study/exchange_core.py` now enforces `0 <= sq < TOTAL_SQUARES`,
  raising `ValueError` for negative or out-of-bounds square indices.
- Study goal distance square bounds and depth underflow:
  `piece_distance`, `side_within`, and `side_distance` in `study/goal_basics.py` now guard
  against out-of-bounds/negative square indices and prevent passing negative `rem_max` into
  recursive `piece_distance` calls.
- Game tree search `zero_k` parameter validation:
  `loop_report` in `study/search.py` now validates that `zero_k` is a non-negative integer.
- CLI state machine desynchronization on analysis commands:
  `handle_calc_report`, `handle_replies`, and `handle_support` in `cli_analysis_cmds.py` and
  `cli_goal_cmds.py` unconditionally invoked `invalidate_preview()` when no preview was active,
  prematurely moving `session.step` to `Step.PICK_DESTINATION` without a selected piece.
  Calls are now gated on `session.preview_shown`, and `session.invalidate_preview()` in `cli_session.py`
  safely falls back to `Step.PICK_PIECE` if `not self.has_selection()`.
- Study & move type safety defects:
  - `pieces_on_square` in `study/common.py` now checks `not isinstance(sq, bool)` to reject booleans
    which would otherwise index squares 0 or 1.
  - `captured_type` in `study/exchange_core.py` and `move_distance` in `study/common.py` now guard
    against non-`Move` instances and out-of-bounds coordinates before accessing attributes.
  - `piece_value` and `promotion_rank` safely handle non-string inputs.
  - `Move.uci` guards against non-string `promotion` attributes before calling `.lower()`.
  - `parse_bounded_int` in `cli_session.py`, `sanitize_display_text`, and `parse_goal` in `study/goal_basics.py`
    safely reject non-string inputs.
- `PatternWindow` interface consistency & validation:
  Added `clear_current()` to `PatternWindow` in `calculator/pattern.py`, and added type validation
  on `past`, `current`, and `set_current()` ensuring items are valid `CompareResult` instances,
  matching `ShapeWindow`.

Added 12 targeted regression tests to `test_audit_regressions.py` covering all the above
overflow, underflow, boundary check, state machine synchronization, and type-safety scenarios. Current verification:
**81 root tests and 79 chess tests pass (160 total)**, with `git diff --check` clean.

No dynamic execution, shell commands, network listener, or unsafe object loading
was found in the maintained application paths inspected. Dependencies, ignored
reference sources, generated files, and a fresh Unity runtime run are outside
this follow-up. These checks do not prove that every bug or security issue is
absent; the conservative adjudication/search limits described above still apply.

## Latest review and verification — 2026-10-29

This review covered maintained Python application code, report APIs, launchers,
calculator data and tests, and Unity C# sources and project configuration.
The ignored archived `chess_source/` reference, dependencies, generated Unity
files, binary assets, and Git internals are outside the maintained-source scope.
No archived repository was modified. The figures below supersede the earlier
test counts in this document.

Additional fixes:

- Exchange minimax and sequence totals omitted the material created by
  promotion. For example, `g7xh8=Q` followed by `Kxh8` against a rook was
  incorrectly classified as only POSSIBLE NONNEGATIVE. The pawn's promotion
  gains eight points, leaving a net gain of four even after recapture. Both
  colors now include promotion gains, and the sequence report explains them.
- Direct calls to COMPARE, TRACE, ORDER, CALC, REPLIES, goal marks, and follow-up
  PASS reports did not consistently share one work budget across subreports.
  Public entry points now establish a shared budget; iterative mate scans,
  replies and trace validation charge work to it. Timeout failures preserve
  the board and tracker. TRACE also rejects bad input types and excessive text
  before splitting it.
- Forced mate search (`mate_forced` and `first_move_forces` in `study/search.py`)
  now calls `search_checkpoint()` inside branch iterations so move generation and
  recursive mate checks cooperatively respect node/time quotas.
- Blueprint play could crash on `doll ²` because `isdigit()` accepts characters
  that `int()` cannot parse. Numeric selection now accepts bounded ASCII
  digits. Oversized and non-text commands are rejected without changing state.
- Blueprint imagination accepted unlimited supplied moves and eagerly exhausted
  generators. Interactive lines and automatic ply counts now enforce four
  moves; the lower-level replay helper preserves longer rule demonstrations
  with a 512-ply limit. Infinite iterables are rejected after bounded reads.
- `calculator/play_build.py`:
  - `spoken_move()` guarded against unformatted messages, short strings (< 4 parts),
    and refused/illegal `MoveResult` instances, eliminating `IndexError`.
  - `_mark_at()` validated algebraic coordinate bounds, raising `ValueError` for
    malformed squares, non-strings, or out-of-range rows/columns.
- `chess_module/chess_engine/cli_session.py`:
  - `parse_bounded_int()` and `sanitize_display_text()` enforce strict integer/bool
    and length bounds.
  - `GameSession.select_piece()` enforces board bounds `in_bounds(row, col)`.
  - `GameSession.clear_selection()`, `clear_preview_keep_piece()`, and
    `invalidate_preview()` reset `preview_move` and `pending_promotion` to inactive
    state, preventing stale coordinates from persisting across flow steps.
- `chess_module/chess_engine/cli_goal_cmds.py`:
  - Removed UTF-8 Byte Order Mark (`\xef\xbb\xbf`) that caused syntax/AST parse errors
    when parsed by code analysis and linter tools.
- `chess_module/chess_engine/study/distance_order.py`:
  - `distance_selection()` and `distance_lines()` now guard `board.grid[r][c].is_empty`,
    preventing null byte (`\x00`) string printing and empty piece pseudo-turn processing.
- `chess_module/chess_engine/cli_move_cmds.py`:
  - `handle_game_control()` now safely checks `session.preview_move is not None and getattr(session.preview_move, 'sr', -1) >= 0`
    during draw claims to eliminate `AttributeError` risk if preview state is cleared or malformed.
- `unity/AI-Vision-Motion/Assets/Scripts/CharacterMotion.cs`:
  - Added guards against `float.IsNaN(deltaTime)`, `float.IsInfinity(deltaTime)`,
    and negative `deltaTime < 0f`, plus negative remainder wrap-around protection.
- Blueprint play now exits cleanly on Ctrl+C.
- Per-piece mobility and preview lists generated every piece's legal moves
  repeatedly. They now generate the requested piece's moves only, with regression
  checks against full move generation for both colors, castling, promotion and
  en passant.
- The chess README referenced a nonexistent local `chess.txt`; it now points to
  the archived repository. The root README explicitly lists both test commands.

Verification with PyCharm's configured Python 3.15.2 virtual environment:

```powershell
python -m unittest discover -v
python -m unittest discover -s chess_module -v
```

- **119 root tests passed**, including 29 review and audit regressions in `test_audit_regressions.py` and 15 in `test_review_regressions.py`.
- **81 chess tests passed**: **200 Python tests total**.
- Fresh subprocesses play Fool's Mate through select, preview and finalize in
  all three launch modes, checking clean exit and the winner message.
- Existing suites exercise move-generation counts, seeded games, castling,
  en passant, promotion, pins, mate, stalemate, draw claims, automatic draws,
  repetition, preview isolation, memory, search limits and calculator behavior.
- Unity 6000.6.7f1 completed headless execution passing **nine CharacterMotion timing checks**
  (endpoint rest, leftover time, complete-cycle frames, uneven intervals, zero rest,
  zero travel duration, NaN delta, Infinity delta, and negative delta) with exit code 0.

The security fixes address malformed local input, unvalidated bounds, state desynchronization,
and excessive computation; no remote exploit was demonstrated. Installed dependency
vulnerabilities, complete position reachability, all possible dead positions, and manual visual
playtesting are not certified. Search deadlines are cooperative, and passing
tests does not establish that every bug or security issue is absent.
