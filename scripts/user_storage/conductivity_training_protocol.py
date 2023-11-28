#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import os
# os.system("systemctl stop opentrons-robot-server")
import json
import csv
import pandas as pd
import pickle
import opentrons.execute
from opentrons import protocol_api

# file = '/data/user_storage/Newexperiment.csv'
# data = pd.read_csv(file)

#OT-2
metadata={"apiLevel": "2.11"}


# labware
with open('/data/user_storage/automat_2x4wellplate_20ml_offset.json') as labware_file:
    targetplate = json.load(labware_file)
# with open('/data/user_storage/automat_1x2_conductivity_demo.json') as labware_file:
#     targetplate = json.load(labware_file)
with open('/data/user_storage/sponge.json') as labware_file:
    sponge = json.load(labware_file)
with open('/data/user_storage/automat_2x4wellplate_20ml_offset.json') as labware_file:
    waterplate = json.load(labware_file)

def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(True)
    protocol.comment('light is on')
    
    sponge = protocol.load_labware_from_definition(targetplate, 9)
    plate = protocol.load_labware_from_definition(targetplate, 6)
    water = protocol.load_labware_from_definition(waterplate, 5)
    left_pipette = protocol.load_instrument('p300_single_gen2', mount='left')
    
    def locat_table():
        return ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
    
    def cond_measurement(plate, loc):
        left_pipette.move_to(plate[loc].top(100))
        left_pipette.move_to(plate[loc].bottom(48))
        left_pipette.move_to(plate[loc].top(100))
        left_pipette.move_to(plate[loc].bottom(48))
        protocol.delay(35)
        protocol.comment('Measuring conductivity...')
        protocol.delay(4)
    
    def rinsing(water):
        left_pipette.move_to(water['A1'].top(100))
        left_pipette.move_to(water['A1'].bottom(48))
        protocol.delay(3)
        left_pipette.move_to(water['A2'].top(100))
        left_pipette.move_to(water['A2'].bottom(48))
        protocol.delay(3)
        left_pipette.move_to(water['A3'].top(100))
        left_pipette.move_to(water['A3'].bottom(48))
        protocol.delay(3)
        left_pipette.move_to(water['A3'].top(100))
        return
        
    def drying(sponge, loc):
        left_pipette.move_to(sponge[loc].top(14.5))
        protocol.delay(3)
    
    locats = locat_table()
    
    
    for loc in locats:
        cond_measurement(plate, loc)
        rinsing(water)
        drying(sponge, loc)
        
    protocol.home()
    protocol.comment('Conductivity measurement completed.')
        