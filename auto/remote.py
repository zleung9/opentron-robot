import os
import subprocess
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

    def __init__(self, name, execution_mode="python", config=None, log=False, experiment_path=None):
        super().__init__()
        self.name = name
        self.scp = None
        self.logger = None
        self.local_root_dir = LOCAL_SCRIPTS_DIR
        self.remote_root_dir = REMOTE_SCRIPTS_DIR
        self.local_experiment_path = experiment_path
        self.experiment_name = os.path.basename(experiment_path)
        self.remote_xperiment_path = os.path.join(self.remote_root_dir, self.experiment_name)
        self.mode = execution_mode
        self._start_time = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        self._end_time = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        self._ssh_key_path = os.environ.get("SSH_OT2_SDWF")
        assert self._ssh_key_path, \
            "Please set environment variable 'SSH_OT2_SDWF'. Examples: \n" \
            "Windows: set SSH_OT2_SDWF=C:\\\\Your\\\\path\\\\to\\\\ot2_ssh_key \n" \
            "Mac/Unix: export SSH_OT2_SDWF=/your/path/to/ot2_ssh_key\n"
        assert os.path.isfile(self._ssh_key_path), f"File doesn't exist: {self._ssh_key_path}"

        if config:
            self._hostname = config["ip"]
            self._port = config["port"]
            self._username = config["username"]
            self._passphrase = config["passphrase"]
        if log:
            self.create_logger("experiment")

    @property
    def work_dir(self):
        return self.remote_xperiment_path
    
    def create_logger(self, jobname, append=False, simple_fmt=True):
        self.logger = create_logger(
            logger_name=jobname,
            log_path=os.path.join(self.remote_xperiment_path, jobname+".log"),
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
            self.remote_xperiment_path = self.remote_root_dir + self.experiment_name + "/"
            # Do not use "os.path.join" because the remote path is in linux format

    def disconnect(self):
        """Close the connection to the remote station.
        """
        self.remote_xperiment_path = os.path.join(self.local_root_dir, self.experiment_name)
        self.close()
        

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
            local_path:str=None, 
            remote_path:str=None, 
            modules:list=["ot2.py", "robots.py", "sockets.py", "pump_raspi"]
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
            local_path = self.local_experiment_path
        if remote_path is None:
            remote_path = self.remote_root_dir
        experiment_name = os.path.basename(local_path)
        remote_experiment = os.path.join(remote_path, experiment_name)

        # put experiment folder to remote station
        self.transfer(path_from=local_path, path_to=remote_path, mode="put")
        
        # put latest modules to experiment folder on the remote station
        for module in modules:
            self.transfer( 
                path_from=os.path.join(PACKAGE_DIR, module), 
                path_to=remote_experiment, 
                mode="put"
            )
        

    def download_data(self, 
            data_files:list=["experiment.csv", "metadata.json", "experiment.log"],
            local_path:str=None, 
            remote_path:str=None
        ) -> None:
        """ A wrapper of `transfer` method to upload experiment folder to remote station.
        It first copies modules (e.g. robots.py, ot2.py, etc.) to the experiment folder which is 
        then uploaded to remote station. This step is not necessary for stations that are capable 
        of installing this package. But for stations such as Opentron where 'pip' installation of 
        local package is not allowed, this step helps update the working folder with latest module.

        Parameters
        ----------
        data_files : list
            A list of the name of the eperiment data to download from remote station. 
            Each file usually takes the form of "experiment_folder/data_file.csv"
        local_path : str
            The path to `folder`.
        remote_path : str
            The path to `folder` on the remote station.
        
        """
        # Define path to the experiment folder to be put to the remote station
        if local_path is None:
            local_path = self.local_experiment_path
        if remote_path is None:
            remote_path = self.remote_root_dir
        
        for f in data_files:
            local_file = os.path.join(local_path, f)
            remote_file = self.remote_xperiment_path + f
            # Do not use "os.path.join" because the remote path is in linux format
            
            # put experiment folder to remote station
            try:
                self.transfer(path_from=remote_file, path_to=local_file, mode="get")
            except FileNotFoundError:
                print(f"File {f} doesn't exist on remote station.")
                print(f"Please check the folder name and try again.")
                raise
            else:
                print(f"File {remote_file} downloaded as {local_file}.")


    def execute(self, filename:str, log:bool=False, mode:str="") -> None:
        """Let the Robot execute a script stored on it.
        Parameters
        ----------
        filename : str
            The (python) filename to be executed. The file resides in `self.remote_xperiment_path`.
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
        self._start_time = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
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
                f"cd {self.remote_xperiment_path}; pwd; export RUNNING_ON_PI=1; {' '.join(command)}", 
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
        finally:
            self._end_time = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            if log:
                self.logger.info(f"Execution started at {self._start_time} and ended at {self._end_time}.")
                self.export_metadata()

    def export_metadata(self, comment:str="") -> dict:
        """Export metadata to a json file."""
        # Add date time to the experiment file
        output_csv = f"experiment_{datetime.today().strftime('%Y-%m-%d')}.csv"
        output_log = f"experiment_{datetime.today().strftime('%Y-%m-%d')}.log"
        metadata_path = os.path.join(self.local_experiment_path, "metadata.json")

        shutil.copy2(
            os.path.join(self.remote_xperiment_path, "experiment.csv"), 
            os.path.join(self.remote_xperiment_path, output_csv)
        )
        shutil.copy2(
            os.path.join(self.remote_xperiment_path, "experiment.log"), 
            os.path.join(self.remote_xperiment_path, output_log)
        )

        metadata = {
            "created_by": self.name,
            "start_time": self._start_time,
            "end_time": self._end_time,
            "associated_log": output_log,
            "associated_csv": output_csv,
            "comments": comment
        }
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)
        
        return metadata


if __name__ == "__main__":
    print(PACKAGE_DIR)
    print(ROOT_DIR)
    print(LOCAL_SCRIPTS_DIR)