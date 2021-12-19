from os import listdir, path as ospath, sep
import PySimpleGUI as sg
from backend.adapter import AdapterError
from backend.command import *

class GUI:

    WIDTH, HEIGHT = 750, 700
    # make const of every string that is repeated more than once
    # todo strings should be osci commands (cuz that's how the keys are named in config window)
    connect_button = "Connect"
    disconnect_button = "Disconnect"
    address = "connect"
    factory_reset_osci = "Factory reset Oscilloscope"
    channels = "channels"
    ping_osci_button = "Ping oscilloscope"
    averaging_check = "s :acquire:average"
    average_pts_input = "s :acquire:count"
    set_average_pts_button = "set_avg_pts"
    curr_points_input = "s :acquire:points"
    set_points_button = "set points"
    curr_path = "curr path"
    terminal_button = "Terminal"
    preamble_check = "preamble"
    run_button = "RUN"
    single_button = "SINGLE"
    channels_checkboxes = ("ch1", "ch2", "ch3", "ch4")
    new_config_button = "New config"
    load_config_button = "Load config"
    config_file_combo = "cfg file"
    reinterpret_trimmed_data_check = "reinterpret trimmed data"

    def __init__(self):
        sg.theme("DarkGrey9")
        self.invoker = Invoker()
        self._currently_set_values = {self.channels: []}
        self.layout = self._create_layout()
        self.window = sg.Window(
            "Oscilloscope control",
            self.layout,
            size=(self.WIDTH, self.HEIGHT),
            element_justification="c",
            finalize=True
        )

    def _create_layout(self):
        button_size = (10, 1)

        col_gpib = sg.Col(
            [
                [sg.Text("Address number:"), sg.InputText(size=(12, 1), key=self.address, default_text="7")],
                [
                    sg.Button(self.connect_button, size=button_size),
                    sg.Button(self.disconnect_button, size=button_size),
                ],
                [sg.Button(self.terminal_button, size=button_size)],
                [sg.Button(self.ping_osci_button)],
            ],
            size=(self.WIDTH // 2, 150),
            pad=(0, 0),
        )

        col_osci = sg.Col(
            [
                [sg.Checkbox("Averaging", enable_events=True, default=False, key=self.averaging_check)],
                [sg.Text("Average No.")],
                [
                    sg.InputText("", size=button_size, key=self.average_pts_input),
                    sg.Button("SET", size=button_size, key=self.set_average_pts_button),
                ],
                [sg.Text("Points")],
                [
                    sg.InputText("", size=button_size, key=self.curr_points_input),
                    sg.Button("SET", size=button_size, key=self.set_points_button),
                ],
                [
                    sg.Checkbox("Channel 1", enable_events=True, key=self.channels_checkboxes[0]),
                    sg.Checkbox("Channel 2", enable_events=True, key=self.channels_checkboxes[1]),
                ],
                [
                    sg.Checkbox("Channel 3", enable_events=True, key=self.channels_checkboxes[2]),
                    sg.Checkbox("Channel 4", enable_events=True, key=self.channels_checkboxes[3]),
                ],
                [
                    sg.Checkbox(
                        "Reinterpret trimmed data",
                        enable_events=True,
                        key=self.reinterpret_trimmed_data_check,
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
                    sg.Button(self.run_button, size=button_size, disabled=True),
                    sg.Button(self.single_button, size=button_size, disabled=True),
                ],
                [
                    sg.Checkbox(
                        "Send preamble after each measurement (slower)",
                        enable_events=True,
                        key=self.preamble_check,
                        default=False,
                    )
                ]
            ],
            size=(self.WIDTH // 2, 150),
            pad=(0, 0),
        )

        col_cfg = sg.Col(
            [
                [
                    sg.Button(self.new_config_button),
                    sg.Button(self.load_config_button),
                    sg.Combo(
                        values=[
                            f for f in listdir(ospath.join("assets", "config"))
                            if f.endswith(".txt")
                        ],
                        key=self.config_file_combo,
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
            vertical_scroll_only=True
        )

        return [
            [sg.Frame("GPIB Settings", [[col_gpib]]), sg.Frame("Run and save", [[col_run]])],
            [sg.Frame("Oscilloscope settings", [[col_osci]]), sg.Frame("Config", [[col_cfg]])],
            [sg.Frame("Info", [[col_info]])],
        ]

    def add_set_value_key(self, key, value):
        if isinstance(value, str):
            value = value.lower()
        if isinstance(key, str):
            key = key.lower()
        if key == self.averaging_check:
            if value == "on":
                value = True
            elif value == "off":
                value = False
        self._currently_set_values[key] = value
        
    def get_set_value(self, key):
        return self._currently_set_values[key.lower()]

    def set_gui_values_to_set_values(self):
        for key, value in self._currently_set_values.items():
            if key in self.window.AllKeysDict:
                self.window[key].update(value)

    def initialize_set_values(self):
        self.add_set_value_key(self.average_pts_input, AverageNoCmd().get_set_value())
        self.add_set_value_key(self.curr_points_input, PointsCmd().get_set_value())
        self.add_set_value_key(self.averaging_check, AverageCmd().get_set_value())
        self.add_set_value_key(self.preamble_check, False)

        self.set_gui_values_to_set_values()
        self.update_info()

    def open_config_creation(self):
        # opens a new window for creating a new configuration file
        layout = [
            [sg.Multiline(key="cfg_input", size=(50, 20))],
            [sg.Text("Config name:"), sg.InputText(key="cfg_name", size=(20,1))],
            [sg.Button("Save"), sg.Button("Discard"), sg.Button("Help")]
        ]
        window = sg.Window("Config", [[sg.Col(layout, element_justification="c")]])
        config_content = ""
        config_name = ""
        while True:
            event, values = window.read()
            if event == "Discard":
                if values["cfg_input"]: # ask only if nothing is written
                    ans = sg.popup_yes_no("Are you sure you want to discard the current config?")
                    if ans == "No":
                        continue
                break
            elif event == "Save":
                if not values["cfg_name"]:
                    sg.popup("Config name is empty")
                else:
                    config_content = values["cfg_input"]
                    config_name = values["cfg_name"]
                    break
            elif event == "Help":
                sg.popup("""Write one command per line
Include 's' or 'q' before a command
'#' at the end of a command for a variable input
\nExample:
s :acquire:points 20
s :acquire:count #""")
            elif event == sg.WIN_CLOSED:
                break
        window.close()
        return (config_content, config_name)

    def _create_config_layout(self, file_name):
        
        def parse_line(line):
            if "#" in line:
                return " ".join(line.split()[:-1]), True
            return line, False
            
        rows = []  # layout rows
        buttons = {}  # command: <input> (None if no input #)
        txt_size=(30, 1)
        lines = [line.strip() for line in open(file_name).readlines()]
        for line in lines:
            input_key = None
            cmd, has_input = parse_line(line)
            rows.append([sg.Text(cmd, size=txt_size), sg.Button("Set", key=cmd)])
            if has_input:   # hashtag in line, add input element
                input_key = f"input {len(rows)-1}"
                input_default = self.get_set_value(cmd) if cmd.lower() in self._currently_set_values else ""
                rows[-1].insert(1, sg.InputText(input_default, size=(10, 1), key=input_key))
            buttons[cmd] = input_key
        rows.append([sg.Button("Set all"), sg.Button("Close")])
        column_height = 500
        scroll = True
        rows_height = len(rows) * 35
        if rows_height < 500:
            column_height = rows_height
            scroll = False
        return (sg.Column(rows, scrollable=scroll, vertical_scroll_only=True, size=(400, column_height)), buttons)

    def _run_config_command(self, values, cmd, input_key):
        if input_key is not None:
            val = values[input_key]
        else:
            cmd, val = " ".join(cmd.split()[:-1]), cmd.split()[-1]
        if val == "":
            sg.popup(f"No value in {cmd}")
            return
        CustomCmd(f"{cmd} {val}").do()
        if cmd.lower() in self._currently_set_values:
            self.add_set_value_key(cmd, val)

    def open_config_window(self, file_name):
        layout, button_input_map = self._create_config_layout(file_name)
        window = sg.Window("Run config", [[layout]])
        while True: # button key - button_input_map.key (command), input key - button_input_map[command]
            event, values = window.read()
            if event == "Set all":
                for cmd, input_key in button_input_map.items():
                    self._run_config_command(values, cmd, input_key)
            elif event in button_input_map.keys():
                self._run_config_command(values, event, button_input_map[event])
            elif event in (sg.WIN_CLOSED, "Close"):
                break
        window.close()

    def create_config_file(self, config_content, file_name):
        if config_content:
            open(ospath.join("assets", "config", f"{file_name}.txt"), "w").write(config_content)
        self.window[self.config_file_combo].update(
            values=[f for f in listdir(ospath.join("assets", "config")) if f.endswith(".txt")]
        )

    def update_info(self):
        info_content = [
            f"{key} = {value}" for key, value in self._currently_set_values.items() if value
        ]
        self.window["info"].update("\n".join(info_content))

    def button_activation(self, disable):
        for button in self.single_button, self.run_button:
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
                    try:
                        CustomCmd(cmd_in).do()
                        cmd = " ".join(cmd_in.split()[:-1])
                        val = cmd_in.split()[-1]
                        if cmd in self._currently_set_values:
                            self.add_set_value_key(cmd, val)
                    except AdapterError as e:
                        sg.popup(e)
            elif event in (sg.WIN_CLOSED, "Close"):
                break
        window.close()
        self.update_info()
        
    def get_mismatched_inputboxes(self, values):
        return "".join(
            f"{key} - {value} vs {values[key]} in GUI\n"
            for key, value in self._currently_set_values.items()
            if key in values and values[key] != value
        )
        
    def mismatched_popup(self, mismatched):
        answer = sg.popup_yes_no(f"Values are not set:\n{mismatched}\nSet GUI values to currently set values?")
        if answer == "Yes":
            self.set_gui_values_to_set_values()

    def event_check(self) -> bool:  # returns False if closed
        event, values = self.window.read()
        if event == self.connect_button:
            self.invoker.initialize_cmds(values[self.address])
            self.add_set_value_key(self.address, values[self.address])
            self.button_activation(False)
            self.initialize_set_values()

        elif event == self.disconnect_button:
            LeaveCmdModeCmd().do()
            DisconnectCmd().do()
            self.button_activation(True)
            self.add_set_value_key(self.address, 0)

        elif event == self.new_config_button:
            config_content, config_name = self.open_config_creation()
            self.create_config_file(config_content, config_name)

        elif event == self.load_config_button:
            file_name = values[self.config_file_combo]
            full_path = ospath.join("assets", "config", file_name)
            if not ospath.isfile(full_path):
                sg.popup("File does not exist")
                return True
            if file_name:
                self.open_config_window(full_path)
            else:
                sg.popup("File not chosen")

        elif event == self.set_points_button:
            PointsCmd(values[self.curr_points_input]).check_and_do()
            self.add_set_value_key(self.curr_points_input, values[self.curr_points_input])

        elif event == self.set_average_pts_button:
            AverageNoCmd(values[self.average_pts_input]).check_and_do()
            self.add_set_value_key(self.average_pts_input, values[self.average_pts_input])

        elif event in self.channels_checkboxes:
            if values[event]:
                self._currently_set_values[self.channels].append(event)
            else:
                self._currently_set_values[self.channels].remove(event)

        elif event == self.averaging_check:
            AverageCmd().do(values[self.averaging_check])
            self.add_set_value_key(self.averaging_check, values[self.averaging_check])   # todo key

        elif event == self.reinterpret_trimmed_data_check:
            pass # todo

        elif event == self.preamble_check:
            if values[self.preamble_check]:
                PreampleOnCmd().do()
            else:
                PreambleOffCmd().do()
            self.add_set_value_key(self.preamble_check, values[self.preamble_check])

        elif event == self.single_button:
            mismatched = self.get_mismatched_inputboxes(values)
            if mismatched:
                self.mismatched_popup(mismatched)
                return True
            channels = self.get_set_value(self.channels)
            path = values[self.curr_path].replace("/", sep)
            if channels:
                self.invoker.single_cmds(channels, path)
            else:
                sg.popup("No channels were selected")

        elif event == self.run_button:
            mismatched = self.get_mismatched_inputboxes(values)
            if mismatched:
                self.mismatched_popup(mismatched)
                return True
            channels = self.get_set_value(self.channels)
            if not channels:
                sg.popup("No channels were selected")
                return True
            send_preamble = self.get_set_value(self.preamble_check)
            temp_file = "assets/measurements/temp.txt"
            self.invoker.start_run_cmds(temp_file, channels)
            if sg.popup(custom_text="stop", title="Running", keep_on_top=True) == "stop":
                self.invoker.stop_run_cmds(temp_file, values[self.curr_path], channels, send_preamble)

        elif event == self.factory_reset_osci:
            if sg.popup_yes_no(title="Reset?", keep_on_top=True) == "Yes":
                FactoryResetCmd().do()

        elif event == self.ping_osci_button:
            msg = "ping successful" if CheckIfResponsiveCmd().do() else "couldn't ping"
            sg.popup(msg)

        elif event == self.terminal_button:
            self.open_terminal_window()
            
        elif event == "Browse":
            self.window[self.curr_path].update(values["Browse"])

        elif event in (sg.WIN_CLOSED):
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