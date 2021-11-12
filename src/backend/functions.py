import backend.adapter as ada

class Functions:

    def __init__(self):
        self.adapter = ada.Adapter(testing=True)
        self.adapter.start_hpctrl()

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