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

	def _walk_direction(self, row, col, dr, dc, player, opponent) -> list:
		r = row + dr
		c = col + dc

		to_flip = []

		while 0 <= r < 8 and 0 <= c < 8:
			cell = self.board[r][c]

			if cell == EMPTY:
				return []
			elif cell == opponent:
				to_flip.append((r, c))
			elif cell == player:
				return to_flip

			r += dr
			c += dc

		return []

	def get_valid_moves(self, player) -> list:
		valids = set()
		opponent = WHITE if player == BLACK else BLACK

		for rowIdx, row in enumerate(self.board):
			for colIdx, cell in enumerate(row):
				if cell == EMPTY:
					for dr, dc in DIRECTIONS:
						if self._walk_direction(rowIdx, colIdx, dr, dc, player, opponent):
							valids.add((rowIdx, colIdx))

		return valids

	def make_move(self, player, row, col) -> None:
		opponent = WHITE if player == BLACK else BLACK

		flips = []
		for dr, dc in DIRECTIONS:
			flips += self._walk_direction(row, col, dr, dc, player, opponent)

		if not flips:
			raise ValueError(f"Invalid move: ({row}, {col})")

		self.board[row][col] = player
		for fr, fc in flips:
			self.board[fr][fc] = player


if __name__ == "__main__":
	board = OthelloBoard()
	print(board)
	print(board.get_valid_moves(BLACK))
	board.make_move(BLACK, 2, 3)
	print(board)