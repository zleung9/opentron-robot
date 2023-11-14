import os
import paramiko
from paramiko import SSHClient
from scp import SCPClient
from auto.utils.logger import create_logger

PACKAGE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(PACKAGE_DIR)
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")


class Robot(SSHClient):


    def __init__(self, name, root_dir="/data/user_storage"):
        super().__init__()
        self.root_dir = root_dir
        self.name = name
        self.hostname = None
        self.scp = None
        self.logger = None
        self.connect_raw = self.connect # to override `connect` method


    def create_logger(self, jobname, jobdir, append=False, simple_fmt=True):
            self.logger = create_logger(
                logger_name=jobname,
                log_path=os.path.join(jobdir, jobname+".log"),
                append=append,
                simple_fmt=simple_fmt

            )


    def connect(self, hostname=None, key_path=None, username="root", passphrase=""):
        self.hostname = hostname
        self.set_missing_host_key_policy(paramiko.client.WarningPolicy)
        self.connect_raw(
            hostname=hostname, 
            username=username, 
            passphrase=passphrase, 
            key_filename=key_path
        )
    

    def upload(self, local_path=SCRIPTS_DIR, remote_path='/data/user_storage'):
        """Upload a script to the Robot from a local path.
        """
        self.scp = SCPClient(self.get_transport())
        self.scp.put(local_path, remote_path=remote_path)
    

    def execute(self, script_path, log=True):
        """Let the Robot execute a script stored on it.
        """
        if log: 
             assert self.logger is not None, "Create a logger first!"
        script_name = os.path.basename(script_path)
        # logging 
        if log:
             self.logger.info(f'Executing {script_name}') 
        # Execution
        _ = self.exec_command("export RUNNING_ON_PI=1", get_pty=True)
        _, stdout, stderr = self.exec_command(f"python {script_path}", get_pty=True)
        # logging
        if log:
            for line in stdout:
                self.logger.info(line.rstrip())
            for line in stderr:
                 self.logger.info("ERR>"+line.rstrip())

        return stdout, stderr


if __name__ == "__main__":
    print(__file__)
    pass