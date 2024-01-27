import os
import pandas as pd
from auto.remote import RemoteStation
from auto.utils.database import Database
from auto.utils.data import parse_input_data, parse_output_data, parse_metadata
import json

#####
experiment_path = os.path.dirname(__file__)
experiment_name = os.path.basename(experiment_path)
config_path = os.path.join(experiment_path, "config.json")

with open(config_path, "r") as f:
    config = json.load(f)

# Create OT2 remote station and connect to it.
ot2 = RemoteStation("OT2", execution_mode="ot2", config=config["Remote Stations"]["OT2"])
ot2.connect()

# pull data from database and preprocess
db = Database(db="AI_self-driving_workdlow")
df_input = db.pull(table="ml_mtls")
df_output = db.pull(table="measured_cond_test")
df_metadata = db.pull(table="OT-2_dispensing")

df_input = parse_input_data(db.pull(table="ml_mtls"))
df_input.to_csv(os.path.join(experiment_path,"experiment.csv"), index=False)

#Update script to OT2, run SDWF experiment on OT2 and download result
ot2.put(experiment_path)
ot2.work_dir = os.path.join(ot2.remote_root_dir, experiment_name)
ot2.execute("make_solutions.py", mode="ot2")
ot2.download_data(f"{experiment_name}")

# Push result to database
df_output = parse_output_data(pd.read_csv("experiment.csv"))
df_metadata = parse_metadata(pd.read_csv("experiment.csv"))
Database.push(df_output, table="measured_cond_test")
Database.push(df_metadata, table="OT-2_dispensing")
