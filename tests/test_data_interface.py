import os, json
import unittest
import pandas as pd
from auto.utils.data import (
    parse_metadata, 
    parse_input_data, 
    parse_output_data,
    generate_random_training_set
)
from auto.utils.database import Database
import math

class Test_Data_Interface(unittest.TestCase):    
    
    data_dir = os.path.join(os.path.dirname(__file__), "test_data")
    
    def test_metadata_file_format(self):
        """Test that the metadata file is in the correct format"""
        metadata_path = os.path.join(self.data_dir, "metadata.json")
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        self.assertIn("created_by", metadata)
        self.assertIn("start_time", metadata)
        self.assertIn("end_time", metadata)
        self.assertIn("associated_log", metadata)
        self.assertIn("associated_csv", metadata)
        self.assertIn("comments", metadata)

    def test_parse_metadata(self):
        """Test that the metadata file is parsed correctly. The input should be a dictionary and the output should be a dataframe that is consistent with "OT-2_dispensing" table in the database."""

        df_ot2_dispensing = Database(db="AI_self-driving_workflow").pull(table="OT-2_dispensing")
        expected_columns = list(df_ot2_dispensing.columns)
        metadata_path = os.path.join(self.data_dir, "metadata.json")
        df_metadata = parse_metadata(metadata_path)
        columns = list(df_metadata.columns)
        for col in columns:
            self.assertIn(col, expected_columns)
        for col in expected_columns:
            self.assertIn(col, columns)
    
    def test_parse_input_data_columns(self):
        """Test that the input data is parsed correctly. The input is taken from "ml_mtls" table in the database.
        The output should be a dataframe taht has the folowwing defined columns."""
        
        expected_columns = ["unique_id"] + [f"Chemical{i}" for i in range(1, 17)] + ["Conductivity", "Temperature", "Time"]
        df_ml_mtls = Database(db="AI_self-driving_workflow").pull(table="ml_mtls")
        df_input = parse_input_data(df_ml_mtls)
        columns = list(df_input.columns)
        for col in columns:
            self.assertIn(col, expected_columns)
        for col in expected_columns:
            self.assertIn(col, columns)
    
    def test_parse_input_data_volume(self):
        """Test that the input data is parsed correctly. The total volume of each row should sum up to the "Total Volume" column."""
        expected_total_volume_ml = 12 # in ml
        df_ml_mtls = Database(db="AI_self-driving_workflow").pull(table="ml_mtls")
        df_input = parse_input_data(df_ml_mtls, total_volume_mL=expected_total_volume_ml)
        total_volume_ul = df_input.loc[:, df_input.columns.str.contains("Chemical")].sum(axis=1)
        self.assertEqual(total_volume_ul / 1000, expected_total_volume_ml)

    def test_parse_output_data_columns(self):
        """Test that the metadata file is parsed correctly. The input should be a dictionary and the output should be a dataframe that is consistent with "OT-2_dispensing" table in the database."""

        df_measured_cond = Database(db="AI_self-driving_workflow").pull(table="measured_cond")
        expected_columns = list(df_measured_cond.columns)
        df_experiment = pd.read_csv(os.path.join(self.data_dir, "experiment.csv"))
        df_output = parse_output_data(df_experiment)
        columns = list(df_output.columns)
        for col in columns:
            self.assertIn(col, expected_columns)
        for col in expected_columns:
            self.assertIn(col, columns)

    def test_generate_random_training_set(self):
        """Test that the random training set is generated correctly. The output should be a dataframe with the following columns:
        - unique_id
        - Chemical1, Chemical2, ..., Chemical16
        - Conductivity
        - Temperature
        - Time
        """
        test_num_recipe = 16
        test_num_chemical = 12
        test_total_volume_ml = 12
        
        df_training_set = generate_random_training_set(
            num_recipe=test_num_recipe, 
            num_chemical=test_num_chemical, 
            total_volume_mL=test_total_volume_ml
        )
        columns = list(df_training_set.columns)
        expected_columns = ["unique_id"] + \
                           [f"Chemical{i}" for i in range(1, 17)] + \
                           ["Conductivity", "Temperature", "Time"]
        
        # Test that the columns are as expected
        for col in columns:
            self.assertIn(col, expected_columns)
        for col in expected_columns:
            self.assertIn(col, columns)

        # Test that the number of rows is as expected
        self.assertEqual(len(df_training_set), 16)

        # test that the unique_id, Temperature, Conductivity, and Time columns are all None
        self.assertTrue(all(item is None for item in df_training_set["unique_id"]))
        self.assertTrue(all(item is None for item in df_training_set["Temperature"]))
        self.assertTrue(all(item is None for item in df_training_set["Conductivity"]))
        self.assertTrue(all(item is None for item in df_training_set["Time"]))
        
        # Test that the volume of each row sums up to the total volume
        for row in df_training_set.iloc[:, 1:17].iterrows():
            sum_ = sum(row[1])
            self.assertTrue(math.isclose(sum_, test_total_volume_ml, rel_tol=1e-3))
        

if __name__ == "__main__":
    Test_Data_Interface().test_generate_random_training_set()