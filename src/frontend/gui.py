import PySimpleGUI as sg
from backend.commands import CommandError, Commands
from threading import Thread
from os import listdir

class GUI:

    # WIDTH, HEIGHT = 750, 425
    WIDTH, HEIGHT = 750, 700
    # make const of every string that is repeated more than once
    word_connect = "Connect"
    word_disconnect = "Disconnect"
    word_quit_gui = "Quit GUI"
    word_address = "address"

    def __init__(self):
        sg.theme("DarkGrey9")
        self.currently_set_values = {}
        self.cmd = Commands()
        self.layout = self._create_layout()
        self.window = sg.Window("Oscilloscope control", self.layout, size=(self.WIDTH, self.HEIGHT), element_justification="c")

    def _create_layout(self): 
        button_size = (10, 1)
        # Elements inside the window
        col_gpib = sg.Col([
            [sg.Text("Address number:"), sg.InputText(size=(12, 1), key=self.word_address)],
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
            [sg.Text("Format type:"), sg.Combo(values=["RAW", "average"], default_value="RAW")],
            [sg.Text("File name")],
            [sg.InputText("ch1_meranie", size=(25, 1)), sg.SaveAs("PATH/")],
            [sg.Button("SAVE", size=button_size), sg.Checkbox("AutoSave")],
            [sg.Button("RUN", size=button_size), sg.Button("STOP", size=button_size), sg.Button("SINGLE", size=button_size)]
        ], size=(self.WIDTH/2, 150), pad=(0,0))

        col_cfg = sg.Col([
            [sg.Button("New config"), sg.Button("Load config"), sg.Combo(values=[f for f in listdir("config") if f.endswith(".txt")], key="cfg_file")]],
            key="cfg_col", pad=(0,0), size=(self.WIDTH/2,220), scrollable=True)

        col_info = sg.Col([
            [sg.Multiline(key="info", size=(self.WIDTH, 200))]], size=(self.WIDTH,200)
        )

        return [
            [sg.Frame("GPIB Settings", [[col_gpib]]),
            sg.Frame("Run and save", [[col_run]])],
            [sg.Frame("Oscilloscope settings", [[col_osci]]),
            sg.Frame("Config", [[col_cfg]])],
            [sg.Frame("Info", [[col_info]])]
        ]

    def open_config_creation(self):
        layout = [
            [sg.Multiline(key="cfg_input")],
            [sg.Button("Save"), sg.Button("Discard")],
            [sg.Text("Config name:"), sg.InputText(key="cfg_name")]
        ]
        window = sg.Window("Config", layout)
        config_content = ""
        config_name = ""
        while True:
            event, values = window.read()
            if event == "Discard":
                break
            elif event == "Save":
                config_content = values["cfg_input"]
                config_name = values["cfg_name"]
                break
        window.close()
        return config_content, config_name

    def run_config(self, file_name):
        rows = []
        print(self.currently_set_values)
        with open(file_name) as f:
            for line in f:
                line = line.strip()
                if "#" not in line:
                    rows.append([sg.Text(line), sg.Button("set", key=len(rows))])
                elif len(line.split()) > 1:
                    command = line.split()[:-1][0]
                    input_default = ""
                    if command in self.currently_set_values.keys():
                        input_default = self.currently_set_values[command]
                    rows.append([sg.Text(command), sg.InputText(input_default, size=(10, 1), key=f"b{len(rows)}"), sg.Button("set", key=len(rows))])
                    print(len(rows))
        rows.append([sg.Button("Set all"), sg.Button("Close")])
        window = sg.Window("Run config", rows)
        while True:
            event, values = window.read()
            if event == "Set all":
                for i, row in enumerate(rows[:-1]):
                    label = row[0]
                    if len(row) == 2:
                        self.cmd.send_custom(label.DisplayText)
                        self.currently_set_values[label.DisplayText] = ""
                    elif len(row) == 3:
                        self.cmd.send_custom(f"{label.DisplayText} {values[f'b{i}']}")
                        self.currently_set_values[label.DisplayText] = values[f'b{i}']
            elif event in range(len(rows)):
                i = int(event)
                row = rows[i]
                label = row[0]
                if len(row) == 2:
                    self.cmd.send_custom(label.DisplayText)
                    self.currently_set_values[label.DisplayText] = ""
                elif len(row) == 3:
                    self.cmd.send_custom(f"{label.DisplayText} {values[f'b{i}']}")
                    self.currently_set_values[label.DisplayText] = values[f'b{i}']
            elif event in (sg.WIN_CLOSED, "Close"):
                break
        self.update_info()
        window.close()

    def write_config(self, config_content, file_name):
        if config_content:
            with open(f"config\\{file_name}.txt", "w") as f:
                f.write(config_content)
        self.window["cfg_file"].update(values=[f for f in listdir("config") if f.endswith(".txt")])

    def update_info(self):
        info_content = [f"{key} = {value}" for key, value in self.currently_set_values.items()]
        self.window["info"].update("\n".join(info_content))

    def run(self):
        # Event loop
        while True:
            event, values = self.window.read()
            try:
                if event == self.word_connect:
                    self.cmd.connect_and_enter_cmd_mode(values[self.word_address])
                    self.currently_set_values[event] = values[self.word_address]
                elif event == self.word_disconnect:
                    self.cmd.disconnect_and_exit_cmd_mode()
                elif event == "New config":
                    config_content, config_name = self.open_config_creation()
                    self.write_config(config_content, config_name)
                elif event == "Load config":
                    self.run_config("config\\"+values["cfg_file"])
                elif event in (sg.WIN_CLOSED, self.word_quit_gui):
                    break
                self.update_info()
            except CommandError as e:
                sg.popup(e)
        
        self.cmd.exit()
        self.window.close()