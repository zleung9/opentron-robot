import os
from datetime import datetime
import paramiko
from paramiko import SSHClient
from scp import SCPClient
from auto.utils.logger import create_logger

PACKAGE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(PACKAGE_DIR)
LOCAL_SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
REMOTE_SCRIPTS_DIR = '/data/user_storage/'

class RemoteStation(SSHClient):
    """The class handles the communication between the centralized control computer and remote 
    computers such as Opentrons, Chemspeed or any other computer. 
    It can perform a variety of operations through SSH, operations such as remote command execution, 
    file/data transfer, data retrieval and management.
    The purpose of this class is to enable convenient design of automated experiment involving
    different computers and devices.
    """

    def __init__(self, name, execution_mode="python"):
        super().__init__()
        self.name = name
        self.hostname = None
        self.scp = None
        self.logger = None
        self.work_dir = LOCAL_SCRIPTS_DIR
        self.remote_root_dir = REMOTE_SCRIPTS_DIR
        self.mode = execution_mode

    def create_logger(self, jobname, append=False, simple_fmt=True):
        self.logger = create_logger(
            logger_name=jobname,
            log_path=os.path.join(self.work_dir, jobname+".log"),
            append=append,
            simple_fmt=simple_fmt
        )


    def connect(self, hostname=None, port=22, key_path=None, username="root", passphrase=""):
        """Override the `connect` method in original `SSHClient` class.
        """
        self.hostname = hostname
        self.set_missing_host_key_policy(paramiko.client.WarningPolicy)
        try:
            super().connect(
                hostname=hostname,
                port=port,
                username=username, 
                passphrase=passphrase, 
                key_filename=key_path
            )
        except:
            raise
        else:
            self.work_dir = '/data/user_storage/'


    def transfer(self, filename, local_path=None, remote_path=None, mode="upload"):
        """Upload a script to the Robot from a local path.
        """
        assert mode in ["upload", "download"], "mode must be 'upload' or 'download'"
        if local_path is None:
            local_path = LOCAL_SCRIPTS_DIR
        if remote_path is None:
            remote_path = self.remote_root_dir
        self.scp = SCPClient(self.get_transport())
        if mode == "upload":
            self.scp.put(
                os.path.join(local_path, filename), 
                remote_path=remote_path,
                recursive=True
            )
        else:
            self.scp.get(
                os.path.join(remote_path, filename),
                local_path=local_path,
                recursive=True
            )


    def load(self, filenames, local_path=None, remote_path=None):
        for filename in filenames:
            self.transfer(filename, local_path=local_path, remote_path=remote_path, mode="upload")


    def execute(self, filename:str, log:bool=False, mode:str="") -> None:
        """Let the Robot execute a script stored on it.
        Parameters
        ----------
        filename : str
            The (python) filename to be executed. The file resides in `self.work_dir`.
        log : bool
            If `True` write the output/error messages into the log file also. Default `False`.
        mode : str
            The type of command to execute. There are a few options:
                "python": python script
                "shell": linux shell command
                "ot2": ot2 script (which is written in python)
        
        Returns
        -------
        stdout : Standard output of the script.
        stderr : Standard error message of the script.

        """
        # pre-execution logging
        if log: 
            try:
                assert self.logger is not None, "Logger doesn't exist, log is muted."
                self.logger.info(f'Executing {filename}')
            except AssertionError:
                log = False
        
        # define the command according to mode (python, shell, or ot2, etc.)
        if mode == "":
            mode = self.mode
        if mode == "python":
            command = ["python", filename]
        elif mode == "shell":
            command = ["bash", filename]
        elif mode == "ot2":
            command = ["opentrons_execute", filename]
        # Execution
        try:
            stdin, stdout, stderr = self.exec_command( 
                f"cd {self.work_dir}; pwd; export RUNNING_ON_PI=1; {' '.join(command)}", 
                get_pty=True
            ) # Donot omit "stdin" and "stderr", otherwise "stdout" will not be displayed.
            
            # post-execution logging
            for line in stdout:
                print(line.rstrip())
                if log:
                    self.logger.info(line.rstrip())

        except KeyboardInterrupt as e:
            print(f"Interruption detedted: {datetime.today()}")
            self.exec_command("\x03")
            self.close()
            print(f"Interrupted: {datetime.today()}")

if __name__ == "__main__":
    print(__file__)
    pass