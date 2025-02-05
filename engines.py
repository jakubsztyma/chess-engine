import abc
import math
import random

from chess import Board, SQUARES_180, PAWN,KNIGHT,BISHOP,ROOK,QUEEN,KING, WHITE, BB_SQUARES
from chess.engine import PlayResult

MATE_EVALUATION = 1000


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

class V0Evaluator(BaseEvaluator):
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
        # Calculate material
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

        # Bonus to winning advantage in endgame
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

        # Bonus for simplification while winning
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
        return None, result_sign * MATE_EVALUATION

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
        best_move, evaluation = self.find_move(board, depth=5, is_white=board.turn, alpha=-math.inf,
                                               beta=math.inf)
        return PlayResult(best_move, None)

    def find_move(self, board: Board, depth: int, is_white: bool, alpha: float, beta: float):
        if depth == 0:
            return None, self.evaluator.evaluate(board)

        if board.is_game_over():
            return self._get_board_result(board)

        best_move = None
        best_result = -math.inf if is_white else math.inf  # Anti-optimum
        evaluation_sign = 1 if is_white else -1

        for move in self.get_pruned_moves(board, depth=depth, alpha=alpha, beta=beta):
            board.push(move)

            _, result = self.find_move(board, depth=depth - 1, is_white=board.turn, alpha=alpha, beta=beta)
            if abs(result) >= MATE_EVALUATION: # Reduce mate evaluation with depth # FIXME debug it
                result -= evaluation_sign

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

    def get_pruned_moves(self, board: Board, depth: int, alpha: float, beta: float) -> list:
        moves = list(self.get_legal_moves(board, depth=depth))
        return moves
        # if depth != 2:
        #     return moves
        #
        # priority_bonus_step = 0.1 if board.turn else -0.1 # TODO explain
        # moves_with_evaluation = []
        # for i, move in enumerate(moves):
        #     priority_bonus = (len(moves) - i) * priority_bonus_step
        #     board.push(move)
        #     evaluation = self.evaluator.evaluate(board)
        #     moves_with_evaluation.append((move, evaluation + priority_bonus))
        #     board.pop()
        #
        # moves_with_evaluation.sort(key=lambda m_e: m_e[1], reverse=not bool(board.turn))
        # moves_sorted = [move for move, _ in moves_with_evaluation]
        # return moves_sorted[:1 + math.ceil(len(moves_sorted) * 0.75)] # Prune worst moves # TODO try with other rules

    def get_legal_moves(self, board: Board, depth: int) -> list:
        moves = list(board.legal_moves)
        # FIXME Shuffle piece moves in a smarter way
        # FIXME find a way to promote pawn moves in endgame -- position evaluation?
        # # Shuffle piece moves to try different piece types equally
        # piece_moves = [m for m in moves if PAWN != board.piece_type_at(m.from_square)]
        # random.shuffle(piece_moves)
        # pawn_moves = [m for m in moves if PAWN == board.piece_type_at(m.from_square)] # TODO
        # moves = piece_moves + pawn_moves

        evaluated_moves = [
            (V0Evaluator.VALUE_DICT.get(board.piece_type_at(move.to_square), 0), len(moves) - i, move)
            for i, move in enumerate(moves)
        ]
        evaluated_moves.sort(reverse=True)
        return [e[-1] for e in evaluated_moves]

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

