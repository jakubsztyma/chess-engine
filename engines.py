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

    def _get_board_result(self, board):
        result = board.result()
        match result:
            case "1-0":
                result_sign = 1
            case "0-1":
                result_sign = -1
            case _:
                result_sign = 0
        return None, result_sign * 999

class RandomEngine(BaseEngine):
    def play(self, board: Board, *args, **kwargs):
        random_move = random.choice(list(board.legal_moves))
        return PlayResult(random_move, None)

class MinMaxEngine(BaseEngine):
    def play(self, board: Board, *args, **kwargs):
        best_move, evaluation = self.find_move(board, depth=3, is_white=board.turn)
        return PlayResult(best_move, None)

    def find_move(self, board: Board, depth: int, is_white: bool):
        if depth == 0:
            return None, self.evaluator.evaluate(board)


        if board.is_game_over():
            return self._get_board_result(board)

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




class AlphaBetaEngine(BaseEngine):
    def play(self, board: Board, *args, **kwargs):
        best_move, evaluation = self.find_move(board, depth=4, is_white=board.turn, alpha=-math.inf, beta=math.inf)
        return PlayResult(best_move, None)

    def find_move(self, board: Board, depth: int, is_white: bool, alpha: float, beta: float):
        if depth == 0:
            return None, self.evaluator.evaluate(board)

        if board.is_game_over():
            return self._get_board_result(board)

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

class ABDepthPruningEngine(BaseEngine):
    def play(self, board: Board, *args, **kwargs):
        best_move, evaluation = self.find_move(board, depth=4, is_white=board.turn, alpha=-math.inf,
                                               beta=math.inf)
        return PlayResult(best_move, None)

    def find_move(self, board: Board, depth: int, is_white: bool, alpha: float, beta: float):
        if depth == 0:
            return None, self.evaluator.evaluate(board)

        if board.is_game_over():
            return self._get_board_result(board)

        best_move = None
        best_result = -math.inf if is_white else math.inf  # Anti-optimum

        for move in self.get_pruned_moves(board, depth=depth):
            board.push(move)

            _, result = self.find_move(board, depth=depth - 1, is_white=board.turn, alpha=alpha, beta=beta)

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

    def get_pruned_moves(self, board: Board, depth: int) -> list:
        moves = self.get_legal_moves(board, depth=depth)
        if depth < 2:
            return moves

        moves_with_evaluation = []
        for move in moves:
            board.push(move)
            _, result = self.find_move(board, depth-2, board.turn, -math.inf, math.inf) # Lower depth # TODO use alpha-beta from main search?
            moves_with_evaluation.append((move, result))
            board.pop()

        moves_with_evaluation.sort(key=lambda m_e: m_e[1], reverse=not bool(board.turn))
        moves_sorted = [move for move, _ in moves_with_evaluation]
        return moves_sorted[:1 + math.ceil(len(moves_sorted) * 0.75)] # Prune worst moves # TODO try with other rules

    def get_legal_moves(self, board: Board, depth: int):
        return board.legal_moves

    # TODO restore after finding the better sorting algo than the default
    # random.shuffle(legal_moves) # Shuffle the moves to avoid moving the same piece # TODO restore? Only to extent?
    # if depth <= 1:
    #     return legal_moves
    #
    # moves_with_evaluation = []
    # for move in legal_moves:
    #     board.push(move)
    #     evaluation = self.evaluator.evaluate(board)
    #     moves_with_evaluation.append((move, evaluation))
    #     board.pop()
    #
    # moves_with_evaluation.sort(key=lambda m_e: m_e[1], reverse=not bool(board.turn))
    # return [move for move, _ in moves_with_evaluation]

