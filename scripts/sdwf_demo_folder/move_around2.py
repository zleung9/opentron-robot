import sys
sys.path.append("./")
from ot2 import OT2
from robots import ConductivityMeter as CM
from opentrons import protocol_api

metadata={"apiLevel": "2.11"}

# protocol run function
def run(protocol: protocol_api.ProtocolContext):
    ot2 = OT2(protocol, config="config.json") # ot2
    cm = CM() # conductivity meter
    ot2.start_server(host="169.254.204.106", port=23)
    
    ot2.move1()
    status = ot2.send_message("Start StartSquidStat")
    print(status)
    ot2.move2()
    
    ot2.measure_conductivity(ot2.plate9, cm) # measure cond and update cond
    cm.export_data("demo_cond.csv")

    print("Demo finished...")

if __name__ == "__main__":
    pass
    # cm = CM()
    # for i in range(8):
    #     cm.read_cond(append=True)
    # print(cm.cond_list)
    # print(cm.temp_list)
    # cm.export_data(clear_cache=True)
