# AI-Vision-3D

One calculator for pattern recognition, target ranking, and short simulations. Chess and visual object recognition are separate applications. Each one supplies its own data, and both use the same reasoning system.

Chess data comes from [chess-c99](https://github.com/IWatchSheep/chess-c99), version 16. That repository stays separate and unchanged. It is archived. This project reads its reports and does the ranking work the chess program leaves open.

## Step 1 — Identify available moves

Select a chess piece. List every legal move, and count the squares it can reach.

chess-c99 already does this. Typing a square lists that piece’s legal destinations. The rules are the full game, checked against standard move-count positions.

## Step 2 — Examine move effects

Move the piece onto one available square for a moment. Watch how that changes every other piece: which squares are now blocked, and which squares are now open.

chess-c99 already does this for one previewed move. The preview lists every other piece’s legal squares before and after the move, then the squares gained, lost, and unchanged. The `R` report adds protections, attacks, and threats. Nothing is played until the move is confirmed.

## Step 3 — Remember five moves

Store the board before and after each of the last five moves: the previous four, and the current move. Compare those five moves to see how the board has changed.

This comparison is new work for AI-Vision-3D. chess-c99 keeps position keys so it can apply the draw rules, including fivefold repetition. A pawn move or a capture clears that record. It does not store or compare a window of the last five moves.

## Step 4 — Build a reusable strategy and target calculator

Grok defines 20 chess strategies as visual arrangements of the board.

Show a reference strategy on the left and the current board on the right. Score how closely the current board matches each strategy. Rank those matches from strongest to weakest in the **Strategy Forming List**. Rank the pieces that matter most in the **Greatest Target Pieces List**.

Use **See–Think–Do** to choose each of four simulated future moves. After every simulated move, update the **Theoretical Strategy Forming List** and the **Theoretical Greatest Target Pieces List**.

This ranking is new. chess-c99 measures chess facts and does not choose a move. Its reports are inputs to the lists above:

- Squares gained, lost, and unchanged
- Legal replies, and whether a reply stops a threat, leaves it, or allows one
- Lines of future moves within a ply limit, and whether a goal is forced or only possible
- Protection, attacks, and threats
- Goal squares and the routes that reach them
- Fact-by-fact comparison of candidate moves

The strategy and target calculator is its own component. The chess application supplies board positions, rules, strategies, and targets as inputs.

Other applications supply their own shapes, strategies, and targets.

A visual AI application, for example, supplies a person it has observed and a 3D doll model. The calculator compares their shapes and returns a match confidence. Using **See–Think–Do**, it chooses four simulated adjustments to the doll. After each adjustment, it recalculates the theoretical strategies and targets.

## How the projects connect

**chess-c99** supplies chess rules, legal moves, board states, and the consequences of a move.

**The AI-Vision-3D calculator** matches patterns, ranks strategies, ranks targets, and runs the four See–Think–Do simulations.

**Unity** is the 3D view. The project already in this repository is the bidirectional motion scene. The visual application still supplies an observed shape and a 3D model. A 3D chessboard can use the same calculator later.

The first adapter is the Python program in this repository. It sends the engine commands it already accepts and reads the text reports back:

- `fen <FEN>` sets the board, and `fen` prints it
- a square, then a destination, previews a move
- `R` prints the fact report
- `replies` lists the other side’s answers
- `loop N` lists future lines
- `goal` and `routes` measure target squares
- `compare` lines up candidate moves fact by fact

A later structured interface can carry the same facts without parsing the text. The chess engine stays as it is.

**Goal:** One reusable calculator that accepts different applications, recognizes patterns, evaluates targets, simulates possible changes, and supports decisions. Chess and visual object recognition remain separate applications on that shared reasoning system.
