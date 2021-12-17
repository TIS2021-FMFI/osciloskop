from backend.adapter import Adapter
from backend.measurement import *
from abc import ABC, abstractmethod


class CommandError(Exception):
    pass

class Command(ABC):
    timeout = 5

    @staticmethod
    @abstractmethod
    def do():
        pass

    @staticmethod
    @classmethod
    def get_set_value():
        pass

    def check_and_do(self):
        self.check()
        self.do()


class ConnectCmd(Command):
    def __init__(self, address):
        self.address = address

    def do(self):
        adapter.connect(self.address)

    def check(self):
        if self.address not in [str(i) for i in range(1, 32)]:
            raise CommandError(f"'{self.address}' is not a valid address")


class DisconnectCmd(Command):
    def do(self):
        adapter.disconnect()


class EnterCmdModeCmd(Command):
    def do(self):
        adapter.enter_cmd_mode()


class LeaveCmdModeCmd(Command):
    def do(self):
        adapter.exit_cmd_mode()


class CustomCmd(Command):
    def __init__(self, cmd):
        self.cmd = cmd

    def do(self):
        """
        sends a command
        """
        return adapter.send([self.cmd])


class CustomCmdWithOutput(Command):
    def __init__(self, cmd):
        self.cmd = cmd

    def do(self):
        """
        sends one command and returns output from hpctrl
        """
        return adapter.send_and_get_output([self.cmd], self.timeout)


class FileCmd(Command):
    def __init__(self, path):
        self.path = path

    def do(self):
        """
        sets path where the measured data should be stored
        """
        adapter.send(f"file {self.path}")


class PointsCmd(Command):
    def __init__(self, points=None):
        self.points = points

    def do(self):
        adapter.send(f"s: ACQUIRE:POINTS {self.points}")

    def check(self):
        if self.points not in [str(i) for i in range(16, 4097)] and self.points.lower() != "auto":
            raise CommandError(f"{self.points} is not a valid value")

    def get_set_value(self):
        return adapter.send_and_get_output(["q: ACQUIRE:POINTS?"], self.timeout)


class AverageNoCmd(Command):
    def __init__(self, count=None):
        self.count = count

    def do(self):
        adapter.send(f"s: ACQUIRE:count {self.count}")

    def check(self):
        if self.count not in [str(i) for i in range(1, 4097)]:
            raise CommandError(f"{self.count} is not a valid value")

    def get_set_value(self):
        return adapter.send_and_get_output(["q: ACQUIRE:count?"], self.timeout)


class AverageCmd(Command):
    def __init__(self, turn_on=None):
        self.turn_on = turn_on

    def do(self):
        if self.turn_on:
            adapter.send("s :acquire:average on")
        else:
            adapter.send("s :acquire:average off")


    def get_set_value(self):
        return adapter.send_and_get_output(["q :ACQUIRE:average?"], self.timeout) == "ON"


class ExitHpctrlCmd(Command):
    def do(self):
        adapter.kill_hpctrl()


class CheckIfResponsiveCmd(Command):
    def do(self):
        """
        do method returns true if hpctrl responds to q *IDN?
        """
        return adapter.is_osci_responsive()


class GetPreambleCmd(Command):
    def do(self):
        """
        do method returns preamble data
        """
        return adapter.send_and_get_output(["q :WAVEFORM:PREAMBLE?"], self.timeout)


class FactoryResetCmd(Command):
    def do(self):
        adapter.send("s *RST")


class TurnOnRunModeCmd(Command):
    def do(self):
        adapter.send("s run")


class SetFormatToWordCmd(Command):
    def do(self):
        adapter.send("s :waveform:format word")


class PreampleOnCmd(Command):
    def do(self):
        adapter.send("pon")


class PreambleOffCmd(Command):
    def do(self):
        adapter.send("poff")


class StartDataAcquisitionCmd(Command):
    def do(self):
        adapter.send("*")


class StopDataAcquisitionCmd(Command):
    def do(self):
        adapter.send("?")


class Invoker:
    
    def start_run_cmds(self, file_to_store_data_from_hpctrl, channels):
        LeaveCmdModeCmd().do()
        FileCmd(file_to_store_data_from_hpctrl).do()
        EnterCmdModeCmd().do()
        adapter.send(channels_to_string(channels))
        StartDataAcquisitionCmd().do()
        
    def stop_run_cmds(self, file_with_data, folder_to_store_measurements, channels, is_preamble):
        StopDataAcquisitionCmd().do()
        chans = channels_to_string(channels)
        if is_preamble:
            MultipleMeasurementsWithPreambles(file_with_data, chans).save_to_disk(
                folder_to_store_measurements
            )
        else:
            preamble = GetPreambleCmd().do()
            MultipleMeasurementsNoPreambles(file_with_data, preamble, chans).save_to_disk(
                folder_to_store_measurements
            )
            
    def single_cmds(self, channels, path):
        measurements = []
        adapter.send("s single")
        for i in channels_to_string(channels):
            adapter.send(f"s :waveform:source channel{i}")
            adapter.send("s :waveform:data?")
            data = adapter.send_and_get_output("16", timeout=5)
            preamble = GetPreambleCmd().do()
            measurements.append(Measurement(preamble, data, i))
        SingleMeasurements(measurements).save_to_disk(path)
        
    def initialize_cmds(self, address):
        ConnectCmd(address).check_and_do()
        EnterCmdModeCmd().do()
        SetFormatToWordCmd().do()
        TurnOnRunModeCmd().do()
        PreambleOffCmd().do()


def channels_to_string(channels):
    return "".join(ch[2:] for ch in channels)


adapter = Adapter(testing=True)
adapter.start_hpctrl()
