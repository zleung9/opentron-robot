import numpy as np
import pandas as pd 

TOTAL_VOLUME_mL = 12
FACTOR = 0.001

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

def get_amount_from_recipe(df: pd.DataFrame, total_volume_mL = TOTAL_VOLUME_mL, 
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