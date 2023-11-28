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
with open('/data/user_storage/automat_2x4wellplate_50ml.json') as labware_file:
    wellplate50ml_steel = json.load(labware_file)
with open('/data/user_storage/automat_2x4_sheetmetal.json') as labware_file:
    wellplate50ml_sheet = json.load(labware_file)
with open('/data/user_storage/sponge.json') as labware_file:
    sponge = json.load(labware_file)
# with open('/data/user_storage/automat_2x4wellplate_20ml_offset.json') as labware_file:
#     waterplate = json.load(labware_file)
with open('/data/user_storage/automat_2x4_sheetmetal_offset.json') as labware_file:
    waterplate = json.load(labware_file)

def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(True)
    protocol.comment('light is on')
    
    source1 = protocol.load_labware_from_definition(wellplate50ml_sheet, 5)
    # source2 = protocol.load_labware_from_definition(wellplate50ml_steel, 8)
    tiprack = protocol.load_labware('opentrons_96_tiprack_1000ul', 1)
    plate1 = protocol.load_labware_from_definition(targetplated, 6)
    plate2 = protocol.load_labware_from_definition(targetplated, 9)
    
    right_pipette = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tiprack])
    
    chemicallocat_1 = {'Chemical1_1': ['A1'], 'Chemical5_1': ['B1'],\
                       'Chemical2_1': ['A2'], 'Chemical6_1': ['B2'],\
                       'Chemical3_1': ['A3'], 'Chemical7_1': ['B3'],\
                       'Chemical4_1': ['A4'], 'Chemical8_1': ['B4']}
    
    # chemicallocat_2 = {'Chemical5_1': ['A1'], 'Chemical5_2': ['B1'],\
                       # 'Chemical6_1': ['A2'], 'Chemical6_2': ['B2'],\
                       # 'Chemical7_1': ['A3'], 'Chemical7_2': ['B3'],\
                       # 'Chemical8_1': ['A4'], 'Chemical8_2': ['B4']}
    
    tip_locat = {'Chemical1_1': ['A1'], 'Chemical1_2': ['A1'],\
                 'Chemical2_1': ['B1'], 'Chemical2_2': ['B1'],\
                 'Chemical3_1': ['C1'], 'Chemical3_2': ['C1'],\
                 'Chemical4_1': ['D1'], 'Chemical4_2': ['D1'],\
                 'Chemical5_1': ['E1'], 'Chemical5_2': ['E1'],\
                 'Chemical6_1': ['F1'], 'Chemical6_2': ['F1'],\
                 'Chemical7_1': ['G1'], 'Chemical7_2': ['G1'],\
                 'Chemical8_1': ['H1'], 'Chemical8_2': ['H1']}
    mixing_tip = 'A2'
    
    right_pipette.well_bottom_clearance.aspirate = 3
    right_pipette.well_bottom_clearance.dispense = 45
    blow_out = True
    
    # def dispense_Helper_func(tip, source, amounts):
    #     right_pipette.pick_up_tip(tiprack[tip])
    #     print("source plate: ", source)
    #     print("amounts: ", amounts)
    #     myIdx = 0
    #     counter = 0
    #     for microLiter in amounts:
    #         if microLiter != 0:
    #             overmaxvalue_Helper_func(microLiter, source, myIdx, amounts, counter)
    #         myIdx += 1
    #     return
  
    # def overmaxvalue_Helper_func(liq_amount, source, myIdx, amounts, counter):
    #     if liq_amount <= 1000:
    #         counter += (liq_amount/1000)
    #         aspirate_action(liq_amount, source)
    #         dispense_action(liq_amount, myIdx, amounts, counter)
    #         return
    #     else:
    #         red_amount = liq_amount - 1000
    #         if red_amount < 100:
    #             red_amount = liq_amount - 900
    #             counter += 0.9
    #             aspirate_action(900, source)
    #             dispense_action(900, myIdx, amounts, counter)
    #             overmaxvalue_Helper_func(red_amount, source, myIdx, amounts, counter)
    #         else:
    #             counter += 1
    #             aspirate_action(1000, source)
    #             dispense_action(1000, myIdx, amounts, counter)
    #             overmaxvalue_Helper_func(red_amount, source, myIdx, amounts, counter)
    #     return

    # def aspirate_action(microLiter, source):
    #     right_pipette.aspirate(microLiter, source)
    #     protocol.delay(2)
    #     right_pipette.touch_tip(v_offset=-3)
    #     return
    
    # def dispense_action(microLiter, myIdx, amounts, counter):
    #     if myIdx < 8:
    #         right_pipette.dispense(microLiter, plate1.wells()[myIdx]).blow_out()
    #         print(1000*counter, "out of", amounts[myIdx], "uL dispensed into", plate1.wells()[myIdx])
    #     else:
    #         right_pipette.dispense(microLiter, plate2.wells()[myIdx-8]).blow_out()
    #         print(1000*counter, "out of", amounts[myIdx], "uL dispensed into", plate2.wells()[myIdx-8])
    #     protocol.delay(2)
    #     return
    
    
    # # Liquid Dispensing
    # for chemical in data.columns:
    #     if (data[chemical] == 0).all() or (chemical not in chemicallocat_1.keys()):
    #         continue
    #     elif chemical in chemicallocat_1.keys():
    #         print("Current Chemical: ", chemical)
    #         tip = tip_locat[chemical][0]
    #         chemical_source = source1[chemicallocat_1[chemical][0]]
    #         dispense_Helper_func(tip, chemical_source, data[chemical])
    #         right_pipette.return_tip()
    #     # elif chemical in chemicallocat_2.keys():
    #     #     print("Current Chemical: ", chemical)
    #     #     tip = tip_locat[chemical][0]
    #     #     chemical_source = source2[chemicallocat_2[chemical][0]]
    #     #     dispense_Helper_func(tip, chemical_source, data[chemical])
    #     #     right_pipette.return_tip()
    
    # tip = mixing_tip
    # right_pipette.pick_up_tip(tiprack[tip])
    # for i in plate1.wells():
    #     right_pipette.mix(3, 1000, location = i.bottom(5))
    # for i in plate2.wells():
    #     right_pipette.mix(3, 1000, location = i.bottom(5))
    # right_pipette.return_tip()
    
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
    
    def locat_dict():
        plate = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
        return plate
    
    def cond_measurement(plate, loc):
        left_pipette.move_to(plate[loc].top(60))
        left_pipette.move_to(plate[loc].bottom(48.9))
        left_pipette.move_to(plate[loc].bottom(70))
        left_pipette.move_to(plate[loc].bottom(48.9))
        # protocol.delay(35)
        protocol.comment('Measuring conductivity...')
        # protocol.delay(4)
    
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
        left_pipette.move_to(sponge[loc].top(131.5))
        os.system("python /data/user_storage/dry.py")
        protocol.delay(14)
        # left_pipette.move_to(sponge[loc].top(15.5))
        
    locats = locat_dict()
    
    for plate_number in range(2):
        for loc in locats:
            if plate_number == 0:
                cond_measurement(plate1, loc)
            else:
                cond_measurement(plate2, loc)
            # rinsing(water)
            drying(sponge, 'A3')
            break
        break
    
    # protocol.comment("Bringing OT-2 home...")
    # protocol.home()
    # protocol.comment('Conductivity measurement completed.')