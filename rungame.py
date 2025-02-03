"""
Example of use of GameSession and Engine to make Stockfish play itself.
"""
from dataclasses import dataclass

import chess
import chess.engine, chess.pgn
import time

from engines import RandomEngine, AlphaBetaEngine, BasicMaterialEvaluator, AdvancedMaterialEvaluator


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


if __name__ == '__main__':
    # Provide the path to the Stockfish engine

    # TODO use stockfish for evaluation
    # engine_path = "/opt/homebrew/bin/stockfish"  # Update this path
    # stockfish = chess.engine.SimpleEngine.popen_uci(engine_path)

    GAMES_COUNT = 100
    white_result = 0

    game_results = []
    for i in range(GAMES_COUNT):
        game_result = Game(AlphaBetaEngine(AdvancedMaterialEvaluator()), AlphaBetaEngine(BasicMaterialEvaluator())).play()
        print(f"Game {i} result: {game_result.result}")
        game_results.append(game_result)

    white_result = sum(gr.result for gr in game_results)
    fullmove_number = sum(gr.fullmove_number for gr in game_results)
    elapsed = sum(gr.elapsed for gr in game_results)
    # Best against random: Match result: 25 : 0, Elapsed: 149.67 (but quite a lot time elapsed)
    # Match result: 10 : 0, Elapsed: 76.9123067855835. Fullmoves: 273. Time per move: 0.2817300614856538
    print(
          f"Match result: {white_result} : {GAMES_COUNT - white_result}, "
          f"Elapsed: {elapsed}. "
          f"Fullmoves: {fullmove_number}. "
          f"Time per move: {elapsed / fullmove_number}"
      )
