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
        "pcount": None
    }
    try:
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                clean_line = line.strip()
                
                if "Server started" in clean_line:
                    status["running"] = True
                
                if "Version:" in clean_line and not status["version"]:
                    status["version"] = line.split("Version:")[-1].strip()
                
                if "There are" in clean_line and "players online" in clean_line:
                    cleaned = clean_line.split("INFO]")[-1].strip()
                    if ":" in cleaned:
                        _, player_data = cleaned.split("players online:", 1)
                        players = [p.strip() for p in player_data.split(",") if p.strip()]
                        status["pcount"] = str(len(players))
    
    except FileNotFoundError:
        status["error"] = "Log not found"
    return jsonify(status)

@app.route('/players', methods=['GET'])
def get_players():
    try:
        # Clear a temp log or marker if needed
        with open('/bedrock/server_input', 'w') as f:
            f.write('list\n')

        time.sleep(2.5)  # Give the server time to process

        players = {}
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                clean_line = line.strip()
                if "There are" in clean_line and "players online:" in clean_line:
                    cleaned = clean_line.split("INFO]")[-1].strip()
                    # Example: There are 2/20 players online: Steve, Alex
                    raw_data = cleaned
                    if ":" in cleaned:
                        _, player_data = cleaned.split("players online:", 1)
                        raw_data2 = player_data
                        players = [p.strip() for p in player_data.split(",") if p.strip()]
                    
                    break
        return jsonify(players=players,raw_data=raw_data,raw_data2=raw_data2)
    except Exception as e:
        return jsonify(error=str(e)), 500


# DO NOT include app.run() here.
# Gunicorn will handle running the app.
