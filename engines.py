import abc
import math
import random

from chess import Board, SQUARES_180, PAWN,KNIGHT,BISHOP,ROOK,QUEEN,KING, WHITE, BB_SQUARES
from chess.engine import PlayResult



class BaseEvaluator:
    @abc.abstractmethod
    def evaluate(self, board: Board):
        pass

class BasicMaterialEvaluator(BaseEvaluator):
    VALUE_DICT = {
        PAWN: 1,
        KNIGHT: 3,
        BISHOP: 3.01,
        ROOK: 5,
        QUEEN: 9,
        KING: 0,
    }
    def evaluate(self, board: Board) -> float:
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

class AdvancedMaterialEvaluator(BaseEvaluator):
    VALUE_DICT = {
        PAWN: 1,
        KNIGHT: 3,
        BISHOP: 3.01,
        ROOK: 5,
        QUEEN: 9,
        KING: 0,
    }
    def evaluate(self, board: Board) -> float:
        white_material = black_material = 0
        for square in SQUARES_180:
            piece_type = board.piece_type_at(square)
            if piece_type:
                mask = BB_SQUARES[square]
                color = bool(board.occupied_co[WHITE] & mask)

                piece_value = self.VALUE_DICT[piece_type]
                if color == WHITE:
                    white_material += piece_value
                else:
                    black_material += piece_value

        material_difference = white_material - black_material

        # TODO refactor code
        worse_material = min(white_material, black_material)
        if worse_material < 2:
            better_material = max(white_material, black_material)
            cutoff_result = None
            if worse_material == 0:
                if better_material >= 6.5:
                    cutoff_result = 50. + better_material # This should almost always be winning except for very rare cases
                elif better_material >= 5:
                    cutoff_result = 10. + better_material # This should usually be winning except for rare cases
            if 0 < worse_material < 2:
                if better_material >= 10:
                    cutoff_result = 10. + better_material # This should usually be winning except for rare cases
            if cutoff_result is not None:
                if black_material > white_material:
                    cutoff_result = - cutoff_result
                return cutoff_result

        percentage_left = (white_material + black_material) / 78.
        offset = 1. - percentage_left
        if abs(material_difference) > 1.95:
            if black_material > white_material:
                offset = -offset

        return material_difference + offset


class BaseEngine(abc.ABC):
    def __init__(self, evaluator: BaseEvaluator):
        self.evaluator = evaluator

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
    def play(self, board: Board, *args, **kwargs):
        best_move, evaluation = self.find_move(board, depth=3, is_white=board.turn, alpha=-math.inf, beta=math.inf)
        return PlayResult(best_move, None)

    def find_move(self, board: Board, depth: int, is_white: bool, alpha: float, beta: float):
        if depth == 0:
            return None, self.evaluator.evaluate(board)

        if board.is_game_over():
            result = board.result()
            match result:
                case "1-0":
                    result_sign = 1
                case "0-1":
                    result_sign = -1
                case _:
                    result_sign = 0
            return None, result_sign * 999


        best_move = None
        best_result = -math.inf if is_white else math.inf # Anti-optimum

        legal_moves = list(board.legal_moves)
        random.shuffle(legal_moves) # Shuffle the moves to avoid moving the same piece
        for move in legal_moves:
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


