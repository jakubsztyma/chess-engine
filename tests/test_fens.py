import pytest
from chess import Board

from engine.ab_depth_prune import ABDepthPruningEngine
from engine.evaluators import V0Evaluator


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
    ("6K1/8/k7/8/3Q4/2n5/P7/1r3R2 w - - 2 96", ("d4c3", "f1b1", "d4b3")),

])
def test_fen_response(fen: str, expected_response: str):
    board = Board(fen)

    response = ABDepthPruningEngine(V0Evaluator()).play(board)

    if isinstance(expected_response, str):
        assert response.move.uci() == expected_response
    else:
        assert response.move.uci() in expected_response
