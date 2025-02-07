import time

import math

from engine.base import BaseEngine, ExpectedTimeoutException
from engine.evaluators import V0Evaluator
from chess import Board, PAWN,KNIGHT,BISHOP,ROOK,QUEEN,KING,SQUARES_180,BB_SQUARES,WHITE,BLACK
from chess.engine import PlayResult, Limit


class ABDepthPruningEngine(BaseEngine):
    def play(self, board: Board, limit: Limit):
        is_white = board.turn
        anti_optimum = -math.inf if is_white else math.inf

        self.start_time = time.time()
        self.time = limit.time
        play_result = None
        best_line = None

        move_evaluation_map = [[anti_optimum, move] for move in self.get_legal_moves(board)]
        for depth in range(1, self.max_depth + 1):
            try:
                alpha = -math.inf
                beta = math.inf

                best_result = anti_optimum

                move_evaluation_map.sort(key=lambda it: it[0], reverse=is_white)
                for move_item in move_evaluation_map:
                    move = move_item[1]
                    board.push(move)
                    line, evaluation = self.find_move(board, depth=depth - 1, alpha=alpha, beta=beta)
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
            except ExpectedTimeoutException:
                play_result = PlayResult(best_line[-1], None)
                break

        return play_result

    def _play(self, *args, **kwargs):
        pass


    def find_move(self, board: Board, depth: int, alpha: float, beta: float):
        is_white = board.turn
        self.check_timeout()
        if depth == 0:
            return [None], self.evaluator.evaluate(board)

        if board.is_game_over():
            return self._get_board_result(board, depth)
        # if board.can_claim_threefold_repetition():
        #     return None, 0. # TODO find a proper way to implement that

        best_line = None
        best_result = -math.inf if is_white else math.inf  # Anti-optimum

        for move in self.get_pruned_moves(board, depth=depth, alpha=alpha, beta=beta):
            board.push(move)

            line, evaluation = self.find_move(board, depth=depth - 1, alpha=alpha, beta=beta)

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
                break

        return best_line, best_result

    def get_pruned_moves(self, board: Board, depth: int, alpha: float, beta: float) -> list:
        moves = list(self.get_legal_moves(board))
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

    def get_legal_moves(self, board: Board) -> list:
        moves = list(board.legal_moves)
        # FIXME Shuffle piece moves in a smarter way
        # FIXME find a way to promote pawn moves in endgame and opening -- position evaluation?
        # # Shuffle piece moves to try different piece types equally
        # piece_moves = [m for m in moves if PAWN != board.piece_type_at(m.from_square)]
        # random.shuffle(piece_moves)
        # pawn_moves = [m for m in moves if PAWN == board.piece_type_at(m.from_square)] # TODO
        # moves = piece_moves + pawn_moves
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
            if board.fullmove_number > 50: # Better endgame rule
                piece_order_value = piece_order_endgame.get(board.piece_type_at(move.from_square))
            else:
                piece_order_value = piece_order.get(board.piece_type_at(move.from_square))
            move_order = len(moves) - i
            evaluated_moves.append((is_castling, capture_value, piece_order_value, move_order, move))


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
