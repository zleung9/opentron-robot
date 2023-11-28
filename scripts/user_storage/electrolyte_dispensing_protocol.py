#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import json
import pandas as pd
from opentrons import protocol_api

#OT-2
metadata={"apiLevel": "2.11"}


# labware
with open('/data/user_storage/automat_2x4wellplate_20ml.json') as labware_file:#'/data/user_storage/automat_2x4wellplate_20ml.json') as labware_file:
    wellplate20ml = json.load(labware_file)
with open('/data/user_storage/automat_2x5_wellplate_coin_cell.json') as labware_file:#/data/user_storage/automat_2x4wellplate_coincell.json') as labware_file:
    wellplatecoin = json.load(labware_file)

def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(True)
    protocol.comment('light is on')
    source1 = protocol.load_labware_from_definition(wellplate20ml, 3)
    tiprack = protocol.load_labware('opentrons_96_tiprack_1000ul', 1)
    plate = protocol.load_labware_from_definition(wellplatecoin, 6)
    right_pipette = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tiprack])
    

    right_pipette.well_bottom_clearance.aspirate = 8
    right_pipette.well_bottom_clearance.dispense = 10
    
    # for i in range(len(plate.rows())):
    #     right_pipette.distribute(100, source1.wells(i), [plate.rows()[i]], blow_out=True, blowout_location='source well', mix_before=(2,1000), trash=False)    
        
    right_pipette.distribute(90, source1.wells(0), [plate.rows()[0], plate.rows()[1]], blow_out=True, blowout_location='source well', mix_before=(2,1000), trash=True)
        
    protocol.comment("Bringing OT-2 home...")
    protocol.home()