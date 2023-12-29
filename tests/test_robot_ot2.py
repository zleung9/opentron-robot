import os
import json
from auto.ot2 import OT2
from auto import protocol_api

class Test_OT2():
    test_path = os.path.dirname(__file__)
    exp_path = os.path.join(test_path, "demo_exp_1")
    with open(os.path.join(exp_path,"config.json"), "r") as f:
        config = json.load(f)

    def test_generate_dispensing_queue(self):
        ot2 = OT2(protocol_api.ProtocolContext, config=self.config)
        ot2.generate_dispensing_queue(n=1, m=2)
        print(ot2.dispensing_queue)

if __name__ == "__main__":
    test = Test_OT2()
    test.test_generate_dispensing_queue()