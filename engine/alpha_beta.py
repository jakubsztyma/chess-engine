import math

from engine.base import BaseEngine
from chess import Board
from chess.engine import PlayResult


class AlphaBetaEngine(BaseEngine):
    def play(self, board: Board, *args, **kwargs):
        best_move, evaluation = self.find_move(board, depth=4, is_white=board.turn, alpha=-math.inf, beta=math.inf)
        return PlayResult(best_move, None)

    def find_move(self, board: Board, depth: int, is_white: bool, alpha: float, beta: float):
        if depth == 0:
            return None, self.evaluator.evaluate(board)

        if board.is_game_over():
            return self._get_board_result(board, depth)

        best_move = None
        best_result = -math.inf if is_white else math.inf # Anti-optimum

        for move in self.get_legal_moves(board, depth=depth):
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

    def get_legal_moves(self, board: Board, depth: int):
        return board.legal_moves
