import abc
import math
import random

from chess import Board, SQUARES_180, PAWN,KNIGHT,BISHOP,ROOK,QUEEN,KING, WHITE, BB_SQUARES
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
        PAWN: 1,
        KNIGHT: 3,
        BISHOP: 3.01,
        ROOK: 5,
        QUEEN: 9,
        KING: 0,
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
        evaluation = 0
        for square in SQUARES_180:
            piece_type = board.piece_type_at(square)
            if piece_type:
                mask = BB_SQUARES[square]
                color = bool(board.occupied_co[WHITE] & mask)

                piece_value = self.VALUE_DICT[piece_type]
                if color == WHITE:
                    evaluation += piece_value
                else:
                    evaluation -= piece_value

        return evaluation
