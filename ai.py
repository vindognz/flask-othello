"""Contains the AI"""

from board import EMPTY, BLACK, WHITE, SYMBOLS, DIRECTIONS, OthelloBoard

class OthelloAI:
    def __init__(self, depth):
        """
        Initialize the OthelloAI object
        """
        self.depth = depth

    def evaluate(self, board: OthelloBoard, player):
        """
        Evaluates the board position by a simple piece counting heuristic
        If the return value is greater than zero, the player is winning
        If the return value is lower than zero, the opponent is winning
        If the return value IS zero, the game position is equal
        """
        opponent = WHITE if player == BLACK else BLACK

        player_count = sum(row.count(player) for row in board.board)
        opponent_count = sum(row.count(opponent) for row in board.board)

        return player_count - opponent_count

    def _copy_board(self, board: OthelloBoard):
        new_board = OthelloBoard()
        new_board.board = [row[:] for row in board.board]

        return new_board

    def minimax(self, board: OthelloBoard, depth, current_player, player):
        """
        I'm scared.
        """

        if depth == 0:
            return self.evaluate(board, player)

        valid_moves = board.get_valid_moves(current_player)

        if len(valid_moves) == 0:
            current_player = WHITE if current_player == BLACK else BLACK

            valid_moves = board.get_valid_moves(current_player)

            if len(valid_moves) == 0:
                return self.evaluate(board, player) # game over
            else:
                return self.minimax(board, depth, current_player, player)

        opponent = WHITE if current_player == BLACK else BLACK
        is_maximising = (current_player == player)
        best_score = -float('inf') if is_maximising else float('inf')

        for row, col in valid_moves:
            new_board = self._copy_board(board)
            new_board.make_move(current_player, row, col)

            score = self.minimax(new_board, depth-1, opponent, player)
            best_score = max(best_score, score) if is_maximising else min(best_score, score)

        return best_score

    def get_best_move(self, board: OthelloBoard, player):
        """
        Wrapper for minimax()
        """
        valid_moves = board.get_valid_moves(player)
        best_score = -float('inf')
        best_move = None

        opponent = WHITE if player == BLACK else BLACK

        for row, col in valid_moves:
            new_board = self._copy_board(board)
            new_board.make_move(player, row, col)

            score = self.minimax(new_board, self.depth, opponent, player)

            if score > best_score:
                best_score = score
                best_move = (row, col)

        return best_move


if __name__ == "__main__":
    import time
    import os
    board = OthelloBoard()
    ai = OthelloAI(depth=4)

    player = BLACK

    while board.get_valid_moves(BLACK) or board.get_valid_moves(WHITE):
        os.system('clear')
        print(board)
        t0 = time.time()
        move = ai.get_best_move(board, player)
        t1 = time.time()
        print(f"AI ({player}) picked: {move} in {t1-t0:.2f}s")

        if move is not None:
            board.make_move(player, *move)

        player = WHITE if player == BLACK else BLACK

        # time.sleep(0.5)