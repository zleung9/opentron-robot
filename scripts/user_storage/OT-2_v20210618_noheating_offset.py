#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import os
# os.system("systemctl stop opentrons-robot-server")
import json
import csv
import pandas as pd
import opentrons.execute
from opentrons import protocol_api

file = '/data/user_storage/Newexperiment.csv'
data = pd.read_csv(file)

#OT-2
metadata={"apiLevel": "2.10"}


# labware
with open('/data/user_storage/automat_2x4wellplate_20ml_offset.json') as labware_file:
    wellplate20ml = json.load(labware_file)
with open('/data/user_storage/automat_2x4wellplate_50ml.json') as labware_file:
    wellplate50ml = json.load(labware_file)
with open('/data/user_storage/automat_1x2_aluminum_plate.json') as heatinglabware_file:
    heatingplate = json.load(heatinglabware_file)


def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(True)
    protocol.comment('light is on')
    # temp_mod = protocol.load_module('Temperature Module', '9')
    # temp_plate = temp_mod.load_labware_from_definition(heatingplate)
    # temp_mod.set_temperature(60)
    source1 = protocol.load_labware_from_definition(wellplate50ml, 2)
    tiprack = protocol.load_labware('opentrons_96_tiprack_1000ul', 1)
    plate = protocol.load_labware_from_definition(wellplate20ml, 3)
    left_pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])
    
    chemicallocat_1 = { 'DEC': ['A1'], 'DMC': ['A2'], '1,3-dioxolane': ['A3'], '1,2-dimethoxyethane': ['A4'], 'PC': ['B1'], 'Sulfolane': ['B2'], 'VC': ['B3'], 'FEC': ['B4'] }
    chemicallocat_2 = {'EC': ['A1']}
    left_pipette.well_bottom_clearance.aspirate = 3
    left_pipette.well_bottom_clearance.dispense = 45
    
    def dispense_Helper_func(source, amounts):
        left_pipette.pick_up_tip()
        print("source plate: ", source)
        print("amounts: ", amounts)
        myIdx = 0        
        for microLiter in amounts:
            if microLiter != 0:
                overmaxvalue_Helper_func(microLiter, source, myIdx, amounts)
            myIdx += 1
        return
  
    def overmaxvalue_Helper_func(liq_amount, source, myIdx, amounts):
        if liq_amount <= 1000:
            aspirate_action(liq_amount, source)
            dispense_action(liq_amount, myIdx, amounts)
            return
        else:
            half_amount = liq_amount / 2
            overmaxvalue_Helper_func(half_amount, source, myIdx, amounts)
            overmaxvalue_Helper_func(half_amount, source, myIdx, amounts)
        return

    def aspirate_action(microLiter, source):
        left_pipette.aspirate(microLiter, source)
        protocol.delay(2)
        left_pipette.touch_tip(v_offset=-3)
        return
    
    def dispense_action(microLiter, myIdx, amounts):
        left_pipette.dispense(microLiter, plate.wells()[myIdx])
        print(amounts[myIdx], " dispensed into ", plate.wells()[myIdx])
        protocol.delay(2)
        blowout_location='trash'
        return
        
    for chemical in data.columns:
        if ((data[chemical] == 0).all()) or (chemical not in chemicallocat_1.keys()) and (chemical not in chemicallocat_2.keys()):
            continue
        if chemical in chemicallocat_1.keys():
            print("current Chemical: ", chemical)
            chemical_source = source1[chemicallocat_1[chemical][0]]
            dispense_Helper_func(chemical_source, data[chemical])
            blow_out = True,
            blowout_location='trash'
            left_pipette.drop_tip()
    
    protocol.comment("Bringing OT-2 home...")
    protocol.home()
    
    # for chemical in data.columns:
    #     if chemical in chemicallocat_2.keys():
    #         chemical_source = temp_plate[chemicallocat_2[chemical][0]] 
    #         print("temp_plate: ",chemical_source)
    #         dispense_Helper_func(chemical_source, data[chemical])
    #         blow_out=True,
    #         blowout_location='trash'
    #         right_pipette.drop_tip()