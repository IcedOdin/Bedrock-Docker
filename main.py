from flask import Flask, request, jsonify, render_template, redirect
import os
import time

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

@app.route("/status")
def status():
    status = {
        "running": False,
        "version": None,
        "players": None
    }
    try:
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if "Server started" in line:
                    status["running"] = True
                if "Version:" in line and not status["version"]:
                    status["version"] = line.split("Version:")[-1].strip()
                if "Player connected" in line or "Player disconnected" in line:
                    status["players"] = "Check console/logs"
    except FileNotFoundError:
        status["error"] = "Log not found"
    return jsonify(status)

@app.route('/players', methods=['GET'])
def get_players():
    try:
        # Clear a temp log or marker if needed
        with open('/bedrock/server_input', 'w') as f:
            f.write('list\n')

        time.sleep(1.5)  # Give the server time to process

        players = []
        with open("/bedrock/logs/latest.log", "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if "There are" in line and "players online:" in line:
                    # Example: There are 2/20 players online: Steve, Alex
                    parts = line.strip().split(":")
                    if len(parts) > 1:
                        players = [p.strip() for p in parts[1].split(",") if p.strip()]
                    break
        return jsonify(players=players)
    except Exception as e:
        return jsonify(error=str(e)), 500


# DO NOT include app.run() here.
# Gunicorn will handle running the app.
