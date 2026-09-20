""" Bitboard representation for Othello AI search """

from board import EMPTY, BLACK, WHITE

FULL_BOARD = (1 << 64) - 1

NOT_A_FILE = 0xfefefefefefefefe
NOT_H_FILE = 0x7f7f7f7f7f7f7f7f

DIRECTIONS = (
    ( 8,  FULL_BOARD),        # down
    (-8, FULL_BOARD),         # up
    ( 1,  NOT_A_FILE),        # right
    (-1, NOT_H_FILE),         # left
    ( 9,  NOT_A_FILE),        # down-right
    ( 7,  NOT_H_FILE),        # down-left
    (-7, NOT_A_FILE),         # up-right
    (-9, NOT_H_FILE),         # up-left
)

class BitBoard:
    def __init__(self, black=0, white=0, current_player=BLACK):
        """ Initializes a BitBoard object """
        self.black = black
        self.white = white
        self.current_player = current_player
        self._cached_moves = None

    @classmethod
    def from_board(cls, board):
        black = 0
        white = 0

        for row in range(8):
            for col in range(8):
                bit = 1 << (row * 8 + col)

                if board.board[row][col] == BLACK:
                    black |= bit
                elif board.board[row][col] == WHITE:
                    white |= bit

        return cls(black=black, white=white, current_player=board.current_player)

    def to_board(self):
        board = [[EMPTY] * 8 for _ in range(8)]

        for row in range(8):
            for col in range(8):
                bit = 1 << (row * 8 + col)

                if self.black & bit:
                    board[row][col] = BLACK
                elif self.white & bit:
                    board[row][col] = WHITE

        return board

    @property
    def opponent(self):
        return WHITE if self.current_player == BLACK else BLACK

    def _player_bits(self, player):
        return self.black if player == BLACK else self.white

    def _set_player_bits(self, player, bits):
        if player == BLACK:
            self.black = bits
        else:
            self.white = bits

    def _compute_valid_moves(self, player):
        """ Actually calculate the valid-move bitmask (no caching yet) """
        player_bits = self._player_bits(player)
        opponent_bits = self._player_bits(WHITE if player == BLACK else BLACK)

        empty = FULL_BOARD & ~(player_bits | opponent_bits)
        moves = 0

        for shift, mask in DIRECTIONS:
            if shift > 0:
                x = (player_bits << shift) & mask
            else:
                x = (player_bits >> -shift) & mask

            x &= opponent_bits
            potential = x

            while x:
                if shift > 0:
                    x = (x << shift) & mask
                else:
                    x = (x >> -shift) & mask

                x &= opponent_bits
                potential |= x

            if shift > 0:
                moves |= (potential << shift) & mask
            else:
                moves |= (potential >> -shift) & mask

        return moves & empty

    def get_valid_moves(self, player=None):
        """ Get the valid-move bitmask and cache it """
        if player is None:
            player = self.current_player

        if player == self.current_player:
            if self._cached_moves is None:
                self._cached_moves = self._compute_valid_moves(player)
            return self._cached_moves

        return self._compute_valid_moves(player)

    def make_move(self, row, col):
        """ Return a new BitBoard with the move applied. """
        move = 1 << (row * 8 + col)
        player = self.current_player
        opponent = self.opponent

        player_bits = self._player_bits(player)
        opponent_bits = self._player_bits(opponent)

        flipped = 0

        for shift, mask in DIRECTIONS:
            if shift > 0:
                x = (move << shift) & mask
            else:
                x = (move >> -shift) & mask

            captured = 0

            while x & opponent_bits:
                captured |= x
                if shift > 0:
                    x = (x << shift) & mask
                else:
                    x = (x >> -shift) & mask

            if x & player_bits:
                flipped |= captured

        player_bits |= move | flipped
        opponent_bits &= ~flipped

        if player == BLACK:
            black, white = player_bits, opponent_bits
        else:
            black, white = opponent_bits, player_bits

        result = BitBoard(black=black, white=white, current_player=opponent)

        # populate the new board's cache directly
        next_player_moves = result._compute_valid_moves(opponent)

        if next_player_moves:
            result._cached_moves = next_player_moves
            return result

        mover_moves = result._compute_valid_moves(player)

        if not mover_moves:
            # neither player has a move = game over, current_player stays as opponent
            result._cached_moves = next_player_moves
            return result

        # opponent has no moves = pass back to the original mover
        result.current_player = player
        result._cached_moves = mover_moves
        return result



if __name__ == "__main__":
    from board import OthelloBoard

    board = OthelloBoard()

    for move_number in range(60):
        bitboard = BitBoard.from_board(board)

        normal_moves = board.get_valid_moves(board.current_player)
        bb_moves = bitboard.get_valid_moves(board.current_player)

        converted_moves = {
            (square // 8, square % 8)
            for square in range(64)
            if bb_moves & (1 << square)
        }

        assert normal_moves == converted_moves, (
            f"Move generation mismatch on move {move_number}!\n"
            f"Normal: {normal_moves}\n"
            f"Bitboard: {converted_moves}"
        )

        if not normal_moves:
            print("\nGame over!")
            break

        move = sorted(normal_moves)[0]

        board.make_move(*move)
        bitboard = bitboard.make_move(*move)

        assert bitboard.to_board() == board.board, (
            f"Position mismatch after move {move_number}!\n"
            f"Move: {move}"
        )

        assert bitboard.current_player == board.current_player, (
            f"Player mismatch after move {move_number}!\n"
            f"BitBoard: {bitboard.current_player}\n"
            f"Board: {board.current_player}"
        )

        print(f"Move {move_number}: {move}")

    print("\nBitBoard survived move generation + make_move!")