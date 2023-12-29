import os
import json
import shutil
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

    def __init__(self, name, execution_mode="python", config=None):
        super().__init__()
        self.name = name
        self.scp = None
        self.logger = None
        self.work_dir = LOCAL_SCRIPTS_DIR
        self.remote_root_dir = REMOTE_SCRIPTS_DIR
        self.mode = execution_mode
        if config:
            self._hostname = config["ip"]
            self._ssh_key_path = config["ssh_key"]
            self._port = config["port"]
            self._username = config["username"]
            self._passphrase = config["passphrase"]

    def create_logger(self, jobname, append=False, simple_fmt=True):
        self.logger = create_logger(
            logger_name=jobname,
            log_path=os.path.join(self.work_dir, jobname+".log"),
            append=append,
            simple_fmt=simple_fmt
        )


    def connect(self):
        """Override the `connect` method in original `SSHClient` class.
        """
        self.set_missing_host_key_policy(paramiko.client.WarningPolicy)
        try:
            super().connect(
                hostname=self._hostname,
                port=self._port,
                username=self._username, 
                passphrase=self._passphrase, 
                key_filename=self._ssh_key_path
            )
        except:
            raise
        else:
            self.work_dir = '/data/user_storage/'


    def transfer(self, path_from=None, path_to=None, mode="put"):
        """Upload a script to the Robot from a local path.
        """
        assert path_from is not None, "Provide file path to transfer from"
        assert path_to is not None, "Provide file path to transfer to"

        if mode == "local":
            shutil.copy2(path_from, path_to)
        elif mode == "put":
            self.scp = SCPClient(self.get_transport())
            self.scp.put(path_from, remote_path=path_to, recursive=True)
        elif mode == "get":
            self.scp = SCPClient(self.get_transport())
            self.scp.get(path_from, local_path=path_to, recursive=True)
        else:
            print("mode must be one of: 'local', 'upload' or 'download'")
            raise


    def put(self, 
            folder:str, 
            local_path:str=None, 
            remote_path:str=None, 
            modules:list=["ot2.py", "robots.py", "sockets.py"]
        ) -> None:
        """ A wrapper of `transfer` method to upload experiment folder to remote station.
        It first copies modules (e.g. robots.py, ot2.py, etc.) to the experiment folder which is 
        then uploaded to remote station. This step is not necessary for stations that are capable 
        of installing this package. But for stations such as Opentron where 'pip' installation of 
        local package is not allowed, this step helps update the working folder with latest module.

        Parameters
        ----------
        folder : str
            The the name of the eperiment folder to run on remote station.
        local_path : str
            The path to `folder`.
        remote_path : str
            The path to `folder` on the remote station
        modules : list[str]
            A list of modules (or module files) to be put to the experiment folder on the remote
        station. This ensures the experiment imports the latest module. By default it contains the
        following files: `ot2.py`, `robots.py` and `sockets.py`.
        
        """
        # Define path to the experiment folder to be put to the remote station
        if local_path is None:
            local_path = LOCAL_SCRIPTS_DIR
        if remote_path is None:
            remote_path = self.remote_root_dir
        local_experiment = os.path.join(local_path, folder)
        remote_experiment = os.path.join(remote_path, folder)

        # put experiment folder to remote station
        self.transfer(path_from=local_experiment, path_to=remote_path, mode="put")
        
        # put latest modules to experiment folder on the remote station
        for module in modules:
            self.transfer( 
                path_from=os.path.join(PACKAGE_DIR, module), 
                path_to=remote_experiment, 
                mode="put"
            )

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
    print(PACKAGE_DIR)
    print(ROOT_DIR)
    print(LOCAL_SCRIPTS_DIR)