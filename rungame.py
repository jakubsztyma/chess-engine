"""
Example of use of GameSession and Engine to make Stockfish play itself.
"""
from dataclasses import dataclass
from multiprocessing import Pool

import chess
import chess.engine, chess.pgn
import time

from engine.ab_depth_prune import ABDepthPruningEngine
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

            best_move = engine.play(board.copy(), chess.engine.Limit(time=0.1)).move  # 0.1 seconds for move
            try:
                board.push(best_move)
            except Exception as ex:
                print(ex)
                print(game)
                return
            node = node.add_variation(best_move)  # Add game node

            if board.is_game_over():
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
    return Game(ABDepthPruningEngine(V0Evaluator()), RandomEngine(BasicMaterialEvaluator())).play()

if __name__ == '__main__':
    # Provide the path to the Stockfish engine

    # TODO use stockfish for evaluation
    # engine_path = "/opt/homebrew/bin/stockfish"  # Update this path
    # stockfish = chess.engine.SimpleEngine.popen_uci(engine_path)

    GAMES_COUNT = 25
    white_result = 0


    with Pool(5) as pool:
        async_results = [
            pool.apply_async(play_game, ()) for _ in range(GAMES_COUNT)
        ]
        game_results = [r.get() for r in async_results]
        for i, gr in enumerate(game_results):
            print(f"Game {i} result: {gr.result}")

    white_result = sum(gr.result for gr in game_results)
    fullmove_number = sum(gr.fullmove_number for gr in game_results)
    elapsed = sum(gr.elapsed for gr in game_results)
    # Best against random: Match result: 100 : 0, Elapsed: 111.25655889511108. Fullmoves: 5888. Time per move: 0.01889547535582729
    # Best against MinMax: Match result: 18.5 : 6.5, Elapsed: 978.7190129756927. Fullmoves: 5079. Time per move: 0.1926991559314221
    # Best against MinMax (depth 5): Match result: 24 : 1, Elapsed: 1119.2212266921997. Fullmoves: 1208. Time per move: 0.9265076379902315

    print(
          f"Match result: {white_result} : {GAMES_COUNT - white_result}, "
          f"Elapsed: {elapsed}. "
          f"Fullmoves: {fullmove_number}. "
          f"Time per move: {elapsed / fullmove_number}"
      )
