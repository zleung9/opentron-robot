# -*- coding: utf-8 -*-
"""
Copyright 2019 - 2022 Automat Solutions, Inc. All rights reserved. All programs in this software package are confidential trade secret information and/or proprietary information of Automat Solutions, Inc. Code or other information in this package also m ay be confidential and/or proprietary to Automat Solutions, Inc. The package is intended for internal use only and no warranties are given. Possession and use of these programs outside of Automat Solutions, Inc. must conform strictly to a license agreement between the user and Automat Solutions, Inc. Receipt or possession of this program does not convey any rights to use, disclose, reproduce, or distribute this program without specific written authorization of Automat Solutions, Inc.

This file is subject to the terms and conditions defined in file 'LICENSE.TXT', which is part of this source code package.
"""

from pump_raspi import raspi_comm

if __name__ == "__main__":
	raspi_comm.trigger_pump()