import serial
from abc import ABC
import pandas as pd

class Robot(ABC):
    def __init__(self): ...


class ConductivityMeter(Robot):
    def __init__(self): 
        super().__init__()
        self._cond = None # unit: S/cm
        self._temp = None # unit: C
        self._check = False
        self.cond_list = []
        self.temp_list = []
        self.slot_list = []
    
    def read_cond(self, slot:str, verbose=False, append=True):
        port = "/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0"
        self._check = False
        with serial.Serial(port, 9600, timeout=2) as ser:
            ser.write('GETMEAS <CR>'.encode()+ b"\r\n")
            s = ser.read(1000).decode()
            s_list = s.split(',')
            temperature = s_list[12]
            temp_unit = s_list[13]

            cond_unit = s_list[9]
            if cond_unit == 'mS/cm':
                conductivity = round(float(s_list[8])/1000,5) # Unit: mS/cm
            elif cond_unit == 'uS/cm':
                conductivity = round(float(s_list[8])/1000000,11) # Unit: uS/cm

            if verbose:
                print("Conductivity of this sample is: " + str(conductivity) + str(cond_unit))
                print("Temperature at time of measurement is: " + str(temperature) + str(temp_unit))

            self._temp = temperature
            self._cond = conductivity
            self._check = True

            if append:
                self.slot_list.append(slot)
                self.cond_list.append(self._cond)
                self.temp_list.append(self._temp)


    def clear_cache(self):
        self.cond_list = []
        self.temp_list = []
        self.slot_list = []

    def export_data(self, fname, metadata=None, clear_cache=True):
        """
        """
        data = {
            "Well": self.slot_list,
            "measured_conductivity(S/cm)": self.cond_list,
            "temperature(C)": self.temp_list
        }
        df_data = pd.DataFrame(data)
        if metadata is None:
            df = df_data
        else:
            df_metadata = pd.DataFrame(data)
            df = pd.concat([df_metadata, df_data], axis=1)
        
        if clear_cache:
            self.clear_cache()

        df.to_csv(fname, index=False)
        self._exported_data = df


class ChemSpeed(Robot):
    def __init__(self):
        super().__init__()


class SquidStad(Robot):
    def __init__(self):
        super().__init__()