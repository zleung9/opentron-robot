import sys
sys.path.append("./")
import time
import datetime
print(f"Script starts at: {datetime.datetime.today()}")
time.sleep(1)
print("Loading opentron modules...") # Usually takes ~15 seconds
from ot2 import OT2
from robots import ConductivityMeter as CM
from opentrons import protocol_api
print("Loading complete...")

time.sleep(1)

metadata={"apiLevel": "2.11"}

# protocol run function
def run(protocol: protocol_api.ProtocolContext):
    ot2 = OT2(protocol) # ot2
    cm = CM() # conductivity meter
    ot2.start_server(host="169.254.204.106", port=23)
    
    ot2.movearound()
    status = ot2.send_message("Start StartSquidStat")
    print(status)
    ot2.movearound()
    for i in range(8):
        ot2.movearound()
        cm.read_cond(append=True)
        print(f"Conductivity measured: {i+1}!")
    
    cm.export_data("demo_cond.csv")
    # ot2.demo()
    print("Demo finished...")

if __name__ == "__main__":
    # run(None)
    print("Start")
    for i in range(10):
        time.sleep(1)
        print(datetime.datetime.today())
    # cm = CM()
    # for i in range(8):
    #     cm.read_cond(append=True)
    # print(cm.cond_list)
    # print(cm.temp_list)
    # cm.export_data(clear_cache=True)
