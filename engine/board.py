from contextlib import contextmanager

from chess import Board, Move, scan_reversed, BB_SQUARES, PAWN

class ExtendedBoard(Board):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pieces_map = {}
        for square in scan_reversed(self.occupied):
            self._assign_piece(square)


    @contextmanager
    def apply(self, move: Move):
        try:
            yield self.push(move)
        finally:
            self.pop()

    def push(self, move: Move):
        is_en_passant = self.is_en_passant(move)
        super().push(move)

        del self.pieces_map[move.from_square]
        self._assign_piece(move.to_square)

        if is_en_passant:
            # En passant
            column = move.to_square % 8
            row = move.from_square // 8
            del self.pieces_map[8 * row + column]


    def pop(self):
        move = super().pop()
        is_en_passant = self.is_en_passant(move)

        self._assign_piece(move.from_square)
        self._assign_piece(move.to_square)

        if is_en_passant:
            # En passant
            column = move.to_square % 8
            row = move.from_square // 8
            capture_square = 8 * row + column
            self._assign_piece(capture_square)
        return move

    def _assign_piece(self, square):
        piece_at = self.piece_at(square)
        if piece_at:
            sign = (1 if piece_at.color else -1)
            self.pieces_map[square] = sign * piece_at.piece_type
        else:
            del self.pieces_map[square]

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