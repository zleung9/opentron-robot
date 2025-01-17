import sys
from PySide2.QtCore import QIODevice, QThread, QObject, Signal
from PySide2.QtSerialPort import QSerialPort
from PySide2.QtWidgets import QApplication
from SquidstatPyLibrary import AisDeviceTracker
from SquidstatPyLibrary import AisCompRange
from SquidstatPyLibrary import AisDCData
from SquidstatPyLibrary import AisACData
from SquidstatPyLibrary import AisExperimentNode
from SquidstatPyLibrary import AisErrorCode
from SquidstatPyLibrary import AisExperiment
from SquidstatPyLibrary import AisInstrumentHandler
from SquidstatPyLibrary import AisCyclicVoltammetryElement


app = QApplication([])


def convert_to_csv_line(data_list):
    return ','.join(str(item) for item in data_list) 


class SerialPortReader(QObject):
    dataReceived = Signal(str)

    def __init__(self, port):
        super().__init__()
        self.port = port

    def run(self):
        if not self.port.isOpen():
            self.port.open(QIODevice.ReadOnly)
        while self.port.isOpen():
            if self.port.waitForReadyRead():
                data = self.port.readAll().data().decode()
                self.dataReceived.emit(data)

    def writeData(self, data):
        if not self.port.isOpen():
            self.port.open(QIODevice.WriteOnly)
        self.port.write(data.encode())

    def closePort(self):
        if self.port.isOpen():
            self.port.close()

class ExperimentManager:
    def __init__(self, total_channels):
        self.total_channels = total_channels
        self.running_channels = set()

    def start_experiment(self, channel):
        if channel not in self.running_channels and 0 <= channel < self.total_channels:
            self.running_channels.add(channel)
            return True
        return False  # Experiment already running or invalid channel

    def complete_experiment(self, channel):
        if channel in self.running_channels:
            self.running_channels.remove(channel)

    def is_experiment_running(self, channel):
        return channel in self.running_channels

    def get_running_channels(self):
        return list(self.running_channels)



class WriteCSV:
    def __init__(self, filename):
        self.filename = filename
        self.file = None

    def write_header(self, header):
        if self.file is None:
            self.file = open(self.filename, 'w')
        self.file.write(convert_to_csv_line(header) + '\n')

    def write_data(self, data):
        if self.file is not None:
            self.file.write(convert_to_csv_line(data) + '\n')

    def close(self):
        if self.file is not None:
            self.file.close()


class WriterThread(QThread):
    plotData = Signal(int, float, float, float)
    stopToPlot = Signal(int)

    def __init__(self, numberOfchannel, experiment_manager):
        super().__init__()
        self.timestamps = []
        self.voltages = []
        self.currents = []
        self.experiment_manager = experiment_manager
        self.csv_writers = [WriteCSV(f'dataFile_channel{channel}.csv') for channel in range(numberOfchannel)]

    def run(self):
        for csv_writer in self.csv_writers:
            csv_writer.write_header(['Timestamp', 'Working Electrode Voltage', 'Current'])
        self.plotData.connect(self.add_data)
        self.stopToPlot.connect(self.close)

    def add_data(self,channel, timestamp, voltage, current):
        self.timestamps.append(timestamp)
        self.voltages.append(voltage)
        self.currents.append(current)
        self.csv_writers[channel].write_data([timestamp, voltage, current])

    def close(self, channel):
        self.csv_writers[channel].close()
        self.experiment_manager.complete_experiment(channel)
        
        # Check if there are no running channels left
        if len(self.experiment_manager.get_running_channels()) == 0:
            app.quit() 



tracker = AisDeviceTracker.Instance()


def onNewDeviceConnected(deviceName):
    print("Device is Connected: %s" % deviceName)
    handler = tracker.getInstrumentHandler(deviceName)
    if handler:
    
        # Initialize ExperimentManager with total number of channels
        experiment_manager = ExperimentManager(total_channels=handler.getNumberOfChannels())
    
        writerThread = WriterThread(handler.getNumberOfChannels(), experiment_manager)
        writerThread.start()

        

        handler.activeDCDataReady.connect(lambda channel, data: (
            print("timestamp:", "{:.9f}".format(data.timestamp), "workingElectrodeVoltage: ",
                  "{:.9f}".format(data.workingElectrodeVoltage), "current: ", "{:.9f}".format(data.current)),
            writerThread.plotData.emit(channel, data.timestamp, data.workingElectrodeVoltage, data.current)
        ))
        ### To define AC exp result data format 
        # handler.activeACDataReady.connect(lambda channel, data: print("frequency:", "{:.9f}".format(data.frequency),
        #                                                               "absoluteImpedance: ", "{:.9f}".format(
        #                                                                   data.absoluteImpedance), "phaseAngle: ",
        #                                                               "{:.9f}".format(data.phaseAngle)))
        handler.experimentNewElementStarting.connect(lambda channel, data: print("start step ", data.stepName))
        handler.experimentStopped.connect(lambda channel: (print("Experiment Completed: %d" % channel),
                                                           writerThread.stopToPlot.emit(channel),
                                                           handler.startIdleSampling(channel)))

        experiment = AisExperiment()

        CvElement = AisCyclicVoltammetryElement(0.0,2.5,5.2,3.0,0.0005,1.0)
        CvElement.setStartVoltage(0) # V
        CvElement.setFirstVoltageLimit(2.5) # V
        CvElement.setSecondVoltageLimit(5.2) # V
        CvElement.setEndVoltage(3) # V
        CvElement.setdEdt(0.1)#(0.0005) # V/s
        CvElement.setSamplingInterval(1) # s
        CvElement.setApproxMaxCurrent(0.01) # A
        CvElement.setNumberOfCycles(1)
        CvElement.setStartVoltageVsOCP(True)
        CvElement.setFirstVoltageLimitVsOCP(False)
        CvElement.setSecondVoltageLimitVsOCP(False)
        CvElement.setEndVoltageVsOCP(False)

        print(CvElement.getName())
        print(CvElement.getStartVoltage(), 'V start')
        print(CvElement.getFirstVoltageLimit(), 'V first')
        print(CvElement.getSecondVoltageLimit(), 'V second')
        print(CvElement.getEndVoltage(), ' V end')
        print(CvElement.getNumberOfCycles(), ' cycles')
        print(CvElement.getdEdt(), 'V/s')
        print(CvElement.getSamplingInterval(), 's')
        print(CvElement.getApproxMaxCurrent(), 'A')
        print(CvElement.isStartVoltageVsOCP(), ' Start Voltage vs OCP')
        print(CvElement.isFirstVoltageLimitVsOCP(), ' First Voltage vs OCP')
        print(CvElement.isSecondVoltageLimitVsOCP(), ' Second Voltage vs OCP')
        print(CvElement.isEndVoltageVsOCP(), ' End Voltage vs OCP')

        #experiment.appendElement(ccElement, 1)
        experiment.appendElement(CvElement, 1)

        error = handler.uploadExperimentToChannel(0, experiment)
        if error.value() != AisErrorCode.ErrorCode.Success:
            print(error.message())
            return	
            
        
        error = handler.uploadExperimentToChannel(1, experiment)
        if error.value() != AisErrorCode.ErrorCode.Success:
            print(error.message())
            return	
            
			
        error = handler.uploadExperimentToChannel(2, experiment)
        if error.value() != AisErrorCode.ErrorCode.Success:
            print(error.message())
            return	
            
			
        error = handler.uploadExperimentToChannel(3, experiment)
        if error.value() != AisErrorCode.ErrorCode.Success:
            print(error.message())
            return	
                    
        error_value = handler.startUploadedExperiment(0).value()
        if error_value != AisErrorCode.ErrorCode.Success:
            print("Experiment is not started on channel 1 because: " + error.message())
            return
            
        experiment_manager.start_experiment(0)    
        
        error_value |= handler.startUploadedExperiment(1).value()
        if error_value != AisErrorCode.ErrorCode.Success:
            print("Experiment is not started on channel 1 because: " + error.message())
            return
            
        experiment_manager.start_experiment(1) 
        
        error_value |= handler.startUploadedExperiment(2).value()
        if error_value != AisErrorCode.ErrorCode.Success:
            print("Experiment is not started on channel 1 because: " + error.message())
            return
            
        experiment_manager.start_experiment(2)     
        
        error_value |= handler.startUploadedExperiment(3).value()
        if error_value != AisErrorCode.ErrorCode.Success:
            print("Experiment is not started on channel 1 because: " + error.message())
            return
        experiment_manager.start_experiment(3) 

tracker.newDeviceConnected.connect(onNewDeviceConnected)

error = tracker.connectToDeviceOnComPort("COM3")
if error.value() != AisErrorCode.ErrorCode.Success:
    print(error.message())

sys.exit(app.exec_())