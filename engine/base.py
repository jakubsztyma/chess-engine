import abc
import random
from chess import Board
from chess.engine import PlayResult

from engine.evaluators import MATE_EVALUATION, BaseEvaluator


class BaseEngine(abc.ABC):
    def __init__(self, evaluator: BaseEvaluator):
        self.evaluator = evaluator

    @abc.abstractmethod
    def play(self, board: Board, *args, **kwargs):
        pass

    def quit(self):
        pass

    def _get_board_result(self, board: Board, depth: int):
        result = board.result()
        match result:
            case "1-0":
                result_sign = 1
            case "0-1":
                result_sign = -1
            case _:
                result_sign = 0

        # Mate evaluation decreases with depth (when depth parameter is lower)
        return None, result_sign * (MATE_EVALUATION + depth)


class RandomEngine(BaseEngine):
    def play(self, board: Board, *args, **kwargs):
        random_move = random.choice(list(board.legal_moves))
        return PlayResult(random_move, None)
