import backend.adapter as ada
import time

class Functions:
    _instance = None

    def __new__(self):
        if self._instance is None:
            self._instance = super(Functions, self).__new__(self)

            self.adapter = ada.Adapter(testing=True)
            self.adapter.start_hpctrl()

        return self._instance

    def connect(self, address: int = 7):
        self.adapter.connect(address)

    def disconnect(self):
        self.adapter.disconnect()

    def enter_cmd(self):
        self.adapter.enter_cmd_mode()

    def exit_cmd(self):
        self.adapter.exit_cmd_mode()

    def send_custom(self, message: str):
        self.adapter.send(message.split("\n"))

    def _freeze_test(self):
        print("starting 5 second sleep")
        time.sleep(5)
        print("finished 5 second sleep")
