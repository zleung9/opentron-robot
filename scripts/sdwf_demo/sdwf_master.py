import os
import pandas as pd
from auto.remote import RemoteStation
from auto.utils.database import Database
from auto.utils.data import (
    parse_input_data, 
    parse_output_data, 
    parse_metadata,
    generate_random_training_set,
    ask_for_composition_id,
    get_new_batch_number,
    # check_new_recipes
)
import json

#####
experiment_path = os.path.dirname(__file__)
experiment_name = os.path.basename(experiment_path)
config_path = os.path.join(experiment_path, "config.json")


def main():

    # Ask for composition id
    comp_id = ask_for_composition_id()

    # Load config file
    with open(config_path, "r") as f:
        config = json.load(f)

    # pull data from database and preprocess
    db = Database(db="test_db")
    df_input = parse_input_data(db.pull(table="ml_mtls"), composition_id=comp_id)
    # df_input = generate_random_training_set(num_chemical=10)
    df_input.to_csv(os.path.join(experiment_path,"experiment.csv"), index=False)

    # df_new_recipes = check_new_recipes(comp_id, db=db)
    # if df_new_recipes.empty():
    #     print("No new recipes to run")
    #     return

    # # Create OT2 remote station and connect to it.
    # ot2 = RemoteStation(
    #     name="Automat_Control_SDWF", 
    #     execution_mode="ot2", 
    #     config=config["Remote Stations"]["OT2"]
    # )
    # ot2.connect()
    # #Update script to OT2, run SDWF experiment on OT2 and download result
    # ot2.put(experiment_path)
    # ot2.work_dir = os.path.join(ot2.remote_root_dir, experiment_name)
    # ot2.execute("make_solutions.py", mode="ot2")
    # ot2.download_data(f"{experiment_name}")


    # Push result to database
    df_input["Conductivity"] = 0.1
    df_input["Temperature"] = 25
    df_input["Time"] = "2021-07-01 12:00:00"
    df_input.to_csv(os.path.join(experiment_path,"experiment.csv"), index=False)
    
    
    df_metadata = parse_metadata("metadata.json", db=db)
    
    df_output = parse_output_data(
        pd.read_csv("experiment.csv"), 
        composition_id=comp_id, 
        batch_number=df_metadata["experiment_id"].values[0],
        db=db
    )
    print(df_output)
    db.push(df_metadata, table="OT-2_dispensing")
    db.push(df_output, table="measured_cond")


if __name__ == "__main__":
    main()
