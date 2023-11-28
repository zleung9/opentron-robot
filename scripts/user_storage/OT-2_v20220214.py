#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import json
import pandas as pd
from opentrons import protocol_api

file = '/data/user_storage/Newexperiment.csv'
data = pd.read_csv(file)

#OT-2
metadata={"apiLevel": "2.11"}


# labware
with open('/data/user_storage/automat_2x4wellplate_20ml.json') as labware_file:
    wellplate20ml = json.load(labware_file)
with open('/data/user_storage/automat_2x4wellplate_50ml.json') as labware_file:
    wellplate50ml = json.load(labware_file)
with open('/data/user_storage/automat_1x2_aluminum_plate.json') as heatinglabware_file:
    heatingplate = json.load(heatinglabware_file)


def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(True)
    protocol.comment('light is on')
    temp_mod = protocol.load_module('Temperature Module', '9')
    temp_plate = temp_mod.load_labware_from_definition(heatingplate)
    temp_mod.set_temperature(60)
    source1 = protocol.load_labware_from_definition(wellplate50ml, 2)
    source2 = protocol.load_labware_from_definition(wellplate50ml, 5)
    tiprack = protocol.load_labware('opentrons_96_tiprack_1000ul', 1)
    plate = protocol.load_labware_from_definition(wellplate20ml, 3)
    right_pipette = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tiprack])
    
    chemicallocat_1 = { 'DEC': ['A1'], 'DMC': ['A2'], '1,3-dioxolane': ['A3'],\
                       '1,2-dimethoxyethane': ['A4'], 'PC': ['B1'], 'VC': ['B2'],'FEC': ['B3'] }
    chemicallocat_2 = {'diglyme': ['A1'], 'TTE': ['A2'], 'Sulfolane': ['A3'], 'SN': ['A4'], 'PS': ['B1']}
    chemicallocat_3 = {'EC': ['A1']}
    right_pipette.well_bottom_clearance.aspirate = 3
    right_pipette.well_bottom_clearance.dispense = 45
    
    def dispense_Helper_func(source, amounts):
        right_pipette.pick_up_tip()
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
            red_amount = liq_amount - 1000
            if red_amount < 100:
                red_amount = liq_amount - 900
                aspirate_action(900, source)
                dispense_action(900, myIdx, amounts)
                overmaxvalue_Helper_func(red_amount, source, myIdx, amounts)
            else:
                aspirate_action(1000, source)
                dispense_action(1000, myIdx, amounts)
                overmaxvalue_Helper_func(red_amount, source, myIdx, amounts)
        return

    def aspirate_action(microLiter, source):
        right_pipette.aspirate(microLiter, source)
        protocol.delay(2)
        right_pipette.touch_tip(v_offset=-3)
        return
    
    def dispense_action(microLiter, myIdx, amounts):
        right_pipette.dispense(microLiter, plate.wells()[myIdx])
        print(amounts[myIdx], " dispensed into ", plate.wells()[myIdx])
        protocol.delay(2)
        blowout_location='trash'
        return
        
    for chemical in data.columns:
        if ((data[chemical] == 0).all()) or (chemical not in chemicallocat_1.keys()) and (chemical not in chemicallocat_2.keys()):
            continue
        elif chemical in chemicallocat_1.keys():
            print("Current Chemical: ", chemical)
            chemical_source = source1[chemicallocat_1[chemical][0]]
            dispense_Helper_func(chemical_source, data[chemical])
            blow_out = True,
            blowout_location='trash'
            right_pipette.drop_tip()
        elif chemical in chemicallocat_2.keys():
            print("Current Chemical: ", chemical)
            chemical_source = source2[chemicallocat_2[chemical][0]]
            dispense_Helper_func(chemical_source, data[chemical])
            blow_out = True,
            blowout_location='trash'
            right_pipette.drop_tip()
        elif chemical in chemicallocat_3.keys():
            print("Current Chemical: ", chemical)
            chemical_source = temp_plate[chemicallocat_3[chemical][0]] 
            print("temp_plate: ",chemical_source)
            dispense_Helper_func(chemical_source, data[chemical])
            blow_out=True,
            blowout_location='trash'
            right_pipette.drop_tip()
            
    protocol.comment("Bringing OT-2 home...")
    protocol.home()