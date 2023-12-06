from auto.utils.socket_connect import SocketServer
from auto.robots.robot import Robot
from opentrons import protocol_api


class OT2(Robot):
    def __init__(self, protocol: protocol_api.ProtocolContext):
        super().__init__()
        self.protocol = protocol
        self.server = None # by default the server is down
        self.client = None 
        self.load_tiprack()
        self.load_pipette()
        self.load_plate()


    def start_server(self, host="169.254.230.44", port=23):
        self.server = SocketServer(host=host, port=port)


    def send_message(self, message=None):
        self.server.client_start("Start SquidStat")


    def load_tiprack(self):
        self.tiprack = None

    def movearound(self) -> None:
        """For demo only.
        """
        print("Moving things around and making solutions...")
    
    def demo(self) -> None: ...

    def load_pipette(self):
        self.lpip = None
        self.rpip = None


    def sleep(self, t):
        self.protocol.delay(t)


    def load_plate(self):
        self.plate = None


    def aspirate(self, microLiter, source):
        self.rpip.aspirate(microLiter, source)
        self.protocol.delay(2)
        self.rpip.touch_tip(v_offset=-3)
    
    
    def dispense_action(self, microLiter, myIdx, amounts, counter, well_shift):
        self.rpip.dispense(microLiter, self.plate.wells()[myIdx]).blow_out()
        print(1000*counter, "out of", amounts[myIdx-well_shift], "uL dispensed into", self.plate.wells()[myIdx])
        self.protocol.delay(2)


    def mix(self, mixing_tip, well_shift):
        self.rpip.pick_up_tip(self.tiprack[mixing_tip])
        if well_shift < 8:
            self.rpip.mix(3, 1000, location = self.plate.wells()[well_shift].bottom(5))
        else:
            self.rpip.mix(3, 1000, location = self.plate.wells()[well_shift-8].bottom(5))
        self.rpip.return_tip()