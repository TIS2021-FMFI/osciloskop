import PySimpleGUI as sg
from backend.commands import CommandError, Commands
from threading import Thread

class GUI:

    WIDTH, HEIGHT = 500, 800

    def __init__(self):
        sg.theme("DarkGrey9")
        self.func = Commands()
        self.layout = self._create_layout()
        self.window = sg.Window("Oscilloscope control", self.layout, size=(self.WIDTH, self.HEIGHT), element_justification="c")

    def _create_layout(self): 
        button_size = (10, 1)
        # Elements inside the window
        col_gpib = sg.Col([
            [sg.Text("Address number:"), sg.InputText("7", size=(12, 1), key="address")],
            [sg.Button("Connect", size=button_size), sg.Button("Disconnect", size=button_size)],
            [sg.Button("Terminal", size=button_size)]
        ], size=(self.WIDTH, 100), pad=(0,0))
        
        col_osci = sg.Col([
            [sg.Text("Average No.")],
            [sg.InputText("100"), sg.Button("SET", size=button_size)],
            [sg.Text("Points")],
            [sg.InputText("4096"), sg.Button("SET", size=button_size)],
            [sg.Checkbox("Channel 1"), sg.Checkbox("Channel 2")],
            [sg.Checkbox("Channel 3"), sg.Checkbox("Channel 4")],
            [sg.Button("Reset Oscilloscope")]
        ], size=(self.WIDTH, 220), pad=(0, 0))

        col_run = sg.Col([
            [sg.Text("Format type:"), sg.Combo(values=["RAW", "average", "histogram H/V", "versus"], default_value="versus")],
            [sg.Text("File name")],
            [sg.InputText("ch1_meranie", size=(25, 1)), sg.SaveAs("PATH/")],
            [sg.Button("SAVE", size=button_size), sg.Checkbox("AutoSave")],
            [sg.Button("RUN", size=button_size), sg.Button("STOP", size=button_size), sg.Button("SINGLE", size=button_size)]
        ], size=(self.WIDTH, 150))

        col_testing = sg.Col([
            [sg.Button("Send custom", size=button_size), sg.InputText("AAA", size=(15, 1), key="custom")],
            [sg.Button("Quit GUI", size=button_size)],
            [sg.Button("FREEZE", size=button_size)]
        ], size=(self.WIDTH, 100))

        col_info = sg.Col([
            [sg.Text("Current address: None", key="curr_add")]
        ], size=(self.WIDTH, 100))

        return [
            [sg.Frame("GPIB Settings", [[col_gpib]])],
            [sg.Frame("Oscilloscope settings", [[col_osci]])],
            [sg.Frame("Run and save", [[col_run]])],
            [sg.Frame("Testing", [[col_testing]])],
            [sg.Frame("Info", [[col_info]])]
        ]

    def run(self):
        # Event loop
        while True:
            event, values = self.window.read()
            try:
                if event == "Connect":
                    self.func.connect(values["address"])
                elif event == "Disconnect":
                    self.func.disconnect()
                    self.window["curr_add"].update("Current address: None")
                elif event == "Send custom":
                    self.func.send_custom(values["custom"])
                elif event == "FREEZE":
                    Thread(target=self.func._freeze_test).start()
                elif event in (sg.WIN_CLOSED, "Quit GUI"):
                    break
            except CommandError as e:
                sg.popup(e)

        self.window.close()