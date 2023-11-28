# SDWF Movement System


# ----------------------------------------------------------------------

# In[ ]:
import json
import pandas as pd
import opentrons.execute
from opentrons import protocol_api


#OT-2
metadata={"apiLevel": "2.11"}

# labware
with open('/data/user_storage/nic8vial.json') as labware_file:
    SDWFVoltageProbe = json.load(labware_file)



def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(True)
    protocol.comment('light is on')
    pickup_rack = protocol.load_labware_from_definition(SDWFVoltageProbe, 11)
    tiprack = protocol.load_labware_from_definition(SDWFVoltageProbe, 1)
    plate = protocol.load_labware_from_definition(SDWFVoltageProbe, 9)
    home_position = protocol.load_labware_from_definition(SDWFVoltageProbe, 2)
    
    right_pipette = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tiprack])
    
    # right_pipette.well_bottom_clearance.aspirate = 3
    # right_pipette.well_bottom_clearance.dispense = 45
    

    
    # Pickup
    
    def pickup_probe(loc):
        test_offset = 0
        right_pipette.pick_up_tip(pickup_rack.wells()[0].bottom(0))
        right_pipette.move_to(tiprack[loc].bottom(80))
        protocol.delay(2)
        right_pipette.move_to(tiprack[loc].bottom(test_offset), speed=10)
        protocol.delay(2)
        right_pipette.move_to(tiprack[loc].bottom(80))
        protocol.delay(2)


    def cond_measurement(loc):
        right_pipette.move_to(plate[loc].bottom(100))
        right_pipette.move_to(plate[loc].bottom(14), speed=100)
        protocol.delay(6)
        protocol.comment('Measuring conductivity...')
        protocol.delay(2)
        right_pipette.move_to(plate[loc].bottom(100))
    
    def dispense():
        # right_pipette.drop_tip(protocol.fixed_trash['A1'].bottom(60))
        right_pipette.move_to(tiprack['A1'].bottom(100))
        right_pipette.move_to(tiprack['A1'].bottom(12))
        right_pipette.drop_tip(tiprack['A1'].bottom(10))
        
    
    def main():
        pickup_probe('A1')
        cond_measurement('A1')
        dispense()


    
    main()
    right_pipette.move_to(tiprack['A1'].bottom(100))
    right_pipette.move_to(home_position['A1'].bottom(100))
    protocol.home()
    protocol.comment('Conductivity measurement completed.')