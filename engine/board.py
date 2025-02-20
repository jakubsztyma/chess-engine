from contextlib import contextmanager

from chess import Board, Move, scan_reversed, BB_SQUARES, PAWN, square_file, ROOK

CASTLING_ROOK_MOVES = {
    (4, 6): (7, 5),
    (4, 2): (0, 3),
    (60, 62): (63,61),
    (60, 58): (56,59),
}

class ExtendedBoard(Board):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pieces_map = {}
        for square in scan_reversed(self.occupied):
            piece_type_at = self.piece_type_at(square)
            if piece_type_at:
                self.pieces_map[square] = piece_type_at


    @contextmanager
    def apply(self, move: Move):
        try:
            yield self.push(move)
        finally:
            self.pop()

    def is_castling(self, move: Move) -> bool:
        if self.kings & BB_SQUARES[move.from_square]:
            column_diff = (move.from_square & 7) - (move.to_square & 7)
            return column_diff < -1 or 1 < column_diff
        return False

    def push(self, move: Move):
        is_en_passant = self.is_en_passant(move)
        is_castling = self.is_castling(move)
        super().push(move)

        if move.from_square != 0 or move.to_square != 0: # Not null
            if is_castling:
                rook_from, rook_to = CASTLING_ROOK_MOVES[(move.from_square, move.to_square)]
                del self.pieces_map[rook_from]
                self.pieces_map[rook_to] = ROOK

            if is_en_passant:
                # En passant
                column = move.to_square % 8
                row = move.from_square // 8
                del self.pieces_map[8 * row + column]

            piece = self.pieces_map.pop(move.from_square)
            self.pieces_map[move.to_square] = piece


    def pop(self):
        move = super().pop()

        if move.from_square != 0 or move.to_square != 0: # Not null
            piece_type = self.pieces_map.pop(move.to_square)
            self.pieces_map[move.from_square] = piece_type
            # Assign piece to to_square if it was a capture
            piece_type_at = self.piece_type_at(move.to_square)
            if piece_type_at:
                self.pieces_map[move.to_square] = piece_type_at

            if  self.is_en_passant(move):
                # En passant
                column = move.to_square % 8
                row = move.from_square // 8
                capture_square = 8 * row + column
                self.pieces_map[capture_square] = self.piece_type_at(capture_square)
            elif self.is_castling(move):
                rook_from, rook_to = CASTLING_ROOK_MOVES[(move.from_square, move.to_square)]
                del self.pieces_map[rook_to]
                self.pieces_map[rook_from] = ROOK
        return move

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