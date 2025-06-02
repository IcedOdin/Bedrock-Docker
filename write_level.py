from amulet.level.formats.leveldb_world.format import BedrockLevelDAT
from amulet_nbt import ByteTag
from pathlib import Path


WORLD_PATH = Path("/bedrock/worlds")

def get_level_dat_path():
    properties_path = Path("/bedrock/server.properties")
    with open(properties_path) as f:
        for line in f:
            if line.startswith("level-name"):
                level_name = line.strip().split('=')[1]
                return WORLD_PATH / level_name / "level.dat"
    raise FileNotFoundError("World path not found")


# Load the level.dat file
file = str(get_level_dat_path())
print (file)
print (get_level_dat_path().exists())

    
level_dat = BedrockLevelDAT.from_file(file)   
compound = level_dat.compound

# Enable bonus chest and cheats
compound["bonusChestEnabled"] = ByteTag(1)
compound["bonusChestSpawned"] = ByteTag(1)
compound["cheatsEnabled"] = ByteTag(1)
compound["commandsEnabled"] = ByteTag(1)

# Access the experiments compound
experiments = level_dat.compound["experiments"]

# Modify values or add new ones
experiments["experiments_ever_used"] = ByteTag(1)  # Turn off gametest
experiments["gametest"] = ByteTag(1)  # Turn off gametest
#experiments["new_experiment"] = ByteTag(1)  # Add a new custom experiment


# Save the modified level.dat
level_dat.save("level.dat")
