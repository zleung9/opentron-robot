import os
from auto.remote import RemoteStation
import json
from auto.utils.database import Database
from auto.utils.data import generate_metadata, get_amount_from_recipe
import pandas as pd
import argparse

def main():

    # Parse config file and ask user for work_dir and experiment_name
    with open("config.json", "r") as f:
        config = json.load(f)
    config, update_config = parse_config(config)
    work_dir = config["System"]["work_dir"]
    experiment_name = config["System"]["experiment_name"]
    if update_config:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

    # Create RemoteStation OT2, upload experiment to OT2 and set remote work_dir
    ot2 = RemoteStation("OT2", execution_mode="ot2", config=config["Remote Stations"]["OT2"])
    ot2.connect()
    
    # pull data from database and preprocess
    db = Database(db="AI_self-driving_workdlow")
    df_input = get_amount_from_recipe(db.pull(table="measured_cond"))
    df_input.to_csv(os.path.join(work_dir, experiment_name,"experiment.csv"), index=False)
    ot2.put([experiment_name], local_path=work_dir)
    ot2.work_dir = os.path.join(ot2.remote_root_dir, experiment_name)
    
    # ot2.execute("move_around.py", mode="python")
    ot2.execute("make_solutions.py", mode="ot2")

    # get restulst from OT2
    ot2.download_data(f"{experiment_name}/experiment.csv")
    df_experiment = pd.read_csv(os.path.join(work_dir, experiment_name,"experiment.csv"))
    df_output, df_metadata = generate_metadata(df_experiment)

    # Push result to database
    Database.push(df_output, table="measured_cond")
    Database.push(df_metadata, table="metadata")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run SDWF")
    parser.add_argument("-h", "--help", action="help", help="show this help message and exit")
    args = parser.parse_args()
    return args

def parse_config(config):
    """Parse config file and ask user for work_dir and experiment_name"""
    # Ask user for working directory
    update_config = False
    default_work_dir = config["System"]["work_dir"]
    work_dir = input(
        f"\nConfirm that working directory below. [Enter] to confirm or enter your own path:\n{default_work_dir}\n"
    )
    if not work_dir:
       work_dir = default_work_dir # press enter to use default path
    else:
        config["System"]["work_dir"] = work_dir # update config file with the latest work_dir
        update_config = True
    # Ask suer for experiment name
    default_experiment_name = config["System"]["experiment_name"]
    experiment_name = input(
        f"Confirm the experiment name below. [Enter] to confirm or enter your own name:\n{default_experiment_name}\n"
    )
    if not experiment_name:
        experiment_name = default_experiment_name
    else:
        config["System"]["experiment_name"] = experiment_name
        update_config = True
    
    return config, update_config

if __name__ == "__main__":
    main()