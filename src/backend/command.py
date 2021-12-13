from backend.adapter import Adapter
from backend.measurement import Measurement, SingleMeasurement


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


class EnterCmdModeCmd(Command):
    def do(self):
        self.adapter.enter_cmd_mode()


class LeaveCmdModeCmd(Command):
    def do(self):
        self.adapter.exit_cmd_mode()


class DisconnectCmd(Command):
    def do(self):
        self.adapter.disconnect()


class CustomCmd(Command):
    def __init__(self, cmd):
        self.cmd = cmd

    def do(self):
        """
        sends one command
        """
        self.adapter.send([self.cmd])


class FileCmd(Command):
    def __init__(self, path):
        self.path = path

    def do(self):
        """
        sets path where the measured data should be stored
        """
        self.adapter.send([f"file {self.path}"])


class PointsCmd(Command):
    def __init__(self, points):
        self.points = points

    def do(self):
        self.adapter.send([f"s: ACQUIRE:POINTS {self.points}"])

    def check(self):
        if self.points not in [str(i) for i in range(16, 4097)] or self.points != "auto":
            raise CommandError(f"{self.points} is not a valid value")

    def get_set_value(self):
        return self.adapter.send_and_get_output([f"q: ACQUIRE:POINTS?"])


class AvarageNoCmd(Command):
    def __init__(self, count):
        self.count = count

    def do(self):
        self.adapter.send([f"s: ACQUIRE:count {self.count}"])

    def check(self):
        if self.count not in [str(i) for i in range(1, 4097)]:
            raise CommandError(f"{self.count} is not a valid value")

    def get_set_value(self):
        return self.adapter.send_and_get_output([f"q: ACQUIRE:count?"])


class AvarageCmd(Command):
    def __init__(self, turn_on):
        self.turn_on = turn_on

    def do(self):
        if self.turn_on:
            self.adapter.send(["s :acquire:average on"])
        else:
            self.adapter.send(["s :acquire:average off"])

    def get_set_value(self):
        return self.adapter.send_and_get_output(["q :acquire:average?"])


class SingleCmd(Command):
    def __init__(self, channels, path):
        self.channels = channels
        self.path = path

    def do(self):
        """
        do method returns array of measurements
        """
        measurements = []
        self.adapter.send(["s single"])
        for i in self.channels:
            chan = i[2:]
            self.adapter.send([f"s :waveform:source channel{chan}"])
            self.adapter.send([f"s :waveform:data?"])
            data = self.adapter.send_and_get_output(["16"], 5)
            preamble = PreambleCmd().do()
            measurements.append(Measurement(preamble, data, chan))
        SingleMeasurement(measurements).save_to_disc(self.path)


class ExitHpctrlCmd(Command):
    def do(self):
        self.adapter.kill_hpctrl()


class CheckIfResponsiveCmd(Command):
    def do(self):
        """
        do method returns true if hpctrl responds to q *IDN?
        """
        return self.adapter.is_osci_responsive()


class PreambleCmd(Command):
    def do(self):
        """
        do method returns preamble data
        """
        return self.adapter.send_and_get_output(["q :WAVEFORM:PREAMBLE?"])