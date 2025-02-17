from contextlib import contextmanager

from chess import Board, Move, scan_reversed, BB_SQUARES

class ExtendedBoard(Board):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pieces = {}
        for square in scan_reversed(self.occupied):
            self._assign_piece(square)

    @contextmanager
    def apply(self, move: Move):
        try:
            yield self.push(move)
        finally:
            self.pop()

    def push(self, move: Move):
        is_en_passant = move.to_square == self.ep_square
        super().push(move)

        if is_en_passant:
            # En passant
            column = move.to_square % 8
            row = move.from_square // 8
            del self.pieces[8*row + column]

        self.pieces.pop(move.from_square)
        self._assign_piece(move.to_square)

    def pop(self):
        move = super().pop()
        is_en_passant = move.to_square == self.ep_square
        self._assign_piece(move.from_square)
        self.pieces.pop(move.to_square)

        if is_en_passant:
            # En passant
            column = move.to_square % 8
            row = move.from_square // 8
            capture_square = 8 * row + column
            self._assign_piece(capture_square)
        return move

    def _assign_piece(self, square):
        piece_at = self.piece_at(square)
        sign = (1 if piece_at.color else -1)
        self.pieces[square] = sign * piece_at.piece_type

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