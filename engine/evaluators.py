import abc
import random

from chess import Board, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, SQUARES_180, BB_SQUARES, WHITE, BLACK, lsb, \
    scan_reversed

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
        None: 0,
    }
    def evaluate(self, board: Board) -> float:
        # TODO check for checkmate in an efficient way
        # if board.is_checkmate():
        #     sign = 1 if board.turn else -1
        #     return sign * MATE_EVALUATION

        evaluation = self._evaluate_material(board) + self._evaluate_position(board)
        # Add tiny random number to avoid having the same result for different positions
        return evaluation + random.uniform(0, 0.01)

    def _evaluate_position(self, board: Board) -> float:
        evaluation = 0.
        evaluation += self._evaluate_checks(board)
        return evaluation

    def _evaluate_piece_position(self, board, piece_type, square, color):
        is_endgame = board.fullmove_number > 60
        row, column  = divmod(square, 8)
        row_center_distance = abs(row - 3.5)
        column_center_distance = abs(column - 3.5)
        # Pawn and piece position
        if piece_type  == PAWN:
            # Bonus on advanced pieces
            pawn_advance_coefficient = 0.03
            if column in (3, 4) or is_endgame: # Central in middlegame, all in endgame
                if color == BLACK:
                    row = (7-row)
                return pawn_advance_coefficient * row
        elif piece_type in (KNIGHT, BISHOP):
            # Bonus on centralized pieces (in extended center)
            piece_centralized_coefficient = 0.015
            if row < 2 or row > 5 or column < 2 or row > 5:
                piece_center_distance = row_center_distance + column_center_distance
                return -piece_centralized_coefficient * piece_center_distance
        elif piece_type == ROOK:
            # Move to center columns but avoid center rows
            rook_active_coefficient = 0.02
            return rook_active_coefficient * (row_center_distance - column_center_distance)
        elif piece_type == KING:
            # King position
            king_coefficient = 0.01
            sign = 1
            king_center_distance = row_center_distance + column_center_distance  # TODO what distance works best
            if is_endgame:  # TODO better condition
                # Centralized king is good in endgame
                sign *= -1
            return king_coefficient * sign * king_center_distance  # TODO find coefficient
        elif piece_type == QUEEN:
            if not is_endgame:
                queen_coefficient = 0.03
                if color == BLACK:
                    row = (7 - row)
                row_second_rank_distance = abs(1 - row)
                return queen_coefficient * (column_center_distance + row_second_rank_distance)

        return 0.

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

        # Bonus for simplification
        percentage_left = (white_material + black_material) / 78.
        offset = 1. - percentage_left
        if abs(material_difference) > 1.95:
            if black_material > white_material:
                offset = -offset

        return material_difference + offset


PAWN_ADVANCE_COEFFICIENT = 0.05
PIECE_CENTRALIZED_COEFFICIENT = -0.015
ROOK_ACTIVE_COEFFICIENT = 0.02
KING_COEFFICIENT = 0.01
QUEEN_COEFFICIENT = 0.03
CENTRAL_COLUMNS = (3, 4)
PAWN_POSITION_EVALUATION = tuple(
    1 + (PAWN_ADVANCE_COEFFICIENT * row if column in CENTRAL_COLUMNS else 0)
    for row in range(8) for column in range(8)
)
PAWN_POSITION_ENDGAME_EVALUATION = tuple(
    1 + PAWN_ADVANCE_COEFFICIENT * row
    for row in range(8) for column in range(8)
)
PIECE_POSITION_EVALUATION = tuple(
    3 + (PIECE_CENTRALIZED_COEFFICIENT * (abs(3.5 - row) + abs(3.5 - column)) if row < 2 or row > 5 or column < 2 or row > 5 else 0)
    for row in range(8) for column in range(8)
)
ROOK_POSITION_EVALUATION = tuple(
    5 + ROOK_ACTIVE_COEFFICIENT * (abs(3.5 - row) - abs(3.5 - column))
    for row in range(8) for column in range(8)
)
KING_POSITION_EVALUATION = tuple(
    KING_COEFFICIENT * (abs(3.5 - row) + abs(3.5 - column))
    for row in range(8) for column in range(8)
)
QUEEN_POSITION_EVALUATION = tuple(
    9 + QUEEN_COEFFICIENT * (abs(1 - row) + abs(3.5 - column))
    for row in range(8) for column in range(8)
)

class V1Evaluator(BaseEvaluator):
    VALUE_DICT = {
        PAWN: 1,
        KNIGHT: 3,
        BISHOP: 3.01,
        ROOK: 5,
        QUEEN: 9,
        KING: 0,
        0: 0,
        None: 0,
    }
    def evaluate(self, board: Board) -> float:
        evaluation = self._evaluate_material(board) + self._evaluate_position(board)
        # Add tiny random number to avoid having the same result for different positions
        return evaluation + random.uniform(0, 0.01)

    def _evaluate_position(self, board: Board) -> float:
        evaluation = 0.
        evaluation += self._evaluate_checks(board)
        # 1-move evaluation
        # TODO evaluate promotions
        # Max capture
        # TODO generate only capture to optimize
        captures_generator = (self.VALUE_DICT[board.piece_type_at(move.to_square)] for move in board.legal_moves)
        max_capture = max(captures_generator, default=0.)
        coefficient = 0.7 if board.turn else -0.7
        return evaluation + coefficient * max_capture

    def _evaluate_checks(self, board: Board) -> float:
        # TODO check checkmate before pushing the move?
        turn_sign = -1 if board.turn else 1
        if board.is_check():
            # Being in check makes evaluation worse
            if board.is_checkmate():
                return turn_sign * MATE_EVALUATION
            return turn_sign * 0.2
        return 0.

    def _evaluate_material(self, board: Board) -> float:
        white_material = black_material = 0
        occupied_by_white = board.occupied_co[WHITE]
        is_endgame = board.fullmove_number > 60
        # Calculate material
        for square in scan_reversed(board.occupied):
            mask = BB_SQUARES[square]
            is_white = occupied_by_white & mask > 0
            if board.pawns & mask:
                # TODO implement endgame evaluation
                if not is_white:
                    square = square ^ 0x38
                if is_endgame:
                    piece_value = PAWN_POSITION_ENDGAME_EVALUATION[square]
                else:
                    piece_value = PAWN_POSITION_EVALUATION[square]
            elif board.knights & mask:
                piece_value = PIECE_POSITION_EVALUATION[square]
            elif board.bishops & mask:
                piece_value = PIECE_POSITION_EVALUATION[square]
            elif board.rooks & mask:
                piece_value = ROOK_POSITION_EVALUATION[square]
            elif board.kings & mask:
                sign = 1
                # TODO what distance works best
                if is_endgame:  # TODO better condition
                    # Centralized king is good in endgame
                    sign *= -1
                piece_value = sign * KING_POSITION_EVALUATION[square]  # TODO find coefficient
            else:
                if not is_endgame:
                    if not is_white:
                        square = square ^ 0x38
                    piece_value = QUEEN_POSITION_EVALUATION[square]
                else:
                    piece_value = 9.

            if is_white:
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

        # Bonus for simplification if black is not winning a log
        material_difference = white_material - black_material
        percentage_left = (white_material + black_material) / 78.
        offset = 1. - percentage_left
        if abs(material_difference) > 1.95:
            if black_material > white_material:
                offset = -offset

        return material_difference + offset