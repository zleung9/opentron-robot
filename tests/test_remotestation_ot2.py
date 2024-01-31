from datetime import datetime
import unittest
from auto.remote import RemoteStation

class Test_OT2(unittest.TestCase):

    def test_logger_creation(self):
        """Test that the logger is created correctly"""
        name = "test"
        today = datetime.today().strftime('%Y-%m-%d')

        ot2 = RemoteStation(name=name, log=False)
        ot2.work_dir = "./test_data"
        ot2.create_logger(name, append=False, simple_fmt=True)
        self.assertIsNotNone(ot2.logger)
        self.assertEqual(ot2.logger.name, f"{name}")
        
        ot2.logger.info(f"Test log: {today}")
        with open(f"./test_data/{name}.log", "r") as f:
            log = f.read()
        self.assertIn(f"Test log: {today}", log)