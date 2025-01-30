"""
Example of use of GameSession and Engine to make Stockfish play itself.
"""

import chess.engine

# Provide the path to the Stockfish engine
engine_path = "/opt/homebrew/bin/stockfish"  # Update this path
engine = chess.engine.SimpleEngine.popen_uci(engine_path)

# Create a new chess board
board = chess.Board()

while board.result() == "*":
    # Get the best move from the engine
    result = engine.play(board, chess.engine.Limit(time=0.1))  # 0.5 seconds for move
    side = "White" if board.turn else "Black"
    print(f"{board.fullmove_number} {side}: {result.move}")
    board.push(result.move)

print(board.result())

# Close the engine when done
engine.quit()
