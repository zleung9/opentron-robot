from socket import socket
from _thread import start_new_thread
from threading import Thread
import sys
from time import sleep


host = '127.0.0.1'
port = 1233
ThreadCount = 0


class SocketThread(Thread):
    """ A customized thread that runs a server that listen on clients. 
    Reference:
    https://alexandra-zaharia.github.io/posts/how-to-return-a-result-from-a-python-thread/
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = "" # Empty by default.
        self.server = None # Server is not setup yet
        self.client_list = [] # No clients connected by default
        self.host = "169.254.230.44"
        self.port = 24

    def run(self):
        """Overwride the run() method by storing the result of the target in the result member
        """
        if self._target is None:
            self.result = self.start_server() # not target function, directly start the server
        try:
            self.result = self._target(*self._args, **self._kwargs)
        except Exception as exc:
            print(f'{type(exc).__name__}: {exc}', file=sys.stderr)  # properly handle the exception
        

    def join(self, *args, **kwargs):
        """Override the join() method such as to return the result member
        """
        super().join(*args, **kwargs)
        return self.result
    

    def client_handler(self, connection):
        connection.send(str.encode('You are now connected to the replay server... Type BYE to stop'))
        while True:
            data = connection.recv(2048)
            self.result = data.decode('utf-8')
            if self.result == 'BYE':
                break
            reply = f'Server: {self.result}'
            connection.sendall(str.encode(reply))
        connection.close()
        self.client_list.remove(connection)


    def accept_connections(self):
        client, address = self.server.accept()
        print('Connected to: ' + address[0] + ':' + str(address[1]))
        start_new_thread(self.client_handler, (client, ))
        self.client_list.append(client)

    def start_server(self):
        host = self.host
        port = self.port
        self.server = socket()
        try:
            self.server.bind((host, port))
        except socket.error as e:
            print(str(e))
        print(f'Server is up and listing on the port {port}...')
        self.server.listen()

        while True:
            self.accept_connections()



class ReturnValueThread(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = None

    def run(self):
        if self._target is None:
            return  # could alternatively raise an exception, depends on the use case
        try:
            self.result = self._target(*self._args, **self._kwargs)
        except Exception as exc:
            print(f'{type(exc).__name__}: {exc}', file=sys.stderr)  # properly handle the exception

    def join(self, *args, **kwargs):
        super().join(*args, **kwargs)
        return self.result


if __name__ == "__main__":
    thread = SocketThread()
    thread.host = "169.254.230.44"
    thread.port = 24
    while True:
        print(thread.result)
        sleep(3)
        if thread.result == "BYE":
            break
    print("Finally stopped!")

