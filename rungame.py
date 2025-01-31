"""
Example of use of GameSession and Engine to make Stockfish play itself.
"""

import chess
import chess.engine

from engines import RandomEngine


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

            result = engine.play(board, chess.engine.Limit(time=0.1))  # 0.5 seconds for move
            print(f"{board.fullmove_number} {side}: {result.move}")
            board.push(result.move)

        print(board.result())

        # Close the engine when done
        self.white.quit()
        self.black.quit()

if __name__ == '__main__':
    # Provide the path to the Stockfish engine
    engine_path = "/opt/homebrew/bin/stockfish"  # Update this path
    stockfish = chess.engine.SimpleEngine.popen_uci(engine_path)

    Game(stockfish, RandomEngine()).play()