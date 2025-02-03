"""
Example of use of GameSession and Engine to make Stockfish play itself.
"""

import chess
import chess.engine, chess.pgn
import time

from engines import RandomEngine, AlphaBetaEngine


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

        while board.result() == "*":
            # Get the best move from the engine
            if board.turn:
                engine = self.white
            else:
                engine = self.black

            best_move = engine.play(board.copy(), chess.engine.Limit(time=0.1)).move  # 0.1 seconds for move
            board.push(best_move)
            node = node.add_variation(best_move)  # Add game node

            if board.is_game_over():
                break


        # Close the engine when done
        self.white.quit()
        self.black.quit()

        print(game) # PGN

        best_move = board.result()
        match best_move:
            case "1-0":
                return 1
            case "0-1":
                return 0
            case _:
                return 0.5


if __name__ == '__main__':
    # Provide the path to the Stockfish engine

    # TODO use stockfish for evaluation
    # engine_path = "/opt/homebrew/bin/stockfish"  # Update this path
    # stockfish = chess.engine.SimpleEngine.popen_uci(engine_path)

    GAMES_COUNT = 25
    white_result = 0


    start = time.time()
    for i in range(GAMES_COUNT):
        game_result = Game(AlphaBetaEngine(), RandomEngine()).play()
        if game_result < 1:
            break
        end = time.time()
        print(f"Game {i}: {game_result}, Elapsed: {end-start}")
        white_result += game_result

    end = time.time()
    # Match result: 24.0 : 1.0, Elapsed: 65.82187390327454
    print(f"Match result: {white_result} : {GAMES_COUNT - white_result}, Elapsed: {end-start}")
