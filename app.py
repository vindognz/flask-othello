""" Flask backend for FlaskOthello """

from flask import Flask, jsonify, request, session
import secrets

from board import OthelloBoard, BLACK, WHITE

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


@app.route("/game/new", methods=['POST'])
def new_game():
    player_id = get_or_create_player_id()

    data = request.get_json(silent=True) or {}
    host_colour = data.get('host_colour')

    game_id = secrets.token_urlsafe(GAME_ID_LENGTH)
    games[game_id] = {
        "board": OthelloBoard(),
        "black_session": None,
        "white_session": None
    }

    if host_colour == "white":
        games[game_id]["white_session"] = player_id
    else:
        games[game_id]["black_session"] = player_id

    return jsonify({"game_id": game_id}), 200

@app.route("/game/<game_id>", methods=['GET'])
def get_game(game_id):
    if game_id in games:
        game = games[game_id]
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

        return jsonify({"board":game["board"].board, "current_player": game["board"].current_player, "your_colour": your_colour, "current_legal_moves": list(game["board"].get_valid_moves(game["board"].current_player))})


    return jsonify({"error": "Game not found."}), 404
