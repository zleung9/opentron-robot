import json

class Test_Config():

    with open("demo_exp_1/config.py", "r") as f:
        config = json.load(f)
    
    def test_attributes(self):
        assert True