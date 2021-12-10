import os
from backend.adapter import Adapter
from time import sleep


class CommandError(Exception):
    pass

class Commands:
    _instance = None

    def __new__(self):
        if self._instance is None:
            self._instance = super(Commands, self).__new__(self)
            self.adapter = Adapter(testing=False)
            self.adapter.start_hpctrl()

        return self._instance

    def connect(self, address: str):
        min_address = 1
        max_address = 31
        if address not in [str(i) for i in range(min_address, max_address+1)]:
            raise CommandError(f"{address} is not a valid address")
        if not self.adapter.connect(int(address)):
            raise CommandError("Could not connect")

    def enter_cmd_mode(self):
        if not self.adapter.enter_cmd_mode():
            raise CommandError("Could not enter the CMD mode")

    def connect_and_enter_cmd_mode(self, address: str):
        self.connect(address)
        self.enter_cmd_mode()

    def leave_cmd_mode(self):
        if not self.adapter.exit_cmd_mode():
            raise CommandError("Could not leave the CMD mode")

    def disconnect(self):
        if not self.adapter.disconnect():
            raise CommandError("Could not disconnect")

    def disconnect_and_exit_cmd_mode(self):
        self.leave_cmd_mode()
        self.disconnect()

    def send_custom(self, message: str):
        if not self.adapter.send(message.split("\n")):
            raise CommandError("Something went wrong")

    def set_path(self, path: str):
        if not self.adapter.send([f"FILE {path}"]):
            raise CommandError("Something went wrong")

    def set_points(self, points: str):
        # TODO: points can be also auto (also range should be checked)
        if not points.isnumeric():
            raise CommandError(f"{points} is not a number")
        if not self.adapter.send([f"s: ACQUIRE:POINTS {points}"]):
            raise CommandError("Something went wrong")

    def set_average_no(self, count: str):
        if not count.isnumeric():
            raise CommandError(f"{count} is not a number")
        if not self.adapter.send([f"s: ACQUIRE:count {count}"]):
            raise CommandError("Something went wrong")

    def turn_on_average(self):
        if not self.adapter.send(["s :acquire:average on"]):
            raise CommandError("Something went wrong")

    def turn_off_average(self):
        if not self.adapter.send(["s :acquire:average off"]):
            raise CommandError("Something went wrong")

    def single(self, channels):
        if not self.adapter.send(["s single"]):
            raise CommandError("Something went wrong")
        for i in channels:
            if not self.adapter.send([f"s :waveform:source channel{i[2:]}"]):
                raise CommandError("Something went wrong")
            if not self.adapter.send([f"s :waveform:data?"]):
                raise CommandError("Something went wrong")
            res = self.adapter.send_and_get_output(["16"], 5)
            if not res:
                raise CommandError("Something went wrong")
            self.save_measurement(i, res)

    def exit(self):
        self.adapter.disconnect()
        self.adapter.kill_hpctrl()

    def _freeze_test(self):
        print("starting 5 second sleep")
        sleep(5)
        print("finished 5 second sleep")

    def osci_is_responsive(self):
        return self.adapter.osci_is_responsive()

    def save_measurement(self, file_name, msg):
        with open(os.path.join("assets", "measurements", file_name), "w") as f:
            f.writelines(msg)