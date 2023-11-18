import os
import subprocess
import paramiko
from paramiko import SSHClient
from scp import SCPClient
from auto.utils.logger import create_logger

PACKAGE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(PACKAGE_DIR)
LOCAL_SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")


class Robot(SSHClient):


    def __init__(self, name):
        super().__init__()
        self.name = name
        self.hostname = None
        self.scp = None
        self.logger = None
        self.local = True # by default this Robot is local
        self.work_dir = LOCAL_SCRIPTS_DIR


    def create_logger(self, jobname, append=False, simple_fmt=True):
        self.logger = create_logger(
            logger_name=jobname,
            log_path=os.path.join(self.work_dir, jobname+".log"),
            append=append,
            simple_fmt=simple_fmt
        )


    def connect(self, hostname=None, key_path=None, username="root", passphrase=""):
        """Override the `connect` method in original `SSHClient` class.
        """
        self.hostname = hostname
        self.set_missing_host_key_policy(paramiko.client.WarningPolicy)
        try:
            super().connect(
                hostname=hostname, 
                username=username, 
                passphrase=passphrase, 
                key_filename=key_path
            )
        except:
            raise
        else:
            self.work_dir = '/data/user_storage/'
            self.local = False # now it is a remote Robot


    def transfer(self, filename, local_path=None, remote_path=None, mode="upload"):
        """Upload a script to the Robot from a local path.
        """
        assert mode in ["upload", "download"], "mode must be 'upload' or 'download'"
        if local_path is None:
            local_path = LOCAL_SCRIPTS_DIR
        if remote_path is None:
            remote_path = self.work_dir
        self.scp = SCPClient(self.get_transport())
        if mode == "upload":
            self.scp.put(
                os.path.join(local_path, filename), 
                remote_path=remote_path
            )
        else:
            self.scp.get(
                os.path.join(remote_path, filename),
                local_path=local_path
            )


    def upload(self, filename, local_path=None, remote_path=None):
        self.transfer(filename, local_path=local_path, remote_path=remote_path, mode="upload")
    
    
    def download(self, filename, local_path=None, remote_path=None):
        self.transfer(filename, local_path=local_path, remote_path=remote_path, mode="download")


    def execute(self, filename, log=True, mode="python"):
        """Let the Robot execute a script stored on it.
        """
        # pre-execution logging
        if log: 
            try:
                assert self.logger is not None, "Logger doesn't exist, log is muted."
                self.logger.info(f'Executing {filename}')
            except AssertionError:
                log = False
        
        script_path = os.path.join(self.work_dir, filename)
        
        # define the command according to mode (python, shell, or ot2, etc.)
        if mode == "python":
            command = ["python", script_path]
        elif mode == "shell":
            command = ["bash", script_path]
        elif mode == "ot2":
            command = ["opentrons_execute", script_path]
        
        # Execution
        if self.local: # run the script locally without connection to remote computer
            result = subprocess.run(
                command,
                capture_output=True, # capture stdout and stderr
                text=True, # capture output as str instead of bytes
            )
            stdout = result.stdout
            stderr = result.stderr
        else: # run script on a remote computer through ssh connection
            _ = self.exec_command("export RUNNING_ON_PI=1", get_pty=True)
            stdin, stdout, stderr = self.exec_command(" ".join(command), get_pty=True)
            # stdout = stdout.read().decode() # read text from ChannelFile object
            # stderr = stderr.read().decode() # read text from ChannelFile object
        
        # post-execution logging
        if log:
            for line in stdout.split("\n"):
                self.logger.info(line.rstrip())
            for line in stderr.split("\n"):
                self.logger.info("ERR>"+line.rstrip())

        # need to return output to be used as input for succeeding scripts
        return stdin, stdout, stderr 


if __name__ == "__main__":
    print(__file__)
    pass