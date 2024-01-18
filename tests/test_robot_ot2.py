import os
import unittest
import json
from unittest.mock import patch
from auto.ot2 import OT2
from auto import protocol_api
import pandas as pd

class Test_OT2(unittest.TestCase):

    os.path.dirname(__file__)
    with open(os.path.join("test_data","config.json"), "r") as f:
        config = json.load(f)
    
    @patch("auto.ot2.OT2.load_labware")
    def test_generate_dispensing_queue(self, mock_load_labware):
        mock_load_labware.return_value = None
        ot2 = OT2(protocol_api.ProtocolContext, config=self.config)
        ot2.generate_dispensing_queue(
            formula_input_path=os.path.join("test_data", "experiment.csv"),
            volume_limit=5000,
            verbose=True
        )
        self.assertEqual(len(ot2._dispensing_queue), 80)

    def test_read_formulation(self):
        formula_input_path = os.path.join("test_data", "experiment.csv")
        df = pd.read_csv(formula_input_path).reset_index(drop=True)
        print(df)
    
    def test_input_data(self):
        ...





if __name__ == "__main__":
    # unittest.main()
    test = Test_OT2()
    test.test_read_formulation()