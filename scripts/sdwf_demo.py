import os
import pandas as pd
from auto.remote import RemoteStation
from auto.utils.database import Database, get_amount_from_recipe
import json

#####
SSH_KEY_PATH = "C:\\Users\\Automat\\Documents\\automation_control\\.ssh\\ssh_key_OT2_SDWF"
ROOT_PATH = "C:\\Users\\Automat\\Documents\\automation_control\\scripts\\"
EXP_FOLDER = "demo_exp_1"

#####
experiment_path = os.path.join(ROOT_PATH, EXP_FOLDER)
config_path = os.path.join(experiment_path, "config.json")
with open(config_path, "r") as f:
    config = json.load(f)


# Create OT2 remote station and connect to it.
ot2 = RemoteStation("OT2", execution_mode="ot2", config=config["Remote Stations"]["OT2"])
ot2.connect()


# pull data from database
df = get_amount_from_recipe(Database.pull())
df.to_csv(os.path.join(experiment_path,"experiment.csv"), index=False)

#Update script to OT2
ot2.put(
    EXP_FOLDER,
    local_path='C:\\users\\automat\\documents\\automation_control\\tests\\'
)
ot2.work_dir = os.path.join(ot2.remote_root_dir, "demo_exp_1/")

# Download data from OT2
ot2.download_data(f"{EXP_FOLDER}/experiment.csv")
df = pd.read_csv(os.path.join(experiment_path,"experiment.csv"))
Database.push(df, table="recipes")

