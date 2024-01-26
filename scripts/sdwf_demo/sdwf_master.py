import os
import pandas as pd
from auto.remote import RemoteStation
from auto.utils.database import Database
from auto.utils.data import generate_metadata, get_amount_from_recipe
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
# db = Database(db="AI_self-driving_workdlow")
# df_input = get_amount_from_recipe(db.pull(table="ml_mtls"))
# df_input.to_csv(os.path.join(experiment_path,"experiment.csv"), index=False)

#Update script to OT2
ot2.put(experiment_path)
ot2.work_dir = os.path.join(ot2.remote_root_dir, experiment_name)

# Run SDWF experiment on OT2 and download result
ot2.execute("make_solutions.py", mode="ot2")
# ot2.download_data(f"{experiment_name}/experiment.csv")

# # Push result to database
# df_experiment = pd.read_csv(os.path.join(experiment_path,"experiment.csv"))
# df_output, df_metadata = generate_metadata(df_experiment)
# Database.push(df_output, table="measured_cond")
# Database.push(df_metadata, table="metadata")
