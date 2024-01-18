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

    def load_labware(self, definition:str, n:int):
        """Load labware from a json file.
        Parameters
        ----------
        definition : str
            The path to the json file.
        n : int
            The slot number to load the labware.
        
        Returns
        -------
        labware : opentrons.labware.Labware
            The labware object.
        """
        if definition.endswith(".json"):
            with open(definition, "r") as f:
                labware = self.protocol.load_labware_from_definition(json.load(f), n)
        else:
            labware = self.protocol.load_labware(definition, n)
        return labware

    def load_config(self, config) -> None:
        """ Park labwares into slots and mount pipettes onto arms.
        """
        # Park labwares
        self.config = config
        config = config["Robots"]["OT2"] # only take the configuration for OT2 robotics
        for key, value in config["labwares"].items():
            n = int(key)
            self.lot[n] = self.load_labware(value, n)
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

    def replace_plate_for_conductivity(self, lot_index, put_back=False):
        """ Replace the plate for conductivity measurement. The reason to do so is that there is an 
        offset between the pipette tip and the conductivity meter. The offset is about 10 mm.
        Parameters
        ----------
        lot_index : int
            The index of the plate to be replaced.
        put_back : bool
            If True, replace the plate back to the original slot.
        """
        del self.protocol.deck[str(lot_index)]

        if put_back:
            new_def = self.config["Robots"]["OT2"]["labwares"][str(lot_index)]
        else:
            new_def = self.config["Robots"]["Conductivity Meter"]["labwares"][str(lot_index)]

        self.lot[lot_index] = self.load_labware(new_def, lot_index)
        print(f"Plate {lot_index} changed to {new_def}!")

    def rinse_cond_arm(self, lot_index:int):
        """ Rinse the conductivity meter arm. After measuring conductivity for one solution, the
        conductivity meter arm will move to the plate with four water wells. The conductivity meter
        arm will rinse itself in the four wells. In each well, the arm will move up and down for 3
        times.
        """
        plate = self.lot[lot_index]  # Assuming lot_index is defined elsewhere
        self.protocol.max_speeds['x'] = 100
        for slot in ["A1", "A2", "A3", "A4"]:
            self.cond_arm.move_to(plate[slot].top(100))
            self.protocol.delay(2)
            for _ in range(3):
                self.cond_arm.move_to(plate[slot].bottom(48.4))
                self.cond_arm.move_to(plate[slot].bottom(75))
            self.protocol.delay(3)
                
        print("Conductivity meter arm rinsed.")

    def dry_cond_arm(self, lot_index:int):
        """ Dry the conductivity meter arm. After rinsing itself in the four solvent wells, the arm will move to the sponge
        deck position. It will then trigger the blow dryer and move slowly up and down to dry the probe evenly.
        """
        plate = self.lot[lot_index]  # Assuming lot_index is defined elsewhere
        slot = ['A4']
        self.left_pipette.move_to(plate[slot].top(55.5))
        self.left_pipette.move_to([plate][slot].top(15.5))
        self.left_pipette.move_to(plate[slot].top(93))
        os.system("python /data/user_storage/dry.py")
        self.protocol.max_speeds['z'] = 14
        self.protocol.delay(3.5)
        self.left_pipette.move_to(plate[slot].top(102))
        self.left_pipette.move_to(plate[slot].top(74))
        self.left_pipette.move_to(plate[slot].top(93))
        self.protocol.delay(3)
        del self.protocol.max_speeds['z']
        del self.protocol.max_speeds['x']
        self.left_pipette.move_to(plate[slot].top(15.5))
        self.protocol.delay(1)


    def measure_conductivity(self, cond_meter:ConductivityMeter, lot_index:int):
        """ Measure conductivity of the plate.
        Parameters
        ----------
        cond_meter : ConductivityMeter
            The conductivity meter object.
        lot_index : int
            The index of the plate to be measured.
        """
        self.replace_plate_for_conductivity(lot_index)
        formulations = self.config["Formulations"]
        plate = self.lot[lot_index]
        for slot in formulations:
            self.cond_arm.move_to(plate[slot].top(50))
            self.cond_arm.move_to(plate[slot].bottom(20))
            self.sleep(1)
            cond_meter.read_cond(slot, name=formulations[slot]["name"], append=True)
            self.cond_arm.move_to(plate[slot].top(50))
            print(f"Conductivity measured: {slot}!")
            self.rinse_cond_arm(lot_index)
            self.dry_cond_arm(lot_index)
            
        self.replace_plate_for_conductivity(lot_index, put_back=True)

if __name__ == "__main__":
    ot2 = OT2(protocol_api.ProtocolContext())