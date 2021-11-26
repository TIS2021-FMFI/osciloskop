import PySimpleGUI as sg
from backend.commands import CommandError, Commands
from threading import Thread

class GUI:

    WIDTH, HEIGHT = 750, 425
    # make const of every string that is repeated more than once
    word_connect = "Connect"
    word_disconnect = "Disconnect"
    word_quit_gui = "Quit GUI"
    word_address = "address"

    def __init__(self):
        sg.theme("DarkGrey9")
        self.cmd = Commands()
        self.layout = self._create_layout()
        self.window = sg.Window("Oscilloscope control", self.layout, size=(self.WIDTH, self.HEIGHT), element_justification="c")

    def _create_layout(self): 
        button_size = (10, 1)
        # Elements inside the window
        col_gpib = sg.Col([
            [sg.Text("Address number:"), sg.InputText("7", size=(12, 1), key=self.word_address)],
            [sg.Button(self.word_connect, size=button_size), sg.Button(self.word_disconnect, size=button_size)],
            [sg.Button("Terminal", size=button_size)]
        ], size=(self.WIDTH/2, 150), pad=(0,0))
        
        col_osci = sg.Col([
            [sg.Text("Average No.")],
            [sg.InputText("100", size=button_size), sg.Button("SET", size=button_size)],
            [sg.Text("Points")],
            [sg.InputText("4096", size=button_size), sg.Button("SET", size=button_size)],
            [sg.Checkbox("Channel 1"), sg.Checkbox("Channel 2")],
            [sg.Checkbox("Channel 3"), sg.Checkbox("Channel 4")],
            [sg.Button("Reset Oscilloscope")]
        ], size=(self.WIDTH/2, 220), pad=(0,0))

        col_run = sg.Col([
            [sg.Text("Format type:"), sg.Combo(values=["RAW", "average", "histogram H/V", "versus"], default_value="versus")],
            [sg.Text("File name")],
            [sg.InputText("ch1_meranie", size=(25, 1)), sg.SaveAs("PATH/")],
            [sg.Button("SAVE", size=button_size), sg.Checkbox("AutoSave")],
            [sg.Button("RUN", size=button_size), sg.Button("STOP", size=button_size), sg.Button("SINGLE", size=button_size)]
        ], size=(self.WIDTH/2, 150), pad=(0,0))

        col_cfg = sg.Col([[sg.Input(key='Config file', enable_events=True, visible=False)],
            [sg.FileBrowse("Load config", target='Config file'), sg.Button("New config")]],
            key="cfg_col", pad=(0,0), size=(self.WIDTH/2,220), scrollable=True)

        return [
            [sg.Frame("GPIB Settings", [[col_gpib]]),
            sg.Frame("Run and save", [[col_run]])],
            [sg.Frame("Oscilloscope settings", [[col_osci]]),
            sg.Frame("Config", [[col_cfg]])]
        ]

    def open_config_creation(self):
        layout = [
            [sg.Multiline(key="cfg_input")],
            [sg.Button("Save"), sg.Button("Discard")]
        ]
        window = sg.Window("Config", layout)
        config_content = ""
        while True:
            event, values = window.read()
            if event == "Save":
                config_content = values["cfg_input"]
                break
            elif event == "Discard":
                break
        window.close()
        return config_content

    def run(self):
        # Event loop
        while True:
            event, values = self.window.read()
            try:
                print(event)
                if event == self.word_connect:
                    self.cmd.connect_and_enter_cmd_mode(values[self.word_address])
                elif event == self.word_disconnect:
                    self.cmd.disconnect_and_exit_cmd_mode()
                    self.window["curr_add"].update("Current address: None")
                elif event == "New config":
                    config_content = self.open_config_creation()
                    if config_content:
                        with open("config/kkt.txt", "w") as f:
                            f.write(config_content)
                elif event == "Config file":
                    rows = []
                    with open(values["Config file"]) as f:
                        for line in f:
                            if "#" not in line:
                                rows.append([sg.Text(line),sg.Button("set")])
                            elif len(line.split()) > 1:
                                command = line.split()[:-1][0]
                                rows.append([sg.Text(command), sg.InputText(size=(10, 1)), sg.Button("set")])
                    for row in rows:
                        self.window.extend_layout(self.window["cfg_col"], [row,])
                    self.window["cfg_col"].contents_changed()

                elif event in (sg.WIN_CLOSED, self.word_quit_gui):
                    break
            except CommandError as e:
                sg.popup(e)
        
        self.cmd.exit()
        self.window.close()