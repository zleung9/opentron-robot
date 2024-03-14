import sys
import os
import json
from itertools import product
import pandas as pd
import numpy as np
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
    from opentrons import protocol_api, types
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
        self._has_tip = False # Initiate the tip status: whether the pipette has picked a tip.
        self._formulation_input_path = "" # The path to the csv file containing the formulations
        self.formulations = None # Initiate formulations
        self._source_locations = [] # locations where the source chemical is stored
        self._source_locations_viscous = [] # locations where the source chemical is viscous
        self._target_locations = [] # locations where the target chemical is stored
        self._target_locations_dispensed = []
        self._last_source = None # the last source location
        self.dispensing_queue = [] # the queue of dispensing actions
        self.cover_deck_status = [0, 0] # initialize the tower stack status (empty)
        self.cover_deck_plate_index = None # the index of the cover deck plate
        self.cover_thickness = None # the thickness of the cover
        self.cover_offset = None # the offset of the cover deck w.r.t. top left vial
        self.cover_deck_0 = None # the left side of the cover deck plate
        self.cover_deck_1 = None # the right side of the cover deck plate
        self.config = {} # the configuration of the OT2
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
                config = json.load(f)
                labware = self.protocol.load_labware_from_definition(config, n)
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
        config = config["Robots"]["OT2"] # only take the configuration for OT2 robotics

        # Park labwares
        for key, value in config["labwares"].items():
            n = int(key)
            self.lot[n] = self.load_labware(value, n)
            if "tiprack" in value:
                self.tiprack = self.lot[n]

        # load the cover deck plate and related locations
        self.cover_deck_plate_index = config["cover_deck"][0] # plate number for cover deck
        self.cover_deck_0 = self.lot[self.cover_deck_plate_index]["A1"]
        self.cover_deck_1 = self.lot[self.cover_deck_plate_index]["A2"]
        source_plate_config_json = config["labwares"][str(config["chemical_wells"][0])]
        with open(source_plate_config_json, "r") as f:
            _config = json.load(f)
            locations = np.array([
                [_config["wells"][well]["x"], _config["wells"][well]["y"]]
                for well in ["A1", "A2", "B1", "B2"]
            ])
            center = locations.mean(axis=0) # center of the left blocks
            offset = center - locations[0] # offset of the center of left block w.r.t. A1
        # load the cover thickness
        with open(config["labwares"][str(self.cover_deck_plate_index)], "r") as f:
            _config = json.load(f)
            self.cover_thickness = _config["wells"]["A1"]["depth"]
        
        # x, y, z offset of the cover deck
        self.cover_offset = types.Point(x=offset[0], y=offset[1], z=self.cover_thickness)
        # Create a list of all possible source locations
        self._source_locations = list(product( # [(2, "A3"), (2, "A4"), (6, "B3"), (6, "B4"), etc.]
            config["chemical_wells"], 
            ["A1", "A2", "B1", "B2", "A3", "A4", "B3", "B4"]
        ))
        self._source_locations_viscous = [tuple(v) for v in config["viscous"]] # viscous sources

        # Create a list of all possible target locations
        self._target_locations = list(product( # [(2, "A3"), (2, "A4"), (6, "B3"), (6, "B4"), etc.]
            config["formula_wells"], 
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
                # Get the normal speed_rate of the pipette. The actual rate will be multiplied by the speed_factor.
                self._aspirate_rate = self.pip_arm.flow_rate.aspirate
                self._dispense_rate = self.pip_arm.flow_rate.dispense
                self._blow_out_rate = self.pip_arm.flow_rate.blow_out

    
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

    def pick_up_tip(self, location=None) -> None:
        """Pick up a tip from the tiprack.
        """
        assert not self._has_tip, "The pipette already has a tip."
        self.pip_arm.pick_up_tip(location)
        self._has_tip = True
    
    def drop_tip(self, location=None) -> None:
        """Drop the tip to the waste.
        """
        assert self._has_tip, "No tip to drop."
        self.pip_arm.drop_tip(location)
        self._has_tip = False

    def aspirate(self, volume, location, speed_factor=1, z=5):
        """ Pippete will aspirate at `z`mm above the bottom of the well. 
        """
        self.pip_arm.flow_rate.aspirate = self._aspirate_rate * speed_factor # change the speed of the pipette
        self.pip_arm.aspirate(volume, location.bottom(z=z))
        self.sleep(1.0)
        self.pip_arm.touch_tip(v_offset=-7)
        if speed_factor < 1:
            self.sleep(2.0)
        self.sleep(3.0)

    
    
    def dispense(self, volume, location, speed_factor=1, z=-5):
        """ Pippete will dispense at `z`mm below the top of the well and push out extra 10 uL. 
        """
        self.pip_arm.flow_rate.dispense = self._dispense_rate * speed_factor # change the speed of the pipette
        self.pip_arm.dispense(volume, location.top(z=z))
        self.pip_arm.flow_rate.blow_out = self._blow_out_rate / speed_factor
        self.sleep(2.0)
        self.pip_arm.blow_out()
        self.sleep(1.0)


    def dispense_chemical(
            self, 
            source:tuple=(None,None),  
            target:tuple=(None,None),
            volume:float=0,
            speed_factor:float=1,
            verbose:bool=False
        )-> None:
        """ Second lowest level of action: take a certain amount of chemical from a slot and  dispense it to the target slot. At the end of the queue will always be a dummy action that has a `None` source. This action will be used to drop the tip and finish the dispensing.
        
        Parameters
        ----------
        source : tuple(int, str)
            The location_index tuple consisting of the plate index and well index of the source. 
            e.g. (9, "A3") means the A3 slot in plate 9.
        target : tuple(int, str)
            The location_index tuple of the target. See `source`.
        volume : float
            The amount in uL to be dispsensed.
        speed_factor : float
            The speed factor of the pipette. If the source is viscous, the speed factor will be smaller than 1.
        """
        m, i = source
        n, j = target
        
        # Tip handling at the beginning/end and between chemical dispensing.
        if source == self._last_source: # If the source is the same as the last source, no need to change tip.
            assert self._has_tip, "The pipette does not have a tip." 
        else: # If the source is different from the last source, change tip.
            if self._has_tip: # If the pipette has a tip, drop it.
                self.drop_tip()
            if m is not None: # do not pick up a tip at the end of the dispensing
                self.pick_up_tip()
            else:
                return

        if verbose:
            print(f"Dispensing {volume:.1f} uL from {source} to {target} with speed factor {speed_factor}.")
        
        # slow down the z-axis speed for viscous chemicals
        if speed_factor < 1:
            self.protocol.max_speeds['a'] = 60
        self.aspirate(volume, self.lot[m][i], speed_factor=speed_factor)
        self.dispense(volume, self.lot[n][j], speed_factor=speed_factor)
        # reset the max z-axis speed
        try: 
            del self.protocol.max_speeds['a']
        except KeyError:
            pass
        # Update the last source as a reference for the next dispensing action
        self._last_source = source


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
        chemical_names = [s for s in df.columns if "Chemical" in s]
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
        for individual source and target. The generated queue is stored in dictionary `self.dispensing_queue`. 
        The keys are block names and the values are blocks of continuous dispensing actions.
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

        Notes
        -----
        The queue is actually a dictionary of lists. Keys are the name of blocks. Each inner list is a continuous queue meaning no interruption is triggered. Between each inner list, a `move_cover` action is performed to cover the executed source vials.Each inner list contains the source location, target location, and amount.
            
        Examples
        --------
        The 'experiment.csv' contains 8 columns (8 chemicals) and 1 row (one solution). The source plate is 4 (A1 throught B4) and the target plate is 2 (A1 only). The following command will generate a dictionary of two fields: "4A" and "4B". Each field contains a list of lists. Each inner list contains the source location, target location, and amount. "4A" and "4B" are the left and right block of plate 4.
        >>> generate_dispensing_queue(formula_input_path='experiment.csv', volume_limit=5000, verbose=True)
        {
            [
                [(4, 'A1'), (2, 'A1'), 2, 1],
                [(4, 'A2'), (2, 'A1'), 2, 1],
                [(4, 'B1'), (2, 'A1'), 2, 1],
                [(4, 'B2'), (2, 'A1'), 2, 1]
            ],
            [
                [(4, 'A3'), (2, 'A1'), 2, 1],
                [(4, 'A4'), (2, 'A1'), 3, 1],
                [(4, 'B3'), (2, 'A1'), 3, 1],
                [(4, 'B4'), (2, 'A1'), 3, 1]
            ]
        }
        ...

        """
        _dispensing_queue = []
        _cont_dispensing_queue = [] # The dispensing queue for each chemical
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
            if source in self._source_locations_viscous:
                speed_factor = 0.5 # slow down the pipette speed for viscous chemicals
            else:
                speed_factor = 1
            # Generate the dispensing queue for each chemical
            for j, volume in volume_all.items():
                target = self._target_locations[j] # The target location of the chemical
                if volume == 0: continue # skip empty volume
                _cont_dispensing_queue.append([source, target, volume, speed_factor])
            if not ((i+1) % 4):  # add to the queue every 4 chemicals
                if _cont_dispensing_queue:
                    _dispensing_queue.append(_cont_dispensing_queue)
                _cont_dispensing_queue = []  # reset the queue
        
        # Append a last void sub-queue to the queue to indicate the end of the dispensing
        _dispensing_queue.append([[(None, None), (None, None), 0, 1]]) 
        # Update the target locations that will have been dispensed
        self._target_locations_dispensed = self._target_locations[: len(self.formulations)]
        self.dispensing_queue = _dispensing_queue

        if verbose:
            for sub_queue in self.dispensing_queue:
                print("\n")
                for queue in sub_queue:
                    print(queue)

    def _block_to_location(self, block, status=None):
        """Get the average location of the block.
        Parameters
        ----------
        block : tuple(int, int)
            The block name. The definition is (plate_index, 0 or 1), where 0 and 1 are the left and right block of the plate.
        status : list[int, int], optional
            The status of the cover deck. The default is None.
        
        Returns
        -------
        loc : opentrons.types.Location
            The location of the block.
        """
        n, side = block
        # If it involves the cover deck, update the status and adjust the height where the pipette moves to.
        if status:
            if side == 0:
                loc = self.cover_deck_0.top().move(types.Point(x=0, y=0, z=status[0]*self.cover_thickness))
            elif side == 1:
                loc = self.cover_deck_1.top().move(types.Point(x=0, y=0, z=status[1]*self.cover_thickness))
            else:
                raise ValueError("The block name is not valid.")
        else:
            if side == 0:
                loc = self.lot[n]["A1"].top().move(self.cover_offset)
            elif side == 1:
                loc = self.lot[n]["A3"].top().move(self.cover_offset)
            else:
                raise ValueError("The block name is not valid.")
        
        return loc


    def move_cover(self, from_block, to_block, verbose=False):
        """Move the pipette to cover the source vials.
        Parameters
        ----------
        from_block : tuple(int, int)
            The source block name. The definition is (plate_index, 0 or 1), where 0 and 1 are the left and right block of the plate.
        to_block : tuple(int, int)
            The target block name. The definition is the same as `from_block`.
        verbose : bool, optional
            If True, print the movement. The default is False.
        """
        if self._has_tip: # make sure the tip is dropped before moving the cover
            self.drop_tip()

        status = self.cover_deck_status # get the status of the cover deck
        
        # always pick cover from higher side and put cover to lower side
        assert from_block != to_block, "The source and target blocks are the same."
        
        # translate the blocks to locations
        if from_block == "deck":
            from_block = (self.cover_deck_plate_index, np.argmax(status)) 
            from_location = self._block_to_location(from_block, status=status)
            status[from_block[1]] -= 1 
        else:
            from_location = self._block_to_location(from_block)
        if to_block == "deck":
            to_block = (self.cover_deck_plate_index, np.argmin(status))
            to_location = self._block_to_location(to_block, status=status)
            status[to_block[1]] += 1   
        else:
            to_location = self._block_to_location(to_block)
        assert min(status) >= 0, "Cover deck is empty."

        # move the cover around
        self.pip_arm.move_to(from_location)
        ot2.pip_arm.pick_up_tip(from_location)
        self.pip_arm.move_to(to_location)
        ot2.pip_arm.drop_tip(to_location)
        if verbose:
            print(f"Cover from {from_block} to {to_block} moved. Deck status: {status}")
        
        self.cover_deck_status = status # update the status of the cover deck


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
        self.protocol.max_speeds['z'] = None
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
            self.cond_arm.move_to(self.adjust(well.bottom(49)))
            self.sleep(1)
            cond_meter.read_cond(uid=row["unique_id"], append=True)
            self.cond_arm.move_to(self.adjust(well.top(50)))
            print(f"Conductivity measured: {(n, i)}!")
            self.rinse_cond_arm() # Rinse the arm
            self.dry_cond_arm() # Dry the arm
        
    
if __name__ == "__main__":
    ot2 = OT2(protocol_api.ProtocolContext())