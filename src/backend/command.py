from backend.adapter import Adapter
from backend.measurement import (
    Measurement,
    MultipleMeasurementsNoPreambles,
    MultipleMeasurementsWithPreambles,
    SingleMeasurements,
)


class CommandError(Exception):
    pass


class Command:
    adapter = Adapter(testing=True)
    adapter.start_hpctrl()

    def __init__(self):
        pass

    def do(self):
        pass

    def get_set_value(self):
        pass

    def check(self):
        pass

    def check_and_do(self):
        self.check()
        self.do()


class ConnectCmd(Command):
    def __init__(self, address):
        self.address = address

    def do(self):
        self.adapter.connect(self.address)

    def check(self):
        if self.address not in [str(i) for i in range(1, 32)]:
            raise CommandError(f"'{self.address}' is not a valid address")


class DisconnectCmd(Command):
    def do(self):
        self.adapter.disconnect()


class EnterCmdModeCmd(Command):
    def do(self):
        self.adapter.enter_cmd_mode()


class LeaveCmdModeCmd(Command):
    def do(self):
        self.adapter.exit_cmd_mode()


class CustomCmd(Command):
    def __init__(self, cmd):
        self.cmd = cmd

    def do(self):
        """
        sends a command
        """
        return self.adapter.send([self.cmd])


class CustomCmdWithOutput(Command):
    def __init__(self, cmd, timeout=5):
        self.cmd = cmd
        self.timeout = timeout

    def do(self):
        """
        sends one command and returns output from hpctrl
        """
        return self.adapter.send_and_get_output([self.cmd], self.timeout)


class FileCmd(Command):
    def __init__(self, path):
        self.path = path

    def do(self):
        """
        sets path where the measured data should be stored
        """
        CustomCmd(f"file {self.path}").do()


class PointsCmd(Command):
    def __init__(self, points):
        self.points = points

    def do(self):
        CustomCmd(f"s: ACQUIRE:POINTS {self.points}").do()

    def check(self):
        if self.points not in [str(i) for i in range(16, 4097)] and self.points != "auto":
            raise CommandError(f"{self.points} is not a valid value")

    def get_set_value(self):
        return CustomCmdWithOutput(f"q: ACQUIRE:POINTS?").do()


class AvarageNoCmd(Command):
    def __init__(self, count):
        self.count = count

    def do(self):
        CustomCmd(f"s: ACQUIRE:count {self.count}").do()

    def check(self):
        if self.count not in [str(i) for i in range(1, 4097)]:
            raise CommandError(f"{self.count} is not a valid value")

    def get_set_value(self):
        return CustomCmdWithOutput(f"q: ACQUIRE:count?").do()


class AvarageCmd(Command):
    def __init__(self, turn_on):
        self.turn_on = turn_on

    def do(self):
        if self.turn_on:
            CustomCmd("s :acquire:average on").do()
        else:
            CustomCmd("s :acquire:average off").do()

    def get_set_value(self):
        return CustomCmdWithOutput("q :acquire:average?").do()


class ExitHpctrlCmd(Command):
    def do(self):
        self.adapter.kill_hpctrl()


class CheckIfResponsiveCmd(Command):
    def do(self):
        """
        do method returns true if hpctrl responds to q *IDN?
        """
        return self.adapter.is_osci_responsive()


class GetPreambleCmd(Command):
    def do(self):
        """
        do method returns preamble data
        """
        return CustomCmdWithOutput("q :WAVEFORM:PREAMBLE?").do()


class FactoryResetCmd(Command):
    def do(self):
        CustomCmd("s *RST").do()


class TurnOnRunModeCmd(Command):
    def do(self):
        CustomCmd("s run").do()


class SetFormatToWordCmd(Command):
    def do(self):
        CustomCmd("s :waveform:format word").do()


class PreampleOnCmd(Command):
    def do(self):
        CustomCmd("pon").do()


class PreambleOffCmd(Command):
    def do(self):
        CustomCmd("poff").do()


class StartDataAcquisitionCmd(Command):
    def do(self):
        CustomCmd("*").do()


class StopDataAcquisitionCmd(Command):
    def do(self):
        CustomCmd("?").do()


class StartRunCmds:
    def __init__(self, file_to_store_data_from_hpctrl, channels):
        self.file_to_store_data_from_hpctrl = file_to_store_data_from_hpctrl
        self.channels = channels

    def do(self):
        LeaveCmdModeCmd().do()
        FileCmd(self.file_to_store_data_from_hpctrl).do()
        EnterCmdModeCmd().do()
        CustomCmd(channels_to_string(self.channels)).do()
        StartDataAcquisitionCmd().do()


class StopRunCmds:
    def __init__(self, file_with_data, folder_to_store_measurements, channels, isPreamble):
        self.file_with_data = file_with_data
        self.folder_to_store_measurements = folder_to_store_measurements
        self.channels = channels
        self.isPreamble = isPreamble

    def do(self):
        StopDataAcquisitionCmd().do()
        chans = channels_to_string(self.channels)
        if self.isPreamble:
            MultipleMeasurementsWithPreambles(self.file_with_data, chans).save_to_disc(
                self.folder_to_store_measurements
            )
        else:
            preamble = GetPreambleCmd().do()
            MultipleMeasurementsNoPreambles(self.file_with_data, preamble, chans).save_to_disc(
                self.folder_to_store_measurements
            )


class SingleCmds:
    def __init__(self, channels, path):
        self.channels = channels
        self.path = path

    def do(self):
        """
        do method returns array of measurements
        """
        measurements = []
        CustomCmd("s single").do()
        for i in channels_to_string(self.channels):
            CustomCmd(f"s :waveform:source channel{i}").do()
            CustomCmd(f"s :waveform:data?").do()
            data = CustomCmdWithOutput("16").do()
            preamble = GetPreambleCmd().do()
            measurements.append(Measurement(preamble, data, i))
        SingleMeasurements(measurements).save_to_disc(self.path)


class InitializeCmds:
    def __init__(self, address):
        self.address = address

    def do(self):
        ConnectCmd(self.address).check_and_do()
        EnterCmdModeCmd().do()
        SetFormatToWordCmd().do()
        TurnOnRunModeCmd().do()
        PreambleOffCmd().do()


def channels_to_string(channels):
    res = ""
    for ch in channels:
        res += ch[2:]
    return res
