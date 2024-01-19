import os
import serial
from abc import ABC
import pandas as pd
from datetime import datetime

class Robot(ABC):
    def __init__(self, config=None): 
        self.config = {}    

    def load_config(self, config) -> None: 
        raise NotImplementedError


class ConductivityMeter(Robot):
    def __init__(self, config=None): 
        super().__init__(config=config)
        self._cond = None # unit: S/cm
        self._temp = None # unit: C
        self._time = None 
        self._check = False
        self.result_list = []

    def load_config(self, config):
        self.config = config
        cwd = os.path.dirname(__file__)
        self._formulation_input_path = os.path.join(cwd, "experiment.csv")

    def read_cond(self, uid=None, verbose=False, append=True):
        port = "/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0"
        self._check = False
        with serial.Serial(port, 9600, timeout=2) as ser:
            ser.write('GETMEAS <CR>'.encode()+ b"\r\n")
            s = ser.read(1000).decode()
            s_list = s.split(',')
            
            # measure temperature
            temperature = s_list[12]
            temp_unit = s_list[13]
            
            # measure conductivity
            cond_unit = s_list[9]
            if cond_unit == 'mS/cm':
                conductivity = round(float(s_list[8])/1000,5) # Unit: mS/cm
            elif cond_unit == 'uS/cm':
                conductivity = round(float(s_list[8])/1000000,11) # Unit: uS/cm
            
            # record time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if verbose:
                print("Conductivity of this sample is: " + str(conductivity) + str(cond_unit))
                print("Temperature at time of measurement is: " + str(temperature) + str(temp_unit))
            self._temp = temperature
            self._cond = conductivity
            self._time = current_time

        if append:
            self.result_list.append(
                {
                    "uid": uid, 
                    "Conductivity": self._cond, 
                    "Temperature": self._temp,
                    "Time": self._time
                }
            )


    def clear_cache(self):
        self.result_list  = []


    def export_result(self, file_path:str=None, clear_cache=True):
        """Export result to formulation file
        Parameters
        ----------
        file_path: str
            Path to the formulation file. If None, the result will be exported to the original formulation file.
        clear_cache: bool
            Clear the cache after exporting the result.
        """

        df = pd.read_csv(self._formulation_input_path, incex_col="unique_id")
        for result in self.result_list:
            uid = result["uid"]
            df.loc[uid, "Conductivity"] = result["Conductivity"]
            df.loc[uid, "Temperature"] = result["Temperature"]
            df.loc[uid, "Time"] = result["Time"]

        if file_path is None:
            file_path = self._formulation_input_path
        df.reset_index(inplace=True)
        df.to_csv(file_path, index=False)

        if clear_cache:
            self.clear_cache()

class ChemSpeed(Robot):
    def __init__(self):
        super().__init__()


class SquidStad(Robot):
    def __init__(self):
        super().__init__()