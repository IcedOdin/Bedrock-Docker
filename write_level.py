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

def check_path():
    print (get_level_dat_path().exists())
    val = get_level_dat_path().exists()
    return val

def load_settings():
    # Load the level.dat file
    file_path = str(get_level_dat_path())
    level_dat = BedrockLevelDAT.from_file(file_path)   
    compound = level_dat.compound
    
    # Enable bonus chest and cheats
    compound["bonusChestEnabled"] = ByteTag(1)
    compound["bonusChestSpawned"] = ByteTag(0)
    compound["cheatsEnabled"] = ByteTag(1)
    compound["commandsEnabled"] = ByteTag(1)
    compound["commandblockoutput"] = ByteTag(1)
    compound["commandblocksenabled"] = ByteTag(1)
    compound["sendcommandfeedback"] = ByteTag(1)
    compound["functioncommandlimit"] = ByteTag(10000)
    
    
    # Access the experiments compound
    experiments = level_dat.compound["experiments"]
    
    # Modify values or add new ones
    experiments["experiments_ever_used"] = ByteTag(1)  # Turn on gametest
    experiments["gametest"] = ByteTag(1)  # Turn on gametest
    experiments["saved_with_toggled_experiments"] = ByteTag(1)  # Turn on Toggeled Experiments
    
    
    # Save the modified level.dat
    level_dat.save("level.dat")

if check_path() == True:
    load_settings()
    print ("Loading Settings ....")
else:
    print ("Skipping for now....")

