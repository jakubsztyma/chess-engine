"""
Example of use of GameSession and Engine to make Stockfish play itself.
"""
import os
import random
from copy import deepcopy
from dataclasses import dataclass
from multiprocessing import Pool

import chess
import chess.engine, chess.pgn
import time

from engine.ab_depth_prune import ABDeppeningEngine
from engine.alpha_beta import AlphaBetaEngine
from engine.base import RandomEngine
from engine.basilisk import BasiliskEngine
from engine.board import ExtendedBoard
from engine.minmax import MinMaxEngine
from engine.evaluators import BasicMaterialEvaluator, V0Evaluator


@dataclass
class GameResult:
    result: int
    fullmove_number: int
    elapsed: float
    visited_nodes: int
    depth_sum: int

# Create a new chess board
class Game:
    def __init__(self, white, black):
        self.white = white
        self.black = black

    def play(self):
        random.seed(time.time() + os.getpid()) # Necessary to avoid duplicating games in processes
        game = chess.pgn.Game()
        game.headers["White"] = str(self.white)
        game.headers["Black"] = str(self.black)
        node = game

        board = chess.Board()

        start = time.time()
        while board.result() == "*":
            # Get the best move from the engine
            if board.turn:
                engine = self.white
            else:
                engine = self.black

            best_move = engine.play(deepcopy(board), chess.engine.Limit(time=0.3)).move
            board.push(best_move)
            node = node.add_variation(best_move)  # Add game node

            if board.is_game_over(claim_draw=True):
                break


        # Close the engine when done
        self.white.quit()
        self.black.quit()

        print(game) # PGN

        elapsed = time.time() - start
        match board.result():
            case "1-0":
                result =  1
            case "0-1":
                result = 0
            case _:
                result = 0.5

        visited_nodes = self.white.visited_nodes
        depth_sum = sum(self.white.achieved_depths)
        return GameResult(result, board.fullmove_number, elapsed, visited_nodes, depth_sum)

def play_game():
    return Game(BasiliskEngine(V0Evaluator()), BasiliskEngine(V0Evaluator())).play()

if __name__ == '__main__':
    # Provide the path to the Stockfish engine

    # TODO use stockfish for evaluation
    # engine_path = "/opt/homebrew/bin/stockfish"  # Update this path
    # stockfish = chess.engine.SimpleEngine.popen_uci(engine_path)

    GAMES_COUNT = 100
    white_result = 0


    with Pool(10) as pool:
        async_results = [
            pool.apply_async(play_game, ()) for _ in range(GAMES_COUNT)
        ]
        game_results = [r.get() for r in async_results]
        for i, gr in enumerate(game_results):
            print(f"Game {i} result: {gr.result}")

    white_result = sum(gr.result for gr in game_results)
    fullmove_number = sum(gr.fullmove_number for gr in game_results)
    elapsed = sum(gr.elapsed for gr in game_results)
    visited_nodes = sum(gr.visited_nodes for gr in game_results)
    depth_sum = sum(gr.depth_sum for gr in game_results)
    # Best against random: Match result: 25 : 0, Elapsed: 115.12515902519226. Fullmoves: 605. Time per move: 0.19028951904990457
    # Best against MinMax (time 0.2): Match result: 24.5 : 0.5, Elapsed: 369.31914925575256. Fullmoves: 984. Time per move: 0.3753243386745453
    # Best against AlphaBeta (time 0.3): Match result: 94.0 : 6.0, Elapsed: 2281.0306215286255. Fullmoves: 3981. Time per move: 0.5729793070908379. Nodes per move: 10764.485556392867. Average depth: 4.687766892740518.


    print(
          f"\n"
          f"Match result: {white_result} : {GAMES_COUNT - white_result}, "
          f"Elapsed: {elapsed}. "
          f"Fullmoves: {fullmove_number}. "
          f"Time per move: {elapsed / fullmove_number}. "
          f"Nodes per move: {visited_nodes / fullmove_number}. "
          f"Average depth: {depth_sum / fullmove_number}. "
      )
