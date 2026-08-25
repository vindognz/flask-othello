"""Contains the AI"""

from board import EMPTY, BLACK, WHITE, SYMBOLS, DIRECTIONS, OthelloBoard

WEIGHTS = [
    [100, -20,  10,   5,   5,  10, -20, 100],
    [-20, -50, - 2, - 2, - 2, - 2, -50, -20],
    [ 10, - 2,   1,   1,   1,   1, - 2,  10],
    [  5, - 2,   1,   0,   0,   1, - 2,   5],
    [  5, - 2,   1,   0,   0,   1, - 2,   5],
    [ 10, - 2,   1,   1,   1,   1, - 2,  10],
    [-20, -50, - 2, - 2, - 2, - 2, -50, -20],
    [100, -20,  10,   5,   5,  10, -20, 100]
]

MOBILITY_WEIGHT = 3 # value determined by some trialing

class OthelloAI:
    def __init__(self, depth):
        """
        Initialize the OthelloAI object
        """
        self.depth = depth

    def evaluate(self, board: OthelloBoard, player):
        """
        Evaluates the board position by a positional weight and mobility heuristic
        If the return value is greater than zero, the player is winning
        If the return value is lower than zero, the opponent is winning
        If the return value IS zero, the game position is equal
        """
        opponent = WHITE if player == BLACK else BLACK

        player_score = 0
        opponent_score = 0

        for row_idx, row in enumerate(board.board):
            for col_idx, cell in enumerate(row):
                if cell == player:
                    player_score += WEIGHTS[row_idx][col_idx]
                elif cell == opponent:
                    opponent_score += WEIGHTS[row_idx][col_idx]

        positional_score = player_score - opponent_score
        mobility_score = len(board.get_valid_moves(player)) - len(board.get_valid_moves(opponent))

        return positional_score + mobility_score * MOBILITY_WEIGHT

    def _copy_board(self, board: OthelloBoard):
        new_board = OthelloBoard.__new__(OthelloBoard)
        new_board.board = [row[:] for row in board.board]
        new_board.current_player = board.current_player

        return new_board

    def minimax(self, board: OthelloBoard, depth, player, alpha=-float('inf'), beta=float('inf')):
        """
        I'm scared.
        """
        if depth == 0:
            return self.evaluate(board, player)

        current_player = board.current_player
        valid_moves = board.get_valid_moves(current_player)

        if len(valid_moves) == 0:
            board.pass_turn()
            valid_moves = board.get_valid_moves(board.current_player)

            if len(valid_moves) == 0:
                # game over
                opponent = WHITE if player == BLACK else BLACK
                player_count = sum(row.count(player) for row in board.board)
                opponent_count = sum(row.count(opponent) for row in board.board)
                return (player_count - opponent_count) * 10000
            else:
                return self.minimax(board, depth, player, alpha, beta)

        is_maximising = (current_player == player)
        best_score = -float('inf') if is_maximising else float('inf')

        valid_moves = sorted(valid_moves, key=lambda move: WEIGHTS[move[0]][move[1]], reverse=True)

        for row, col in valid_moves:
            new_board = self._copy_board(board)
            new_board.make_move(row, col)

            score = self.minimax(new_board, depth - 1, player, alpha, beta)

            if is_maximising:
                best_score = max(best_score, score)
                alpha = max(alpha, score)
            else:
                best_score = min(best_score, score)
                beta = min(beta, score)

            if beta <= alpha:
                break

        return best_score

    def get_best_move(self, board: OthelloBoard, player):
        """
        Wrapper for minimax()
        """
        valid_moves = board.get_valid_moves(player)
        best_score = -float('inf')
        best_move = None

        valid_moves = sorted(valid_moves, key=lambda move: WEIGHTS[move[0]][move[1]], reverse=True)

        for row, col in valid_moves:
            new_board = self._copy_board(board)
            new_board.make_move(row, col)

            score = self.minimax(new_board, self.depth, player)

            if score > best_score:
                best_score = score
                best_move = (row, col)

        return best_move


if __name__ == "__main__":
    import time
    import subprocess
    board = OthelloBoard()
    ai = OthelloAI(depth=3)

    times = []

    while board.get_valid_moves(BLACK) or board.get_valid_moves(WHITE):
        try:
            subprocess.run(["clear"], check=False)
            print(board)
            t0 = time.time()
            move = ai.get_best_move(board, board.current_player)
            t1 = time.time()
            print(f"AI ({board.current_player}) picked: {move} in {t1-t0:.2f}s")
            times.append(t1-t0)

            if move is not None:
                board.make_move(*move)
            else:
                board.pass_turn()

            # time.sleep(0.5)

        except KeyboardInterrupt:
            print("Exiting...")
            break

    print("Minimum time:", min(times))
    print("Maximum time:", max(times))
    print("Average time:", sum(times)/len(times))