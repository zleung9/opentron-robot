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

file = '/data/user_storage/Newexperiment.csv'
data = pd.read_csv(file)

#OT-2
metadata={"apiLevel": "2.11"}

# labware
with open('/data/user_storage/automat_2x4wellplate_20ml.json') as labware_file:
    targetplated = json.load(labware_file)
# with open('/data/user_storage/automat_2x4wellplate_50ml.json') as labware_file:
#     wellplate50ml = json.load(labware_file)
with open('/data/user_storage/automat_2x4_sheetmetal.json') as labware_file:
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
    tiprack = protocol.load_labware('opentrons_96_tiprack_1000ul', 1)
    plate = protocol.load_labware_from_definition(targetplated, 6)
    
    right_pipette = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tiprack])
    
    chemicallocat_1 = {'6M_LiTFSI1': ['A1'], 'DI Water1': ['A2'], \
                       '6M_LiTFSI2': ['B1'], 'DI Water2': ['B2']}
    
    tip_locat = {'6M_LiTFSI1': ['A1'], 'DI Water1': ['B1'],\
                 '6M_LiTFSI2': ['A1'], 'DI Water2': ['B1']}
    
    right_pipette.well_bottom_clearance.aspirate = 3
    right_pipette.well_bottom_clearance.dispense = 45
    
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
        right_pipette.aspirate(microLiter, source)
        protocol.delay(2)
        right_pipette.touch_tip(v_offset=-3)
        return
    
    def dispense_action(microLiter, myIdx, amounts, counter):
        right_pipette.dispense(microLiter, plate.wells()[myIdx])
        print(1000*counter, "out of", amounts[myIdx-well_shift], "uL dispensed into", plate.wells()[myIdx])
        protocol.delay(2)
        return
    
    def track_well():
        target_counts_dict = pickle.load(open('/data/user_storage/target_counts.pkl', 'rb'))
        well_shift = target_counts_dict['ot2_target_well_shift']
        return well_shift
    
    ## Liquid Dispensing
    well_shift = track_well()
    for chemical in data.columns:
        if (data[chemical] == 0).all() or chemical not in chemicallocat_1.keys():
            continue
        elif chemical in chemicallocat_1.keys():
            print("Current Chemical: ", chemical)
            tip = tip_locat[chemical][0]
            chemical_source = source1[chemicallocat_1[chemical][0]]
            dispense_Helper_func(tip, chemical_source, data[chemical], well_shift)
            if chemical == list(chemicallocat_1.keys())[1] or chemical == list(chemicallocat_1.keys())[-1]:
                right_pipette.mix(3, 1000, location = plate.wells()[track_well()].bottom(5))
            blow_out = True
            right_pipette.return_tip()
            
    # protocol.comment("Bringing OT-2 home...")
    # protocol.home()
    
    ## Conductivity run
    with open('/data/user_storage/automat_2x4wellplate_20ml_offset.json') as labware_file:
        targetplatec = json.load(labware_file)
    del protocol.deck['6']
    plate = protocol.load_labware_from_definition(targetplatec, 6)
    sponge = protocol.load_labware_from_definition(targetplatec, 9)
    water = protocol.load_labware_from_definition(waterplate, 5)
    left_pipette = protocol.load_instrument('p300_single_gen2', mount='left')
    
    def locat_table():
        target_counts_dict = pickle.load(open('/data/user_storage/target_counts.pkl', 'rb'))
        well_i = target_counts_dict['ot2_target_well_shift']
        if well_i == 0:
            return ['A1']
        elif well_i == 1:
            return ['A2']
        elif well_i == 2:
            return ['A3']
        elif well_i == 3:
            return ['A4']
        elif well_i == 4:
            return ['B1']
        elif well_i == 5:
            return ['B2']
        elif well_i == 6:
            return ['B3']
        elif well_i == 7:
            return ['B4']
    
    def cond_measurement(plate, loc):
        left_pipette.move_to(plate[loc].top(100))
        left_pipette.move_to(plate[loc].bottom(48.9))
        left_pipette.move_to(plate[loc].top(100))
        left_pipette.move_to(plate[loc].bottom(48.9))
        protocol.delay(35)
        protocol.comment('Measuring conductivity...')
        protocol.delay(4)
    
    def rinsing(water):
        left_pipette.move_to(water['A1'].top(100))
        left_pipette.move_to(water['A1'].bottom(48.4))
        protocol.delay(3)
        left_pipette.move_to(water['A2'].top(100))
        left_pipette.move_to(water['A2'].bottom(48.4))
        protocol.delay(3)
        left_pipette.move_to(water['A3'].top(100))
        left_pipette.move_to(water['A3'].bottom(48.4))
        protocol.delay(3)
        left_pipette.move_to(water['A3'].top(100))
        return
        
    def drying(sponge, loc):
        left_pipette.move_to(sponge[loc].top(15))
        protocol.delay(3)
    
    locats = locat_table()
    
    
    for loc in locats:
        cond_measurement(plate, loc)
        rinsing(water)
        drying(sponge, loc)
        
    protocol.home()
    protocol.comment('Conductivity measurement completed.')