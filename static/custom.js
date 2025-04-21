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
  const cmd = document.getElementById('command-input').value;
  fetch('/command', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command: cmd })
  })
  .then(r => r.json())
  .then(data => {
    document.getElementById('command-response').innerText = JSON.stringify(data, null, 2);
  });
}

// Later: Add fetch('/status') here to update live server info
function updateStatus() {
  fetch('/status')
    .then(res => res.json())
    .then(data => {
      document.getElementById('server-status').innerText = data.running ? '🟢 Online' : '🔴 Offline';
      document.getElementById('server-version').innerText = data.version || '–';
      document.getElementById('player-count').innerText = data.players || '–';
    });
}

setInterval(updateStatus, 5000); // update every 5s
updateStatus(); // initial load
