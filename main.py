from flask import Flask, request, jsonify, render_template, redirect
import os
import time
import re

app = Flask(__name__)

SETTINGS_PATH = "/bedrock/server.properties"
PIPE_PATH = "/bedrock/server_input"
PID_PATH = "/bedrock/bedrock_server.pid"
LOG_PATH = "/bedrock/logs/latest.log"

VALID_COMMANDS = [
    "list", "tell", "say", "kick", "ban", "ban-ip", "pardon", "pardon-ip",
    "whitelist", "op", "deop", "give", "tp", "teleport", "setworldspawn",
    "setmaxplayers", "time", "gamemode", "difficulty", "weather", "effect",
    "title", "clear", "clone", "fill", "summon", "kill", "me", "save-all",
    "save-on", "save-off", "stop", "xp", "help"
]

# --- Utility Functions ---
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

def send_to_pipe(command):
    if not os.path.exists(PIPE_PATH):
        raise Exception("Command pipe does not exist")
    with open(PIPE_PATH, 'w') as fifo:
        fifo.write(command + '\n')

# --- Routes ---
@app.route("/health")
def health():
    return jsonify(status="ok"), 200

@app.route("/", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        new_settings = request.form.to_dict()
        write_properties(SETTINGS_PATH, new_settings)
        return redirect("/")
    settings = parse_properties(SETTINGS_PATH)
    return render_template("settings.html", settings=settings, commands=VALID_COMMANDS)

@app.route("/command", methods=["POST"])
def command():
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'Missing "command" in request'}), 400

    try:
        send_to_pipe(data['command'])
        return jsonify({'status': 'Command sent', 'command': data['command']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/console", methods=["GET", "POST"])
def console():
    status = None
    if request.method == "POST":
        base_command = request.form.get("base_command")
        args = request.form.get("args", "")
        if base_command in VALID_COMMANDS:
            full_command = f"{base_command} {args}".strip()
            print (full_command)
            try:
                send_to_pipe(full_command)
                status = f"Sent: {full_command}"
            except Exception as e:
                status = f"Error: {e}"
        else:
            status = f"Invalid command: {base_command}"
    return render_template("console.html", commands=VALID_COMMANDS, status=status)

@app.route("/restart", methods=["POST"])
def restart():
    full_command = f"reload"
    try:
        send_to_pipe(full_command)
        status = f"Sent: {full_command}"
    except Exception as e:
        status = f"Error: {e}"
    return "Restarting..."

@app.route('/status', methods=['GET'])
def status():

    result = {
        "player_count": "0/0",
        "players": [],
        "running": False,
        "version": None
    }

    try:
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()

        # Reverse lines to get latest entries first
        lines = lines[::-1]

        found_players = False

        for i, line in enumerate(lines):
            # Detect server started
            if not result["running"] and "Server started" in line:
                result["running"] = True

            # Detect version
            if not result["version"]:
                version_match = re.search(r"Version:\s*([\d\.]+)", line)
                if version_match:
                    result["version"] = version_match.group(1)

            # Detect player count
            if "There are" in line and "players online" in line:
                match = re.search(r"There are (\d+)/(\d+) players online", line)
                if match:
                    result["player_count"] = f"{match.group(1)}/{match.group(2)}"

                    # Check next line for player names, if any
                    if i > 0:
                        next_line = lines[i - 1].strip()
                        if next_line and not next_line.startswith("["):
                            result["players"] = [name.strip() for name in next_line.split(",")]
                    found_players = True
                    break

    except Exception as e:
        result["error"] = f"Log read failed: {e}"

    return jsonify(result)


# DO NOT include app.run() here.
# Gunicorn will handle running the app.
