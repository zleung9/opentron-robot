#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import os
import json
import csv
import pandas as pd
import pickle
import serial
import opentrons.execute
from opentrons import protocol_api

#OT-2
metadata={"apiLevel": "2.11"}

# labware
with open('/data/user_storage/sponge.json') as labware_file:
    sponge = json.load(labware_file)
with open('/data/user_storage/automat_2x4wellplate_20ml_offset.json') as labware_file:
    waterplate = json.load(labware_file)
with open('/data/user_storage/automat_2x4wellplate_20ml_offset.json') as labware_file:
    targetplatec = json.load(labware_file)


def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(True)
    protocol.comment('light is on')
    
    plate1 = protocol.load_labware_from_definition(targetplatec, 6)
    plate2 = protocol.load_labware_from_definition(targetplatec, 9)
    sponge = protocol.load_labware_from_definition(targetplatec, 3)
    water = protocol.load_labware_from_definition(waterplate, 2)
    left_pipette = protocol.load_instrument('p300_single_gen2', mount='left')
        
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
    
    ## Conductivity run
    print("Checking connection with conductivity meter.")
    connection, cond = read_cond()
        
    def locat_dict():
        plate = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
        return plate
    
    def cond_measurement(plate, loc):
        left_pipette.move_to(plate[loc].top(60))
        left_pipette.move_to(plate[loc].bottom(49))
        left_pipette.move_to(plate[loc].bottom(85))
        left_pipette.move_to(plate[loc].bottom(49))
        protocol.delay(60)
        protocol.comment('Measuring conductivity...')
        _, cond = read_cond()
        left_pipette.move_to(plate[loc].top(60))
        protocol.delay(3)
        return cond
    
    def rinsing(water):
        protocol.max_speeds['x'] = 100
        left_pipette.move_to(water['A1'].top(100))
        left_pipette.move_to(water['A1'].bottom(48.4))
        left_pipette.move_to(water['A1'].bottom(75))
        left_pipette.move_to(water['A1'].bottom(48.4))
        left_pipette.move_to(water['A1'].bottom(75))
        left_pipette.move_to(water['A1'].bottom(48.4))
        protocol.delay(3)
        left_pipette.move_to(water['A1'].top(80))
        protocol.delay(2)
        left_pipette.move_to(water['A2'].top(80))
        left_pipette.move_to(water['A2'].bottom(48.4))
        left_pipette.move_to(water['A2'].bottom(75))
        left_pipette.move_to(water['A2'].bottom(48.4))
        left_pipette.move_to(water['A2'].bottom(75))
        left_pipette.move_to(water['A2'].bottom(48.4))
        protocol.delay(3)
        left_pipette.move_to(water['A2'].top(80))
        protocol.delay(2)
        left_pipette.move_to(water['A3'].top(80))
        left_pipette.move_to(water['A3'].bottom(48.4))
        left_pipette.move_to(water['A3'].bottom(75))
        left_pipette.move_to(water['A3'].bottom(48.4))
        left_pipette.move_to(water['A3'].bottom(75))
        left_pipette.move_to(water['A3'].bottom(48.4))
        protocol.delay(3)
        left_pipette.move_to(water['A3'].top(80))
        protocol.delay(2)
        left_pipette.move_to(water['A4'].top(80))
        left_pipette.move_to(water['A4'].bottom(48.4))
        left_pipette.move_to(water['A4'].bottom(75))
        left_pipette.move_to(water['A4'].bottom(48.4))
        left_pipette.move_to(water['A4'].bottom(75))
        left_pipette.move_to(water['A4'].bottom(48.4))
        protocol.delay(3)
        left_pipette.move_to(water['A4'].top(80))
        protocol.delay(2)

        return
        
    def drying(sponge, loc):
        left_pipette.move_to(sponge[loc].top(55.5))
        left_pipette.move_to(sponge[loc].top(15.5))
        left_pipette.move_to(sponge[loc].top(93))
        os.system("python /data/user_storage/dry.py")
        protocol.max_speeds['z'] = 14
        protocol.delay(3.5)
        left_pipette.move_to(sponge[loc].top(102))
        left_pipette.move_to(sponge[loc].top(74))
        left_pipette.move_to(sponge[loc].top(93))
        protocol.delay(3)
        del protocol.max_speeds['z']
        del protocol.max_speeds['x']
        left_pipette.move_to(sponge[loc].top(15.5))
        protocol.delay(1)
        
    locats = locat_dict()
    
    conductivity_values = {'cond': []}
    for plate_number in range(2):
        for loc in locats:
            if plate_number == 0:
                cond = cond_measurement(plate1, loc)
            else:
                cond = cond_measurement(plate2, loc)
            conductivity_values['cond'].append(cond)
            rinsing(water)
            drying(sponge, 'A4')
                
    ## Create Pickle with conductivity values list
    pkl_path = '/data/user_storage/conductivity_list.pkl'
    pickle.dump(conductivity_values, open(pkl_path, 'wb'))
    
    protocol.comment("Bringing OT-2 home...")
    protocol.home()
    protocol.comment('Conductivity measurement completed.')