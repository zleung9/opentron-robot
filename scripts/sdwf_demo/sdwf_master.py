

import os
import pandas as pd
from auto.remote import RemoteStation
from auto.utils.database import Database
from auto.utils.data import (
    parse_output_data, 
    parse_metadata,
    ask_for_composition_id,
    get_new_recipes
)
import json

#####
experiment_path = os.path.dirname(__file__)
experiment_name = os.path.basename(experiment_path)
config_path = os.path.join(experiment_path, "config.json")

def main():

    # Ask for composition id
    comp_id = ask_for_composition_id()

    # pull data from database and preprocess
    db = Database(db="test_db")
    df_input = get_new_recipes(comp_id, db=db)
    if df_input.empty:
        print("No new recipes to run")
        return
    else:
        # Save the experiment input to experiment folder
        df_input.to_csv(os.path.join(experiment_path,"experiment.csv"), index=False)

    # Create OT2 remote station and connect to it.
    with open(config_path, "r") as f:
        config = json.load(f)
    ot2 = RemoteStation(
        name="Automat_Control_SDWF", 
        execution_mode="ot2", 
        config=config["Remote Stations"]["OT2"],
        experiment_name=experiment_name
    )
    ot2.connect()
    print(ot2.work_dir)
    #Update script to OT2, run SDWF experiment on OT2 and download result
    ot2.put(experiment_path)
    # ot2.execute("make_solutions.py", mode="ot2")
    ot2.download_data()
    ot2.disconnect()
    
    # Parse output data and metadata and push result to database
    ot2.export_metadata(comment="Another successful run of SDWF experiment on OT2.")
    df_metadata = parse_metadata("metadata.json", db=db)
    df_output = parse_output_data(
        pd.read_csv("experiment.csv"), 
        composition_id=comp_id, 
        batch_number=df_metadata["experiment_id"].values[0],
        db=db
    )
    db.push(df_metadata, table="OT-2_dispensing")
    db.push(df_output, table="measured_cond")


if __name__ == "__main__":
    main()
