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
		"""
		Initialize the standard Othello starting position.

		>>> board = OthelloBoard()
		>>> board.board[3][3], board.board[3][4]
		(2, 1)
		>>> board.board[4][3], board.board[4][4]
		(1, 2)
		>>> sum(row.count(EMPTY) for row in board.board)
		60
		"""
		self.board = [[EMPTY] * 8 for _ in range(8)]
		
		# Standard start pos = white at d4 + e5, black at e4 + d5
		self.board[3][3] = WHITE
		self.board[3][4] = BLACK
		self.board[4][3] = BLACK
		self.board[4][4] = WHITE

	def __repr__(self) -> str:
		"""
		Pretty print the board.

		>>> board = OthelloBoard()
		>>> print(board)
		   a  b  c  d  e  f  g  h
		1  ·  ·  ·  ·  ·  ·  ·  ·
		2  ·  ·  ·  ·  ·  ·  ·  ·
		3  ·  ·  ·  ·  ·  ·  ·  ·
		4  ·  ·  · ⚪ ⚫  ·  ·  ·
		5  ·  ·  · ⚫ ⚪  ·  ·  ·
		6  ·  ·  ·  ·  ·  ·  ·  ·
		7  ·  ·  ·  ·  ·  ·  ·  ·
		8  ·  ·  ·  ·  ·  ·  ·  ·
		"""
		lines = ["   a  b  c  d  e  f  g  h"]
		for i, row in enumerate(self.board):
			line = f"{i+1} "
			line += " ".join(SYMBOLS[piece] for piece in row)
			lines.append(line)
		return "\n".join(lines)

	def _walk_direction(self, row, col, dr, dc, player, opponent) -> list:
		"""
		Walk one direction from (row, col); return opponent positions to
		flip, or [] if the direction doesn't end in player's own piece.

		>>> board = OthelloBoard()

		# From d3 (2,3), walking down (1,0): hits white at d4, black at d5
		>>> board._walk_direction(2, 3, 1, 0, BLACK, WHITE)
		[(3, 3)]

		# From d3 (2,3), walking right (0,1): immediately empty, invalid
		>>> board._walk_direction(2, 3, 0, 1, BLACK, WHITE)
		[]

		# Walking off the edge of the board without hitting own piece
		>>> board._walk_direction(0, 0, -1, -1, BLACK, WHITE)
		[]
		"""
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
		"""
		Return the set of all legal (row, col) moves for player.

		>>> board = OthelloBoard()
		>>> sorted(board.get_valid_moves(BLACK))
		[(2, 3), (3, 2), (4, 5), (5, 4)]
		>>> sorted(board.get_valid_moves(WHITE))
		[(2, 4), (3, 5), (4, 2), (5, 3)]
		"""
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
		"""
		Place player's piece at (row, col) and flip captured pieces.
		Raises ValueError if the move is illegal.

		>>> board = OthelloBoard()
		>>> board.make_move(BLACK, 2, 3)
		>>> board.board[2][3], board.board[3][3]
		(1, 1)
		>>> board.make_move(BLACK, 0, 0)
		Traceback (most recent call last):
			...
		ValueError: Invalid move: (0, 0)
		"""
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
	import doctest
	doctest.testmod()

	import ai

	board = OthelloBoard()
	print(board)
	AI = ai.OthelloAI(1)
	print(AI.evaluate(board, BLACK))
	# print(board.get_valid_moves(BLACK))
	# board.make_move(BLACK, 2, 3)
	# print(board)