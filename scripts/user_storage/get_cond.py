# -*- coding: utf-8 -*-
"""
Copyright 2019 - 2022 Automat Solutions, Inc. All rights reserved. All programs in this software package are confidential trade secret information and/or proprietary information of Automat Solutions, Inc. Code or other information in this package also m ay be confidential and/or proprietary to Automat Solutions, Inc. The package is intended for internal use only and no warranties are given. Possession and use of these programs outside of Automat Solutions, Inc. must conform strictly to a license agreement between the user and Automat Solutions, Inc. Receipt or possession of this program does not convey any rights to use, disclose, reproduce, or distribute this program without specific written authorization of Automat Solutions, Inc.

This file is subject to the terms and conditions defined in file 'LICENSE.TXT', which is part of this source code package.
"""

import serial

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

if __name__ == "__main__":
    read_cond()