from contextlib import contextmanager

from chess import Board, Move

class ExtendedBoard(Board):
    @contextmanager
    def apply(self, move: Move):
        try:
            yield self.push(move)
        finally:
            self.pop()

    def check_game_over(self) -> int | None:
        """Faster version of board.is_game_over"""
        # TODO faster versions of used functions (eg use already generated moves to check checkmate)?
        # TODO add stalemate condition (reuse generate_legal_moves?)
        # Normal game end.
        if self.is_checkmate():
            return 1 if not self.turn else -1
        if self.pawns | self.rooks | self.queens == 0:
            return 0
        if not any(self.generate_legal_moves()):
            return 0

        if self.is_fifty_moves():
            return 0
        if self.is_repetition(2):
            return 0

        return None