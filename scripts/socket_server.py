import socket

HOST = "169.254.230.44"  # Standard loopback interface address (localhost)
PORT = 24  # Port to listen on (non-privileged ports are > 1023)


if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                print(data)
                if data == b"stop":
                    break
                conn.sendall(data)