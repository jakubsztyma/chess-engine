from contextlib import contextmanager

from chess import Board, Move, scan_reversed, BB_SQUARES, PAWN, square_file

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

    def is_castling(self, move: Move) -> bool:
        if move.from_square in (4, 60):
            if self.kings & BB_SQUARES[move.from_square]:
                column_diff = (move.from_square - move.to_square) & 7
                return column_diff < -1 or 1 < column_diff
        return False

    def push(self, move: Move):
        is_en_passant = self.is_en_passant(move)
        is_castling = self.is_castling(move)
        super().push(move)

        if is_castling:
            # TODO optimize
            self._assign_piece(0)
            self._assign_piece(3)
            self._assign_piece(5)
            self._assign_piece(7)
            self._assign_piece(56)
            self._assign_piece(59)
            self._assign_piece(61)
            self._assign_piece(63)

        if is_en_passant:
            # En passant
            column = move.to_square % 8
            row = move.from_square // 8
            del self.pieces_map[8 * row + column]

        piece = self.pieces_map.pop(move.from_square)
        self.pieces_map[move.to_square] = piece


    def pop(self):
        move = super().pop()
        piece_type = self.pieces_map.pop(move.to_square)
        self.pieces_map[move.from_square] = piece_type
        self._assign_piece(move.to_square)

        if  self.is_en_passant(move):
            # En passant
            column = move.to_square % 8
            row = move.from_square // 8
            capture_square = 8 * row + column
            self._assign_piece(capture_square)
        elif self.is_castling(move):
            # TODO optimize
            self._assign_piece(0)
            self._assign_piece(3)
            self._assign_piece(5)
            self._assign_piece(7)
            self._assign_piece(56)
            self._assign_piece(59)
            self._assign_piece(61)
            self._assign_piece(63)
        return move

    def _assign_piece(self, square: int):
        piece_type_at = self.piece_type_at(square)
        if piece_type_at:
            self.pieces_map[square] = piece_type_at
        else:
            self.pieces_map.pop(square,  None)

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