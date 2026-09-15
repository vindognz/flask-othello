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
        self.transposition_table = {}

        self.tt_hits = 0
        self.tt_lookups = 0

    def _board_key(self, board: OthelloBoard, player):
        """
        Returns an entry key for the transposition table
        """
        return (
            tuple(tuple(row) for row in board.board),
            board.current_player,
            player,
        )

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
        new_board.last_move = board.last_move
        new_board.last_flips = board.last_flips
        new_board.move_history = board.move_history[:]

        return new_board

    def _make_move_search(self, board: OthelloBoard, row, col):
            """
            Make a move for minimax and return the pieces that were flipped
            Does not touch move_history, last_move, last_flips or game_over.
            """
            player = board.current_player
            opponent = WHITE if player == BLACK else BLACK
    
            flips = []
    
            for dr, dc in DIRECTIONS:
                flips += board._walk_direction(row, col, dr, dc, player, opponent)
    
            board.board[row][col] = player
    
            for fr, fc in flips:
                board.board[fr][fc] = player
    
            board.current_player = opponent
    
            return flips
    
    def _undo_move_search(self, board: OthelloBoard, row, col, flips, player):
        """
        Undo a move made by _make_move_search()
        """
        board.board[row][col] = EMPTY

        for fr, fc in flips:
            board.board[fr][fc] = player

        board.current_player = player

    def minimax(self, board: OthelloBoard, depth, player, alpha=-float('inf'), beta=float('inf')):
        """
        I'm scared.
        """
        key = self._board_key(board, player)

        alpha_original = alpha
        beta_original = beta

        self.tt_lookups += 1 # DEBUG

        tt_entry = self.transposition_table.get(key)
        tt_move = None

        if tt_entry is not None:
            self.tt_hits += 1 # DEBUG
            stored_depth, stored_score, stored_flag, stored_move = tt_entry
            tt_move = stored_move

            if stored_depth >= depth:
                if stored_flag == "EXACT":
                    return stored_score
                elif stored_flag == "LOWER":
                    alpha = max(alpha, stored_score)
                elif stored_flag == "UPPER":
                    beta = min(beta, stored_score)

                if alpha >= beta:
                    return stored_score

        current_player = board.current_player
        valid_moves = board.get_valid_moves(current_player)

        if len(valid_moves) == 0:
            passed_board = self._copy_board(board)
            passed_board.pass_turn()
            valid_moves = passed_board.get_valid_moves(passed_board.current_player)

            # game over
            if len(valid_moves) == 0:
                opponent = WHITE if player == BLACK else BLACK
                player_count = sum(row.count(player) for row in board.board)
                opponent_count = sum(row.count(opponent) for row in board.board)

                score = (player_count - opponent_count) * 10000
                self.transposition_table[key] = (depth, score, "EXACT", None)

                return score
            
            if depth == 0:
                score = self.evaluate(board, player)
                self.transposition_table[key] = (depth, score, "EXACT", None)

                return score
            
            score = self.minimax(passed_board, depth, player, alpha, beta)
            self.transposition_table[key] = (depth, score, "EXACT", None)

            return score

        if depth == 0:
            score = self.evaluate(board, player)
            self.transposition_table[key] = (depth, score, "EXACT", None)

            return score

        is_maximising = (current_player == player)
        best_score = -float('inf') if is_maximising else float('inf')

        best_move = None

        valid_moves = sorted(valid_moves, key=lambda move: WEIGHTS[move[0]][move[1]], reverse=True)

        if tt_move in valid_moves:
            valid_moves.remove(tt_move)
            valid_moves.insert(0, tt_move)

        for row, col in valid_moves:
            mover = board.current_player

            flips = self._make_move_search(board, row, col)
            score = self.minimax(board, depth - 1, player, alpha, beta)
            self._undo_move_search(board, row, col, flips, mover)

            if is_maximising:
                if score > best_score:
                    best_score = score
                    best_move = (row, col)

                alpha = max(alpha, score)
            else:
                if score < best_score:
                    best_score = score
                    best_move = (row, col)

                beta = min(beta, score)

            if beta <= alpha:
                break

        if best_score <= alpha_original:
            flag = "UPPER"
        elif best_score >= beta_original:
            flag = "LOWER"
        else:
            flag = "EXACT"

        self.transposition_table[key] = (depth, best_score, flag, best_move)
        
        return best_score

    def get_best_move(self, board: OthelloBoard, player):
        """
        Wrapper for minimax()
        """
        if player != board.current_player:
            raise ValueError("Player must match board.current_player")

        # self.transposition_table.clear()

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
    ai = OthelloAI(depth=7)

    times = []

    with open("benchmark.log", "w") as log:
        move_number = 1

        while board.get_valid_moves(BLACK) or board.get_valid_moves(WHITE):
            try:
                subprocess.run(["clear"], check=False)
                print(board)

                t0 = time.time()
                move = ai.get_best_move(board, board.current_player)
                t1 = time.time()

                elapsed = t1 - t0
                entry = f"Move {move_number}: AI ({board.current_player}) -> {move} in {elapsed:.4f}s"

                print(entry)
                log.write(entry + "\n")
                log.flush()

                times.append(elapsed)

                if move is not None:
                    board.make_move(*move)
                else:
                    board.pass_turn()

                move_number += 1

            except KeyboardInterrupt:
                print("Exiting...")
                break

    print("Minimum time:", min(times))
    print("Maximum time:", max(times))
    print("Average time:", sum(times)/len(times))
    print("Transposition table:", len(ai.transposition_table))