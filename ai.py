""" Contains the AI """

from board import BLACK, WHITE, OthelloBoard
from bitboard import BitBoard
import random

WEIGHTS = [
	[100, -20,  10,   5,   5,  10, -20, 100],
	[-20, -50,  -2,  -2,  -2,  -2, -50, -20],
	[ 10,  -2,   1,   1,   1,   1,  -2,  10],
	[  5,  -2,   1,   0,   0,   1,  -2,   5],
	[  5,  -2,   1,   0,   0,   1,  -2,   5],
	[ 10,  -2,   1,   1,   1,   1,  -2,  10],
	[-20, -50,  -2,  -2,  -2,  -2, -50, -20],
	[100, -20,  10,   5,   5,  10, -20, 100]
]

MOBILITY_WEIGHT = 3

# weight corresponding to each bit position.
# bit 0 = (0, 0), bit 63 = (7, 7).
BIT_WEIGHTS = [
	WEIGHTS[row][col]
	for row in range(8)
	for col in range(8)
]


class OthelloAI:
	def __init__(self, depth):
		""" Initialize the OthelloAI object """
		self.depth = depth
		self.transposition_table = {}
		self.tt_hits = 0
		self.tt_lookups = 0

	def _board_key(self, board: BitBoard, player):
		""" Returns an entry key for the transposition table """
		return (board.black, board.white, board.current_player, player)

	def evaluate(self, board: BitBoard, player):
		""" Evaluate a bitboard position using positional weight and mobility """
		opponent = WHITE if player == BLACK else BLACK

		player_bits = board.black if player == BLACK else board.white
		opponent_bits = board.black if player == WHITE else board.white

		player_score = 0
		opponent_score = 0

		bits = player_bits
		while bits:
			bit = bits & -bits
			square = bit.bit_length() - 1
			player_score += BIT_WEIGHTS[square]
			bits ^= bit

		bits = opponent_bits
		while bits:
			bit = bits & -bits
			square = bit.bit_length() - 1
			opponent_score += BIT_WEIGHTS[square]
			bits ^= bit

		positional_score = player_score - opponent_score
		mobility_score = board.get_valid_moves(player).bit_count() - board.get_valid_moves(opponent).bit_count()

		return positional_score + mobility_score * MOBILITY_WEIGHT

	def minimax(self, board: BitBoard, depth, player, alpha=-float("inf"), beta=float("inf")):
		""" Minimax search using bitboards """
		key = self._board_key(board, player)
		alpha_original = alpha
		beta_original = beta

		self.tt_lookups += 1

		tt_entry = self.transposition_table.get(key)
		tt_move = None

		if tt_entry is not None:
			self.tt_hits += 1
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

		# no legal moves = pass or game over
		if not valid_moves:
			passed_board = BitBoard(black=board.black, white=board.white, current_player=board.opponent)

			passed_moves = passed_board.get_valid_moves(passed_board.current_player)

			# both players have no moves = game over
			if not passed_moves:
				player_bits = passed_board.black if player == BLACK else passed_board.white
				opponent_bits = passed_board.white if player == BLACK else passed_board.black

				score = (player_bits.bit_count() - opponent_bits.bit_count()) * 10000

				self.transposition_table[key] = (depth, score, "EXACT", None)

				return score

			# passing does not consume search depth.
			score = self.minimax(passed_board, depth, player, alpha, beta)

			self.transposition_table[key] = (depth, score, "EXACT", None)

			return score

		if depth == 0:
			score = self.evaluate(board, player)

			self.transposition_table[key] = (depth, score, "EXACT", None)

			return score

		is_maximising = current_player == player
		best_score = -float("inf") if is_maximising else float("inf")
		best_move = None

		# convert bitboard moves into (row, col).
		moves = []
		bits = valid_moves

		while bits:
			bit = bits & -bits
			square = bit.bit_length() - 1
			row = square // 8
			col = square % 8
			moves.append((row, col))
			bits ^= bit

		# same move ordering as the original AI
		moves.sort(
			key=lambda move: WEIGHTS[move[0]][move[1]],
			reverse=True
		)

		if tt_move in moves:
			moves.remove(tt_move)
			moves.insert(0, tt_move)

		for row, col in moves:
			child = board.make_move(row, col)
			score = self.minimax(child, depth - 1, player, alpha, beta)

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
		""" Accepts an OthelloBoard and returns (row, col) """
		if player != board.current_player:
			raise ValueError("Player must match board.current_player")

		bitboard = BitBoard.from_board(board)
		valid_moves = board.get_valid_moves(player)

		if not valid_moves:
			return None

		if self.depth == 0:
			return random.choice(sorted(valid_moves))

		best_score = -float("inf")
		best_move = None

		valid_moves = sorted(
			valid_moves,
			key=lambda move: WEIGHTS[move[0]][move[1]],
			reverse=True
		)

		for row, col in valid_moves:
			child = bitboard.make_move(row, col)
			score = self.minimax(child, self.depth, player)

			if score > best_score:
				best_score = score
				best_move = (row, col)

		return best_move


if __name__ == "__main__":
	import time
	import subprocess

	board = OthelloBoard()
	ai = OthelloAI(depth=6)
	times = []

	with open("benchmark.log", "w") as log:
		move_number = 1

		while board.get_valid_moves(BLACK) or board.get_valid_moves(WHITE):
			try:
				# subprocess.run(["clear"], check=False)
				print(board)

				t0 = time.time()
				move = ai.get_best_move(board, board.current_player)
				t1 = time.time()

				elapsed = t1 - t0
				entry = (
					f"Move {move_number}: "
					f"AI ({board.current_player}) -> {move} "
					f"in {elapsed:.4f}s"
				)

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

	print("Total moves:", move_number - 1)
	print("Minimum time:", min(times))
	print("Maximum time:", max(times))
	print("Average time:", sum(times) / len(times))
	print("Transposition table:", len(ai.transposition_table))
	print("TT lookups:", ai.tt_lookups)
	print("TT hits:", ai.tt_hits)
