import socket
from time import sleep

HOST = "169.254.1.78"  # Standard loopback interface address (localhost)
PORT = 23  # Port to listen on (non-privileged ports are > 1023)

s = socket.socket()
s.connect((HOST, PORT))
s.settimeout(1)

while True: # receive command every 10 second
    sleep(10)
    try:
        message = s.recv(2048).decode("utf-8")
        if message == "Start SquidStat":
            s.send(str.encode("In Progress"))
            # result = subprocess.run("python exit_on_Completed_experiment.py")
            # stdout, stderr = result.stdout, result.stderr
            for i in range(5):
                sleep(1); print(5-i)
            print("Voltage is measured and data saved!")
            s.send(str.encode("Finish"))
            break
    except:
        continue