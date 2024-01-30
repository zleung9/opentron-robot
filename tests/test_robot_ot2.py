import os
import unittest
import json
from unittest.mock import patch
from auto.ot2 import OT2
from auto import protocol_api
import pandas as pd

class Test_OT2(unittest.TestCase):

    cwd = os.path.dirname(__file__)
    config_path = os.path.join(cwd, "test_data","config.json")
    formulation_path = os.path.join(cwd, "test_data", "experiment.csv")
    with open(config_path, "r") as f:
        config = json.load(f)

    @patch("auto.ot2.OT2.load_labware")
    def test_generate_dispensing_queue(self, mock_load_labware):
        """Test that the dispensing queue is generated correctly"""
        mock_load_labware.return_value = None
        ot2 = OT2(protocol_api.ProtocolContext, config=self.config)
        ot2.generate_dispensing_queue(
            formula_input_path=self.formulation_path,
            volume_limit=5000,
            verbose=False
        )

        self.assertEqual(len(ot2.dispensing_queue), 80)
        self.assertEqual(ot2.chemical_names, [f"Chemical{i}" for i in range(1, 17)])
        self.assertEqual(ot2.formulations.iloc[0]["location"], (2, "A1"))
        self.assertEqual(ot2.formulations.iloc[0]["unique_id"], 111)


    def test_formulation_file_format(self):
        """Test that the formulation file is in the correct format"""
        df = pd.read_csv(self.formulation_path).reset_index(drop=True)
        columns = list(df.columns)
        self.assertTrue(all(f"Chemical{i}" in columns for i in range(1, 17)))
        self.assertIn("Conductivity", columns)
        self.assertIn("Time", columns)
        self.assertIn("Temperature", columns)
        self.assertIn("unique_id", columns)
    





if __name__ == "__main__":
    # unittest.main()
    test = Test_OT2()
    test.test_read_formulation()