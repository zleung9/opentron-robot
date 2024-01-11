# echo-client.py

import socket

HOST = "169.254.230.44"  # Standard loopback interface address (localhost)
PORT = 22  # Port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Hello, world")
    data = s.recv(1024)

print(f"Received {data}")