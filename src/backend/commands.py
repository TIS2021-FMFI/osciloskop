from backend.adapter import Adapter
from time import sleep


class CommandError(Exception):
    pass

class Commands:
    _instance = None

    def __new__(self):
        if self._instance is None:
            self._instance = super(Commands, self).__new__(self)
            self.adapter = Adapter(testing=True)
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
        if not self.adapter.send(f"FILE {path}"):
            raise CommandError("Something went wrong")

    def set_points(self, points: str):
        if not points.isnumeric():
            raise CommandError(f"{points} is not a number")
        if not self.adapter.send(f"s: ACQUIRE:POINTS {points}"):
            raise CommandError("Something went wrong")

    def exit(self):
        self.adapter.disconnect()
        self.adapter.kill_hpctrl()

    def _freeze_test(self):
        print("starting 5 second sleep")
        sleep(5)
        print("finished 5 second sleep")