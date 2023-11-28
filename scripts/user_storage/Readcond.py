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
            conductivity = round(float(s_list[8])/1000,5) # Unit: mS/cm^M
        elif unit == 'uS/cm':
            conductivity = round(float(s_list[8])/1000000,11) # Unit: uS/cm^M
        check = True
        print("Conductivity of this sample is: " + str(conductivity) + str(unit))
        temp = s_list[12]
    return check, conductivity, temp

check, conductivity, temp = read_cond()
print(temp)
