# -*- coding: utf-8 -*-
"""
Copyright 2019 - 2022 Automat Solutions, Inc. All rights reserved. All programs in this software package are confidential trade secret information and/or proprietary information of Automat Solutions, Inc. Code or other information in this package also m ay be confidential and/or proprietary to Automat Solutions, Inc. The package is intended for internal use only and no warranties are given. Possession and use of these programs outside of Automat Solutions, Inc. must conform strictly to a license agreement between the user and Automat Solutions, Inc. Receipt or possession of this program does not convey any rights to use, disclose, reproduce, or distribute this program without specific written authorization of Automat Solutions, Inc.

This file is subject to the terms and conditions defined in file 'LICENSE.TXT', which is part of this source code package.
"""

import os

# local imports
import materials_generation.db_functions as db
from ot2_operation.src import Fullchain as ot2
from ot2_operation.src import conductivity_functions


def drive_pilot_demo(comp_id: int, robot_ip: str, ssh_key: str) -> None:
    '''
    :param comp_id: composition ID
    :param robot_ip: IP address of OT-2
    :param ssh_key: path to OT-2 ssh key
    :return: None
    '''
    
    try:
        new_recipes, ml_recipes = db.check_for_new_recipes(comp_id)
        print(ml_recipes)
        if new_recipes:
            ### OT-2 operation
            df, cond, temp, connection = ot2.ot2_operations(robot_ip, ssh_key, ml_recipes)
            if not connection:
                ot2.online(robot_ip, ssh_key)
                print("Dispensing interrupted due to conductivity meter connection or OT-2 protocol interruption")
                return
            df = conductivity_functions.saveDB(df, cond, temp)
            ot2.online(robot_ip, ssh_key)
    except KeyboardInterrupt:
        ot2.online(robot_ip, ssh_key)


if __name__ == '__main__':
    # Define function input variables
    print(__file__)
    robot_ip = '169.254.204.106'
    ssh_key = os.path.join(os.getcwd(), 'ot2_operation', 'ot2_ssh_key_outside')
    # Run workflow
    drive_pilot_demo(comp_id=1, robot_ip=robot_ip, ssh_key=ssh_key)
