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

class MinMaxEngine(BaseEngine): # TODO improve the code
    def play(self, board: Board, *args, **kwargs):
        best_move, evaluation = self.find_move(board, depth=3, is_white=board.turn)
        return PlayResult(best_move, None)

    def find_move(self, board: Board, depth: int, is_white: bool):
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

            _, result = self.find_move(board, depth=depth-1, is_white=board.turn)

            if (is_white and result > best_result) or (not is_white and result < best_result):
                best_move = move
                best_result = result

            board.pop()

        return best_move, best_result

    def evaluate_board(self, board: Board) -> float:
        evaluation = 0
        for piece in board.fen():
            match piece.lower():
                case "p":
                    piece_value = 1
                case "n":
                    piece_value = 3
                case "b":
                    piece_value = 3
                case "r":
                    piece_value = 5
                case "q":
                    piece_value = 9
                case _:
                    piece_value = 0

            if piece.isupper():
                evaluation += piece_value
            else:
                evaluation -= piece_value
        return evaluation

