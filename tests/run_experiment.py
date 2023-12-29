import os
from auto.remote import RemoteStation
import datetime
import json

#####
ROOT_PATH = "C:\\Users\\Automat\\Documents\\automation_control\\scripts\\"
EXP_FOLDER = "demo_exp_1"

with open("config.json", "r") as f:
    config = json.load(f)

ot2 = RemoteStation("OT2", execution_mode="ot2", config=config["Remote Stations"]["OT2"])
ot2.connect()

#Update script to OT2
ot2.load(
    ["demo_exp_1"],
    local_path='C:\\users\\automat\\documents\\automation_control\\scripts\\' 
)
ot2.work_dir = os.path.join(ot2.remote_root_dir, "demo_exp_1/")
# ot2.execute("move_around.py", mode="python")
ot2.execute("move_around2.py", mode="ot2")