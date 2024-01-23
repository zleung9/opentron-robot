import numpy as np
import pandas as pd 

TOTAL_VOLUME_mL = 12
FACTOR = 1000

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

def get_amount_from_recipe(df, total_volume_mL: int = TOTAL_VOLUME_mL, 
                           target_columns: list = ["Conductivity"],
                           drop_empty_columns: bool = False):
    """Convert compositions (percentages) to actual amount in microliters. 
    Parameters
    ----------
    df : pandas.DataFrame
        The recipe of the experiment pulled from database "measured_cond_table".
    Returns
    -------
    df : pandas.DataFrame
        The recipe of the experiment with actual amount in microgram.

    """
    
    '''Re-Arrange Columns'''
    id_cols = ["unique_id"]
    chem_cols = [c for c in df.colunms if c.startswith('Chemical')]
    df = df.rename({"measured_conductivity": "Conductivity"})
    metadata = [line.rstrip("\n") for line in open("metadata_cols.txt")] # Or is the metadata added by OT2? 
    df_amount = df[id_cols + chem_cols + target_columns + metadata]
    
    df_amount[chem_cols] = df_amount[chem_cols] * (total_volume_mL/FACTOR)
    if drop_empty_columns: 
        df_amount = df_amount.loc[:, (df != 0).any(axis=0)]
    
    return df_amount