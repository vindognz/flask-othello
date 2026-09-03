""" Flask backend for FlaskOthello """

from flask import Flask, jsonify, request, session, render_template
import secrets

from board import OthelloBoard, BLACK, WHITE
from ai import OthelloAI

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Constants
GAME_ID_LENGTH = 4

games = {} # game_id -> {"board": OthelloBoard, "black_session": str|None, "white_session": str|None}

def get_or_create_player_id() -> str:
    """ Return this browser's player_id, or create one if needed. """
    if "player_id" not in session:
        session["player_id"] = secrets.token_hex(8)
    return session["player_id"]

def get_ai_depth(session_value):
    """ Return AI depth if this seat is AI-controlled, else None. """
    if isinstance(session_value, str) and session_value.startswith("AI:"):
        return int(session_value.split(":")[1].strip())
    return None

def serialize_game(board: OthelloBoard, your_colour, both_joined):
    """ Build the JSON response shared by /game and /move """
    return {
        "board": board.board,
        "current_player": board.current_player,
        "your_colour": your_colour,
        "current_legal_moves": list(board.get_valid_moves(board.current_player)),
        "both_joined": both_joined,
        "last_move": list(board.last_move) if board.last_move else None,
        "game_over": board.game_over,
    }


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
        "white_session": None
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
    if game_id in games:
        game = games[game_id]
    else:
        return jsonify({"error": "Game not found"}), 404

    board: OthelloBoard = game["board"]

    player_id = get_or_create_player_id()
    your_colour = None

    # if the player is not holding a seat
        # if a seat is empty
            # CLAIM

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
    else:
        your_colour = None

    both_joined = game["black_session"] is not None and game["white_session"] is not None

    return jsonify(serialize_game(board, your_colour, both_joined))

@app.route("/api/game/<game_id>/move", methods=['POST'])
def make_move(game_id):
    if game_id in games:
        game = games[game_id]
    else:
        return jsonify({"error": "Game not found"}), 404

    if game["black_session"] is None or game["white_session"] is None:
        return jsonify({"error": "Waiting for both players to join"}), 403

    board: OthelloBoard = game["board"]

    player = get_or_create_player_id()
    player_colour = None

    if game["white_session"] == player:
        player_colour = WHITE
    elif game["black_session"] == player:
        player_colour = BLACK

    if not player_colour:
        return jsonify({"error": "Spectators can't make moves"}), 403

    if not player_colour == board.current_player:
        return jsonify({"error": "Not your turn"}), 403

    data = request.get_json(silent=True) or {}
    row = data.get('row')
    col = data.get('col')

    if row is None or col is None:
        return jsonify({"error": "Missing row or col"}), 400

    try:
        board.make_move(row, col)
    except ValueError:
        return jsonify({"error": "Illegal move!"}), 403
    except TypeError:
        return jsonify({"error": "row/col must be integers"}), 400

    # let the AI play
    while not board.game_over:
        current_seat = game["white_session"] if board.current_player == WHITE else game["black_session"]
        depth = get_ai_depth(current_seat)
        if depth is None:
            break  # it's a human's turn, stop here

        ai = OthelloAI(depth=depth)
        ai_move = ai.get_best_move(board, board.current_player)
        if ai_move is not None:
            board.make_move(*ai_move)
        else:
            board.pass_turn()

    both_joined = game["black_session"] is not None and game["white_session"] is not None
    return jsonify(serialize_game(board, player_colour, both_joined))

@app.route("/game/<game_id>", methods=['GET'])
def serve_game_page(game_id):
    return render_template("index.html")

@app.route("/", methods=['GET'])
def landing():
    return render_template("landing.html")



if __name__ == "__main__":
    app.run(debug=True)