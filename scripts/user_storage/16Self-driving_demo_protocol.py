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

file = '/data/user_storage/Newexperiment.csv'
data = pd.read_csv(file)

#OT-2
metadata={"apiLevel": "2.11"}

# labware
with open('/data/user_storage/automat_2x4wellplate_20ml.json') as labware_file:
    targetplated = json.load(labware_file)
with open('/data/user_storage/automat_2x4wellplate_50ml.json') as labware_file:
    wellplate50ml_steel = json.load(labware_file)
# with open('/data/user_storage/automat_2x4_sheetmetal.json') as labware_file:
#     wellplate50ml_sheet = json.load(labware_file)
with open('/data/user_storage/sponge.json') as labware_file:
    sponge = json.load(labware_file)
with open('/data/user_storage/automat_2x4wellplate_20ml_offset.json') as labware_file:
    waterplate = json.load(labware_file)
# with open('/data/user_storage/automat_2x4_sheetmetal_offset.json') as labware_file:
#     waterplate = json.load(labware_file)

def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(True)
    protocol.comment('light is on')
    
    source1 = protocol.load_labware_from_definition(wellplate50ml_steel, 5)
    source2 = protocol.load_labware_from_definition(wellplate50ml_steel, 8)
    tiprack = protocol.load_labware('opentrons_96_tiprack_1000ul', 1)
    plate1 = protocol.load_labware_from_definition(targetplated, 6)
    plate2 = protocol.load_labware_from_definition(targetplated, 9)
    
    right_pipette = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tiprack])
    
    chemicallocat_1 = {'Chemical1_1': ['A1'], 'Chemical5_1': ['B1'],\
                       'Chemical2_1': ['A2'], 'Chemical6_1': ['B2'],\
                       'Chemical3_1': ['A3'], 'Chemical7_1': ['B3'],\
                       'Chemical4_1': ['A4'], 'Chemical8_1': ['B4']}
    
    chemicallocat_2 = {'Chemical9_1': ['A1'], 'Chemical13_1': ['B1'],\
                       'Chemical10_1': ['A2'], 'Chemical14_1': ['B2'],\
                       'Chemical11_1': ['A3'], 'Chemical15_1': ['B3'],\
                       'Chemical12_1': ['A4'], 'Chemical16_1': ['B4']}
    
    tip_locat = {'Chemical1_1': ['A1'], 'Chemical9_1': ['A2'],\
                 'Chemical2_1': ['B1'], 'Chemical10_1': ['B2'],\
                 'Chemical3_1': ['C1'], 'Chemical11_1': ['C2'],\
                 'Chemical4_1': ['D1'], 'Chemical12_1': ['D2'],\
                 'Chemical5_1': ['E1'], 'Chemical13_1': ['E2'],\
                 'Chemical6_1': ['F1'], 'Chemical14_1': ['F2'],\
                 'Chemical7_1': ['G1'], 'Chemical15_1': ['G2'],\
                 'Chemical8_1': ['H1'], 'Chemical16_1': ['H2']}
    
    right_pipette.well_bottom_clearance.aspirate = 3
    right_pipette.well_bottom_clearance.dispense = 45
    right_pipette.flow_rate.aspirate = 150
    right_pipette.flow_rate.dispense = 150
    right_pipette.flow_rate.blow_out = 50
    
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
    
    def dispense_Helper_func(tip, source, amounts, well_shift):
        right_pipette.pick_up_tip(tiprack[tip])
        print("source plate: ", source)
        print("amounts: ", amounts)
        myIdx = well_shift
        counter = 0
        for microLiter in amounts:
            if microLiter != 0:
                overmaxvalue_Helper_func(microLiter, source, myIdx, amounts, counter)
            myIdx += 1
        return
  
    def overmaxvalue_Helper_func(liq_amount, source, myIdx, amounts, counter):
        if liq_amount <= 1000:
            counter += (liq_amount/1000)
            aspirate_action(liq_amount, source)
            dispense_action(liq_amount, myIdx, amounts, counter)
            return
        else:
            red_amount = liq_amount - 1000
            if red_amount < 100:
                red_amount = liq_amount - 900
                counter += 0.9
                aspirate_action(900, source)
                dispense_action(900, myIdx, amounts, counter)
                overmaxvalue_Helper_func(red_amount, source, myIdx, amounts, counter)
            else:
                counter += 1
                aspirate_action(1000, source)
                dispense_action(1000, myIdx, amounts, counter)
                overmaxvalue_Helper_func(red_amount, source, myIdx, amounts, counter)
        return

    def aspirate_action(microLiter, source):
        protocol.max_speeds['a'] = 50
        right_pipette.aspirate(microLiter, source)
        protocol.delay(2)
        right_pipette.touch_tip(v_offset=-3)
        del protocol.max_speeds['a']
        return
    
    def dispense_action(microLiter, myIdx, amounts, counter):
        protocol.max_speeds['a'] = 50
        if myIdx < 8:
            right_pipette.dispense(microLiter, plate1.wells()[myIdx]).blow_out()
            print(1000*counter, "out of", amounts[myIdx-well_shift], "uL dispensed into", plate1.wells()[myIdx])
            protocol.delay(2)
        else:
            right_pipette.dispense(microLiter, plate2.wells()[myIdx-8]).blow_out()
            print(1000*counter, "out of", amounts[myIdx-well_shift], "uL dispensed into", plate2.wells()[myIdx-8])
            protocol.delay(2)
        del protocol.max_speeds['a']
        return
    
    def mixing_action(mixing_tip, well_shift):
        right_pipette.pick_up_tip(tiprack[mixing_tip])
        if well_shift < 8:
            right_pipette.mix(3, 1000, location = plate1.wells()[well_shift].bottom(5))
        else:
            right_pipette.mix(3, 1000, location = plate2.wells()[well_shift-8].bottom(5))
        right_pipette.drop_tip()
    
    def track_well():
        """Tracks well number of workflow iteration. Returns mixing_tip position"""
        target_counts_dict = pickle.load(open('/data/user_storage/target_counts.pkl', 'rb'))
        well_shift = target_counts_dict['ot2_target_well_shift']
        
        tip_position = 'A3'
        letter = str(tip_position[0])
        number = int(tip_position[1])
        for i in range(well_shift):
            letter = chr((ord(letter) - ord('A') + 1) % 26 + ord('A'))
            if letter == 'I':
                letter = 'A'
                number += 1
                if number == 13:
                    number = 1
            tip_position = letter+str(number)
            
        return well_shift, tip_position
    
    ## Liquid Dispensing
    well_shift, mixing_tip = track_well()
    print("Checking connection with conductivity meter.")
    connection, cond = read_cond()
    if not connection:
        return
    for chemical in data.columns:
        if (data[chemical] == 0).all() or (chemical not in chemicallocat_1.keys() and \
                                            chemical not in chemicallocat_2.keys()):
            continue
        elif chemical in chemicallocat_1.keys():
            print("Current Chemical: ", chemical)
            tip = tip_locat[chemical][0]
            chemical_source = source1[chemicallocat_1[chemical][0]]
            dispense_Helper_func(tip, chemical_source, data[chemical], well_shift)
            blow_out = True
            right_pipette.drop_tip()
        elif chemical in chemicallocat_2.keys():
            print("Current Chemical: ", chemical)
            tip = tip_locat[chemical][0]
            chemical_source = source2[chemicallocat_2[chemical][0]]
            dispense_Helper_func(tip, chemical_source, data[chemical], well_shift)
            blow_out = True
            right_pipette.drop_tip()
    
    mixing_action(mixing_tip, well_shift)
        
    ## Conductivity run
    with open('/data/user_storage/automat_2x4wellplate_20ml_offset.json') as labware_file:
        targetplatec = json.load(labware_file)
    del protocol.deck['6']
    del protocol.deck['9']
    plate1 = protocol.load_labware_from_definition(targetplatec, 6)
    plate2 = protocol.load_labware_from_definition(targetplatec, 9)
    sponge = protocol.load_labware_from_definition(targetplatec, 3)
    water = protocol.load_labware_from_definition(waterplate, 2)
    left_pipette = protocol.load_instrument('p300_single_gen2', mount='left')
    
    def locat_table():
        target_counts_dict = pickle.load(open('/data/user_storage/target_counts.pkl', 'rb'))
        well_i = target_counts_dict['ot2_target_well_shift']
        if well_i == 0 or well_i == 8:
            return ['A1']
        elif well_i == 1 or well_i == 9:
            return ['A2']
        elif well_i == 2 or well_i == 10:
            return ['A3']
        elif well_i == 3 or well_i == 11:
            return ['A4']
        elif well_i == 4 or well_i == 12:
            return ['B1']
        elif well_i == 5 or well_i == 13:
            return ['B2']
        elif well_i == 6 or well_i == 14:
            return ['B3']
        elif well_i == 7 or well_i == 15:
            return ['B4']
    
    def cond_measurement(plate, loc):
        left_pipette.move_to(plate[loc].top(60))
        left_pipette.move_to(plate[loc].bottom(49))
        left_pipette.move_to(plate[loc].bottom(95))
        left_pipette.move_to(plate[loc].bottom(49))
        protocol.delay(35)
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
        protocol.delay(3)
        left_pipette.move_to(water['A1'].top(80))
        protocol.delay(2)
        left_pipette.move_to(water['A2'].top(80))
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
        protocol.delay(3)
        left_pipette.move_to(water['A3'].top(80))
        protocol.delay(2)

        return
        
    def drying(sponge, loc):
        left_pipette.move_to(sponge[loc].top(55.5))
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
        del protocol.max_speeds['x']
        left_pipette.move_to(sponge[loc].top(15.5))
        protocol.delay(1)
    
    locats = locat_table()
    print("Checking connection with conductivity meter.")
    connection, cond = read_cond()
    if not connection:
        return
    
    conductivity_values = {'cond': []}
    for loc in locats:
        if well_shift < 8:
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