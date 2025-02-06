import random

import math
from chess import Board
from chess.engine import PlayResult

from engine.base import BaseEngine


class MinMaxEngine(BaseEngine):
    def play(self, board: Board, *args, **kwargs):
        best_move, evaluation = self.find_move(board, depth=3, is_white=board.turn)
        return PlayResult(best_move, None)

    def find_move(self, board: Board, depth: int, is_white: bool):
        if depth == 0:
            return None, self.evaluator.evaluate(board)


        if board.is_game_over():
            return self._get_board_result(board, depth)

        best_move = None
        best_result = -math.inf if is_white else math.inf  # Anti-optimum
        legal_moves = list(board.legal_moves)
        random.shuffle(legal_moves)  # Shuffle to avoid same game
        for move in legal_moves:
            board.push(move)

            _, result = self.find_move(board, depth=depth-1, is_white=board.turn)

            if (is_white and result > best_result) or (not is_white and result < best_result):
                best_move = move
                best_result = result

            board.pop()

        return best_move, best_result
