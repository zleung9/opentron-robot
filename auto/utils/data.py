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

def get_amount_from_recipe(df):
    """Convert compositions (percentages) to actual amount in microgram. 
    Parameters
    ----------
    df : pandas.DataFrame
        The recipe of the experiment pulled from database "measured_cond_table".
    Returns
    -------
    df : pandas.DataFrame
        The recipe of the experiment with actual amount in microgram.

    """
    df_amount = df.copy()
    return df_amount