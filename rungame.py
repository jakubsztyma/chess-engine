"""
Example of use of GameSession and Engine to make Stockfish play itself.
"""
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
from engine.evaluators import BasicMaterialEvaluator, V0Evaluator, V1Evaluator

start_fens = {
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
    "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
    "rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq d6 0 3",
    "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2",
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
    "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq d6 0 2",
    "rnbqkbnr/pppppp1p/6p1/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2",
    "rnbqkbnr/pppp1ppp/8/4p3/2P5/8/PP1PPPPP/RNBQKBNR w KQkq e6 0 2",
    "rnbqkbnr/pppp1ppp/8/4p3/8/5N2/PPPPPPPP/RNBQKB1R w KQkq e6 0 2",
    "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
}

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

    def play(self, time_limit=0.3, move_limit: int=None):
        random.seed(time.time()) # Necessary to avoid duplicating games in processes
        game = chess.pgn.Game()
        game.headers["White"] = str(self.white)
        game.headers["Black"] = str(self.black)
        node = game

        starting_position = random.choice(list(start_fens))
        board = ExtendedBoard(starting_position)

        start = time.time()
        while board.result() == "*":
            if move_limit and board.fullmove_number > move_limit:
                break
            # Get the best move from the engine
            if board.turn:
                engine = self.white
            else:
                engine = self.black

            best_move = engine.play(deepcopy(board), chess.engine.Limit(time=time_limit)).move
            board.push(best_move)
            node = node.add_variation(best_move)  # Add game node

            if board.is_game_over(claim_draw=True):
                break


        # Close the engine when done
        self.white.quit()
        self.black.quit()

        # print(game) # PGN # TODO restore?

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
    return Game(BasiliskEngine(V1Evaluator()), ABDeppeningEngine(V0Evaluator())).play()

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
    # Best against MinMax (time 0.2): Match result: 99.5 : 0.5, Elapsed: 988.6049735546112. Fullmoves: 1754. Time per move: 0.5636288332694477. Nodes per move: 8836.092930444698. Average depth: 5.34036488027366.
    # Best against AlphaBeta (time 0.3): Match result: 98.5 : 1.5, Elapsed: 2341.0207023620605. Fullmoves: 4082. Time per move: 0.5734984572175552. Nodes per move: 14125.004654581087. Average depth: 4.751347378735914.
    # Best against ABD (time 0.3): Match result: 74.5 : 25.5, Elapsed: 3757.678389310837. Fullmoves: 6672. Time per move: 0.5632011974386746. Nodes per move: 10143.320443645083. Average depth: 5.511540767386091.


    print(
          f"\n"
          f"Match result: {white_result} : {GAMES_COUNT - white_result}, "
          f"Elapsed: {elapsed}. "
          f"Fullmoves: {fullmove_number}. "
          f"Time per move: {elapsed / fullmove_number}. "
          f"Nodes per move: {visited_nodes / fullmove_number}. "
          f"Average depth: {depth_sum / fullmove_number}. "
      )
