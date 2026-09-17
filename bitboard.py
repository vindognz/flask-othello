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
    def occupied(self):
        return self.black | self.white

    @property
    def empty(self):
        return FULL_BOARD & ~self.occupied

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

    def get_valid_moves(self, player=None):
        if player is None:
            player = self.current_player

        player_bits = self._player_bits(player)
        opponent_bits = self._player_bits(
            WHITE if player == BLACK else BLACK
        )

        empty = self.empty
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

        if normal_moves != converted_moves:
            print(f"\nMISMATCH ON MOVE {move_number}")
            print(board)
            print("Normal:  ", sorted(normal_moves))
            print("Bitboard:", sorted(converted_moves))
            print()

            # which squares differ
            print("Missing from bitboard:")
            print(sorted(normal_moves - converted_moves))

            print("Extra in bitboard:")
            print(sorted(converted_moves - normal_moves))

            break

        print(f"Move {move_number}: {len(normal_moves)} valid moves")

        if not normal_moves:
            board.pass_turn()

            if not board.get_valid_moves(board.current_player):
                print("\nGame over — both players have no moves.")
                break

            continue

        move = sorted(normal_moves)[0]
        board.make_move(*move)

    else:
        print("\nBitboard worked the entire game")