"""
Example of use of GameSession and Engine to make Stockfish play itself.
"""
from copy import deepcopy
from dataclasses import dataclass
from multiprocessing import Pool

import chess
import chess.engine, chess.pgn
import time

from engine.ab_depth_prune import ABDepthPruningEngine
from engine.alpha_beta import AlphaBetaEngine
from engine.base import RandomEngine
from engine.minmax import MinMaxEngine
from engine.evaluators import BasicMaterialEvaluator, V0Evaluator


@dataclass
class GameResult:
    result: int
    fullmove_number: int
    elapsed: float

# Create a new chess board
class Game:
    def __init__(self, white, black):
        self.white = white
        self.black = black

    def play(self):
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

            try:
                best_move = engine.play(deepcopy(board), chess.engine.Limit(time=0.2)).move
                board.push(best_move)
            except Exception as ex:
                print(ex)
                print(game)
                break
            node = node.add_variation(best_move)  # Add game node

            if board.is_game_over(claim_draw=True):  # TODO how does claim_draw work exactly?
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

        return GameResult(result, board.fullmove_number, elapsed)

def play_game():
    return Game(ABDepthPruningEngine(V0Evaluator()), AlphaBetaEngine(BasicMaterialEvaluator())).play()

if __name__ == '__main__':
    # Provide the path to the Stockfish engine

    # TODO use stockfish for evaluation
    # engine_path = "/opt/homebrew/bin/stockfish"  # Update this path
    # stockfish = chess.engine.SimpleEngine.popen_uci(engine_path)

    GAMES_COUNT = 25
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
    # Best against random: Match result: 25 : 0, Elapsed: 115.12515902519226. Fullmoves: 605. Time per move: 0.19028951904990457
    # Best against MinMax (time 0.2): Match result: 24.5 : 0.5, Elapsed: 369.31914925575256. Fullmoves: 984. Time per move: 0.3753243386745453
    # Best against AlphaBeta (time 0.2): Match result: 22.5 : 2.5, Elapsed: 443.1456003189087. Fullmoves: 1173. Time per move: 0.37778823556599206

    print(
          f"Match result: {white_result} : {GAMES_COUNT - white_result}, "
          f"Elapsed: {elapsed}. "
          f"Fullmoves: {fullmove_number}. "
          f"Time per move: {elapsed / fullmove_number}"
      )
