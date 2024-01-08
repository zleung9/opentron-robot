import os
import pandas as pd
from auto.remote import RemoteStation
from auto.utils.database import Database
from auto.utils.data import generate_metadata, get_amount_from_recipe
import json

#####
SSH_KEY_PATH = "C:\\Users\\Automat\\Documents\\automation_control\\.ssh\\ssh_key_OT2_SDWF"
ROOT_PATH = "C:\\Users\\Automat\\Documents\\automation_control\\scripts\\"
EXP_FOLDER = "sdwf_demo_folder"

#####
experiment_path = os.path.join(ROOT_PATH, EXP_FOLDER)
config_path = os.path.join(experiment_path, "config.json")
with open(config_path, "r") as f:
    config = json.load(f)

# Create OT2 remote station and connect to it.
ot2 = RemoteStation("OT2", execution_mode="ot2", config=config["Remote Stations"]["OT2"])
ot2.connect()

# pull data from database and preprocess
db = Database(db="AI_self-driving_workdlow")
df_input = get_amount_from_recipe(db.pull(table="measured_cond"))

#Update script to OT2
df_input.to_csv(os.path.join(experiment_path,"experiment.csv"), index=False)
ot2.put(EXP_FOLDER,local_path=ROOT_PATH)
ot2.work_dir = os.path.join(ot2.remote_root_dir, EXP_FOLDER)

# Run SDWF experiment on OT2
ot2.execute("make_solutions.py", mode="ot2")

# get restulst from OT2
ot2.download_data(f"{EXP_FOLDER}/experiment.csv")
df_experiment = pd.read_csv(os.path.join(experiment_path,"experiment.csv"))
df_output, df_metadata = generate_metadata(df_experiment)

# Push result to database
Database.push(df_output, table="measured_cond")
Database.push(df_metadata, table="metadata")
