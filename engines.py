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
        best_move = next(iter(board.legal_moves))
        best_result = -9999999 # TODO

        for move_white in board.legal_moves:
            board.push(move_white)
            if board.is_checkmate():
                board.pop()
                best_move = move_white
                best_result = 999999
                break

            for move_black in board.legal_moves:
                board.push(move_black)

                result = sum(self.evaluale_piece(c) for c in board.fen())

                if result > best_result:
                    best_move = move_white
                    best_result = result

                board.pop()
            board.pop()

        return PlayResult(best_move, None)

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

