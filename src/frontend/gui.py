from os import listdir, path as ospath, sep
import PySimpleGUI as sg
from backend.adapter import AdapterError
from backend.command import *

class GUI:

    WIDTH, HEIGHT = 750, 700
    # make const of every string that is repeated more than once
    # todo strings should be osci commands (cuz that's how the keys are named in config window)
    connect = "Connect"
    disconnect = "Disconnect"
    quit_gui = "quit GUI"
    address = "address"
    factory_reset_osci = "Factory reset Oscilloscope"
    channels = "Channels"
    ping_osci = "Ping oscilloscope"
    averaging = "Averaging"
    average_pts = "average_pts"
    set_average_pts = "set_avg_pts"
    curr_points = "curr_points"
    set_points = "set_points"
    curr_path = "curr_path"
    terminal = "Terminal"
    run = "RUN"
    single = "SINGLE"
    ch1, ch2, ch3, ch4 = "ch1", "ch2", "ch3", "ch4"
    new_config = "New config"
    load_config = "Load config"
    config_file = "cfg_file"
    reinterpret_trimmed_data = "reinterpret_trimmed_data"
    set_preamble = "set_preamble"

    def __init__(self):
        sg.theme("DarkGrey9")
        self.invoker = Invoker()
        self.layout = self._create_layout()
        self.window = sg.Window(
            "Oscilloscope control",
            self.layout,
            size=(self.WIDTH, self.HEIGHT),
            element_justification="c",
            finalize=True
        )
        self.initialize_set_values()

    def _create_layout(self):
        button_size = (10, 1)

        col_gpib = sg.Col(
            [
                [sg.Text("Address number:"), sg.InputText(size=(12, 1), key=self.address)],
                [
                    sg.Button(self.connect, size=button_size),
                    sg.Button(self.disconnect, size=button_size),
                ],
                [sg.Button(self.terminal, size=button_size)],
                [sg.Button(self.ping_osci)],
            ],
            size=(self.WIDTH // 2, 140),
            pad=(0, 0),
        )

        col_osci = sg.Col(
            [
                [sg.Checkbox(self.averaging, enable_events=True, default=True, key=self.averaging)],
                [sg.Text("Average No.")],
                [
                    sg.InputText("100", size=button_size, key=self.average_pts),
                    sg.Button("SET", size=button_size, key=self.set_average_pts),
                ],
                [sg.Text("Points")],
                [
                    sg.InputText("4096", size=button_size, key=self.curr_points),
                    sg.Button("SET", size=button_size, key=self.set_points),
                ],
                [
                    sg.Checkbox("Channel 1", enable_events=True, key=self.ch1),
                    sg.Checkbox("Channel 2", enable_events=True, key=self.ch2),
                ],
                [
                    sg.Checkbox("Channel 3", enable_events=True, key=self.ch3),
                    sg.Checkbox("Channel 4", enable_events=True, key=self.ch4),
                ],
                [
                    sg.Checkbox(
                        "Send preamble after each measurement (slower)",
                        enable_events=True,
                        key=self.set_preamble,
                        default=False,
                    )
                ],
                [
                    sg.Checkbox(
                        "Reinterpret trimmed data",
                        enable_events=True,
                        key=self.reinterpret_trimmed_data,
                        default=False,
                    )
                ],
                [sg.Button(self.factory_reset_osci)],
            ],
            size=(self.WIDTH // 2, 280),
            pad=(0, 0),
        )

        col_run = sg.Col(
            [
                [sg.Text("Directory in which the measurements will be saved:")],
                [
                    sg.InputText(
                        key=self.curr_path, default_text="assets/measurements", enable_events=True
                    )
                ],
                [sg.FolderBrowse("Browse", initial_folder="assets", change_submits=True, enable_events=True)],
                [
                    sg.Button(self.run, size=button_size, disabled=True),
                    sg.Button(self.single, size=button_size, disabled=True),
                ],
            ],
            size=(self.WIDTH // 2, 140),
            pad=(0, 0),
        )

        col_cfg = sg.Col(
            [
                [
                    sg.Button(self.new_config),
                    sg.Button(self.load_config),
                    sg.Combo(
                        values=[
                            f for f in listdir(ospath.join("assets", "config"))
                            if f.endswith(".txt")
                        ],
                        key=self.config_file,
                    ),
                ]
            ],
            key="cfg_col",
            pad=(0, 0),
            size=(self.WIDTH // 2, 100),
        )

        col_info = sg.Col(
            [[sg.Multiline(key="info", disabled=True, size=(self.WIDTH, 200))]],
            size=(self.WIDTH, 200),
            scrollable=True,
        )

        return [
            [sg.Frame("GPIB Settings", [[col_gpib]]), sg.Frame("Run and save", [[col_run]])],
            [sg.Frame("Oscilloscope settings", [[col_osci]]), sg.Frame("Config", [[col_cfg]])],
            [sg.Frame("Info", [[col_info]])],
        ]
        
    def initialize_set_values(self):
        self.currently_set_values = {self.channels: []}
        self.currently_set_values[self.average_pts] = AverageNoCmd().get_set_value()
        self.currently_set_values[self.curr_points] = PointsCmd().get_set_value()
        self.currently_set_values[self.averaging] = AverageCmd().get_set_value()
        self.currently_set_values["preamble"] = False
        for key, value in self.currently_set_values.items():
            if key in self.window.AllKeysDict:
                self.window[key].update(value)
        self.update_info()

    def open_config_creation(self):
        # opens a new window for creating a new configuration file
        layout = [
            [sg.Multiline(key="cfg_input", size=(50, 20))],
            [sg.Button("Save"), sg.Button("Discard")],
            [sg.Text("Config name:"), sg.InputText(key="cfg_name")],
        ]
        window = sg.Window("Config", layout)
        config_content = ""
        config_name = ""
        while True:
            event, values = window.read()
            if event == "Discard":
                break
            elif event == "Save":
                if not values["cfg_name"]:
                    sg.popup("Config name is empty")
                else:
                    config_content = values["cfg_input"]
                    config_name = values["cfg_name"]
                    break
            elif event == sg.WIN_CLOSED:
                break
        window.close()
        return (config_content, config_name)

    def _create_config_layout(self, file_name):
        rows = []  # layout rows
        buttons = []  # [command_text, input_key]
        with open(file_name) as f:
            for line in f:
                line = line.strip()
                if "#" not in line:
                    rows.append([sg.Text(line), sg.Button("set", key=len(rows))])
                    buttons.append((line,))
                elif len(line.split()) > 1:
                    command = line.split()[:-1][0]
                    input_default = ""
                    if command in self.currently_set_values.keys():
                        input_default = self.currently_set_values[command]
                    input_key = f"input {len(rows)}"
                    buttons.append((command, input_key))
                    rows.append(
                        [
                            sg.Text(command),
                            sg.InputText(input_default, size=(10, 1), key=input_key),
                            sg.Button("set", key=len(rows)),
                        ]
                    )
        rows.append([sg.Button("Set all"), sg.Button("Close")])
        return (rows, buttons)

    def _run_config_command(self, row_index, values, buttons):
        command = buttons[row_index][0]
        value = values[buttons[row_index][1]] if len(buttons[row_index]) == 2 else True
        CustomCmd(f"{command} {value}").do()
        self.currently_set_values[command] = value

    def open_config_window(self, file_name):
        layout, buttons = self._create_config_layout(file_name)
        window = sg.Window("Run config", layout)
        while True:
            event, values = window.read()
            if event == "Set all":
                for i in range(len(buttons)):
                    self._run_config_command(i, values, buttons)
            elif event in range(len(buttons)):
                self._run_config_command(int(event), values, buttons)
            elif event in (sg.WIN_CLOSED, "Close"):
                break
        window.close()

    def create_config_file(self, config_content, file_name):
        if config_content:
            open(ospath.join("assets", "config", f"{file_name}.txt"), "w").write(config_content)
        self.window[self.config_file].update(
            values=[f for f in listdir(ospath.join("assets", "config")) if f.endswith(".txt")]
        )

    def update_info(self):
        info_content = [
            f"{key} = {value}" for key, value in self.currently_set_values.items() if value
        ]
        self.window["info"].update("\n".join(info_content))

    def button_activation(self, disable):
        for button in self.single, self.run:
            self.window[button].update(disabled=disable)

    def open_terminal_window(self):
        cmd_input, cmd_output, cmd_send = "cin", "cout", "csend"
        layout = [
            [sg.InputText(key=cmd_input, size=(50, 20)), sg.Button("Send", key=cmd_send, bind_return_key=True)],
            [sg.Multiline(key=cmd_output, disabled=True, size=(60, 450), autoscroll=True)],
        ]
        window = sg.Window("Terminal", layout, size=(450, 500))
        while True:
            event, values = window.read()
            if event == cmd_send:
                window[cmd_input].update("")
                cmd_in = values[cmd_input]
                window[cmd_output].update(value=f">>> {cmd_in}\n", append=True)
                if cmd_in in ("clr", "cls", "clear"):
                    window[cmd_output].update("")
                    continue
                if len(cmd_in.split()) > 1 and cmd_in.split()[0] == "q":  # asking for output
                    try:
                        output = CustomCmdWithOutput(cmd_in).do()
                    except AdapterError as e:
                        sg.popup(e)
                        continue
                    window[cmd_output].update(value=output + "\n", append=True)
                else:
                    CustomCmd(cmd_in).do()
                # self.initialize_set_values() # todo - ak sa v terminali posle nieco co je zobrazene v gui
            elif event in (sg.WIN_CLOSED, "Close"):
                break
        window.close()
        
    def get_mismatched_inputboxes(self, values):
        res = []
        if values[self.average_pts] != self.currently_set_values[self.average_pts]:
            res.append("Average No.")
        if values[self.curr_points] != self.currently_set_values[self.curr_points]:
            res.append("Points")
        return res

    def event_check(self) -> bool:  # returns False if closed
        event, values = self.window.read()
        if event == self.connect:
            self.invoker.initialize_cmds(values[self.address])
            self.currently_set_values[self.address] = values[self.address]
            self.button_activation(False)

        elif event == self.disconnect:
            LeaveCmdModeCmd().do()
            DisconnectCmd().do()
            self.button_activation(True)
            self.currently_set_values[self.address] = 0

        elif event == self.new_config:
            config_content, config_name = self.open_config_creation()
            self.create_config_file(config_content, config_name)

        elif event == self.load_config:
            file_name = values[self.config_file]
            full_path = ospath.join("assets", "config", file_name)
            if not ospath.isfile(full_path):
                sg.popup("File does not exist")
                return True
            if file_name:
                self.open_config_window(full_path)
            else:
                sg.popup("File not chosen")

        elif event == self.set_points:
            PointsCmd(values[self.curr_points]).check_and_do()
            self.currently_set_values["points"] = values[self.curr_points]

        elif event == self.set_average_pts:
            AverageNoCmd(values[self.average_pts]).check_and_do()
            self.currently_set_values[self.average_pts] = values[self.average_pts]

        elif event in (self.ch1, self.ch2, self.ch3, self.ch4):
            if values[event]:
                self.currently_set_values[self.channels].append(event)
            else:
                self.currently_set_values[self.channels].remove(event)

        elif event == self.averaging:
            AverageCmd(values[self.averaging]).do()
            self.currently_set_values["average"] = values[self.averaging]

        elif event == self.reinterpret_trimmed_data:
            pass # todo

        elif event == self.set_preamble:
            if values[self.set_preamble]:
                PreampleOnCmd().do()
            else:
                PreambleOffCmd().do()
            self.currently_set_values["preamble"] = values[self.set_preamble]

        elif event == self.single:
            mismatched = self.get_mismatched_inputboxes(values)
            if mismatched:
                sg.popup(f"Values are not set: {', '.join(mismatched)}")
                return True
            channels = self.currently_set_values[self.channels]
            path = values[self.curr_path].replace("/", sep)
            if channels:
                self.invoker.single_cmds(channels, path)
            else:
                sg.popup("No channels were selected")

        elif event == self.run:
            mismatched = self.get_mismatched_inputboxes(values)
            if mismatched:
                sg.popup(f"Values are not set: {', '.join(mismatched)}")
                return True
            channels = self.currently_set_values[self.channels]
            if not channels:
                sg.popup("No channels were selected")
                return True
            send_preamble = self.currently_set_values["preamble"]
            temp_file = "assets/measurements/temp.txt"
            self.invoker.start_run_cmds(temp_file, channels)
            if sg.popup(custom_text="stop", title="Running", keep_on_top=True) == "stop":
                self.invoker.stop_run_cmds(temp_file, values[self.curr_path], channels, send_preamble)

        elif event == self.factory_reset_osci:
            if sg.popup_yes_no(title="Reset?", keep_on_top=True) == "Yes":
                FactoryResetCmd().do()

        elif event == self.ping_osci:
            msg = "ping successful" if CheckIfResponsiveCmd().do() else "couldn't ping"
            sg.popup(msg)

        elif event == self.terminal:
            self.open_terminal_window()
            
        elif event == "Browse":
            self.window[self.curr_path].update(values["Browse"])

        elif event in (sg.WIN_CLOSED, self.quit_gui):
            return False

        return True

    def main_loop(self):
        while True:
            try:
                if not self.event_check():
                    break
                self.update_info()
            except (CommandError, AdapterError) as e:
                sg.popup(e)

        LeaveCmdModeCmd().do()
        ExitHpctrlCmd().do()
        self.window.close()