import os
from auto.remote import RemoteStation
from auto.utils.database import Database
from auto.utils.data import (
    parse_output_data, 
    parse_metadata,
    ask_for_composition_id,
    get_new_recipes
)
import json


def main():
    """Main function for running SDWF experiment on OT2."""    
    try:
        config_path = os.path.join(os.getcwd(), "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise Exception(
            "Config file not found in the experiment directory.\n"
            "Please make sure you are in the experiment folder!"
        )
    else:
        experiment_path = os.getcwd()

    # Create OT2 remote station and connect to it.
    ot2 = RemoteStation(
        name="Automat_Control_SDWF", 
        execution_mode="ot2", 
        config=config["Remote Stations"]["OT2"],
        experiment_path=experiment_path
    )
    ot2.connect()
    
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

    #Update script to OT2, run SDWF experiment on OT2 and download result
    ot2.put()
    ot2.execute("make_solutions.py", mode="ot2")
    ot2.download_data()
    ot2.disconnect()
    
    # Parse output data and metadata and push result to database
    ot2.export_metadata(comment="Another successful run of SDWF experiment on OT2.")
    df_metadata = parse_metadata(experiment_path, db=db)
    df_output = parse_output_data(
        experiment_path, 
        composition_id=comp_id, 
        batch_number=df_metadata["experiment_id"].values[0],
        db=db
    )
    db.push(df_metadata, table="OT-2_dispensing")
    db.push(df_output, table="measured_cond")


if __name__ == "__main__":
    main()
