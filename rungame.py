"""
Example of use of GameSession and Engine to make Stockfish play itself.
"""

import chess
import chess.engine
import time

from engines import RandomEngine, MinMaxEngine, AlphaBetaEngine


# Create a new chess board
class Game:
    def __init__(self, white, black):
        self.white = white
        self.black = black

    def play(self):
        board = chess.Board()

        while board.result() == "*":
            # Get the best move from the engine
            if board.turn:
                side = "White"
                engine = self.white
            else:
                side = "Black"
                engine = self.black

            result = engine.play(board.copy(), chess.engine.Limit(time=0.1))  # 0.1 seconds for move
            # print(f"{board.fullmove_number} {side}: {result.move}")
            board.push(result.move)
            if board.is_game_over():
                break


        # Close the engine when done
        self.white.quit()
        self.black.quit()

        result = board.result()
        match result:
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
        end = time.time()
        print(f"Game {i}: {game_result}, Elapsed: {end-start}")
        white_result += game_result

    end = time.time()
    # Match result: 23.5 : 1.5, Elapsed: 143.66650891304016
    print(f"Match result: {white_result} : {GAMES_COUNT - white_result}, Elapsed: {end-start}")
