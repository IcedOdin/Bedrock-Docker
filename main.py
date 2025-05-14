# API Backend for Minecraft Server
# Import section
import os
import json
import zipfile
import time
import re
import shutil
import nbtlib

# From Section
from nbtlib import load, tag
from amulet_nbt import load as load_nbt
from pathlib import Path
from flask import Flask, request, jsonify, render_template, redirect
from werkzeug.utils import secure_filename
from activate import activate_behavior_packs, activate_resource_packs

app = Flask(__name__)

SETTINGS_PATH = "/bedrock/server.properties"
PIPE_PATH = "/bedrock/server_input"
PID_PATH = "/bedrock/bedrock_server.pid"
LOG_PATH = "/bedrock/logs/latest.log"

WORLD_PATH = Path("/bedrock/worlds")
UPLOAD_FOLDER_BEHAVIOR = Path('/bedrock/behavior_packs')
UPLOAD_FOLDER_RESOURCE = Path('/bedrock/resource_packs')
ALLOWED_EXTENSIONS = {'zip', 'mcpack'}

type_map = {
    int: tag.Int,
    str: tag.String,
    bool: tag.Byte,  # Minecraft often stores booleans as 0/1 bytes
    float: tag.Float
}

VALID_COMMANDS = [
    "list", "tell", "say", "kick", "ban", "ban-ip", "pardon", "pardon-ip",
    "whitelist", "op", "deop", "give", "tp", "teleport", "setworldspawn",
    "setmaxplayers", "time", "gamemode", "difficulty", "weather", "effect",
    "title", "clear", "clone", "fill", "summon", "kill", "me", "save-all",
    "save-on", "save-off", "stop", "xp", "help", "fakeplayer", "player",
    "./fakeplayer", "./player"
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pack(file_path, extract_to):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def get_level_name():
    prop_path = Path("/bedrock/server.properties")
    if not prop_path.exists():
        return "Bedrock level"

    with open(prop_path, 'r') as f:
        for line in f:
            if line.startswith("level-name"):
                return line.strip().split("=")[1]
    return "Bedrock level"

def inspect_level_dat(world_path):
    level_dat_path = Path(world_path) / 'level.dat'
    level_dat = nbtlib.load(level_dat_path)
    data = level_dat.root['Data']

    for key, value in data.items():
        print(f"{key}: {value}")

def set_level_dat_property(world_path, key, value):
    level_dat_path = Path(world_path) / 'level.dat'
    level_dat = nbtlib.load(level_dat_path)
    data = level_dat.root['Data']

    if key in data:
        data[key] = value
        level_dat.save()
        print(f"Updated {key} to {value}")
    else:
        print(f"Key '{key}' not found in level.dat")

def get_level_dat_path():
    properties_path = Path("/bedrock/server.properties")
    with open(properties_path) as f:
        for line in f:
            if line.startswith("level-name"):
                level_name = line.strip().split('=')[1]
                return WORLD_PATH / level_name / "level.dat"
    raise FileNotFoundError("World path not found")

def serialize(tag):
    if isinstance(tag, dict):
        return {k: serialize(v) for k, v in tag.items()}
    elif isinstance(tag, list):
        return [serialize(i) for i in tag]
    elif hasattr(tag, 'value'):
        return serialize(tag.value)
    else:
        return tag

def serialize_nbt(tag):
    if hasattr(tag, "value"):
        return serialize_nbt(tag.value)
    elif isinstance(tag, dict):
        return {k: serialize_nbt(v) for k, v in tag.items()}
    elif isinstance(tag, list):
        return [serialize_nbt(i) for i in tag]
    else:
        return tag

# --- Routes ---
@app.route('/api/level-settings/debug', methods=['GET'])
def get_level_settings_debug():
    try:
        nbt_file = load(get_level_dat_path())

        # Check if it's a NamedTag with a tag property
        if hasattr(nbt_file, 'tag'):
            data = nbt_file.tag
        else:
            data = nbt_file

        # Return a structured SNBT string instead of attempting to access .value
        return jsonify({
            "snbt": str(data.snbt())
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/level-settings', methods=['GET'])
def get_level_settings():
    level_dat_path = get_level_dat_path()
    nbt_file = load(level_dat_path)
    
    # .root doesn't exist — access 'Data' directly
    data = nbt_file['Data']

    response = {
        k: v.py() for k, v in data.items()
        if isinstance(v, (tag.String, tag.Int, tag.Byte, tag.Float, tag.Compound))
    }
    return jsonify(response)

@app.route('/api/level-settings/update', methods=['POST'])
def update_level_setting():
    data = request.json
    key = data.get('key')
    value = data.get('value')

    if not key or value is None:
        return jsonify({'error': 'Key and value required'}), 400

    level_dat_path = get_level_dat_path()
    nbt_file = load(level_dat_path)
    nbt_data = nbt_file['Data']  # <- use like this

    current = nbt_data.get(key)
    if current is None:
        return jsonify({'error': f'Key {key} not found'}), 404

    # Handle primitive types only for now
    if isinstance(current, tag.Int):
        nbt_data[key] = tag.Int(int(value))
    elif isinstance(current, tag.Byte):
        nbt_data[key] = tag.Byte(int(bool(value)))
    elif isinstance(current, tag.String):
        nbt_data[key] = tag.String(str(value))
    elif isinstance(current, tag.Float):
        nbt_data[key] = tag.Float(float(value))
    else:
        return jsonify({'error': f'Unsupported type for {key}'}), 400

    nbt_file.save()
    return jsonify({'message': f'{key} updated successfully'})

@app.route('/upload/behavior-pack', methods=['POST'])
def upload_behavior_pack():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = UPLOAD_FOLDER_BEHAVIOR / filename
        file.save(save_path)

        # Extract pack
        extract_path = UPLOAD_FOLDER_BEHAVIOR / filename.rsplit('.', 1)[0]
        os.makedirs(extract_path, exist_ok=True)
        extract_pack(save_path, extract_path)
        os.remove(save_path)

        # Read manifest.json to find UUID
        manifest_path = extract_path / "manifest.json"
        if not manifest_path.exists():
            return jsonify({"error": "manifest.json not found in pack"}), 400

        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                uuid = manifest["header"]["uuid"]
        except Exception as e:
            return jsonify({"error": f"Failed to parse manifest.json: {str(e)}"}), 400

        # Copy into world behavior_packs folder
        level_name = get_level_name()
        world_behavior_dir = Path(f"/bedrock/worlds/{level_name}/behavior_packs")
        os.makedirs(world_behavior_dir, exist_ok=True)
        shutil.copytree(extract_path, world_behavior_dir / extract_path.name, dirs_exist_ok=True)

        # Create permission folder and copy permissions.json
        default_config_path = Path("/bedrock/config/default")
        uuid_dir = default_config_path / uuid
        os.makedirs(uuid_dir, exist_ok=True)

        source_permissions = default_config_path / "permissions.json"
        if source_permissions.exists():
            shutil.copy(source_permissions, uuid_dir / "permissions.json")
            
        activate_behavior_packs()

        return jsonify({"message": f"Pack uploaded, extracted, installed to world, and granted permission ({uuid})"}), 200

    return jsonify({"error": "Invalid file type"}), 400

@app.route('/upload/resource-pack', methods=['POST'])
def upload_resource_pack():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = UPLOAD_FOLDER_RESOURCE / filename
        file.save(save_path)

        # Extract pack
        extract_path = UPLOAD_FOLDER_RESOURCE / filename.rsplit('.', 1)[0]
        os.makedirs(extract_path, exist_ok=True)
        extract_pack(save_path, extract_path)
        os.remove(save_path)

        # Read manifest.json to find UUID
        manifest_path = extract_path / "manifest.json"
        if not manifest_path.exists():
            return jsonify({"error": "manifest.json not found in pack"}), 400

        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                uuid = manifest["header"]["uuid"]
        except Exception as e:
            return jsonify({"error": f"Failed to parse manifest.json: {str(e)}"}), 400

        # Copy into world behavior_packs folder
        level_name = get_level_name()
        world_behavior_dir = Path(f"/bedrock/worlds/{level_name}/resource_packs")
        os.makedirs(world_resource_dir, exist_ok=True)
        shutil.copytree(extract_path, world_resource_dir / extract_path.name, dirs_exist_ok=True)

        # Create permission folder and copy permissions.json
        default_config_path = Path("/bedrock/config/default")
        uuid_dir = default_config_path / uuid
        os.makedirs(uuid_dir, exist_ok=True)

        source_permissions = default_config_path / "permissions.json"
        if source_permissions.exists():
            shutil.copy(source_permissions, uuid_dir / "permissions.json")
            
        activate_resource_packs()            

        return jsonify({"message": f"Pack uploaded, extracted, installed to world, and granted permission ({uuid})"}), 200

    return jsonify({"error": "Invalid file type"}), 400

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
                        
                        # Only include if it's not another timestamp line
                        if not re.match(r"^\[?\d{4}-\d{2}-\d{2}", next_line):
                            # Players might be comma separated or line-separated
                            potential_players = [p.strip() for p in next_line.split(",") if p.strip()]
                            result["players"] = potential_players                        

                    found_players = True
                    break

    except Exception as e:
        result["error"] = f"Log read failed: {e}"

    return jsonify(result)


# DO NOT include app.run() here.
# Gunicorn will handle running the app.
