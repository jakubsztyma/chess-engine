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
        return PlayResult(next(iter(board.legal_moves)), None)