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
cat << END > templates/settings.html
<!DOCTYPE html>
<html>
<head>
  <title>Minecraft Server Settings</title>
  <style>
    body { font-family: sans-serif; padding: 2em; background: #eee; }
    input, select { width: 100%; margin: 0.3em 0; }
    form { background: white; padding: 1em; border-radius: 10px; }
  </style>
</head>
<body>
  <h2>Bedrock Server Settings</h2>
  <form method="post">
    {% for key, value in settings.items() %}
      <label>{{ key }}:</label>
      <input name="{{ key }}" value="{{ value }}">
    {% endfor %}
    <br>
    <button type="submit">Save Settings</button>
  </form>
  <form method="post" action="/restart" style="margin-top: 1em;">
    <button type="submit">Restart Server</button>
  </form>
</body>
</html>
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


# DO NOT include app.run() here.
# Gunicorn will handle running the app.
END

# Start Flask API with Gunicorn (4 workers, port 5000)
exec gunicorn -w 2 -b 0.0.0.0:50000 'main:app'
