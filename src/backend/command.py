import threading
import time
import os
import backend.measurement as ms
import PySimpleGUI as sg
from backend.adapter import Adapter, AdapterError
from abc import ABC, abstractmethod


class CommandError(Exception):
    pass


def send_cmd(command):
    adapter.send(command)


def send_cmd_with_output(command, timeout=5):
    return adapter.send_and_get_output(command, timeout)


class Command(ABC):

    @abstractmethod
    def do(self):
        pass

    def check(self):
        pass

    def check_and_do(self):
        self.check()
        self.do()

    def get_set_value(self):
        pass


class ConnectCmd(Command):
    def __init__(self, address):
        self.address = address

    def do(self):
        def exit():
            ExitHpctrlCmd().do()
            raise CommandError("couldn't connect, probably bad address")

        adapter.connect(self.address)
        time.sleep(0.5)

        try:
            if not CheckIfResponsiveCmd().do():
                exit()
        except AdapterError:
            exit()

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


class GetOutput(Command):
    def do(self, timeout=0.2):
        try:
            return adapter.get_output(timeout)
        except AdapterError:
            return None


class CustomCmd(Command):
    def __init__(self, cmd):
        self.cmd = cmd

    def do(self):
        """
        sends a command
        """
        return send_cmd(self.cmd)


class CustomCmdWithOutput(Command):
    def __init__(self, cmd):
        self.cmd = cmd

    def do(self):
        """
        sends one command and returns output from hpctrl
        """
        return send_cmd_with_output(self.cmd)


class FileCmd(Command):
    def __init__(self, path):
        self.path = path

    def do(self):
        """
        sets path where the measured data should be stored
        """
        send_cmd(f"file {self.path}")


class PointsCmd(Command):
    def __init__(self, points=None):
        self.points = points

    def do(self):
        send_cmd(f"s :ACQUIRE:POINTS {self.points}")

    def check(self):
        if self.points not in [str(i) for i in range(16, 4097)] and self.points.lower() != "auto":
            raise CommandError(f"{self.points} is not in range 16-4096")

    def get_set_value(self):
        return send_cmd_with_output("q :ACQUIRE:POINTS?")


class AverageNoCmd(Command):
    def __init__(self, count=None):
        self.count = count

    def do(self):
        send_cmd(f"s :ACQUIRE:count {self.count}")

    def check(self):
        if self.count not in [str(i) for i in range(1, 4097)]:
            raise CommandError(f"{self.count} is not in range 1-4096")

    def get_set_value(self):
        return send_cmd_with_output("q :ACQUIRE:count?")


class AverageCmd(Command):

    def do(self, turn_on):
        if turn_on:
            send_cmd("s :acquire:average on")
        else:
            send_cmd("s :acquire:average off")

    def get_set_value(self):
        return send_cmd_with_output("q :acquire:average?") == "1"


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
        return send_cmd_with_output("q :WAVEFORM:PREAMBLE?")


class FactoryResetCmd(Command):
    def do(self):
        send_cmd("s *RST")


class TurnOnRunModeCmd(Command):
    def do(self):
        send_cmd("s run")


class SetFormatToWordCmd(Command):
    def do(self):
        send_cmd("s :waveform:format word")


class PreambleOnCmd(Command):
    def do(self):
        send_cmd("pon")


class PreambleOffCmd(Command):
    def do(self):
        send_cmd("poff")


class StartDataAcquisitionCmd(Command):
    def do(self):
        send_cmd("*")


class StopDataAcquisitionCmd(Command):
    def do(self):
        send_cmd("?")


class TurnOnChannelCmd(Command):
    def __init__(self, channel):
        self.channel = channel

    def do(self):
        send_cmd(f"s :channel{self.channel}:display on")


class TurnOffChannelCmd(Command):
    def __init__(self, channel):
        self.channel = channel

    def do(self):
        send_cmd(f"s :channel{self.channel}:display off")


class ChannelCmd(Command):
    def __init__(self, channel):
        self.channel = channel

    def do(self):
        pass

    def get_set_value(self):
        return send_cmd_with_output(f"q :channel{self.channel}:display?") == "1"


class ChangeWaveformSourceCmd(Command):
    def __init__(self, channel):
        self.channel = channel

    def do(self):
        send_cmd(f"s :waveform:source channel{self.channel}")

    def get_set_value(self):
        return send_cmd_with_output("q :waveform:source?")


def start_run_cmds(file_to_store_data_from_hpctrl, channels):
    LeaveCmdModeCmd().do()
    FileCmd(file_to_store_data_from_hpctrl).do()
    EnterCmdModeCmd().do()
    CustomCmd(channels_to_string(channels)).do()
    StartDataAcquisitionCmd().do()


def stop_run_cmds(file_with_data, folder_to_store_measurements, channels, is_preamble,
                  reinterpret_trimmed_data, saving_gui_text: sg.Text, run_button: sg.Button, got_error):
    if not got_error:
        StopDataAcquisitionCmd().do()

    def run():
        start = time.time()
        timeout = 5  # in seconds
        while True:
            try:
                hpctrl_output = adapter.get_output(0.2)
                if "!file written" in hpctrl_output:
                    break
            except AdapterError:
                pass
            if time.time() > start + timeout:
                saving_gui_text.update(visible=False)
                run_button.Update("RUN", button_color="#B9BBBE", disabled=False)
                return
            time.sleep(0.5)
        chans = channels_to_string(channels)
        if is_preamble:
            ms.MultipleMeasurementsWithPreambles(file_with_data, chans, reinterpret_trimmed_data,
                                                 saving_gui_text).save_to_disk(
                folder_to_store_measurements
            )
        else:
            time.sleep(0.5)
            preambles = []
            for ch in chans:
                ChangeWaveformSourceCmd(ch).do()
                preamble = GetPreambleCmd().do().split("\n")[-1]
                preambles.append(preamble)
            ms.MultipleMeasurementsNoPreambles(file_with_data, preambles, chans, reinterpret_trimmed_data,
                                               saving_gui_text).save_to_disk(
                folder_to_store_measurements
            )
        saving_gui_text.update(value="Removing temp.txt")
        os.remove(file_with_data)
        saving_gui_text.update(visible=False)
        run_button.Update(disabled=False)

    thread = threading.Thread(target=run, args=())
    thread.daemon = True
    thread.start()


def single_cmds(channels, path, reinterpret_trimmed_data, saving_gui_text):
    CustomCmd("s single").do()
    measurements = []
    for i in channels_to_string(channels):
        ChangeWaveformSourceCmd(i).do()
        CustomCmd("s :waveform:data?").do()
        data = CustomCmdWithOutput("16").do()
        # cut the count
        data = data[(data.find("\n") + 1):]
        preamble = GetPreambleCmd().do()
        measurements.append(ms.Measurement(preamble, data, i, reinterpret_trimmed_data))
    ms.SingleMeasurements(measurements, saving_gui_text).save_to_disk(path)
    TurnOnRunModeCmd().do()
    saving_gui_text.update(visible=False)


def initialize_cmds(address):
    adapter.start_hpctrl()
    ConnectCmd(address).check_and_do()
    EnterCmdModeCmd().do()
    SetFormatToWordCmd().do()
    TurnOnRunModeCmd().do()
    PreambleOffCmd().do()


def disengage_cmd():
    LeaveCmdModeCmd().do()
    DisconnectCmd().do()
    ExitHpctrlCmd().do()


def channels_to_string(channels):
    return "".join(sorted(ch[2:] for ch in channels))


in_production = os.getenv("OSCI_IN_PRODUCTION") == "true"
try:
    adapter = Adapter(testing=not in_production)
except AdapterError as e:
    adapter = e
