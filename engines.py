import abc
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
            return None, sum(self.evaluale_piece(c) for c in board.fen())

        if len(list(board.legal_moves)) == 0: # FIXME improve
            return None, 0 # Draw

        best_move = next(iter(board.legal_moves))
        best_result = -9999999 if is_white else 9999999 # TODO

        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate(): # TODO improve the code
                best_move = move
                board.pop()
                break

            _, result = self.find_move(board, depth=depth-1, is_white=board.turn)

            if (is_white and result > best_result) or (not is_white and result < best_result):
                best_move = move
                best_result = result

            board.pop()

        return best_move, best_result

    def evaluale_piece(self, piece: str) -> float:
        piece_lower = piece.lower()
        if piece_lower == "p":
            piece_value = 1
        elif piece_lower == "n":
            piece_value = 3
        elif piece_lower == "b":
            piece_value = 3
        elif piece_lower == "r":
            piece_value = 5
        elif piece_lower == "q":
            piece_value = 9
        else:
            piece_value = 0

        if piece.islower():
            piece_value = -piece_value
        return piece_value

