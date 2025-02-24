from contextlib import contextmanager

from chess import Board, Move, BB_SQUARES, BB_ALL, msb

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

    def is_castling(self, move: Move) -> bool:
        if self.kings & BB_SQUARES[move.from_square]:
            column_diff = (move.from_square & 7) - (move.to_square & 7)
            return column_diff < -1 or 1 < column_diff
        return False

    def generate_almost_legal_fast(self):
        king_mask = self.kings & self.occupied_co[self.turn]
        king = msb(king_mask)
        checkers = self.attackers_mask(not self.turn, king)
        if checkers:
            blockers = self._slider_blockers(king)
            for move in self._generate_evasions(king, checkers, BB_ALL, BB_ALL):
                if self._is_safe(king, blockers, move):
                    yield move
        else:
            # Do not check if the move is safe if there is no check
            yield from self.generate_pseudo_legal_moves(BB_ALL, BB_ALL)