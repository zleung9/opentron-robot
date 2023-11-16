import os
import paramiko
from paramiko import SSHClient
from scp import SCPClient
from auto.utils.logger import create_logger

PACKAGE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(PACKAGE_DIR)
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")


class Robot(SSHClient):


    def __init__(self, name, root_dir="/data/user_storage", connect=False):
        super().__init__()
        self.root_dir = root_dir
        self.name = name
        self.hostname = None
        self.scp = None
        self.logger = None


    def create_logger(self, jobname, jobdir, append=False, simple_fmt=True):
        self.logger = create_logger(
            logger_name=jobname,
            log_path=os.path.join(jobdir, jobname+".log"),
            append=append,
            simple_fmt=simple_fmt
        )


    def connect(self, hostname=None, key_path=None, username="root", passphrase=""):
        """Override the `connect` method in original `SSHClient` class.
        """
        self.hostname = hostname
        self.set_missing_host_key_policy(paramiko.client.WarningPolicy)
        super().connect(
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
        # pre-execution logging
        if log: 
            try:
                assert self.logger is not None, "Logger doesn't exist, log is muted."
                self.logger.info(f'Executing {os.path.basename(script_path)}')
            except AssertionError:
                log = False
        # Execution
        _ = self.exec_command("export RUNNING_ON_PI=1", get_pty=True)
        _, stdout, stderr = self.exec_command(f"python {script_path}", get_pty=True)
        # post-execution logging
        if log:
            for line in stdout:
                self.logger.info(line.rstrip())
            for line in stderr:
                self.logger.info("ERR>"+line.rstrip())
        # need to return output to be used as input for succeeding scripts
        return stdout, stderr 


if __name__ == "__main__":
    print(__file__)
    pass