import time

import math

from engine.base import BaseEngine, ExpectedTimeoutException
from engine.evaluators import V0Evaluator, MATE_EVALUATION
from chess import Board, PAWN,KNIGHT,BISHOP,ROOK,QUEEN,KING,SQUARES_180,BB_SQUARES,WHITE,BLACK, Outcome, Termination
from chess.engine import PlayResult, Limit


class ABDeppeningEngine(BaseEngine):
    def play(self, board: Board, limit: Limit):
        self.start_time = time.time()
        self.time = limit.time
        best_line, best_result = self.find_move(board, self.max_depth, master_alpha=-math.inf, master_beta=math.inf, is_top_level=True)
        return PlayResult(best_line[-1], None)


    def _play(self, *args, **kwargs):
        pass

    def check_game_over(self, board: Board) -> int | None:
        """Faster version of board.is_game_over"""
        # TODO faster versions of used functions (eg use already generated moves to check checkmate)?
        # TODO add stalemate condition (reuse generate_legal_moves?)
        # Normal game end.
        if board.is_checkmate():
            return 1 if not board.turn else -1
        if board.pawns | board.rooks | board.queens == 0:
            return 0
        if not any(board.generate_legal_moves()):
            return 0

        if board.is_fifty_moves():
            return 0
        if board.is_repetition(2):
            return 0

        return None


    def find_move(self, board: Board, max_depth: int, master_alpha: float, master_beta: float, is_top_level=False):
        self.visited_nodes += 1
        is_white = board.turn
        anti_optimum = -math.inf if is_white else math.inf
        self.check_timeout()

        if max_depth == 0:
            return [], self.evaluator.evaluate(board)

        if not is_top_level:
            game_over_result = self.check_game_over(board)
            if game_over_result is not None:
                return [], game_over_result * (MATE_EVALUATION + max_depth)

        best_line = None
        best_result = anti_optimum

        move_evaluation_map = [[anti_optimum, move] for move in self.get_legal_moves(board)]
        min_depth = 2 if is_top_level else max_depth
        for depth in range(min_depth, max_depth + 1):
            alpha = master_alpha
            beta = master_beta
            best_result = anti_optimum
            move_evaluation_map.sort(key=lambda it: it[0], reverse=is_white)
            try:
                for i, move_item in enumerate(move_evaluation_map):
                    move = move_item[1]
                    board.push(move)
                    line, evaluation = self.find_move(board, max_depth=depth - 1, master_alpha=alpha, master_beta=beta)
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

                    board.pop()

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


    def get_legal_moves(self, board: Board) -> list:
        moves = list(board.legal_moves)
        # # Shuffle piece moves to try different piece types equally
        piece_order = {
            BISHOP:4,
            KNIGHT:4,
            QUEEN: 3,
            PAWN: 2,
            ROOK: 1,
            KING: 0,
        }
        piece_order_endgame = {
            QUEEN:6,
            PAWN: 5,
            ROOK: 4,
            KING: 3,
            BISHOP: 2,
            KNIGHT: 1,
        }

        evaluated_moves = []
        for i, move in enumerate(moves):
            is_castling = board.is_castling(move)
            capture_value = V0Evaluator.VALUE_DICT.get(board.piece_type_at(move.to_square), 0)
            if board.fullmove_number > 50: # TODO Better endgame rule
                piece_order_value = piece_order_endgame.get(board.piece_type_at(move.from_square))
            else:
                piece_order_value = piece_order.get(board.piece_type_at(move.from_square))
            move_order = len(moves) - i
            evaluated_moves.append((is_castling, capture_value, piece_order_value, move_order, move))


        evaluated_moves.sort(reverse=True)
        return [e[-1] for e in evaluated_moves]
