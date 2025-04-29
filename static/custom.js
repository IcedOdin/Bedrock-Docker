function restartServer() {
  fetch('/restart', { method: 'POST' })
    .then(r => r.text())
    .then(msg => {
      document.getElementById('restart-status').innerHTML = `
        <div class="alert alert-info">${msg}</div>
      `;
    });
}

function sendCommand() {
    const baseCommand = document.getElementById("command-select").value;
    const args = document.getElementById("command-args").value;
    const fullCommand = `${baseCommand} ${args}`.trim();

    fetch("/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: fullCommand })
    })
    .then(res => res.json())
    .then(data => {
      document.getElementById("command-response").textContent = JSON.stringify(data);
    })
    .catch(err => {
      document.getElementById("command-response").textContent = "Error sending command.";
      console.error(err);
    });
  }

// Later: Add fetch('/status') here to update live server info
function updateStatus() {
  fetch('/status')
    .then(res => res.json())
    .then(data => {
      document.getElementById('server-status').innerText = data.running ? '🟢 Online' : '🔴 Offline';
      document.getElementById('server-version').innerText = data.version || '–';
      document.getElementById('player-count').textContent = data.player_count || "0/0";

      const listElement = document.getElementById('player-list');
      listElement.innerHTML = '';

      if (data.players && data.players.length > 0) {
        data.players.forEach(player => {
          const li = document.createElement('li');
          li.textContent = player;
          listElement.appendChild(li);
        });
      } else {
        const li = document.createElement('li');
        li.textContent = 'No players online.';
        listElement.appendChild(li);
      }
    })
    .catch(err => {
      document.getElementById('player-count').textContent = "?/?";
      const listElement = document.getElementById('player-list');
      listElement.innerHTML = '<li>Error fetching status.</li>';
      console.error("Failed to fetch status:", err);
    });
}

// Update every 10 seconds
setInterval(updateStatus, 10000); //update every 10seconds
updateStatus(); // initial call      



