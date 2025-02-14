import abc
import random
import time

from chess import Board
from chess.engine import PlayResult, Limit

from engine.evaluators import MATE_EVALUATION, BaseEvaluator

class ExpectedTimeoutException(Exception):
    pass

class BaseEngine(abc.ABC):
    def __init__(self, evaluator: BaseEvaluator):
        self.evaluator = evaluator
        self.max_depth = 12
        self.time = None
        self.start_time = None
        self.visited_nodes = 0
        self.achieved_depths = []
        self.board = None

    @abc.abstractmethod
    def _play(self, board: Board, depth: int, *args, **kwargs):
        pass

    def play(self, board: Board, limit: Limit):
        self.start_time = time.time()
        self.time = limit.time
        play_result = None
        for depth in range(1, self.max_depth + 1):
            try:
                play_result = self._play(board, depth)
            except ExpectedTimeoutException:
                break

        return play_result

    def check_timeout(self):
        elapsed = time.time() - self.start_time
        if elapsed > self.time - 0.01: # Leave some time for cleanup
            raise ExpectedTimeoutException()

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
        return [], result_sign * (MATE_EVALUATION + depth)


class RandomEngine(BaseEngine):
    def play(self, board: Board, *args, **kwargs):
        return self._play(board)

    def _play(self, board: Board, *args, **kwargs):
        random_move = random.choice(list(board.legal_moves))
        return PlayResult(random_move, None)
