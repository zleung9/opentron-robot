import sys
import json
sys.path.append("./")
from robots import Robot
from sockets import SocketServer
from opentrons import protocol_api


class OT2(Robot):
    def __init__(self, protocol: protocol_api.ProtocolContext):
        super().__init__()
        self.server = None # by default the server is down
        self.client = None 
        if type(protocol) is protocol_api.ProtocolContext:
            self.protocol = protocol
            self.load_tiprack()
            self.load_pipette()
            self.load_plate()


    def start_server(self, host="169.254.230.44", port=23):
        self.server = SocketServer(host=host, port=port)


    def send_message(self, message=None):
        message = self.server.client_start("Start SquidStat")
        return message

    def load_plate(self):
        with open('/data/user_storage/automat_2x4wellplate_20ml.json') as labware_file:
            targetplated = json.load(labware_file)
        self.plate = self.protocol.load_labware_from_definition(targetplated, 9)

    def load_tiprack(self):
        self.tiprack1 = self.protocol.load_labware('opentrons_96_tiprack_1000ul', 1)
        self.tiprack2 = self.protocol.load_labware('opentrons_96_tiprack_1000ul', 11)


    def load_pipette(self):
        self.lpip = self.protocol.load_instrument(
            'p300_single_gen2',
            mount='left'
        )
        self.rpip = self.protocol.load_instrument(
            'p1000_single_gen2', 
            mount='right', 
            tip_racks=[self.tiprack1]
        )

    def movearound(self) -> None:
        """For demo only.
        """
        print("Moving things around...")
    
    def demo(self) -> None: ...


    def sleep(self, t):
        self.protocol.delay(t)


    def aspirate(self, microLiter, source):
        self.rpip.aspirate(microLiter, source)
        self.sleep(2)
        self.rpip.touch_tip(v_offset=-3)
    
    
    def dispense_action(self, microLiter, myIdx, amounts, counter, well_shift):
        self.rpip.dispense(microLiter, self.plate.wells()[myIdx]).blow_out()
        print(1000*counter, "out of", amounts[myIdx-well_shift], "uL dispensed into", self.plate.wells()[myIdx])
        self.sleep(2)


    def mix(self, mixing_tip, well_shift):
        self.rpip.pick_up_tip(self.tiprack1[mixing_tip])
        if well_shift < 8:
            self.rpip.mix(3, 1000, location = self.plate.wells()[well_shift].bottom(5))
        else:
            self.rpip.mix(3, 1000, location = self.plate.wells()[well_shift-8].bottom(5))
        self.rpip.return_tip()
    
    def move1(self):

        self.sleep(3)
        self.rpip.move_to(self.plate["B1"].top(20))
        self.rpip.pick_up_tip(self.tiprack1["A1"])

        # fake dispensing
        self.rpip.move_to(self.plate["B1"].top(10))
        self.rpip.move_to(self.plate["B1"].top(60))
        self.rpip.move_to(self.plate["B1"].top(-10))
        self.rpip.drop_tip(self.tiprack1["A1"])

        # pickup voltage meter
        self.rpip.pick_up_tip(self.tiprack2["A2"])
        self.rpip.move_to(self.plate["B1"].top(10))
        self.rpip.move_to(self.plate["B1"].top(-20))
        

    def move2(self):

        self.sleep(3)
        self.rpip.pick_up_tip(self.tiprack2["A1"].top(50)) # fake pick up
        self.rpip.move_to(self.tiprack2["A1"].top(30))
        self.rpip.drop_tip(self.tiprack2["B4"]) # drop voltage meter
        self.sleep(2)

        self.sleep(2)
        self.lpip.move_to(self.plate["B1"].top(10)) 
        self.lpip.move_to(self.plate["B1"].top(-20))
        self.lpip.move_to(self.plate["B1"].top(60))

if __name__ == "__main__":
    ot2 = OT2(protocol_api.ProtocolContext())