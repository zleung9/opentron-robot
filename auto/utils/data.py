import os
import json
import numpy as np
import pandas as pd 
from auto.utils.database import Database

TEST_DB = "test_db"
TOTAL_VOLUME_mL = 12
FACTOR = 1000
METADATA_COLS = ["Temperature", "Time"]


def parse_input_data(
        df: pd.DataFrame, 
        total_volume_mL = TOTAL_VOLUME_mL, 
        target: str = "Conductivity",
        drop_empty_columns: bool = False
    ) -> pd.DataFrame:

    """Convert compositions (percentages) to actual amount in microliters. 
    Parameters
    ----------
    - df : pandas.DataFrame
        The recipe of the experiment pulled from database "measured_cond_table".
    
    - total_volume_ml: int
        Total volume of the solution. currently set to defualt but can be changed 
        upon funciton call 
                    
    - target: str 
        String communicating target parameter for OT2; default is conductivity
                
    - drop_empty_columns: bool
        Drops all zero columns in dataframe; default is False      
    
    Returns
    -------
    df_amount : pandas.DataFrame
        The recipe of the experiment with actual amount in microliters and with specific columns detailed in proposal.

    """
    
    '''Re-name target column'''
    target = "Conductivity"
    df = df.rename(columns={f"predicted_conductivity": target})
    df[target] = np.nan # delete the predicted value from the input data
        
    '''Re-Arrange Columns'''
    id_cols = ["unique_id"]
    chem_cols = [c for c in df.columns if c.startswith('Chemical')]
    df_amount = df[id_cols + chem_cols + [target]]
    for c in METADATA_COLS:
        df_amount[c] = np.nan
    
    df_amount[chem_cols] = df_amount[chem_cols] * (total_volume_mL * FACTOR)
    if drop_empty_columns: 
        df_amount = df_amount.loc[:, (df != 0).any(axis=0)]
    
    return df_amount


def get_new_batch_number(db=None, source: str = "lab") -> int:
    if not db:
        db = Database(db=TEST_DB)
    assert source in ("lab", "ml")
    if source == "lab": 
        lab_data = db.pull(table="OT-2_dispensing")
        new_batch_number = lab_data["experiment_id"].max() + 1
    elif source == "ml":
        ml_data = db.pull(table="ml_mtls")
        new_batch_number = ml_data["lab_batch"].max() + 1
   
    return new_batch_number
        
        
def parse_output_data(
        experiment_path: str,
        total_volume_mL = TOTAL_VOLUME_mL, 
        composition_id: int = 1,
        batch_number: int = None,
        db:Database = None
    ) -> pd.DataFrame:

    df = pd.read_csv(os.path.join(experiment_path, "experiment.csv"))
    if not db:
        db = Database(db=TEST_DB)
    assert batch_number is not None
    chem_cols = [c for c in df.columns if c.startswith('Chemical')]
    total_volume_uL = total_volume_mL * FACTOR
    df[chem_cols] = df[chem_cols] / total_volume_uL 
    df = df.rename(columns={"unique_id": "ml_id"})
    df["lab_batch"] = batch_number
    df = df.rename(columns={"Conductivity": "measured_conductivity"})
    df["Composition_id"] = composition_id
    df.drop(columns=["Time"], inplace=True)
    return df


def parse_metadata(experiment_path: str, db=None) -> pd.DataFrame:
    """Given the ourput metadata as a json, generate the csv file that is consistent with "OT-2_dispensing" table in database. 
    """
    if not db:
        db = Database(db=TEST_DB)
    metadata_path = os.path.join(experiment_path, "metadata.json")
    metadata = json.load(open(metadata_path, "r"))
    metadata["experiment_id"] = get_new_batch_number(source="lab", db=db)
    mdf = pd.DataFrame(metadata, index=[0])
    return mdf


def ask_for_composition_id(trial=0):
    """Helper function to get the composition_id for the training set. 
    Repeat until a valid integer is given."""
    
    if trial == 3:
        raise ValueError("You have tried 3 times, please contact the administrator for help.")
    try:
        comp_id = input("Please introduce the Composition_id for this training set round:\n>> ")
        trial += 1
        return int(comp_id)
    except:
        print("Composition_id needs to be an integer, try again!\r")
        return ask_for_composition_id(trial=trial)


def generate_training_set(
        num_recipe: int = 16,
        max_num_chemical: int = 16,
        num_chemical: int = 16,
        total_volume_mL: int = TOTAL_VOLUME_mL,
        stock_solution_indices: list = []
    ) -> pd.DataFrame:
    """Generate a random initial training set for the SDWF experiment. 

    Parameters
    ----------
    num_recipe : int, optional
        The number of recipes in the training set. Default is 16.
    num_chemical : int, optional
        The number of chemicals in each recipe. Default is 16.
    max_num_chemical : int, optional
        The maximum number of chemicals in each recipe. Default is 16.
    total_volume_mL : int, optional
        The total volume in milliliters for each recipe. Default is TOTAL_VOLUME_mL.
    stock_solution_indices : list, optional
        The indices of stock solutions to measure. Default is an empty list.

    Returns
    -------
    df : pandas.DataFrame
        The training set. Its format is defined in Table 1 in the proposal.
    """
    df_list = []
    chemical_names = [f"Chemical{i+1}" for i in range(max_num_chemical)]
    num_recipe = len(stock_solution_indices) if stock_solution_indices else num_recipe
    
    for i in range(num_recipe):
        unique_id = [None] # unique_id is None because it is not generated by Machine learning
        if i == 0 or i == num_recipe - 1: # the first and last recipes are dummy solutions
            percentage_composition = np.ones(max_num_chemical) / max_num_chemical
        else:
            percentage_composition = np.zeros(max_num_chemical)
            if stock_solution_indices: # create recipes for stock solutions only
                percentage_composition[stock_solution_indices[i] - 1] = 1
            else: # create random recipes with only `num_chemical` chemicals activated
                percentage_composition[:num_chemical] = np.random.dirichlet(np.ones(num_chemical), size=1).squeeze()
        volume_composition = list(percentage_composition * total_volume_mL * FACTOR)
        other = [None, None, None]
        row = unique_id + volume_composition + other 
        df_list.append(row)
    
    df = pd.DataFrame(
        df_list, 
        columns=['unique_id'] + chemical_names + ['Conductivity', "Temperature", "Time"])
    return df


def get_new_recipes(
        composition_id=None, 
        db=None, 
        max_num_recipe=16,
        max_num_chemical=16
    ) -> pd.DataFrame:
    """
    Check if there are new recipes to run for the given composition_id.
    
    This function pulls data from the "ml_mtls" table and compares it with data pulled from the "measured_cond" table.
    If for a given composition_id, there are recipes in "ml_mtls" but not in "measured_cond", it will return the new recipes.
    Otherwise, it will return an empty DataFrame or raise an error if there are measurements but no machine learning data.
    
    Args:
        composition_id (int, optional): The composition ID to check for new recipes. Defaults to None.
        db (Database, optional): The database object to use for pulling data. Defaults to None.
        num_recipe (int, optional): The number of recipes to include in the training set. Defaults to 16.
        num_chemical (int, optional): The number of chemicals to include in the training set. Defaults to 16.
    
    Returns:
        pandas.DataFrame: The new recipes as a DataFrame if there are any, otherwise an empty DataFrame.
    
    Raises:
        ValueError: If there are machine learning data for the given composition_id but no measurements found in the database.
    
    """
    if not db:
        db = Database(db=TEST_DB)
    df_ml = db.pull(table="ml_mtls")
    df_mc = db.pull(table="measured_cond")
    
    if composition_id is not None:
        df_ml = df_ml.loc[df_ml["Composition_id"] == composition_id]
        df_mc = df_mc.loc[df_mc["Composition_id"] == composition_id]
    
    mc_ids = df_mc["ml_id"].values
    ml_ids = df_ml["unique_id"].values
    
    new_ml_ids = list(set(ml_ids) - set(mc_ids)) # recipes in ml_mtls but not in measured_cond
    new_mc_ids = list(set(mc_ids) - set(ml_ids)) # recipes in measured_cond but not in ml_mtls
    print(f"Found {len(mc_ids)} measurements and {len(ml_ids)} predictions for composition_id: {composition_id}")
    print(f"{len(new_ml_ids)} predictions have yet to be measured.")
    print(f"{len(new_mc_ids)} measurements are not found in ml_mtls table (They might be initial training set).")
    id_ = input("Continue? [Enter] to proceed or type 'no' to exit. Type integer for a different composition ID.\n>> ")
    if id_:
        try:
            return get_new_recipes(
                composition_id=int(id_),
                db=db,
                max_num_recipe=max_num_recipe,
                max_num_chemical=max_num_chemical
            )
        except:
            return pd.DataFrame()

    if new_ml_ids: # there are new recipes in machine learning data, these are the ones to measure
        df_input = parse_input_data(df_ml.loc[df_ml["unique_id"].isin(new_ml_ids)])
        print(f"There are {len(new_ml_ids)} new recipes for composition_id: {composition_id}.")
    else:
        if not new_mc_ids: # Neither new measurements nor new predictions
            print(f"No new predictions or measurements found for composition_id: {composition_id}.")
        else: # New measurements that are not found in ml_mtls table
            print(f"Found {len(new_mc_ids)} measurements for composition_id: {composition_id} that are not in machine learning data. They might be initial training sets.")
        option = input("\nGenerating training set? \n1. Measure stock solutions.\n2. Generate random training set.\n3. Exit\n>> ")
        try:
            if int(option) == 1:
                stock_solution_indices = input("Please provide the indices (1~16) of stock solutions to measure, separated by comma. [Enter] to measure all stock solutions.\n>> ").split(",")
                if stock_solution_indices:
                    stock_solution_indices = [int(i) for i in stock_solution_indices]
                else:
                    stock_solution_indices = [i for i in range(1, max_num_chemical + 1)]
                num_chemical = len(stock_solution_indices)
                num_recipe = len(stock_solution_indices)
                if not num_recipe:
                    raise ValueError("No stock solution indices provided. Exit.")
            elif int(option) == 2:
                stock_solution_indices = []
                num_chemical = input("How many tock solutions to include in the training set? [Enter] for default number: 16\n>>")
                num_chemical = 16 if not num_chemical else min(int(num_chemical), max_num_chemical)
                num_recipe = input("How many new recipes to generate? [Enter] for default number: 16\n>>")
                num_recipe = 16 if not num_recipe else min(int(num_recipe), max_num_recipe)
            else:
                raise ValueError("Exit")
        except:
            return pd.DataFrame()
            
        df_input = generate_training_set(
            num_recipe=num_recipe, 
            num_chemical=num_chemical, 
            stock_solution_indices=stock_solution_indices
        )
        print(f"{num_recipe} new recipes are generated for composition_id: {composition_id}.")
    
    return df_input
