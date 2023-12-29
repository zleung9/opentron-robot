import sys
import json
sys.path.append("./")
from ot2 import OT2
from robots import ConductivityMeter as CM
from opentrons import protocol_api

metadata={"apiLevel": "2.11"}

# protocol run function
def run(protocol: protocol_api.ProtocolContext):
    
    # Define robots and preperation
    with open("config.json") as f:
        config = json.load(f)
    ot2 = OT2(protocol, config=config["Robots"]["OT2"]) # ot2
    cm = CM(config=config["Robots"]["Conductivity Meter"]) # conductivity meter
    ot2.start_server(host="169.254.204.106", port=23)
    
    # Execution
    ot2.move1()
    status = ot2.send_message("Start StartSquidStat")
    print(status)
    ot2.move2()
    
    ot2.measure_conductivity(ot2.plate9, cm) # measure cond and update cond
    cm.export_data("demo_cond.csv")

    print("Demo finished...")


def make_solution(ot2, formulations, config):
    ot2.load_chemicals(config)


if __name__ == "__main__":
    print("Error: cannot execute with python, use 'opentron_execute' instead.")
