""" Flask backend for FlaskOthello """

from flask import Flask, jsonify, request, session, render_template, redirect
import secrets

from board import OthelloBoard, BLACK, WHITE
from ai import OthelloAI

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Constants
GAME_ID_LENGTH = 4

games = {}     # game_id -> {"board": OthelloBoard, "black_session": str|None, "white_session": str|None}
archives = {}  # game_id -> {"board": list, "black": int, "white": int}  (final, read-only state)

def get_or_create_player_id() -> str:
    """ Return this browser's player_id, or create one if needed. """
    if "player_id" not in session:
        session["player_id"] = secrets.token_hex(8)
    return session["player_id"]

def resolve_player(game_id):
    """ Looks up the game and the caller's colour.
        Returns (game, board, player_colour) on success,
        or      (None, None, error_response) on failure.
    """

    if game_id not in games:
        return None, None, (jsonify({"error": "Game not found"}), 404)

    game = games[game_id]
    board = game["board"]
    player = get_or_create_player_id()

    player_colour = None
    if game["white_session"] == player:
        player_colour = WHITE
    elif game["black_session"] == player:
        player_colour = BLACK

    if not player_colour:
        return None, None, (jsonify({"error": "Spectators can't do that"}), 403)

    return game, board, player_colour

def opponent_is_ai(game, your_colour):
    """ Returns True if the seat opposite to your_colour is controlled by the AI. """
    if your_colour is None:
        return False

    opponent_seat = game["white_session"] if your_colour == BLACK else game["black_session"]
    return get_ai_depth(opponent_seat) is not None

def get_ai_depth(session_value):
    """ Return AI depth if this seat is AI-controlled, else None. """
    if isinstance(session_value, str) and session_value.startswith("AI:"):
        return int(session_value.split(":")[1].strip())
    return None

def serialize_game(board: OthelloBoard, your_colour, both_joined, opponent_ai, draw_offered_by):
    """ Build the JSON response shared by /game, /move and /ai-move """
    return {
        "board": board.board,
        "current_player": board.current_player,
        "your_colour": your_colour,
        "current_legal_moves": list(board.get_valid_moves(board.current_player)),
        "both_joined": both_joined,
        "last_move": list(board.last_move) if board.last_move else None,
        "game_over": board.game_over,
        "opponent_is_ai": opponent_ai,
        "draw_offered_by": draw_offered_by
    }

def archive_game(game_id, board: OthelloBoard, resigned_colour=None, agreed_draw=False):
    """ Archive a completed game's state and delete it's entry in games """
    print("[archive_game()] i am archiving the game")
    black_count = sum(row.count(BLACK) for row in board.board)
    white_count = sum(row.count(WHITE) for row in board.board)

    archives[game_id] = {
        "board": board.board,
        "black_count": black_count,
        "white_count": white_count,
        "last_move": list(board.last_move) if board.last_move else None,
        "resigned_colour": resigned_colour,
        "agreed_draw": agreed_draw,
    }

    del games[game_id]

def play_ai_turns(game_id, game, board: OthelloBoard):
    """ Play AI turns until a human's turn, or the game ends.
        Archives the game and returns True if it ended during this call.
    """
    while not board.game_over:
        current_seat = game["white_session"] if board.current_player == WHITE else game["black_session"]
        depth = get_ai_depth(current_seat)
        if depth is None:
            break

        ai = OthelloAI(depth=depth)
        ai_move = ai.get_best_move(board, board.current_player)
        if ai_move is not None:
            board.make_move(*ai_move)
        else:
            board.pass_turn()

    if board.game_over:
        archive_game(game_id, board)
        return True
    return False

def check_draw_offer(game_id, game, board):
    """ If there's a pending draw offer and the opponent is AI, let it pick """
    if game["draw_offered_by"] is None:
        return False

    offerer_colour = game["draw_offered_by"]
    ai_colour = WHITE if offerer_colour == BLACK else BLACK
    ai_seat = game["white_session"] if ai_colour == WHITE else game["black_session"]

    if get_ai_depth(ai_seat) is None:
        return False # opponent isn't AI so there's nothing to auto decide

    ai_count = sum(row.count(ai_colour) for row in board.board)
    opponent_count = sum(row.count(offerer_colour) for row in board.board)

    if ai_count < opponent_count:
        archive_game(game_id, board, agreed_draw=True)
        return True
    else:
        game["draw_offered_by"] = None
        return False


@app.route("/api/game/new", methods=['POST'])
def new_game():
    player_id = get_or_create_player_id()

    data = request.get_json(silent=True) or {}
    host_colour = data.get('host_colour')
    opponent = data.get('opponent')  # "human" or "cpu"
    ai_depth = data.get('ai_depth', 3)  # default depth if not specified

    game_id = secrets.token_urlsafe(GAME_ID_LENGTH)
    games[game_id] = {
        "board": OthelloBoard(),
        "black_session": None,
        "white_session": None,
        "draw_offered_by": None
    }

    if host_colour == "white":
        games[game_id]["white_session"] = player_id
        opponent_seat = "black_session"
    else:
        games[game_id]["black_session"] = player_id
        opponent_seat = "white_session"

    if opponent == "cpu":
        games[game_id][opponent_seat] = f"AI: {ai_depth}"

    return jsonify({"game_id": game_id}), 200

@app.route("/api/game/<game_id>", methods=['GET'])
def get_game(game_id):
    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    game = games[game_id]
    board: OthelloBoard = game["board"]

    player_id = get_or_create_player_id()
    your_colour = None

    if game["white_session"] != player_id and game["black_session"] != player_id:
        if game["white_session"] is None:
            game["white_session"] = player_id
            your_colour = WHITE
        elif game["black_session"] is None:
            game["black_session"] = player_id
            your_colour = BLACK
    elif game["white_session"] == player_id:
        your_colour = WHITE
    elif game["black_session"] == player_id:
        your_colour = BLACK

    both_joined = game["black_session"] is not None and game["white_session"] is not None

    if both_joined:
        if check_draw_offer(game_id, game, board):
            return jsonify(serialize_game(board, your_colour, both_joined, opponent_is_ai(game, your_colour), None))

        if board.last_move is None:
            play_ai_turns(game_id, game, board)

    return jsonify(serialize_game(board, your_colour, both_joined, opponent_is_ai(game, your_colour), game["draw_offered_by"]))

@app.route("/api/game/<game_id>/move", methods=['POST'])
def make_move(game_id):
    game, board, player_colour = resolve_player(game_id)
    if game is None:
        return player_colour # error tuple

    if game["black_session"] is None or game["white_session"] is None:
        return jsonify({"error": "Waiting for both players to join"}), 403

    if not player_colour == board.current_player:
        return jsonify({"error": "Not your turn"}), 403

    data = request.get_json(silent=True) or {}
    row = data.get('row')
    col = data.get('col')

    if row is None or col is None:
        return jsonify({"error": "Missing row or col"}), 400

    try:
        board.make_move(row, col)
        if board.game_over:
            archive_game(game_id, board)
    except ValueError:
        return jsonify({"error": "Illegal move!"}), 403
    except TypeError:
        return jsonify({"error": "row/col must be integers"}), 400

    both_joined = game["black_session"] is not None and game["white_session"] is not None
    return jsonify(serialize_game(board, player_colour, both_joined, opponent_is_ai(game, player_colour), game["draw_offered_by"]))

@app.route("/api/game/<game_id>/ai-move", methods=['POST'])
def ai_move(game_id):
    game, board, player_colour = resolve_player(game_id)
    if game is None:
        return player_colour # error tuple

    play_ai_turns(game_id, game, board)
    both_joined = game["black_session"] is not None and game["white_session"] is not None
    return jsonify(serialize_game(board, player_colour, both_joined, opponent_is_ai(game, player_colour), game["draw_offered_by"]))

@app.route("/api/game/<game_id>/resign", methods=['POST'])
def resign(game_id):
    game, board, player_colour = resolve_player(game_id)
    if game is None:
        return player_colour # error tuple

    archive_game(game_id, board, resigned_colour=player_colour)
    return jsonify({"status": "resigned"}), 200

@app.route("/api/game/<game_id>/respond-draw", methods=['POST'])
def respond_draw(game_id):
    game, board, player_colour = resolve_player(game_id)
    if game is None:
        return player_colour # error tuple

    if game["draw_offered_by"] is None:
        return jsonify({"error": "No draw offer pending"}), 409

    if game["draw_offered_by"] == player_colour:
        return jsonify({"error": "You can't respond to your own offer"}), 403

    data = request.get_json(silent=True) or {}
    accept = data.get("accept")

    if accept:
        archive_game(game_id, board, agreed_draw=True)
        return jsonify({"status": "draw"}), 200

    game["draw_offered_by"] = None
    both_joined = game["black_session"] is not None and game["white_session"] is not None
    return jsonify(serialize_game(board, player_colour, both_joined, opponent_is_ai(game, player_colour), game["draw_offered_by"]))

@app.route("/api/game/<game_id>/offer-draw", methods=['POST'])
def offer_draw(game_id):
    game, board, player_colour = resolve_player(game_id)
    if game is None:
        return player_colour # error tuple

    if game["draw_offered_by"] is None:
        game["draw_offered_by"] = player_colour
    elif game["draw_offered_by"] == player_colour:
        return jsonify({"error": "You already have an unfulfilled draw request"}), 409
    else: # opponent already offered (mutual agreement)
        archive_game(game_id, board, agreed_draw=True)
        return jsonify({"status": "draw"}), 200

    both_joined = game["black_session"] is not None and game["white_session"] is not None
    return jsonify(serialize_game(board, player_colour, both_joined, opponent_is_ai(game, player_colour), game["draw_offered_by"]))

@app.route("/api/archive/<game_id>", methods=['GET'])
def get_archive(game_id):
    if game_id not in archives:
        return jsonify({"error": "Archive not found"}), 404

    archived = archives[game_id]
    return jsonify({
        "board": archived["board"],
        "black_count": archived["black_count"],
        "white_count": archived["white_count"],
        "last_move": archived["last_move"],
        "resigned_colour": archived["resigned_colour"],
        "agreed_draw": archived["agreed_draw"]
    })

@app.route("/game/<game_id>", methods=['GET'])
def serve_game_page(game_id):
    if game_id in archives:
        return redirect(f"/archive/{game_id}")
    return render_template("index.html")

@app.route("/archive/<game_id>", methods=['GET'])
def serve_archive_page(game_id):
    if game_id not in archives:
        return "Archive not found", 404
    return render_template("index.html")

@app.route("/", methods=['GET'])
def landing():
    return render_template("landing.html")



if __name__ == "__main__":
    app.run(debug=True)