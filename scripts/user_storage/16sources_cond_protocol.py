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
import serial

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
    
    source1 = protocol.load_labware_from_definition(wellplate50ml, 5)
    source2 = protocol.load_labware_from_definition(wellplate50ml, 8)
    tiprack = protocol.load_labware('opentrons_96_tiprack_1000ul', 1)
    sponge = protocol.load_labware_from_definition(targetplatec, 3)
    water = protocol.load_labware_from_definition(waterplate, 2)
    left_pipette = protocol.load_instrument('p300_single_gen2', mount='left')
    
    right_pipette = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tiprack])
        
    right_pipette.well_bottom_clearance.aspirate = 3
    right_pipette.well_bottom_clearance.dispense = 45
    
    def read_cond():
        port = "/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0"
        check = False
        with serial.Serial(port, 9600, timeout=2) as ser:
            ser.write('GETMEAS <CR>'.encode()+ b"\r\n")
            s = ser.read(1000).decode()
            s_list = s.split(',')
            unit = s_list[9]
            if unit == 'mS/cm':
                conductivity = round(float(s_list[8])/1000,5) # Unit: mS/cm
            elif unit == 'uS/cm':
                conductivity = round(float(s_list[8])/1000000,11) # Unit: uS/cm
            check = True
            print("Conductivity of this sample is: " + str(conductivity) + str(unit))
        return check, conductivity
    
    def locat_dict():
        source_wells = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
        return {'source1':source_wells, 'source2':source_wells}
    
    def cond_measurement(plate, loc):
        left_pipette.move_to(plate[loc].top(60))
        left_pipette.move_to(plate[loc].bottom(70))
        left_pipette.move_to(plate[loc].bottom(95))
        left_pipette.move_to(plate[loc].bottom(70))
        protocol.delay(35)
        protocol.comment('Measuring conductivity...')
        _, cond = read_cond()
        return cond
    
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
        left_pipette.move_to(sponge[loc].top(93))
        os.system("python /data/user_storage/dry.py")
        protocol.max_speeds['z'] = 10
        protocol.delay(3.5)
        left_pipette.move_to(sponge[loc].top(98))
        left_pipette.move_to(sponge[loc].top(81))
        left_pipette.move_to(sponge[loc].top(93))
        protocol.delay(3)
        del protocol.max_speeds['z']
        left_pipette.move_to(sponge[loc].top(15.5))
        protocol.delay(1)
    
    locats = locat_dict()
    print("Checking connection with conductivity meter.")
    connection, cond = read_cond()
    if not connection:
        return
    
    conductivity_values = {'cond': []}
    for locat in locats.keys():
        for loc in locats[locat]:
            if locat == 'source1':
                cond = cond_measurement(source1, loc)
            elif locat == 'source2':
                cond = cond_measurement(source2, loc)
            rinsing(water)
            drying(sponge, 'A4')
            conductivity_values['cond'].append(cond)
                
    ## Create Pickle with conductivity values list
    pkl_path = '/data/user_storage/conductivity_list.pkl'
    pickle.dump(conductivity_values, open(pkl_path, 'wb'))
    
    protocol.comment("Bringing OT-2 home...")
    protocol.home()
    protocol.comment('Conductivity measurement completed.')