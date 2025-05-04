import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/bedrock/.env")  # Adjust path as needed

def update_properties():
    path = "/bedrock/server.properties"
    if not os.path.isfile(path):
        print("server.properties not found.")
        return

    print("Applying environment variables to server.properties...")

    with open(path, "r") as f:
        lines = f.readlines()

    props = {}
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key, val = line.split("=", 1)
            props[key.strip()] = val.strip()
    

    env_mappings = {
        "server-name": "SERVER_NAME",
        "max-players": "MAX_PLAYERS",
        "level-seed": "LEVEL_SEED",
        "gamemode": "GAME_MODE",
        "difficulty": "DIFFICULTY",
        "level-name": "LEVEL_NAME",
        "allow-cheats": "ALLOW_CHEATS",
        "default-player-permission-level": "DEFAULT_PLAYER_PERMISSION_LEVEL",
        "online-mode": "ONLINE_MODE",
        "server-port": "SERVER_PORT",
        "motd": "MOTD",
        "enable-script-api": "ENABLE_SCRIPT_API"
    }

    for prop_key, env_key in env_mappings.items():
        val = os.getenv(env_key)
        if val is not None:
            print(f"Setting {prop_key} = {val}")
            props[prop_key] = val

    with open(path, "w") as f:
        for k, v in props.items():
            f.write(f"{k}={v}\n")

if __name__ == "__main__":
    update_properties()

