# AI-Vision-3D

One calculator for pattern recognition, target ranking, and short simulations. Chess and visual object recognition are separate applications. Each one supplies its own data, and both use the same reasoning system.

Chess facts come from [chess-python](https://github.com/IWatchSheep/chess-python). That program is the Python form of [chess-c99](https://github.com/IWatchSheep/chess-c99) version 16. The C repository stays archived. `chess-python` measures the position and leaves the choice of a move to this calculator.

## Step 1 — Identify available moves

Select a chess piece. List every legal move, and count the squares it can reach.

chess-python already does this. Typing a square lists that piece’s legal destinations. The rules are the full game. Move counts on the six standard test positions match the published numbers, including 197,281 sequences from the start at four plies.

## Step 2 — Examine move effects

Move the piece onto one available square for a moment. Watch how that changes every other piece: which squares are now blocked, and which squares are now open.

chess-python already does this for one previewed move. The preview lists every other piece’s legal squares before and after the move, then the squares gained, lost, and unchanged. The `R` report adds protections, attacks, and threats. Nothing is played until `F`.

## Step 3 — Remember five moves

Store the board before and after each of the last five moves: the previous four, and the current move. Compare those five moves to see how the board has changed.

chess-python does this with the `memory` command.

- The current move is the preview waiting for `F`.
- `F` stores that preview. The list keeps the latest 4 played moves, oldest first.
- Each entry stores the move, the side that moved, the FEN before, the FEN after, squares gained, squares lost, the unchanged-destination count, and the squares whose piece changed.
- The last line compares the oldest before-position with the latest after-position.
- `P` and `N` drop the preview and leave the played moves in place.
- `restart`, and a FEN that loads, clear the window. A rejected FEN leaves it in place.

The draw-rule history is a different list. A pawn move or a capture clears that list. `memory` keeps its own window.

## Step 4 — Build a reusable strategy and target calculator

Grok defines 20 chess strategies as visual arrangements of the board.

Show a reference strategy on the left and the current board on the right. Score how closely the current board matches each strategy. Rank those matches from strongest to weakest in the **Strategy Forming List**. Rank the pieces that matter most in the **Greatest Target Pieces List**.

Use **See–Think–Do** to choose each of four simulated future moves. After every simulated move, update the **Theoretical Strategy Forming List** and the **Theoretical Greatest Target Pieces List**.

This ranking is the remaining work. chess-python measures chess facts and does not choose a move. Its reports are inputs to the lists above:

- Squares gained, lost, and unchanged
- The five-move window from `memory`
- Legal replies, and whether a reply stops a threat, leaves it, or allows one
- Lines of future moves within a ply limit, and whether a goal is forced or only possible
- Protection, attacks, and threats
- Goal squares and the routes that reach them
- Fact-by-fact comparison of candidate moves

The strategy and target calculator is its own component. The chess application supplies board positions, rules, strategies, and targets as inputs.

Other applications supply their own shapes, strategies, and targets.

A visual AI application, for example, supplies a person it has observed and a 3D doll model. The calculator compares their shapes and returns a match confidence. Using **See–Think–Do**, it chooses four simulated adjustments to the doll. After each adjustment, it recalculates the theoretical strategies and targets.

## How the projects connect

**chess-python** supplies chess rules, legal moves, board states, move consequences, and the five-move window.

**chess-c99** is the archived C original. The same `chess.c` is stored in chess-python as `chess.txt`.

**The AI-Vision-3D calculator** matches patterns, ranks strategies, ranks targets, and runs the four See–Think–Do simulations.

**Unity** is the 3D view. The project in this repository is the bidirectional motion scene. The visual application still supplies an observed shape and a 3D model. A 3D chessboard can use the same calculator later.

Read the chess reports from chess-python with the commands it already accepts:

- `fen <FEN>` sets the board, and `fen` prints it
- a square, then a destination, previews a move; `F` plays it
- `memory` prints the 4 played moves and the current preview
- `R` prints the fact report
- `replies` lists the other side’s answers
- `loop N` lists future lines
- `goal` and `routes` measure target squares
- `compare` lines up candidate moves fact by fact

**Goal:** One reusable calculator that accepts different applications, recognizes patterns, evaluates targets, simulates possible changes, and supports decisions. Chess and visual object recognition remain separate applications on that shared reasoning system.
