import json
import numpy as np
import pandas as pd 
from auto.utils.database import Database

TEST_DB = "test_db"
TOTAL_VOLUME_mL = 12
FACTOR = 1000
METADATA_COLS = ["Temperature", "Time"]

def generate_metadata(df):
    """Given the output data, generate the data to be uploaded back to database as well as
    the metadata for the experiment.
    Parameters
    ----------
    df : pandas.DataFrame
        The output data from the experiment. Its format is defined in Figure 3 in the proposal.
    Returns
    -------
    df : pandas.DataFrame
        The data to be uploaded back to database. Its format is defined in Figure 3 in the proposal.
    df : pandas.DataFrame
        The metadata for the experiment. Its format needs to be difined. It could be a placeholder.
    """
    df_output = df.copy()
    df_metadata = df.copy()
    return df_output, df_metadata

def parse_input_data(df: pd.DataFrame, 
                     total_volume_mL = TOTAL_VOLUME_mL, 
                     target: str = "Conductivity",
                     drop_empty_columns: bool = False,
                     composition_id=None) -> pd.DataFrame:

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

    - composition_id: int
        Composition id for the experiment; default is None. If None select all rows.              
    
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
        df: pd.DataFrame, 
        total_volume_mL = TOTAL_VOLUME_mL, 
        composition_id: int = 1,
        batch_number: int = None,
        db:Database = None
    ) -> pd.DataFrame:
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


def parse_metadata(metadata_path: str, db=None) -> pd.DataFrame:
    """Given the ourput metadata as a json, generate the csv file that is consistent with "OT-2_dispensing" table in database. 
    """
    if not db:
        db = Database(db=TEST_DB)
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


def generate_random_training_set(
        num_recipe: int = 16,
        num_chemical: int = 12,
        total_volume_mL: int = TOTAL_VOLUME_mL
    ) -> pd.DataFrame:
    """Generate a random initial training set for the SDWF experiment. 

    Parameters
    ----------
    num_recipe : int, optional
        The number of recipes in the training set. Default is 16.
    num_chemical : int, optional
        The number of chemicals in each recipe. Default is 12.
    total_volume_mL : int, optional
        The total volume in milliliters for each recipe. Default is TOTAL_VOLUME_mL.

    Returns
    -------
    df : pandas.DataFrame
        The training set. Its format is defined in Table 1 in the proposal.
    """
    df_list = []
    total_num_chemical = 16

    for i in range(num_recipe):
        unique_id = [None] # unique_id is None because it is not generated by Machine learning
        volume_composition = list(np.zeros(total_num_chemical)) # initialize the composition with zeros
        percentage_composition = np.random.dirichlet(np.ones(num_chemical), size=1).tolist()[0]
        volume_composition[:num_chemical] = [p * total_volume_mL for p in percentage_composition]
        other = [None, None, None]
        row = unique_id + volume_composition + other 
        df_list.append(row)
    
    df = pd.DataFrame(df_list, columns=['unique_id', 'Chemical1', 'Chemical2', \
                                 'Chemical3', 'Chemical4','Chemical5', 'Chemical6',\
                                 'Chemical7', 'Chemical8', 'Chemical9', 'Chemical10',\
                                 'Chemical11', 'Chemical12','Chemical13', 'Chemical14',\
                                 'Chemical15', 'Chemical16', 'Conductivity', "Temperature",
                                 "Time"])
    return df


def get_new_recipes(composition_id=None, db=None, num_recipe=16, num_chemical=10):
    """
    Check if there are new recipes to run for the given composition_id.
    
    This function pulls data from the "ml_mtls" table and compares it with data pulled from the "measured_cond" table.
    If for a given composition_id, there are recipes in "ml_mtls" but not in "measured_cond", it will return the new recipes.
    Otherwise, it will return an empty DataFrame or raise an error if there are measurements but no machine learning data.
    
    Args:
        composition_id (int, optional): The composition ID to check for new recipes. Defaults to None.
        db (Database, optional): The database object to use for pulling data. Defaults to None.
        num_recipe (int, optional): The number of recipes to include in the training set. Defaults to 16.
        num_chemical (int, optional): The number of chemicals to include in the training set. Defaults to 10.
    
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
    
    if not df_ml.empty and df_mc.empty:
        raise ValueError(f"No measurement found for composition_id: {composition_id}, but there are machine learning data for it. Please check the database.")
    elif df_ml.empty and df_mc.empty: 
        # It is a new composition id, generate new training set
        df_input = generate_random_training_set(num_recipe=num_recipe, num_chemical=num_chemical)
        print(f"This is a new composition, just generated {num_recipe} training set for composition_id: {composition_id}.")
    elif df_ml.empty and not df_mc.empty: 
        # no machine learning data for this composition_id is generated
        print(f"There are {len(df_mc)} measurements for composition_id: {composition_id}, but no machine learning data is generated for it.")
        yes = input("Do you want to generate new training data for it? (yes/no)\n>> ")
        if yes.lower() == "yes":
            df_input = generate_random_training_set(num_chemical=num_chemical)
        else:
            return pd.DataFrame()
    else:
        # There are both machine learning data and measurements for this composition_id
        mc_ids = df_mc["ml_id"].values
        ml_ids = df_ml["unique_id"].values
        new_ids = list(set(ml_ids) - set(mc_ids))
        df_input = parse_input_data(df_ml.loc[df_ml["unique_id"].isin(new_ids)])
        print(f"There are {len(new_ids)} new recipes for composition_id: {composition_id}.")
    
    return df_input
