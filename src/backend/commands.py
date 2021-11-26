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

    def connect_and_enter_cmd_mode(self, address: str):
        min_address = 1
        max_address = 31
        if address not in [str(i) for i in range(min_address, max_address+1)]:
            raise CommandError(f"{address} is not a valid address")
        if not self.adapter.connect(int(address)):
            raise CommandError("Could not connect")
        if not self.adapter.enter_cmd_mode():
            raise CommandError("Could not enter the CMD mode")


    def disconnect_and_exit_cmd_mode(self):
        if not self.adapter.disconnect():
            raise CommandError("Could not disconnect")
        if not self.adapter.exit_cmd_mode():
            raise CommandError("Could not leave the CMD mode")

    def enter_cmd(self):
        if not self.adapter.enter_cmd_mode():
            raise CommandError("Could not enter CMD mode")

    def exit_cmd(self):
        if not self.adapter.exit_cmd_mode():
            raise CommandError("Could not exit CMD mode")

    def send_custom(self, message: str):
        if not self.adapter.send(message.split("\n")):
            raise CommandError("Something went wrong")

    def _freeze_test(self):
        print("starting 5 second sleep")
        sleep(5)
        print("finished 5 second sleep")