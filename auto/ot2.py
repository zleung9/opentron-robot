import sys
import os
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

try:
    from pump_raspi import raspi_comm
except:
    from auto.pump_raspi import raspi_comm


class OT2(Robot):
    def __init__(self, protocol:protocol_api.ProtocolContext, config=None):
        super().__init__(config=config)
        self.server = None # by default the server is down
        self.client = None
        self.protocol = protocol
        self.lot = {i:None for i in range(1, 12)} # initiate plate 1 to 11
        self.arm = {"left": None, "right": None} # Initiate left and right arm
        self.formulations = None # Initiate formulations
        self._source_locations = []
        self._target_locations = []
        self._target_locations_dispensed = []
        self.dispensing_queue = []
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
        elif not definition: # No labware is placed in that position
            return None
        else:
            labware = self.protocol.load_labware(definition, n)
        return labware


    def load_config(self, config) -> None:
        """ Park labwares into slots and mount pipettes onto arms.
        """
        
        self.config = config
        cwd = os.path.dirname(__file__)
        self._formulation_input_path = os.path.join(cwd, "experiment.csv")

        # Park labwares
        config = config["Robots"]["OT2"] # only take the configuration for OT2 robotics
        for key, value in config["labwares"].items():
            n = int(key)
            self.lot[n] = self.load_labware(value, n)
            if "tiprack" in value:
                self.tiprack = self.lot[n]
        
        # Create a list of all possible source locations
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


    def load_formulations(self, formula_input_path:str=""):
        """ Load the formulations from a csv file. 
        The formulations are stored in `self.formulations`. It contains the following columns:
        unique_id, locations, Chemical1, Chemical2, ..., Chemical16. 
        
        Parameters
        ----------
        formula_input_path : str, optional
            The path to the csv file containing the formulations.
        
        Returns
        -------
        chemical_names : list
            A list of chemical names.
        """
        df = pd.read_csv(formula_input_path).reset_index(drop=True)
        chemical_names = [s for s in df.columns if s.startswith("Chemical")]
        df["location"] = self._target_locations[: len(df)]
        self.formulations = df.loc[:, ["unique_id", "location"] + chemical_names]
        self.chemical_names = chemical_names
    

    def generate_dispensing_queue(
        self, 
        formula_input_path:str=None, 
        volume_limit:float=5000,
        verbose:bool=False
    ):
        """
        Given the target formulations and chemical sources, create a queue of aspiration/dispensing actions
        for individual source and target. The generated queue is stored in `self.dispensing_queue`, where each entry contains the source location, target location, and amount.
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
        # Read the formulations and get all the chemical names in the formulations
        if formula_input_path is None:
            formula_input_path = self._formulation_input_path
        self.load_formulations(formula_input_path)
        assert self.chemical_names is not [], "Call 'ot2.load_formulations()' first"
        # Generate the dispensing queue
        for i, name in enumerate(self.chemical_names):
            volume_all = self.formulations[name]
            # Check if the total volume of the chemical exceeds the limit
            if volume_all.sum() > volume_limit: 
                raise ValueError(f"Volume of {name} exceeds {volume_limit} uL.")
            source = self._source_locations[i] # The source location of the chemical
            # Generate the dispensing queue for each chemical
            for j, volume in volume_all.items():
                target = self._target_locations[j] # The target location of the chemical
                self.dispensing_queue.append([source, target, volume])
                if verbose:
                    print([name, source, target, volume])

        # Update the target locations that will have been dispensed
        self._target_locations_dispensed = self._target_locations[: len(self.formulations)]
            
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
        # delete the existing plate
        del self.protocol.deck[str(lot_index)]

        # load a new plate with offset or put back the original plate 
        definition = self.config["Robots"]["OT2"]["labwares"][str(lot_index)]
        if not put_back:
            definitioin = definition.strip(".json") + "_offset.json"
        
        self.lot[lot_index] = self.load_labware(definition, lot_index)
        print(f"Plate {lot_index} changed to {definitioin}!")


    def rinse_cond_arm(self, n:int=None):
        """ Rinse the conductivity meter arm. After measuring conductivity for one solution, the
        conductivity meter arm will move to the plate with four water wells. The conductivity meter
        arm will rinse itself in the four wells. In each well, the arm will move up and down for 3
        times.
        
        Paramters
        ---------
        n : int
            The index of the plate that contains four water wells.
        
        """
        if not n:
            n = self.config["Robots"]["OT2"]["water_wells"][0]

        self.protocol.max_speeds['x'] = 100
        for i in ["A1", "A2", "A3", "A4"]:
            well = self.lot[n][i]
            self.cond_arm.move_to(self.adjust(well.top(100)))
            self.sleep(2)
            for _ in range(3):
                self.cond_arm.move_to(self.adjust(well.bottom(48.4)))
                self.cond_arm.move_to(self.adjust(well.bottom(75)))
            self.sleep(3)
                
        print("Conductivity meter arm rinsed.")


    def dry_cond_arm(self, n:int=None):
        """ Dry the conductivity meter arm. After rinsing itself in the four solvent wells, the arm will move to the sponge deck position. It will then trigger the blow dryer and move slowly up and down to dry the probe evenly.
        
        Paramters
        ---------
        n : int
            The index of the sponge deck.
        """
        if not n:
            n = self.config["Robots"]["OT2"]["sponge_deck"][0]
        
        deck = self.lot[n]["A4"] 
        self.cond_arm.move_to(self.adjust(deck.top(55.5)))
        self.cond_arm.move_to(self.adjust(deck.top(15.5)))
        self.cond_arm.move_to(self.adjust(deck.top(93)))
        raspi_comm.trigger_pump()
        self.protocol.max_speeds['z'] = 14
        self.sleep(3.5)
        self.cond_arm.move_to(self.adjust(deck.top(102)))
        self.cond_arm.move_to(self.adjust(deck.top(74)))
        self.cond_arm.move_to(self.adjust(deck.top(93)))
        self.sleep(3)
        del self.protocol.max_speeds['z']
        self.cond_arm.move_to(self.adjust(deck.top(15.5)))
        self.sleep(1)


    def adjust(self, location):
        """ Adjust the location of the well by adding offsets.
        
        Parameters
        ----------
        location : opentrons.legacy_api.containers.placeable.Placeable
            The location of the well.
        
        Returns
        -------
        location : opentrons.legacy_api.containers.placeable.Placeable
            The adjusted location of the well.
        """
        x_off, y_off, z_off = self.config["Robots"]["Conductivity Meter"]["offset"]
        return location.move(types.Point(x=x_off, y=y_off, z=z_off))


    def measure_conductivity(self, cond_meter:ConductivityMeter):
        """ Measure conductivity of the plate. `adjust` the location of the well for the conductivity meter arm.
        Parameters
        ----------
        cond_meter : ConductivityMeter
            The conductivity meter object.
        """

        # Measure conductivity for each formulation
        for _, row in self.formulations.iterrows():
            n, i = row["location"]
            well = self.lot[n][i]
            self.cond_arm.move_to(self.adjust(well.top(50)))
            self.cond_arm.move_to(self.adjust(well.bottom(20)))
            self.sleep(1)
            cond_meter.read_cond(uid=row["unique_id"], append=True)
            self.cond_arm.move_to(self.adjust(well.top(50)))
            print(f"Conductivity measured: {(n, i)}!")
            self.rinse_cond_arm() # Rinse the arm
            self.dry_cond_arm() # Dry the arm
        
    
if __name__ == "__main__":
    ot2 = OT2(protocol_api.ProtocolContext())