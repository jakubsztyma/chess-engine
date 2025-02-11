import abc
import random

from chess import Board, PAWN,KNIGHT,BISHOP,ROOK,QUEEN,KING,SQUARES_180,BB_SQUARES,WHITE,BLACK, lsb

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
        evaluation = self._evaluate_material(board) + self._evaluate_position(board)
        # Add tiny random number to avoid having the same result for different positions
        return evaluation + random.uniform(0, 0.01)

    def _evaluate_position(self, board: Board) -> float:
        evaluation = 0.
        evaluation += self._evaluate_checks(board)
        return evaluation

    def _evaluate_piece_position(self, board, piece_type, square, color):
        evaluation = 0.
        row, column  = divmod(square, 8)
        # Pawn and piece position
        if piece_type  == PAWN:
            # Bonus on advanced pieces
            pawn_advance_coefficient = 0.02
            if color == BLACK:
                row = (7-row)
            evaluation += pawn_advance_coefficient * row

        if piece_type in (KNIGHT, BISHOP):
            piece_centralized_coefficient = 0.05
            piece_center_distance = abs(row - 3.5) + abs(column - 3.5)
            evaluation -= piece_centralized_coefficient * piece_center_distance

        if piece_type == ROOK:
            rook_active_coefficient = 0.02
            if column not in (0, 7):
                evaluation += rook_active_coefficient

        # King position
        if piece_type == KING:
            sign = 1
            king_center_distance = abs(row - 3.5) + abs(column - 3.5)  # TODO what distance works best
            if board.fullmove_number > 60:  # TODO better condition
                # Centralized king is good in endgame
                sign *= -1
            evaluation +=  0.01 * sign * king_center_distance  # TODO find coefficient

        return evaluation

    def _evaluate_checks(self, board: Board) -> float:
        turn_sign = -1 if board.turn else 1
        if board.is_check():
            # Being in check makes evaluation worse
            return turn_sign * 0.2
        return 0.

    def _evaluate_material(self, board: Board) -> float:
        white_material = black_material = 0
        # Calculate material
        for square in SQUARES_180:
            piece_type = board.piece_type_at(square)
            if piece_type:
                mask = BB_SQUARES[square]
                color = bool(board.occupied_co[WHITE] & mask)

                piece_value = self.VALUE_DICT[piece_type]
                piece_position = self._evaluate_piece_position(board, piece_type, square, color)
                if color == WHITE:
                    white_material += piece_value + piece_position
                else:
                    black_material += piece_value + piece_position
        material_difference = white_material - black_material
        # Bonus to winning advantage in endgame
        worse_material = min(white_material, black_material)
        if worse_material < 2:
            better_material = max(white_material, black_material)
            cutoff_result = None
            if worse_material == 0:
                if better_material >= 6.5:
                    cutoff_result = 50. + better_material  # This should almost always be winning except for very rare cases
                elif better_material >= 5:
                    cutoff_result = 10. + better_material  # This should usually be winning except for rare cases
            if 0 < worse_material < 2:
                if better_material >= 10:
                    cutoff_result = 10. + better_material  # This should usually be winning except for rare cases
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
