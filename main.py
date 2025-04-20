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


# DO NOT include app.run() here.
# Gunicorn will handle running the app.

