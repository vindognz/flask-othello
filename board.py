""" FlaskOthello board repr """

EMPTY = 0
BLACK = 1
WHITE = 2

SYMBOLS = {
	EMPTY: " ·",
	BLACK: "⚫",
	WHITE: "⚪"
}

DIRECTIONS = [
	[-1, 1],
	[0, 1],
	[1, 1],
	[1, 0],
	[1, -1],
	[0, -1],
	[-1, -1],
	[-1, 0]
]

class OthelloBoard:
	def __init__(self):
		""" Initialize the standard Othello starting position. """
		self.board = [[EMPTY] * 8 for _ in range(8)]
		
		# Standard start pos = white at d4 + e5, black at e4 + d5
		self.board[3][3] = WHITE
		self.board[3][4] = BLACK
		self.board[4][3] = BLACK
		self.board[4][4] = WHITE

	def __repr__(self) -> str:
		"""Pretty priont the board."""
		lines = ["   a  b  c  d  e  f  g  h"]
		for i, row in enumerate(self.board):
			line = f"{i+1} "
			line += " ".join(SYMBOLS[piece] for piece in row)
			lines.append(line)
		return "\n".join(lines)

	def get_valid_moves(self, player) -> list:
		valids = []
		opponent = WHITE if player == BLACK else WHITE

		for rowIdx, row in enumerate(self.board):
			for colIdx, cell in enumerate(row):
				if cell == EMPTY:
					for dr, dc in DIRECTIONS:
						r = rowIdx + dr
						c = colIdx + dc

						other_colour_found = False

						while 0 <= r < 8 and 0 <= c < 8:
							if self.board[r][c] == EMPTY:
								break
							elif self.board[r][c] == opponent:
								other_colour_found = True

							if self.board[r][c] == player and other_colour_found:
								valids.append((rowIdx, colIdx))
								break

							r += dr
							c += dc

		return valids

	def make_move(self, player, row, col) -> None:
		opponent = WHITE if player == BLACK else WHITE

		if (row, col) in self.get_valid_moves(player):
			self.board[row][col] = player

			for dr, dc in DIRECTIONS:
				r = row + dr
				c = col + dc
				to_flip = []

				while 0 <= r < 8 and 0 <= c < 8:
					if self.board[r][c] == EMPTY:
						break
					elif self.board[r][c] == opponent:
						to_flip.append((r, c))
					elif self.board[r][c] == player:
						# found our piece, flip everything collected
						for fr, fc in to_flip:
							self.board[fr][fc] = player
						break

					r += dr
					c += dc


if __name__ == "__main__":
	board = OthelloBoard()
	print(board)
	print(board.get_valid_moves(BLACK))
	board.make_move(BLACK, 2, 3)
	print(board)