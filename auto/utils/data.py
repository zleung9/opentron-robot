import json
import numpy as np
import pandas as pd 
from auto.utils.database import Database

DB = "test_db"
TOTAL_VOLUME_mL = 12
FACTOR = 0.001
db = Database(db=DB)

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

def parse_input_data(df: pd.DataFrame, total_volume_mL = TOTAL_VOLUME_mL, 
                           target: str = "Conductivity",
                           drop_empty_columns: bool = False) -> pd.DataFrame:

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
    if target == "Conductvity":
        df = df.rename({f"measured_conductivity": target})
    
    '''Re-Arrange Columns'''
    id_cols = ["unique_id"]
    chem_cols = [c for c in df.colunms if c.startswith('Chemical')]
    metadata = [line.rstrip("\n") for line in open("metadata_cols.txt")] # Or is the metadata added by OT2? 
    df_amount = df[id_cols + chem_cols + list(target) + metadata]
    
    df_amount[chem_cols] = df_amount[chem_cols] * (total_volume_mL * FACTOR)
    if drop_empty_columns: 
        df_amount = df_amount.loc[:, (df != 0).any(axis=0)]
    
    return df_amount

def get_new_batch_number(source: str = "lab") -> int:
    assert source in ("lab", "ml")
    if source == "lab": 
        lab_data = db.pull(db=DB, table="OT-2_dispensing")
        new_batch_number = lab_data["experiment_id"].max() + 1
    elif source == "ml":
        ml_data = db.pull(db=DB, table="ml_mtls")
        new_batch_number = ml_data["lab_batch"].max() + 1
   
    return new_batch_number
        
        
def parse_output_data(df: pd.DataFrame, total_volume_mL = TOTAL_VOLUME_mL) -> pd.DataFrame:
    chem_cols = [c for c in df.colunms if c.startswith('Chemical')]
    df[chem_cols] = df[chem_cols] / total_volume_mL 
    df = df.rename(columns={"unique_id": "ml_id"})
    df["lab_batch"] = get_new_batch_number(source="lab")
    return df


def parse_metadata(metadata: json) -> pd.DataFrame:
    """Given the ourput metadata as a json, generate the csv file that is consistent with "OT-2_dispensing" table in database. 
    """
    mdf = pd.read_json(metadata)
    return mdf