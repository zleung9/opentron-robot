#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import os
import json
import csv
import pandas as pd
import pickle
import opentrons.execute
from opentrons import protocol_api

#OT-2
metadata={"apiLevel": "2.11"}

# labware
with open('/data/user_storage/automat_2x4wellplate_20ml_offset.json') as labware_file:
    targetplatec = json.load(labware_file)
# with open('/data/user_storage/automat_2x4wellplate_50ml.json') as labware_file:
#     wellplate50ml = json.load(labware_file)
with open('/data/user_storage/automat_2x4wellplate_50ml_offset.json') as labware_file:
    wellplate50ml = json.load(labware_file)
with open('/data/user_storage/sponge.json') as labware_file:
    sponge = json.load(labware_file)
# with open('/data/user_storage/automat_2x4wellplate_20ml_offset.json') as labware_file:
#     waterplate = json.load(labware_file)
with open('/data/user_storage/automat_2x4_sheetmetal_offset.json') as labware_file:
    waterplate = json.load(labware_file)

def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(True)
    protocol.comment('light is on')
    
    source1 = protocol.load_labware_from_definition(wellplate50ml, 2)
    source2 = protocol.load_labware_from_definition(wellplate50ml, 3)
    tiprack = protocol.load_labware('opentrons_96_tiprack_1000ul', 1)
    plate = protocol.load_labware_from_definition(targetplatec, 6)
    sponge = protocol.load_labware_from_definition(targetplatec, 9)
    water = protocol.load_labware_from_definition(waterplate, 5)
    left_pipette = protocol.load_instrument('p300_single_gen2', mount='left')
    
    right_pipette = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tiprack])
        
    right_pipette.well_bottom_clearance.aspirate = 3
    right_pipette.well_bottom_clearance.dispense = 45
       
    def locat_dict():
        source1 = ['A1', 'A2', 'A3', 'A4']
        source2 = ['A1', 'A2', 'A3', 'A4']
        return {'source1':source1, 'source2':source2}
    
    def cond_measurement(plate, loc):
        left_pipette.move_to(plate[loc].top(45))
        left_pipette.move_to(plate[loc].bottom(70)) #48.9
        left_pipette.move_to(plate[loc].top(10))
        left_pipette.move_to(plate[loc].bottom(70)) #48.9
        protocol.delay(30)
        protocol.comment('Measuring conductivity...')
        protocol.delay(4)
    
    def rinsing(water):
        left_pipette.move_to(water['A1'].top(60))
        left_pipette.move_to(water['A1'].bottom(48.4))
        left_pipette.move_to(water['A1'].bottom(75))
        left_pipette.move_to(water['A1'].bottom(48.4))
        protocol.delay(3)
        left_pipette.move_to(water['A2'].top(30))
        left_pipette.move_to(water['A2'].bottom(48.4))
        left_pipette.move_to(water['A2'].bottom(75))
        left_pipette.move_to(water['A2'].bottom(48.4))
        protocol.delay(3)
        left_pipette.move_to(water['A3'].top(30))
        left_pipette.move_to(water['A3'].bottom(48.4))
        left_pipette.move_to(water['A3'].bottom(75))
        left_pipette.move_to(water['A3'].bottom(48.4))
        protocol.delay(3)
        left_pipette.move_to(water['A3'].top(30))
        return
        
    def drying(sponge, loc):
        left_pipette.move_to(sponge[loc].top(15.5))
        protocol.delay(2)
        left_pipette.move_to(sponge[loc].top(118))
        os.system("python /data/user_storage/dry.py")
        protocol.delay(10)
    
    locats = locat_dict()
    
    for locat in locats.keys():
        for loc in locats[locat]:
            if locat == 'source1':
                cond_measurement(source1, loc)
                rinsing(water)
                drying(sponge, 'B4')
            elif locat == 'source2':
                cond_measurement(source2, loc)
                rinsing(water)
                drying(sponge, 'B4')
                
    protocol.comment("Bringing OT-2 home...")
    protocol.home()
    protocol.comment('Conductivity measurement completed.')