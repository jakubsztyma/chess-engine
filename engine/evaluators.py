import abc
import random

from chess import Board, PAWN,KNIGHT,BISHOP,ROOK,QUEEN,KING,SQUARES_180,BB_SQUARES,WHITE,BLACK, lsb

from engine.board import ExtendedBoard

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
    pawn_advance_coefficient = 0.03
    piece_centralized_coefficient = 0.015
    king_coefficient = 0.01
    queen_coefficient = 0.03
    rook_active_coefficient = 0.02
    centeral_columns = (3, 4)
    VALUE_DICT = {
        PAWN: 1,
        KNIGHT: 3,
        BISHOP: 3.01,
        ROOK: 5,
        QUEEN: 9,
        KING: 0,
        0: 0,
    }
    def evaluate(self, board: ExtendedBoard) -> float:
        # TODO check for checkmate in an efficient way
        # if board.is_checkmate():
        #     sign = 1 if board.turn else -1
        #     return sign * MATE_EVALUATION

        evaluation = self._evaluate_material(board) + self._evaluate_position(board)
        # Add tiny random number to avoid having the same result for different positions
        return evaluation + random.uniform(0, 0.01)

    def _evaluate_position(self, board: ExtendedBoard) -> float:
        evaluation = 0.
        evaluation += self._evaluate_checks(board)
        return evaluation

    def _evaluate_piece_position(self, board: ExtendedBoard, piece_type, square, color):
        is_endgame = board.fullmove_number > 60
        row = square // 8
        column = square % 8
        # Pawn and piece position
        if piece_type == PAWN:
            # Bonus on advanced pieces
            if column in self.centeral_columns or is_endgame: # Central in middlegame, all in endgame
                if color == BLACK:
                    row = (7-row)
                return self.pawn_advance_coefficient * row

        row_center_distance = row - 3.5 if row > 3.5 else 3.5 - row # Faster than abs()
        column_center_distance = column - 3.5 if column > 3.5 else 3.5 - column # Faster than abs()
        if piece_type in (KNIGHT, BISHOP):
            # Bonus on centralized pieces (in extended center)
            if row < 2 or row > 5 or column < 2 or row > 5:
                piece_center_distance = row_center_distance + column_center_distance
                return -self.piece_centralized_coefficient * piece_center_distance
        if piece_type == ROOK:
            # Move to center columns but avoid center rows
            return self.rook_active_coefficient * (row_center_distance - column_center_distance)
        if piece_type == KING:
            # King position
            sign = 1
            king_center_distance = row_center_distance + column_center_distance  # TODO what distance works best
            if is_endgame:  # TODO better condition
                # Centralized king is good in endgame
                sign *= -1
            return self.king_coefficient * sign * king_center_distance  # TODO find coefficient
        if piece_type == QUEEN:
            if not is_endgame:
                if color == BLACK:
                    row = (7 - row)
                row_second_rank_distance = abs(1 - row)
                return self.queen_coefficient * (column_center_distance + row_second_rank_distance)

        return 0.

    def _evaluate_checks(self, board: ExtendedBoard) -> float:
        turn_sign = -1 if board.turn else 1
        if board.is_check():
            # Being in check makes evaluation worse
            return turn_sign * 0.2
        return 0.

    def _evaluate_material(self, board: ExtendedBoard) -> float:
        white_material = black_material = 0
        # Calculate material
        for square, piece_type in board.pieces_map.items():
            color = bool(board.occupied_co[WHITE] & BB_SQUARES[square])

            piece_position = self._evaluate_piece_position(board, piece_type, square, color)
            piece_value = self.VALUE_DICT[piece_type] + piece_position
            if color == WHITE:
                white_material += piece_value
            else:
                black_material += piece_value

        # Bonus to winning advantage in endgame
        worse_material = white_material if white_material < black_material else black_material
        if worse_material < 2:
            better_material = white_material if white_material > black_material else black_material
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

        # Bonus for simplification
        material_difference = white_material - black_material
        if material_difference > 1.95 or material_difference < -1.95:
            percentage_left = (white_material + black_material) / 78.
            if white_material > black_material:
                material_difference += percentage_left
            else:
                material_difference -= percentage_left

        return material_difference
