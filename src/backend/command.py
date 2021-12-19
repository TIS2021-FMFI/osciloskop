from backend.adapter import Adapter
from backend.measurement import *
from abc import ABC, abstractmethod


class CommandError(Exception):
    pass

class Command(ABC):

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
       
    @staticmethod
    def send_cmd(command):
        adapter.send(command)
    
    @staticmethod
    def send_cmd_with_output(command, timeout=5):
        return adapter.send_and_get_output(command, timeout)


class ConnectCmd(Command):
    def __init__(self, address):
        self.address = address

    def do(self):
        adapter.connect(self.address)

    def check(self):
        if self.address not in [str(i) for i in range(1, 32)]:
            raise CommandError(f"'{self.address}' is not in range 1-31")


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
        return self.send_cmd(self.cmd)


class CustomCmdWithOutput(Command):
    def __init__(self, cmd):
        self.cmd = cmd

    def do(self):
        """
        sends one command and returns output from hpctrl
        """
        return self.send_cmd_with_output(self.cmd)


class FileCmd(Command):
    def __init__(self, path):
        self.path = path

    def do(self):
        """
        sets path where the measured data should be stored
        """
        self.send_cmd(f"file {self.path}")


class PointsCmd(Command):
    def __init__(self, points=None):
        self.points = points

    def do(self):
        self.send_cmd(f"s: ACQUIRE:POINTS {self.points}")

    def check(self):
        if self.points not in [str(i) for i in range(16, 4097)] and self.points.lower() != "auto":
            raise CommandError(f"{self.points} is not in range 16-4096")

    def get_set_value(self):
        return self.send_cmd_with_output("q :ACQUIRE:POINTS?")


class AverageNoCmd(Command):
    def __init__(self, count=None):
        self.count = count

    def do(self):
        self.send_cmd(f"s: ACQUIRE:count {self.count}")

    def check(self):
        if self.count not in [str(i) for i in range(1, 4097)]:
            raise CommandError(f"{self.count} is not in range 1-4096")

    def get_set_value(self):
        return self.send_cmd_with_output("q :ACQUIRE:count?")


class AverageCmd(Command):

    def do(self, turn_on):
        if turn_on:
            self.send_cmd("s :acquire:average on")
        else:
            self.send_cmd("s :acquire:average off")

    def get_set_value(self):
        return self.send_cmd_with_output("q :acquire:average?") == "1"


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
        return self.send_cmd_with_output("q :WAVEFORM:PREAMBLE?")


class FactoryResetCmd(Command):
    def do(self):
        self.send_cmd("s *RST")


class TurnOnRunModeCmd(Command):
    def do(self):
        self.send_cmd("s run")


class SetFormatToWordCmd(Command):
    def do(self):
        self.send_cmd("s :waveform:format word")


class PreampleOnCmd(Command):
    def do(self):
        self.send_cmd("pon")


class PreambleOffCmd(Command):
    def do(self):
        self.send_cmd("poff")


class StartDataAcquisitionCmd(Command):
    def do(self):
        self.send_cmd("*")


class StopDataAcquisitionCmd(Command):
    def do(self):
        self.send_cmd("?")

class TurnOnChannel(Command):
    def __init__(self, channel):
        self.channel = channel

    def do(self):
        self.send_cmd(f"s :channel{self.channel}:display on")


class Invoker:

    def start_run_cmds(self, file_to_store_data_from_hpctrl, channels):
        LeaveCmdModeCmd().do()
        FileCmd(file_to_store_data_from_hpctrl).do()
        EnterCmdModeCmd().do()
        CustomCmd(channels_to_string(channels)).do()
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
        os.remove(file_with_data)

    def single_cmds(self, channels, path):
        CustomCmd("s single").do()
        measurements = []
        for i in channels_to_string(channels):
            CustomCmd(f"s :waveform:source channel{i}").do()
            CustomCmd("s :waveform:data?").do()
            data = CustomCmdWithOutput("16").do()
            preamble = GetPreambleCmd().do()
            measurements.append(Measurement(preamble, data, i))
        SingleMeasurements(measurements).save_to_disk(path)
        TurnOnRunModeCmd().do()

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
