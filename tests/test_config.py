import os
import json
import unittest
import os
import json

class Test_Config():
    cwd = os.path.dirname(__file__)
    config_path = os.path.join(cwd, "test_data","config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    

    class TestConfig(unittest.TestCase):
        
        def setUp(self):
            cwd = os.path.dirname(__file__)
            config_path = os.path.join(cwd, "test_data", "config.json")
            with open(config_path, "r") as f:
                self.config = json.load(f)

        def test_has_attributes(self):
            self.assertIn("System", self.config)
            self.assertIn("Remote Station", self.config)
            self.assertIn("Robots", self.config)

        def test_system_attributes(self):
            system = self.config["System"]
            self.assertIn("work_dir", system)
            self.assertIn("experiment name", system)

        def test_remote_station_attributes(self):
            remote_station = self.config["Remote Station"]
            self.assertIn("OT2", remote_station)
        
        def test_robot_attributes(self):
            robots = self.config["Robots"]
            self.assertIn("OT2", robots)
            self.assertIn("Conductivity Meter", robots)
            self.assertIn("SquidStat", robots)
            self.assertIn("Robotic Arm", robots)
            self.assertIn("ChemSpeed", robots)

        def test_conductivity_meter_has_offset(self):
            cm = self.config["Robots"]["Conductivity Meter"]
            self.assertIn("offset", cm)
            offset = cm["offset"]
            self.assertEqual(len(offset), 3)
            self.assertIsInstance(offset[0], float)
            self.assertIsInstance(offset[1], float)
            self.assertIsInstance(offset[2], float)
            
        # Add more tests as needed

    if __name__ == "__main__":
        unittest.main()
