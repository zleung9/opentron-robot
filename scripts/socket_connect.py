from socket import socket


class SocketServer(socket):
    def __init__(self, host, port):
        super().__init__()
        self.client = None
        self.start(host=host, port=port)

    def start_client(self, delay=1):
        self.settimeout(delay)
        message = "Start"
        # send a command to start squidstat
        self.client.send(str.enode(message))
        # keep receving response from squidstat 
        while True:
            try:
                message = self.client.recv(2048).decode("utf-8")
                if message == "In Progress":
                    print("Measurement in progress...")
                elif message == "Finished":
                    print("Measurement completed...")
                    break
            except socket.timeout:
                continue


    def start(self, host, port):
        self.bind((host, port))
        print(f'Server is up and listing on the port {port}...')
        self.listen()
        try:
            self.client, self.address = self.accept()
            print("Connected to SquidStat!")
        except:
            print("Failed to connect SquidStat")
            raise
    

class SocketClient(socket):
    def __init__(self, host, port):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.server = None
        self.connect(host=host, port=port)

if __name__ == "__main__":
    HOST = "169.254.230.44"  # Standard loopback interface address (localhost)
    PORT = 24  # Port to listen on (non-privileged ports are > 1023)
    s = SocketServer(host=HOST, port=PORT)
