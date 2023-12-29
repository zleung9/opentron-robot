import sys
import json
sys.path.append("./")
try:
    from robots import Robot, ConductivityMeter
except ModuleNotFoundError:
    from auto.robots import Robot, ConductivityMeter

try:
    from sockets import SocketServer
except ModuleNotFoundError:
    from auto.sockets import SocketServer

try:
    from opentrons import protocol_api
except ModuleNotFoundError:
    from auto import protocol_api

class OT2(Robot):
    def __init__(self, protocol:protocol_api.ProtocolContext, config=None):
        super().__init__(config=config)
        self.server = None # by default the server is down
        self.client = None
        self.protocol = protocol
        self.lot = {i:None for i in range(1, 12)} # initiate plate 1 to 11
        self.arm = {"left": None, "right": None} # Initiate left and right arm
        if config:
            self.load_config(config)

    def load_config(self, config) -> None:
        """ Park labwares into slots and mount pipettes onto arms.
        """
        # Park labwares
        self.config = config
        config = config["Robots"]["OT2"] # only take the configuration for OT2 robotics
        for key, value in config["labwares"].items():
            n = int(key)
            if value.endswith(".json"):
                with open(value, "r") as f:
                    definition = json.load(f)
                self.lot[n] = self.protocol.load_labware_from_definition(definition, n)
            else:
                self.lot[n] = self.protocol.load_labware(value, n)
            if "tiprack" in value:
                self.tiprack = self.lot[n]
        

        # Mount pippetes and conductivity measure
        for side, tip in config["pipettes"].items():
            if tip == "conductivity":
                self.arm[side] = self.protocol.load_instrument("p300_single_gen2", side)
                self.cond_arm = self.arm[side]
            else:
                self.arm[side] = self.protocol.load_instrument(tip, side)
                self.pip_arm = self.arm[side]

    

    def start_server(self, host="169.254.230.44", port=23):
        self.server = SocketServer(host=host, port=port)


    def send_message(self, message=None):
        message = self.server.client_start("Start SquidStat")
        return message


    def movearound(self) -> None:
        """For demo only.
        """
        print("Moving things around and making solutions...")
    

    def demo(self) -> None: ...


    def sleep(self, t:int) -> None:
        """Pause for `t` seconds."""
        self.protocol.delay(t)


    def aspirate(self, volume, location, z=2):
        """ Pippete will aspirate at `z`mm above the bottom of the well. 
        """
        self.pip_arm.aspirate(volume, location.bottom(z=z))
        self.sleep(1)
        self.pip_arm.touch_tip(v_offset=-3)
    
    
    def dispense(self, volume, location, z=2):
        """ Pippete will dispense at `z`mm above the bottom of the well and push out extra 10 uL. 
        """
        self.pip_arm.dispense(volume, location.bottom(z=z))
        self.pip_arm.blow_out()
        self.sleep(1)


    def dispense_chemical(
            self, 
            source:tuple=(None,None),  
            target:tuple=(None,None),
            volume:float=0,
            verbose:bool=False
        )-> None:
        """ Second lowest level of action: take a certain amount of chemical from a slot and 
        dispense it to the target slot.
        
        Parameters
        ----------
        source : tuple(int, str)
            The location_index tuple consisting of the plate index and well index of the source. 
            e.g. (9, "A3") means the A3 slot in plate 9.
        target : tuple(int, str)
            The location_index tuple of the target. See `source`.
        volume : float
            The amount in uL to be dispsensed.
        """
        m, i = source
        n, j = target
        if verbose:
            print(f"Dispensing {volume:.1f} uL from {source} to {target}")
        self.aspirate(volume, self.lot[m][i])
        self.dispense(volume, self.lot[n][j])


    def generate_dispensing_queue(self, m, n, verbose=False):
        """ Given the target formulations and chemical sources. Create a queue of aspiration/dispensing actions
        for individual source and target. For instance, for the following chemcials and formulations,        
            formulations = {
                "B3": {"Chemical1": 20, "Chemical2": 10},
                "B4": {"Chemical1": 10, "Chemical2": 20}
            }
            chemicals = {
                "A3": ["Chemical1", 5000],
                "A4": ["Chemical2", 5000]
            }
        It will generate a queue like below:
            dispensing_queue = [
                [(2, "A3"), (6, "B3"), 20],
                [(2, "A3"), (6, "B4"), 10],
                [(2, "A4"), (6, "B3"), 10],
                [(2, "A4"), (6, "B4"), 20],
            ]

        Parameters
        ----------
        formulations : dict
        chemicls : dict
        n : int
        m: int
        """
        self.dispensing_queue = []
        formulations = self.config["Formulations"]
        chemicals = self.config["Chemicals"]

        for c_slot, (name, total_volume) in chemicals.items():
            total_amount = 0
            for f_slot, formulation in formulations.items():
                try:
                    amount = formulation[name] # only if chemical exists in formulation
                    total_amount += amount # if chemcial exits in formulation, add to total_amount
                except:
                    continue
                source = (m, c_slot)
                target = (n, f_slot)
                self.dispensing_queue.append([source, target, amount])
            if total_amount >= total_volume:
                raise ValueError(
                    f"Need more {name}. Expected: {total_amount:.2f}. Current: {total_volume:.2f}"
                )
        if verbose:
            for l in self.dispensing_queue:
                print(l)




    # def mix(self, mixing_tip, well_shift):
    #     self.pip_arm.pick_up_tip(self.tiprack1[mixing_tip])
    #     if well_shift < 8:
    #         self.pip_arm.mix(3, 1000, location_index = self.lot[9].wells()[well_shift].bottom(5))
    #     else:
    #         self.pip_arm.mix(3, 1000, location_index = self.lot[9].wells()[well_shift-8].bottom(5))
    #     self.pip_arm.return_tip()
    

    
    def move1(self):
        self.sleep(3)
        self.pip_arm.move_to(self.lot[9]["B1"].top(20))
        self.pip_arm.pick_up_tip(self.tiprack1["A1"])

        # fake dispensing
        self.pip_arm.move_to(self.lot[9]["B1"].top(10))
        self.pip_arm.move_to(self.lot[9]["B1"].top(60))
        self.pip_arm.move_to(self.lot[9]["B1"].top(-10))
        self.pip_arm.drop_tip(self.tiprack1["A1"])
        self.pip_arm.move_to(self.tiprack1["A1"].top(60)) # move higher not to block

        # pickup voltage meter
        self.pip_arm.pick_up_tip(self.tiprack2["A2"])
        self.pip_arm.move_to(self.lot[9]["B1"].top(10))
        self.pip_arm.move_to(self.lot[9]["B1"].top(-20))
        

    def move2(self):

        self.sleep(1)
        self.pip_arm.move_to(self.tiprack2["A1"].top(30))
        self.pip_arm.drop_tip(self.tiprack2["B4"]) # drop voltage meter
        
        self.sleep(1)
        self.cond_arm.move_to(self.lot[9]["B1"].top(10)) 
        self.cond_arm.move_to(self.lot[9]["B1"].top(-20))
        self.cond_arm.move_to(self.lot[9]["B1"].top(60))
    
    def measure_conductivity(self, cond_meter:ConductivityMeter, lot_index:int):
        formulations = self.config["Formulations"]
        plate = self.lot[lot_index]
        for slot in formulations:
            self.cond_arm.move_to(plate[slot].top(20)) 
            self.cond_arm.move_to(plate[slot].bottom(10))
            self.sleep(1)
            cond_meter.read_cond(slot, name=formulations[slot]["name"], append=True)
            self.cond_arm.move_to(plate[slot].top(20))

            print(f"Conductivity measured: {slot}!")

if __name__ == "__main__":
    ot2 = OT2(protocol_api.ProtocolContext())