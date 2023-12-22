import sys
import json
sys.path.append("./")
from robots import Robot, ConductivityMeter
from sockets import SocketServer
from opentrons import protocol_api


class OT2(Robot):
    def __init__(self, protocol:protocol_api.ProtocolContext, config_file):
        super().__init__()
        self.server = None # by default the server is down
        self.client = None
        with open(config_file, "r") as f:
            self.config = json.load(f)
        if type(protocol) is protocol_api.ProtocolContext:
            self.load_config(protocol)
            self.protocol = protocol


    def load_config(self, protocol:protocol_api.ProtocolContext) -> None:
        """ Park instruments into slots.
        """
        self.lot = {i:None for i in range(1, 12)} # initiate plate 1 to 11
        for key, value in self.config["labwares"]:
            n = int(key)
            if value.endswith(".json"):
                with open(value, "r") as f:
                    definition = json.load(f)
                self.lot[n] = protocol.load_labware_from_definition(definition, n)
            else:
                self.lot[n] = protocol.load_labware(value, n)

        self.tiprack1 = self.lot[1]
        self.tiprack11 = self.lot[11]

        
        self.pip = {}
        for key, value in self.config["pipettes"]:
            self.pip[key] = protocol.load_instrument(value, key)
        self.lpip = self.pip["left"]
        self.rpip = self.pip["right"]

        with open('/data/user_storage/automat_2x4wellplate_20ml.json') as labware_file:
            targetplated = json.load(labware_file)
        with open('/data/user_storage/automat_2x4wellplate_50ml.json') as labware_file:
            wellplate50ml_steel = json.load(labware_file)

        self.lot[1] = protocol.load_labware('opentrons_96_tiprack_1000ul', 1)
        self.lot[5] = protocol.load_labware_from_definition(wellplate50ml_steel, 5)
        self.lot[8] = protocol.load_labware_from_definition(wellplate50ml_steel, 8)
        self.lot[9] = protocol.load_labware_from_definition(targetplated, 9)
        self.lot[11] = protocol.load_labware('opentrons_96_tiprack_1000ul', 11)

        self.tiprack1 = self.lot[1]
        self.tiprack11 = self.lot[11]

        self.lpip = protocol.load_instrument('p300_single_gen2', mount='left')
        self.rpip = protocol.load_instrument('p1000_single_gen2', mount='right',
            tip_racks=[self.tiprack1]
        )
    

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


    def aspirate(self, microLiter, source):
        self.rpip.aspirate(microLiter, source)
        self.sleep(1)
        self.rpip.touch_tip(v_offset=-3)
    
    
    def dispense(self, microLiter, target):
        self.rpip.dispense(microLiter, target).blow_out()
        self.sleep(1)

    def dispense_chemical(
            self, 
            amount:float=0, 
            source:tuple(int, str)=(None,None),  
            target:tuple(int, str)=(None,None),
            left:bool=True 
        )-> None:
        """ Second lowest level of action: take a certain amount of chemical from a slot and 
        dispense it to the target slot.
        
        Parameters
        ----------
        amount : float
            The amount in uL to be dispsensed.
        source : tuple(int, str)
            The location tuple of the source. e.g. (9, "A3") means the A3 slot in plate 9.
        target : tuple(int, str)
            The location tuple of the target. See `source`.
        left : bool
            If `True`, left pipette is used, otherwise right pipette is used.
        """
        pip = self.lpip if left else self.rpip
        m, i = source
        n, j = target
        pip.move_to(self.lot[m][i].top(10))
        





    # def mix(self, mixing_tip, well_shift):
    #     self.rpip.pick_up_tip(self.tiprack1[mixing_tip])
    #     if well_shift < 8:
    #         self.rpip.mix(3, 1000, location = self.lot[9].wells()[well_shift].bottom(5))
    #     else:
    #         self.rpip.mix(3, 1000, location = self.lot[9].wells()[well_shift-8].bottom(5))
    #     self.rpip.return_tip()
    

    
    def move1(self):
        self.sleep(3)
        self.rpip.move_to(self.lot[9]["B1"].top(20))
        self.rpip.pick_up_tip(self.tiprack1["A1"])

        # fake dispensing
        self.rpip.move_to(self.lot[9]["B1"].top(10))
        self.rpip.move_to(self.lot[9]["B1"].top(60))
        self.rpip.move_to(self.lot[9]["B1"].top(-10))
        self.rpip.drop_tip(self.tiprack1["A1"])
        self.rpip.move_to(self.tiprack1["A1"].top(60)) # move higher not to block

        # pickup voltage meter
        self.rpip.pick_up_tip(self.tiprack2["A2"])
        self.rpip.move_to(self.lot[9]["B1"].top(10))
        self.rpip.move_to(self.lot[9]["B1"].top(-20))
        

    def move2(self):

        self.sleep(1)
        self.rpip.move_to(self.tiprack2["A1"].top(30))
        self.rpip.drop_tip(self.tiprack2["B4"]) # drop voltage meter
        
        self.sleep(1)
        self.lpip.move_to(self.lot[9]["B1"].top(10)) 
        self.lpip.move_to(self.lot[9]["B1"].top(-20))
        self.lpip.move_to(self.lot[9]["B1"].top(60))
    
    def measure_conductivity(self, plate, cond_meter:ConductivityMeter):
        for slot in ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]:
            self.lpip.move_to(plate[slot].top(10)) 
            self.lpip.move_to(plate[slot].top(-20))
            self.lpip.move_to(plate[slot].top(60))
            self.sleep(1)
            cond_meter.read_cond(slot, append=True)
            self.lpip.move_to(plate[slot].top(60))

            print(f"Conductivity measured: {slot}!")

if __name__ == "__main__":
    ot2 = OT2(protocol_api.ProtocolContext())