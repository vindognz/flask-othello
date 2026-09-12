import {
    opponentThinkingMsg,
    aiThinkingMsg,
    yourTurnMsg,
    drawOfferedWaitingMsg,
    drawDeclinedMsg,
} from "./strings.js";

function getGameId() {
    const parts = window.location.pathname.split("/");
    return parts[parts.length - 1];
}

const gameId = getGameId();
const isArchive = window.location.pathname.startsWith("/archive/");

if (!gameId) {
    document.getElementById("status").textContent = "No game ID in URL (you monkey)";
    // i lowkey don't know if this is even a possible case LMAO
}

async function fetchGameState() {
    const url = isArchive ? `/api/archive/${gameId}` : `/api/game/${gameId}`;
    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
        if (!isArchive && response.status === 404) {
            // the game may have just been archived. let's check
            const archiveCheck = await fetch(`/api/archive/${gameId}`);
            if (archiveCheck.ok) {
                window.location.href = `/archive/${gameId}`;
                return;
            }
        }
        document.getElementById("status").textContent = data.error || "Something went wrong";
        return;
    }

    if (isArchive) {
        renderArchive(data);
    } else {
        renderBoard(data);
    }
}

function renderCells(board, lastMove, legalMoves, clickable, flippedCells = []) {
    // shared cell-drawing logic used by both live games and archives
    const container = document.getElementById("container");
    container.innerHTML = "";

    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const cellValue = board[row][col];

            const cell = document.createElement("div");
            cell.className = "cell";

            if (cellValue === 1) {
                cell.classList.add("black");
            } else if (cellValue === 2) {
                cell.classList.add("white");
            }

            if (lastMove && row === lastMove[0] && col === lastMove[1]) {
                cell.classList.add("last-move");
            }

            const wasFlipped = flippedCells.some(
                (pos) => pos[0] === row && pos[1] === col
            );
            if (wasFlipped) {
                cell.classList.add("flipping")
            }

            if (clickable) {
                const isLegal = legalMoves.some(
                    (move) => move[0] === row && move[1] === col
                );
                if (isLegal) {
                    cell.classList.add("legal-move");
                    cell.addEventListener("click", () => handleCellClick(row, col));
                }
            }

            container.appendChild(cell); // add this cell to the grid container
        }
    }
}

let lastAnimatedMove = null;

function renderBoard(data, clearOverride = false) {
    if (clearOverride) {
        statusOverrideActive = false;
    }

    const isMyTurn = data.your_colour === data.current_player;
    const canClick = data.both_joined && isMyTurn && !data.game_over;

    const moveKey = data.last_move ? data.last_move.join(",") : null;
    const isNewMove = moveKey !== null && moveKey !== lastAnimatedMove;
    const flipsToAnimate = isNewMove ? data.last_flips : [];

    if (isNewMove) {
        lastAnimatedMove = moveKey;
    }

    renderCells(data.board, data.last_move, data.current_legal_moves, canClick, flipsToAnimate);
    updateStatus(data);

    if (data.your_colour !== null && data.both_joined) {
        document.getElementById("game-buttons").style.display = "";
    } else {
        document.getElementById("game-buttons").style.display = "none";
    }

    if (data.draw_offered_by !== null && data.draw_offered_by !== data.your_colour) {
        document.getElementById("draw-popup").style.display = "";
    } else {
        document.getElementById("draw-popup").style.display = "none";
    }
}

function renderArchive(data) {
    renderCells(data.board, data.last_move, [], false);

    const status = document.getElementById("status");

    if (data.resigned_colour) {
        const winner = data.resigned_colour === 1 ? "White" : "Black";
        status.textContent = `Archived game - ${winner} won (by resignation)`;
        return;
    }

    const { black_count, white_count } = data;

    if (data.agreed_draw) {
        status.textContent = `Archived game - draw by agreement, ${black_count}-${white_count}`
        return;
    }

    if (black_count === white_count) {
        status.textContent = `Archived game — draw, ${black_count}-${white_count}`;
    } else {
        const winner = black_count > white_count ? "Black" : "White";
        status.textContent = `Archived game — ${winner} won, ${black_count}-${white_count}`;
    }
}

let statusOverrideActive = false;

function setStatus(text, isOverride = false) {
    document.getElementById("status").textContent = text;
    statusOverrideActive = isOverride;
}

function updateStatus(data) {
    const status = document.getElementById("status");

    if (data.game_over) {
        const flatBoard = data.board.flat();
        const blackCount = flatBoard.filter(cell => cell === 1).length;
        const whiteCount = flatBoard.filter(cell => cell === 2).length;
        const winner = blackCount > whiteCount ? "Black" : "White";

        if (blackCount !== whiteCount) {
            status.textContent = `${winner} wins!\n${blackCount}-${whiteCount}`;
        } else {
            status.textContent = `It's a draw!\n${blackCount}-${whiteCount}`;
        }
        return;
    }

    if (statusOverrideActive) {
        return;
    }

    if (data.your_colour === null) {
        status.textContent = "You're spectating.";
        return;
    }

    const yourColourName = data.your_colour === 1 ? "Black" : "White";
    const isMyTurn = data.your_colour === data.current_player;

    if (!data.both_joined) {
        status.textContent = `You're ${yourColourName}. Waiting for opponent to join...`;
        return;
    }

    if (!isMyTurn && !data.opponent_is_ai) {
        status.textContent = opponentThinkingMsg;
    } else {
        status.textContent = yourTurnMsg;
    }
}

async function ensureMinDelay(promise, minMs) {
    const start = Date.now();
    const result = await promise;
    const elapsed = Date.now() - start;

    if (elapsed < minMs) {
        await sleep(minMs - elapsed);
    }

    return result;
}

async function handleCellClick(row, col) {
    const response = await fetch(`/api/game/${gameId}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ row: row, col: col }),
    });

    const data = await response.json();

    if (!response.ok) {
        // document.getElementById("status").textContent = data.error;
        setStatus(data.error);
        return;
    }

    renderBoard(data);

    if (data.game_over) {
        window.location.href = `/archive/${gameId}`;
        return;
    }

    // is it now AI's turn?
    if (data.opponent_is_ai && data.your_colour !== data.current_player) {
        // document.getElementById("status").textContent = aiThinkingMsg;
        setStatus(aiThinkingMsg, true);

        const aiResponse = await ensureMinDelay(
            fetch(`/api/game/${gameId}/ai-move`, {
                method: "POST"
            }), 500
        );
        const aiData = await aiResponse.json();

        if (aiResponse.ok) {
            renderBoard(aiData, true);
            if (aiData.game_over) {
                window.location.href = `/archive/${gameId}`
            }
        }
    }
}

async function handleResign() {
    if (!confirm("Are you sure you want to resign?")) {
        return;
    }

    const response = await fetch(`/api/game/${gameId}/resign`, {
        method: "POST",
    });

    if (response.ok) {
        window.location.href = `/archive/${gameId}`;
    }
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

async function handleOfferDraw() {
    const response = await fetch(`/api/game/${gameId}/offer-draw`, {
        method: "POST",
    });
    const data = await response.json();

    if (!response.ok) {
        // document.getElementById("status").textContent = data.error;
        setStatus(data.error);
        return;
    }

    if (data.status === "draw") {
        window.location.href = `/archive/${gameId}`;
        return;
    }

    renderBoard(data);

    if (!data.opponent_is_ai) {
        return;
    }

    setStatus(drawOfferedWaitingMsg, true);

    const delay = 2500 + Math.random() * 5000;
    await sleep(delay);

    const followUp = await fetch(`/api/game/${gameId}`);
    const followUpData = await followUp.json();

    if (followUpData.game_over) {
        window.location.href = `/archive/${gameId}`;
        return;
    }

    renderBoard(followUpData);
    setStatus(drawDeclinedMsg, true);

    await sleep(3000);
    renderBoard(followUpData, true);
}

async function handleRespondDraw(accept) {
    const response = await fetch(`/api/game/${gameId}/respond-draw`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accept: accept }),
    });
    const data = await response.json();

    if (!response.ok) {
        document.getElementById("status").textContent = data.error;
        return;
    }

    if (data.status == "draw") {
        window.location.href = `/archive/${gameId}`;
        return;
    }

    fetchGameState();
}

document.getElementById("resign-btn")?.addEventListener("click", handleResign);
document.getElementById("offer-draw-btn")?.addEventListener("click", handleOfferDraw);

document.getElementById("accept-draw-btn")?.addEventListener("click", () => handleRespondDraw(true));
document.getElementById("decline-draw-btn")?.addEventListener("click", () => handleRespondDraw(false));

fetchGameState();

if (!isArchive) {
    setInterval(fetchGameState, 1500);
}
