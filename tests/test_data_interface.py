import os, json
from datetime import datetime
import unittest
import pandas as pd
from auto.utils.data import parse_metadata, parse_input_data, parse_output_data
from auto.utils.database import Database

class Test_Data_Interface(unittest.TestCase):    
    
    data_dir = os.path.join(os.path.dirname(__file__), "test_data")
    
    # def test_metadata_file_format(self):
    #     """Test that the metadata file is in the correct format"""
    #     metadata_path = os.path.join(self.data_dir, "metadata.json")
    #     with open(metadata_path, "r") as f:
    #         metadata = json.load(f)
    #     self.assertIn("created_by", metadata)
    #     self.assertIn("start_time", metadata)
    #     self.assertIn("end_time", metadata)
    #     self.assertIn("associated_log", metadata)
    #     self.assertIn("associated_csv", metadata)
    #     self.assertIn("comments", metadata)

    # def test_parse_metadata(self):
    #     """Test that the metadata file is parsed correctly. The input should be a dictionary and the output should be a dataframe that is consistent with "OT-2_dispensing" table in the database."""

    #     df_ot2_dispensing = Database(db="AI_self-driving_workflow").pull(table="OT-2_dispensing")
    #     expected_columns = list(df_ot2_dispensing.columns)
    #     metadata_path = os.path.join(self.data_dir, "metadata.json")
    #     df_metadata = parse_metadata(metadata_path)
    #     columns = list(df_metadata.columns)
        
    #     for col in columns:
    #         self.assertIn(col, expected_columns)
    #     for col in expected_columns:
    #         if col == "experiment_id":
    #             continue
    #         self.assertIn(col, columns)
    
    # def test_parse_input_data_columns(self):
    #     """Test that the input data is parsed correctly. The input is taken from "ml_mtls" table in the database.
    #     The output should be a dataframe taht has the folowwing defined columns."""
        
    #     expected_columns = ["unique_id"] + [f"Chemical{i}" for i in range(1, 17)] + ["Conductivity", "Temperature", "Time"]
    #     df_ml_mtls = Database(db="AI_self-driving_workflow").pull(table="ml_mtls")
    #     df_input = parse_input_data(df_ml_mtls)
    #     columns = list(df_input.columns)
        
    #     for col in columns:
    #         self.assertIn(col, expected_columns)
    #     for col in expected_columns:
    #         self.assertIn(col, columns)
    
    # def test_parse_input_data_volume(self):
    #     """Test that the input data is parsed correctly. The total volume of each row should sum up to the "Total Volume" column."""
    #     expected_total_volume_ml = 12 # in ml
    #     df_ml_mtls = Database(db="AI_self-driving_workflow").pull(table="ml_mtls")
    #     df_input = parse_input_data(df_ml_mtls, total_volume_mL=expected_total_volume_ml)
    #     total_volume_ul = df_input.loc[:, df_input.columns.str.contains("Chemical")].sum(axis=1).round(3)
    #     self.assertEqual(total_volume_ul / 1000, expected_total_volume_ml)
    #     # self.assertTrue((expected_total_volume_ml == total_volume_ul / 1000).all())

    def test_parse_output_data_columns(self):
        """Test that the metadata file is parsed correctly. The input should be a dictionary and the output should be a dataframe that is consistent with "OT-2_dispensing" table in the database."""

        df_measured_cond = Database(db="test_db").pull(table="measured_cond")
        expected_columns = list(df_measured_cond.columns)
        df_experiment = pd.read_csv(os.path.join(self.data_dir, "experiment.csv"))
        df_output = parse_output_data(df_experiment)
        columns = list(df_output.columns)
        for col in columns:
            self.assertIn(col, expected_columns)
        for col in expected_columns:
            self.assertIn(col, columns)
