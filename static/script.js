function getGameId() {
    const parts = window.location.pathname.split("/");
    return parts[parts.length - 1]; // last segment of the path
}

const gameId = getGameId();

if (!gameId) {
    document.getElementById("status").textContent = "No game ID in URL (you monkey)";
}

async function fetchGameState() {
    const response = await fetch(`/api/game/${gameId}`);
    const data = await response.json();

    if (!response.ok) {
        document.getElementById("status").textContent = data.error || "Something went wrong";
        return;
    }

    renderBoard(data);
}

function renderBoard(data) {
    // reminder: data.board is an 8x8 array of numbers: 0 = empty, 1 = black, 2 = white
    const container = document.getElementById("container");
    container.innerHTML = ""; // wipe the old container

    const isMyTurn = data.your_colour === data.current_player;

    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const cellValue = data.board[row][col];

            const cell = document.createElement("div"); // makes a new div
            cell.className = "cell"; // give it a css class so we can style all cells

            if (cellValue === 1) {
                cell.classList.add("black");
            } else if (cellValue === 2) {
                cell.classList.add("white");
            }

            // is this cell a legal move, AND is it actually my turn?
            const isLegal = data.current_legal_moves.some(
                (move) => move[0] === row && move[1] === col
            );

            if (isLegal && isMyTurn) {
                cell.classList.add("legal-move");
                cell.addEventListener("click", () => handleCellClick(row, col));
            }

            container.appendChild(cell); // add this cell to the grid container
        }
    }

    updateStatus(data);
}

function updateStatus(data) {
    const status = document.getElementById("status");

    if (data.your_colour === null) {
        status.textContent = "You're spectating.";
        return;
    }

    const yourColourName = data.your_colour === 1 ? "Black" : "White";
    const isMyTurn = data.your_colour === data.current_player;

    if (data.both_joined) {
        if (isMyTurn) {
            status.textContent = `You're ${yourColourName}. Your turn!`;
        } else {
            status.textContent = `You're ${yourColourName}. Waiting for opponent to move...`;
        }
    } else {
        status.textContent = `You're ${yourColourName}. Waiting for opponent to join...`
    }
}

async function handleCellClick(row, col) {
    const response = await fetch(`/api/game/${gameId}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ row: row, col: col }),
    });

    const data = await response.json();

    if (!response.ok) {
        document.getElementById("status").textContent = data.error;
        return;
    }

    renderBoard(data);
}

fetchGameState(); // load immediately on page load

setInterval(fetchGameState, 1500); // then re-fetch every 1.5s to catch opponent moves