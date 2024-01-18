import sys
import json
from itertools import product
import pandas as pd
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
        self._source_locations = []
        self._target_locations = []
        self._dispensing_queue = []
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
        
        # Create a list of all possible target locations
        self._source_locations = list(product( # [(2, "A3"), (2, "A4"), (6, "B3"), (6, "B4"), etc.]
            self.config["Robots"]["OT2"]["chemical_wells"], 
            ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]
        ))

        # Create a list of all possible target locations
        self._target_locations = list(product( # [(2, "A3"), (2, "A4"), (6, "B3"), (6, "B4"), etc.]
            self.config["Robots"]["OT2"]["formula_wells"], 
            ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]
        ))

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


    def generate_dispensing_queue(
        self, 
        formula_input_path:str=None, 
        volume_limit:float=5000,
        verbose:bool=False
    ):
        """
        Given the target formulations and chemical sources, create a queue of aspiration/dispensing actions
        for individual source and target. The generated queue is stored in `self._dispensing_queue`, where each entry contains the source location, target location, and amount.
        There are at maximum 16 source locations and 16 target locations. The total number of entries in the queue is 16*16=256.

        Parameters
        ----------
        formula_input_path : str, optional
            The path to the csv file containing the formulations.
        volume_limit : float, optional
            The maximum volume of the source chemical. If the total volume of the source chemical exceeds
            the limit, an error is raised. The default is 5000 uL.
        verbose : bool, optional
            If True, print the queue. The default is False.

        Raises
        ------
        ValueError
            If the total amount of any chemical exceeds the volume limit.

        Examples
        --------
        >>> generate_dispensing_queue(formula_input_path='formulations.csv', volume_limit=5000, verbose=True)
        [(4, 'A1'), (2, 'A1'), 2]
        [(4, 'A1'), (2, 'A2'), 2]
        [(4, 'A1'), (2, 'A3'), 2]
        [(4, 'A1'), (2, 'A4'), 2]
        [(4, 'A1'), (2, 'B1'), 2]
        [(4, 'A2'), (2, 'A1'), 3]
        [(4, 'A2'), (2, 'A2'), 3]
        [(4, 'A2'), (2, 'A3'), 3]
        ...

        """
        # Rest of the code remains the same
        ...

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

        for slot in ["A1", "A2", "A3", "A4"]:
            for _ in range(3):
                self.cond_arm.move_to(plate[slot].top())
                self.cond_arm.move_to(plate[slot].bottom(10))
                self.cond_arm.move_to(plate[slot].bottom(5))
        
        print("Conductivity meter arm rinsed.")
        


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
        self.replace_plate_for_conductivity(lot_index, put_back=True)

if __name__ == "__main__":
    ot2 = OT2(protocol_api.ProtocolContext())