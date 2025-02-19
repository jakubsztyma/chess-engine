import time

import math

from engine.base import BaseEngine, ExpectedTimeoutException
from engine.board import ExtendedBoard
from engine.evaluators import V0Evaluator, MATE_EVALUATION
from chess import Board, PAWN,KNIGHT,BISHOP,ROOK,QUEEN,KING,SQUARES_180,BB_SQUARES,WHITE,BLACK, Outcome, Termination
from chess.engine import PlayResult, Limit

PIECE_ORDER = {
    BISHOP: 4,
    KNIGHT: 4,
    PAWN: 3,
    QUEEN: 2,
    ROOK: 1,
    KING: 0,
}
PIECE_ORDER_ENDGAME = {
    QUEEN: 6,
    PAWN: 5,
    ROOK: 4,
    KING: 3,
    BISHOP: 2,
    KNIGHT: 1,
}

class BasiliskEngine(BaseEngine):
    def play(self, board: ExtendedBoard, limit: Limit):
        self.start_time = time.time()
        self.time = limit.time
        self.board = ExtendedBoard(board.fen())
        best_line, best_result = self.find_move(self.max_depth, master_alpha=-math.inf, master_beta=math.inf, is_top_level=True)
        return PlayResult(best_line[-1], None)


    def _play(self, *args, **kwargs):
        pass



    def find_move(self, max_depth: int, master_alpha: float, master_beta: float, is_top_level=False):
        self.visited_nodes += 1
        is_white = self.board.turn
        anti_optimum = -math.inf if is_white else math.inf
        self.check_timeout()

        if max_depth == 0:
            return [], self.evaluator.evaluate(self.board)

        if not is_top_level:
            game_over_result = self.board.check_game_over()
            if game_over_result is not None:
                return [], game_over_result * (MATE_EVALUATION + max_depth)

        best_line = None
        best_result = anti_optimum

        move_evaluation_map = [[anti_optimum, move] for move in self.get_legal_moves()]
        min_depth = 2 if is_top_level else max_depth
        for depth in range(min_depth, max_depth + 1):
            alpha = master_alpha
            beta = master_beta
            best_result = anti_optimum
            move_evaluation_map.sort(key=lambda it: it[0], reverse=is_white)
            try:
                for i, move_item in enumerate(move_evaluation_map):
                    move = move_item[1]
                    with self.board.apply(move):
                        line, evaluation = self.find_move(max_depth=depth - 1, master_alpha=alpha, master_beta=beta)
                        move_item[0] = evaluation

                        if is_white:
                            if evaluation > best_result:
                                best_result = evaluation
                                line.append(move)
                                best_line = line
                            alpha = max(alpha, evaluation)
                        else:
                            if evaluation < best_result:
                                best_result = evaluation
                                line.append(move)
                                best_line = line
                            beta = min(beta, evaluation)

                    if beta <= alpha:
                        if depth == max_depth:
                            return best_line, best_result
                        else:
                            for j in range(i+1, len(move_evaluation_map)):
                                move_evaluation_map[j][0] = anti_optimum
            except ExpectedTimeoutException as ex:
                if is_top_level:
                    self.achieved_depths.append(depth)
                    return best_line, best_result
                else:
                    raise ex
        return best_line, best_result


    def get_legal_moves(self) -> list:
        if self.board.fullmove_number > 50:  # TODO Better endgame rule
            order_dict = PIECE_ORDER_ENDGAME
        else:
            order_dict = PIECE_ORDER

        evaluated_moves = []
        for i, move in enumerate(self.board.legal_moves):
            is_castling = self.board.is_castling(move)
            capture_value = V0Evaluator.VALUE_DICT[self.board.pieces_map.get(move.to_square, 0)]
            piece_order_value = order_dict[self.board.pieces_map[move.from_square]]
            evaluated_moves.append((is_castling, capture_value, piece_order_value, -i, move))


        evaluated_moves.sort(reverse=True)
        yield from (e[-1] for e in evaluated_moves)
