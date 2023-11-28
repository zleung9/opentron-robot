#!/usr/bin/env python
# coding: utf-8

# In[ ]:
    
import opentrons.execute
from opentrons import protocol_api

metadata={"apiLevel": "2.10"}
def run(ctx):
    ctx.comment('hello')