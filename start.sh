#!/bin/bash
set -e

cd /bedrock


# Setup logs
mkdir -p logs
LOGFILE="logs/bedrock_$(date +%Y%m%d_%H%M%S).log"

mkdir -p downloads
# Download latest Bedrock server if not present
echo "Checking for the latest Bedrock server version..."
curl -H "Accept-Encoding: identity" -H "Accept-Language: en" -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.33 (KHTML, like Gecko) Chrome/90.0.$RandNum.212 Safari/537.33" -o downloads/version.html https://minecraft.net/en-us/download/server/bedrock/
DownloadURL=$(grep -o 'https://www.minecraft.net/bedrockdedicatedserver/bin-linux/[^"]*' downloads/version.html)
DownloadFile=$(echo "$DownloadURL" | sed 's#.*/##')


if [ ! -f "$DownloadFile" ]; then
    echo "Downloading $DownloadFile..."
    UserName=$(whoami)
    curl -H "Accept-Encoding: identity" -H "Accept-Language: en" -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.33 (KHTML, like Gecko) Chrome/90.0.$RandNum.212 Safari/537.33" -o "downloads/$DownloadFile" "$DownloadURL"
    unzip -o "downloads/$DownloadFile"
    rm "downloads/$DownloadFile"
    chmod +x bedrock_server
fi

# Start Minecraft Bedrock server in background
/bedrock/bedrock_server > /bedrock/logs/server.log 2>&1 &
echo "Bedrock Server is running....."
# Creating Files the Hard Way
echo "Creating app files......"
mkdir -p static
mkdir -p templates
cat << END > static/custom.js
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
END

cat << END > templates/layout.html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}Bedrock Server UI{% endblock %}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background-color: #121212; color: white; }
    .card { background-color: #1e1e1e; }
    label { text-transform: capitalize; }
  </style>
</head>
<body>
  <nav class="navbar navbar-dark bg-dark mb-4">
    <div class="container">
      <a class="navbar-brand" href="/">🛠️ Bedrock Control Panel</a>
    </div>
  </nav>
  <div class="container">
    {% block content %}{% endblock %}
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  <script src="/static/custom.js"></script>
</body>
</html>
END

cat << END > templates/settings.html
{% extends "layout.html" %}

{% block title %}Server Settings{% endblock %}

{% block content %}
  <div class="row">
    <div class="col-lg-8">
      <form method="post" class="card p-4 mb-4">
        <h2 class="mb-3">⚙️ Server Settings</h2>
        <div class="row g-3">
          {% for key, value in settings.items() %}
            <div class="col-md-6">
              <label for="{{ key }}">{{ key }}</label>
              <input type="text" class="form-control" id="{{ key }}" name="{{ key }}" value="{{ value }}">
            </div>
          {% endfor %}
        </div>
        <div class="mt-4">
          <button type="submit" class="btn btn-success">💾 Save</button>
          <button type="button" class="btn btn-warning" onclick="restartServer()">🔁 Restart</button>
        </div>
        <div id="restart-status" class="mt-3"></div>
      </form>
    </div>
    <div class="col-lg-4">
      <div class="card p-3 mb-4">
        <h4>🖥️ Live Server Info</h4>
        <p>Status: <span id="server-status">Checking...</span></p>
        <p>Version: <span id="server-version">–</span></p>
        <p>Players Online: <span id="player-count">–</span></p>
      </div>
      <div class="card p-3">
        <h4>💬 Send Command</h4>
        <input type="text" id="command-input" class="form-control mb-2" placeholder="Type a command">
        <button class="btn btn-primary w-100" onclick="sendCommand()">▶️ Send</button>
        <div id="command-response" class="mt-3 text-muted small"></div>
      </div>
    </div>
  </div>
{% endblock %}
END

cat << END > main.py
from flask import Flask, request, jsonify, render_template, redirect
import os

app = Flask(__name__)

SETTINGS_PATH = "/bedrock/server.properties"


def parse_properties(path):
    props = {}
    with open(path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                props[k] = v
    return props


def write_properties(path, props):
    with open(path, 'w') as f:
        for key, val in props.items():
            f.write(f"{key}={val}\n")


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok"), 200


@app.route("/command", methods=["POST"])
def send_command():
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'Missing "command" in request'}), 400

    command = data['command']
    try:
        with open(f'/proc/{get_server_pid()}/fd/0', 'w') as stdin:
            stdin.write(command + '\n')
        return jsonify({'status': 'Command sent', 'command': command})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_server_pid():
    try:
        with open("/bedrock/bedrock_server.pid") as f:
            return int(f.read().strip())
    except Exception as ex:
        raise Exception("Bedrock server PID not found: " + str(ex))


@app.route("/", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        new_settings = request.form.to_dict()
        write_properties(SETTINGS_PATH, new_settings)
        return redirect("/")
    settings = parse_properties(SETTINGS_PATH)
    return render_template("settings.html", settings=settings)


@app.route("/restart", methods=["POST"])
def restart():
    os.system("supervisorctl restart bedrock")
    return "Restarting..."

@app.route('/status', methods=['GET'])
def status():
    status = {
        "running": False,
        "version": None,
        "players": None
    }

    try:
        with open("/bedrock/logs/latest.log", "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if "Server started" in line:
                    status["running"] = True
                if "Version:" in line and not status["version"]:
                    status["version"] = line.split("Version:")[-1].strip()
                if "Player connected" in line or "Player disconnected" in line:
                    status["players"] = "Check console/logs"  # Placeholder
    except FileNotFoundError:
        status["error"] = "Log not found"

    return jsonify(status)



# DO NOT include app.run() here.
# Gunicorn will handle running the app.
END

# Start Flask API with Gunicorn (4 workers, port 5000)
exec gunicorn -w 2 -b 0.0.0.0:50000 'main:app'
