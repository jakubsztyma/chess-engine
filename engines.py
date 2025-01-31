import abc
import math
import random

from chess import Board
from chess.engine import PlayResult

class BaseEngine(abc.ABC):
    @abc.abstractmethod
    def play(self, board: Board, *args, **kwargs):
        pass

    def quit(self):
        pass


class RandomEngine(BaseEngine):
    def play(self, board: Board, *args, **kwargs):
        random_move = random.choice(list(board.legal_moves))
        return PlayResult(random_move, None)




class AlphaBetaEngine(BaseEngine):
    VALUE_DICT = {
        "p": -1,
        "n": -3,
        "b": -3,
        "r": -5,
        "q": -9,
        "P": 1,
        "N": 3,
        "B": 3,
        "R": 5,
        "Q": 9,
    }

    # FIXME same game issue
    def play(self, board: Board, *args, **kwargs):
        best_move, evaluation = self.find_move(board, depth=4, is_white=board.turn, alpha=-math.inf, beta=math.inf)
        return PlayResult(best_move, None)

    def find_move(self, board: Board, depth: int, is_white: bool, alpha: float, beta: float):
        if depth == 0:
            return None, self.evaluate_board(board)

        best_move = None
        best_result = -math.inf if is_white else math.inf # TODO describe

        if board.is_checkmate():
            return None, best_result # Minimal result

        first_legal_move = next(iter(board.legal_moves), -1)
        if first_legal_move == -1: # No moves - stalemate
            return None, 0 # Draw

        for move in board.legal_moves:
            board.push(move)

            _, result = self.find_move(board, depth=depth-1, is_white=board.turn, alpha=alpha, beta=beta)

            if is_white:
                if result > best_result:
                    best_result = result
                    best_move = move
                alpha = max(alpha, result)
            else:
                if result < best_result:
                    best_result = result
                    best_move = move
                beta = min(beta, result)

            board.pop()

            if beta <= alpha:
                break

        return best_move, best_result


    def evaluate_board(self, board: Board) -> float:
        return sum(
            self.VALUE_DICT.get(piece, 0)
            for piece in board.fen()
        )