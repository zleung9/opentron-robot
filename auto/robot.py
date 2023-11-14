import os
import paramiko
from paramiko import SSHClient
from scp import SCPClient

PACKAGE_DIR = __package__

class Robot(SSHClient):

    def __init__(self):
        super().__init__()
        self.hostname = None
        self.scp = None

    def connect(self, hostname=None, key_path=None, username="root", passphrase=""):
        self.hostname = hostname
        self.set_missing_host_key_policy(paramiko.client.WarningPolicy)
        self.connect(
            hostname=hostname, 
            username=username, 
            passphrase=passphrase, 
            key_filename=key_path
        )
    
    def fetch(self, local_path=None, remote_path='/data/user_storage'):
        self.scp = SCPClient(self.get_transport())
        self.scp.put(local_path, remote_path=remote_path)


if __name__ == "__main__":
    print(__file__)
    