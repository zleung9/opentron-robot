import sys
import json
sys.path.append("./")
from ot2 import OT2
from robots import ConductivityMeter
from opentrons import protocol_api

metadata={"apiLevel": "2.11"}

# protocol run function
def run(protocol: protocol_api.ProtocolContext):
    
    with open("config.json") as f:
        config = json.load(f)
    ot2 = OT2(protocol, config=config) # ot2
    cm = ConductivityMeter(config=config) # conductivity meter
    # ot2.start_server(host=config["Remote Stations"]["OT2"]["ip"], port=23)

    # Execution
    ot2.pip_arm.tip_racks.append(ot2.tiprack)  # mount tiprack on pipette
    ot2.generate_dispensing_queue(verbose=True) # generate dispensing queue
    for sub_queue in ot2.dispensing_queue:
        # get the block name from the first source vial
        source = sub_queue[0][0]
        if source is None:
            print("Dispensing finished...")
            break
        # block = (source[0], 0 if "1" in source[1] or "2" in source[1] else 1) 
        # ot2.move_cover(block, "deck", verbose=True) # uncover the block before dispensing
        for source, target, volume, speed_factor in sub_queue:
            ot2.dispense_chemical(source, target, volume, speed_factor, verbose=True) 
        # ot2.move_cover("deck", block, verbose=True) # cover the block after dispensing


    ot2.measure_conductivity(cm) # measure cond and update cond
    cm.export_result()

    print("Demo finished...")
    

if __name__ == "__main__":
    print("Error: cannot execute with python, use 'opentron_execute' instead.")
