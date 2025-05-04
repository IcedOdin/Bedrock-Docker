import json
from pathlib import Path

bedrock_root = Path("/bedrock")
server_properties_file = bedrock_root / "server.properties"



def activate_behavior_packs():
    # Parse the world name from server.properties
    level_name = "Bedrock level"  # default
    if server_properties_file.exists():
        with open(server_properties_file) as f:
            for line in f:
                if line.strip().startswith("level-name"):
                    _, value = line.split("=", 1)
                    level_name = value.strip()
                    break

    world_dir = bedrock_root / "worlds" / level_name
    behavior_packs_dir = world_dir / "behavior_packs"
    world_behavior_packs_file = world_dir / "world_behavior_packs.json"

    linked_packs = []
    if behavior_packs_dir.exists():
        for pack_dir in behavior_packs_dir.iterdir():
            manifest_path = pack_dir / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
                    header = manifest.get("header", {})
                    pack_id = header.get("uuid")
                    version = header.get("version")
                    if pack_id and version:
                        linked_packs.append({
                            "pack_id": pack_id,
                            "version": version
                        })

    # Write to world_behavior_packs.json if any packs found
    if linked_packs:
        world_dir.mkdir(parents=True, exist_ok=True)
        with open(world_behavior_packs_file, "w") as f:
            json.dump(linked_packs, f, indent=2)
        print(f"Linked {len(linked_packs)} behavior pack(s) to '{level_name}'.")
    else:
        print("No valid behavior packs found.")


def activate_resource_packs():
    # Parse the world name from server.properties
    level_name = "Bedrock level"  # default
    if server_properties_file.exists():
        with open(server_properties_file) as f:
            for line in f:
                if line.strip().startswith("level-name"):
                    _, value = line.split("=", 1)
                    level_name = value.strip()
                    break

    world_dir = bedrock_root / "worlds" / level_name
    resource_packs_dir = world_dir / "resource_packs"
    world_resource_packs_file = world_dir / "world_resource_packs.json"

    linked_packs = []
    if resource_packs_dir.exists():
        for pack_dir in resource_packs_dir.iterdir():
            manifest_path = pack_dir / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
                    header = manifest.get("header", {})
                    pack_id = header.get("uuid")
                    version = header.get("version")
                    if pack_id and version:
                        linked_packs.append({
                            "pack_id": pack_id,
                            "version": version
                        })

    # Write to world_resource_packs.json if any packs found
    if linked_packs:
        world_dir.mkdir(parents=True, exist_ok=True)
        with open(world_resource_packs_file, "w") as f:
            json.dump(linked_packs, f, indent=2)
        print(f"Linked {len(linked_packs)} resource pack(s) to '{level_name}'.")
    else:
        print("No valid resource packs found.")

