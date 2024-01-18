# -*- coding: utf-8 -*-
"""
Copyright 2019 - 2022 Automat Solutions, Inc. All rights reserved. All programs in this software package are confidential trade secret information and/or proprietary information of Automat Solutions, Inc. Code or other information in this package also m ay be confidential and/or proprietary to Automat Solutions, Inc. The package is intended for internal use only and no warranties are given. Possession and use of these programs outside of Automat Solutions, Inc. must conform strictly to a license agreement between the user and Automat Solutions, Inc. Receipt or possession of this program does not convey any rights to use, disclose, reproduce, or distribute this program without specific written authorization of Automat Solutions, Inc.

This file is subject to the terms and conditions defined in file 'LICENSE.TXT', which is part of this source code package.
"""

import socket
import time
import os

def cond_conn_check():
    """Check connection with meter"""
    UDP_IP = "169.254.239.206"
    UDP_PORT = 5005

    MESSAGE = "check_cond"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(MESSAGE.encode(), (UDP_IP, UDP_PORT))
    
def get_conductivity():
    """Get conductivity from meter"""
    UDP_IP = "169.254.239.206"
    UDP_PORT = 5005

    MESSAGE = "cond"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(MESSAGE.encode(), (UDP_IP, UDP_PORT))
    
def trigger_pump():
    """Trigger vacuum pump"""
    UDP_IP = "169.254.239.206"
    UDP_PORT = 5005

    MESSAGE = "8"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(MESSAGE.encode(), (UDP_IP, UDP_PORT))