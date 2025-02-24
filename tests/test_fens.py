import pytest
from chess import Board
from chess.engine import Limit

from engine.ab_depth_prune import ABDeppeningEngine
from engine.basilisk import BasiliskEngine
from engine.board import ExtendedBoard
from engine.evaluators import V0Evaluator, V1Evaluator


@pytest.mark.parametrize("fen, expected_response", [
    # Mate in 1
    ("4k3/1R4p1/3KP2p/p7/8/6r1/PP6/8 w - - 1 2", "b7b8"),
    ("2K5/k7/8/8/1Q6/8/8/N7 w - - 105 195", ("b4b7", "b4a5")),
    # Mate in 2
    ("2R5/5ppk/7p/p2P4/4P3/2P1n1B1/r6P/7K b - - 1 1", "a2a1"),
    # Mate in 3
    ("2Q1R3/5pkp/1r2p1p1/p7/8/4PB2/P4PPP/6K1 b - - 0 1", "b6b1"),
    # Mate in 5
    ("5k2/2N2p2/2B2P2/5q2/2b5/2P1KP2/1P4rP/R2Q3R b - - 0 29", "f5e5"),
    # Material simplification
    ("6K1/8/k7/8/3Q4/2n5/P7/1r3R2 w - - 2 96", ("d4c3", "f1b1", "d4d3")),
    # Endgame simplification
    ("7r/4P3/1pn5/p1p2kB1/8/2P3K1/PPP5/4R3 w - - 2 34", ("e7e8q", "e7e8r", "e7e8b", "e7e8n")),
    ("r1b5/pp1p4/5P2/2p5/5kPr/1P6/PRPP1P1P/4R1K1 w - - 1 28", ("f6f7",)),
    # Defend against mate
    ("r5k1/p4ppr/2n5/1N4p1/4P3/3PQPPb/PqP4P/R3R1K1 w - - 0 25", ("a1b1", "a2a4", "b5c7", "b5d6")), # Much too shallow
    # Tactical
    ("r1b1kb1r/3ppqpp/np6/1B2B3/P2PN3/1Q2P2P/8/2R1K1R1 w q - 0 27", ("c1c8", "b5c4", "b3f7")),

])
def test_fen_response(fen: str, expected_response: str):
    board = ExtendedBoard(fen)

    response = BasiliskEngine(V1Evaluator()).play(board, Limit(time=0.5))

    if isinstance(expected_response, str):
        assert response.move.uci() == expected_response
    else:
        assert response.move.uci() in expected_response
