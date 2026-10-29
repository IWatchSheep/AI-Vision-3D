"""Hardcoded chess strategy dolls (posed pictures on record).

ASCII boards are the source of truth. Joints are written down for a
later update; printing them must not change any board string.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Strategy:
    """One strategy doll: a posed picture held up against a seen board."""

    number: int
    id: str
    name: str
    stage: str
    sentence: str
    board: list[str]
    fen: str
    joints: list[str] = field(default_factory=list)


def _s(
    number: int,
    id_: str,
    name: str,
    stage: str,
    sentence: str,
    board: list[str],
    fen: str,
    joints: list[str],
) -> Strategy:
    return Strategy(
        number=number,
        id=id_,
        name=name,
        stage=stage,
        sentence=sentence,
        board=list(board),
        fen=fen,
        joints=list(joints),
    )


STRATEGIES: list[Strategy] = [
    _s(
        1,
        "kings-pawn-promotion",
        "King's pawn promotion",
        "beginning doll",
        "The king's pawn has reached the square before promotion. Hold this picture against a game that is still at the start.",
        [
            ".......k",
            "....P...",
            "........",
            "........",
            "........",
            "........",
            "........",
            "....K...",
        ],
        "7k/4P3/8/8/8/8/8/4K3 w - - 0 1",
        ["the white pawn on e7 may later stand on e8 as a queen."],
    ),
    _s(
        2,
        "develop-to-the-center",
        "Develop to the center",
        "formed end",
        "Pawns, knights, and bishops have taken their arranged central places.",
        [
            "r.bqk..r",
            "ppp..ppp",
            "..np.n..",
            "..b.p...",
            "..B.P...",
            "..NP.N..",
            "PPP..PPP",
            "R.BQK..R",
        ],
        "r1bqk2r/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 2 6",
        [
            "the bishop on c4 may later stand on b5.",
            "The knight on f3 may later stand on e5 or g5.",
        ],
    ),
    _s(
        3,
        "starting-array",
        "Starting array",
        "the real board at the beginning",
        "Every piece is still on its home square.",
        [
            "rnbqkbnr",
            "pppppppp",
            "........",
            "........",
            "........",
            "........",
            "PPPPPPPP",
            "RNBQKBNR",
        ],
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        [
            "the pawn on e2 may later stand on e4.",
            "The pawn on d2 may later stand on d4.",
        ],
    ),
    _s(
        4,
        "king-pawn-first-step",
        "King pawn first step",
        "first step",
        "The king's pawn has stepped to e4.",
        [
            "rnbqkbnr",
            "pppppppp",
            "........",
            "........",
            "....P...",
            "........",
            "PPPP.PPP",
            "RNBQKBNR",
        ],
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        ["the pawn on e4 may later stand on e5."],
    ),
    _s(
        5,
        "queen-pawn-first-step",
        "Queen pawn first step",
        "first step",
        "The queen's pawn has stepped to d4.",
        [
            "rnbqkbnr",
            "pppppppp",
            "........",
            "........",
            "...P....",
            "........",
            "PPP.PPPP",
            "RNBQKBNR",
        ],
        "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1",
        ["the pawn on d4 may later stand on d5."],
    ),
    _s(
        6,
        "both-center-pawns",
        "Both center pawns",
        "middle",
        "White's d-pawn and e-pawn both stand in the center, facing Black's e-pawn.",
        [
            "rnbqkbnr",
            "pppp.ppp",
            "........",
            "....p...",
            "...PP...",
            "........",
            "PPP..PPP",
            "RNBQKBNR",
        ],
        "rnbqkbnr/pppp1ppp/8/4p3/3PP3/8/PPP2PPP/RNBQKBNR b KQkq d3 0 2",
        ["the pawn on d4 may later stand on d5."],
    ),
    _s(
        7,
        "fianchetto-kingside",
        "Fianchetto kingside",
        "formed",
        "The light-squared bishop stands on g2, with the knight on f3.",
        [
            "rnbqkbnr",
            "pppppppp",
            "........",
            "........",
            "........",
            ".....N..",
            "PPPPPPBP",
            "RNBQK..R",
        ],
        "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPBP/RNBQK2R w KQkq - 2 3",
        ["the bishop on g2 may later stand on f3 or h3."],
    ),
    _s(
        8,
        "kingside-castle",
        "Kingside castle",
        "formed",
        "White has castled short. The king is on g1 and a rook is on f1.",
        [
            "r.bqk.nr",
            "pppp.ppp",
            "..n.....",
            "..b.p...",
            "..B.P...",
            ".....N..",
            "PPPP.PPP",
            "RNBQ.RK.",
        ],
        "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQ1RK1 b KQkq - 5 4",
        [
            "the king on g1 stays.",
            "The bishop on c4 may later stand on b5.",
        ],
    ),
    _s(
        9,
        "queenside-castle",
        "Queenside castle",
        "formed",
        "White has castled long. The king is on c1 and a rook is on d1.",
        [
            "rnbqk..r",
            "pp..bppp",
            "..p..n..",
            "...p....",
            "...P.B..",
            "..N.....",
            "PPPQPPPP",
            "..KR.BNR",
        ],
        "rnbqk2r/pp2bppp/2p2n2/3p4/3P1B2/2N5/PPPQPPPP/2KR1BNR b kq - 6 6",
        [
            "the king on c1 stays.",
            "The bishop on f4 may later stand on e5 or g5.",
        ],
    ),
    _s(
        10,
        "isolated-queen-pawn",
        "Isolated queen pawn",
        "formed",
        "White's d-pawn has no friendly pawn on the c-file or the e-file.",
        [
            "rnbqkb.r",
            "pp...ppp",
            "..p.pn..",
            "........",
            "...P....",
            "..N..N..",
            "PP..BPPP",
            "R.BQK..R",
        ],
        "rnbqkb1r/pp3ppp/2p1pn2/8/3P4/2N2N2/PP2BPPP/R1BQK2R w KQkq - 0 8",
        ["the pawn on d4 may later stand on d5."],
    ),
    _s(
        11,
        "passed-pawn",
        "Passed pawn",
        "formed",
        "White's e-pawn has no enemy pawn on the d, e, or f files in front of it.",
        [
            "....k...",
            "p......p",
            "........",
            "....P...",
            "........",
            "........",
            "........",
            "....K...",
        ],
        "4k3/p6p/8/4P3/8/8/8/4K3 w - - 0 1",
        ["the pawn on e5 may later stand on e6 or e7."],
    ),
    _s(
        12,
        "rook-on-the-open-file",
        "Rook on the open file",
        "formed",
        "A white rook stands on the open e-file.",
        [
            "....k...",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
            "....R.K.",
        ],
        "4k3/8/8/8/8/8/8/4R1K1 w - - 0 1",
        ["the rook on e1 may later stand on e4 or e8."],
    ),
    _s(
        13,
        "bishop-pair",
        "Bishop pair",
        "formed",
        "White's two bishops stand on open diagonals, c4 and f4.",
        [
            "....k...",
            "........",
            "........",
            "........",
            "..B..B..",
            "........",
            "........",
            "....K...",
        ],
        "4k3/8/8/8/2B2B2/8/8/4K3 w - - 0 1",
        [
            "the bishop on c4 may later stand on b5 or d5.",
            "The bishop on f4 may later stand on e5 or g5.",
        ],
    ),
    _s(
        14,
        "knight-outpost",
        "Knight outpost",
        "formed",
        "A knight on d5 is supported by the pawn on e4.",
        [
            "....k...",
            "........",
            "........",
            "...N....",
            "....P...",
            "........",
            "........",
            "....K...",
        ],
        "4k3/8/8/3N4/4P3/8/8/4K3 w - - 0 1",
        ["the knight on d5 may later stand on c7, e7, b6, or f6."],
    ),
    _s(
        15,
        "pin-against-the-king",
        "Pin against the king",
        "formed",
        "The bishop on b5 looks through the knight on c6 toward the king on e8.",
        [
            "r.bqkbnr",
            "pppp.ppp",
            "..n.....",
            ".B..p...",
            "....P...",
            ".....N..",
            "PPPP.PPP",
            "RNBQKB.R",
        ],
        "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3",
        ["the bishop on b5 may later stand on a4."],
    ),
    _s(
        16,
        "back-rank-pressure",
        "Back rank pressure",
        "formed",
        "A white rook has reached e8 beside the black king, whose own pawns stand on f7, g7, and h7.",
        [
            "....R.k.",
            ".....ppp",
            "........",
            "........",
            "........",
            "........",
            "........",
            "....K...",
        ],
        "4R1k1/5ppp/8/8/8/8/8/4K3 b - - 0 1",
        ["the rook on e8 may later stand on a8, d8, or f8."],
    ),
    _s(
        17,
        "knight-fork",
        "Knight fork",
        "formed",
        "The knight on d5 attacks the black king on e7 and the black queen on b6 in the same picture.",
        [
            "........",
            "....k...",
            ".q......",
            "...N....",
            "........",
            "........",
            "........",
            "....K...",
        ],
        "8/4k3/1q6/3N4/8/8/8/4K3 b - - 0 1",
        ["the knight on d5 may later stand on e7, c7, b6, or f6."],
    ),
    _s(
        18,
        "castled-king-shelter",
        "Castled king shelter",
        "formed",
        "Both kings have castled short, each with a three-pawn shelter.",
        [
            "r.bq.rk.",
            "pppp.ppp",
            "..n..n..",
            "..b.p...",
            "..B.P...",
            ".....N..",
            "PPPP.PPP",
            "RNBQ.RK.",
        ],
        "r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQ1RK1 b - - 6 5",
        [
            "the king on g1 stays behind f2, g2, and h2.",
            "Those three pawns are the shelter joints.",
        ],
    ),
    _s(
        19,
        "queen-and-bishop-battery",
        "Queen and bishop battery",
        "formed",
        "The queen on b3 and the bishop on c4 both aim toward f7.",
        [
            "r.bqkbnr",
            "pppp.ppp",
            "..n.....",
            "....p...",
            "..B.P...",
            ".Q......",
            "PPPP.PPP",
            "RNB.K.NR",
        ],
        "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/1Q6/PPPP1PPP/RNB1K1NR b KQkq - 3 3",
        ["the queen on b3 may later stand on a4 or c2."],
    ),
    _s(
        20,
        "doubled-rooks",
        "Doubled rooks",
        "formed",
        "Two white rooks stand one behind the other on the d-file.",
        [
            "....k...",
            "........",
            "........",
            "........",
            "........",
            "........",
            "...R....",
            "...RK...",
        ],
        "4k3/8/8/8/8/8/3R4/3RK3 w - - 0 1",
        ["the rook on d2 may later stand on d7 or d8."],
    ),
]


def get_strategy(id_or_number: str | int) -> Strategy:
    """Return a strategy by id string or number."""
    for strategy in STRATEGIES:
        if strategy.id == id_or_number or strategy.number == id_or_number:
            return strategy
    raise KeyError(f"No strategy matching {id_or_number!r}")


def board_to_fen_pieces(board: list[str]) -> str:
    """Build the FEN piece-placement field from an ASCII board (rank 8 first)."""
    ranks: list[str] = []
    for row in board:
        empty = 0
        parts: list[str] = []
        for ch in row:
            if ch == ".":
                empty += 1
            else:
                if empty:
                    parts.append(str(empty))
                    empty = 0
                parts.append(ch)
        if empty:
            parts.append(str(empty))
        ranks.append("".join(parts))
    return "/".join(ranks)


def fen_piece_field(fen: str) -> str:
    """Return the piece-placement field of a FEN string."""
    return fen.split()[0]


def print_joints(strategy: Strategy) -> None:
    """Print joint sentences without changing any board string."""
    for joint in strategy.joints:
        print(joint)


def print_strategy(strategy: Strategy) -> None:
    """Print one doll: number, name, stage, sentence, board, FEN, joints."""
    print(f"{strategy.number}. {strategy.name}")
    print(f"Stage: {strategy.stage}")
    print(strategy.sentence)
    for row in strategy.board:
        print(row)
    print(f"FEN: {strategy.fen}")
    print_joints(strategy)
    print("Joints were not moved.")
