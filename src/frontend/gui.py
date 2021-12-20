from os import listdir, path as ospath, sep
import PySimpleGUI as sg
from backend.adapter import AdapterError
from backend.command import *

class GUI:

    WIDTH, HEIGHT = 600, 500

    # input values (input fields, checkboxes etc used in info box)
    averaging_check = "s :acquire:average"
    average_pts_input = "s :acquire:count"
    curr_points_input = "s :acquire:points"
    channels_checkboxes = ("ch1", "ch2", "ch3", "ch4")
    channels = "channels"   # key for a list of currently checked channels
    preamble_check = "preamble"
    trimmed_check = "reinterpret trimmed data"
    address = "connect"

    # other elements (buttons, labels, ..)
    connect_button = "Connect"
    disconnect_button = "Disconnect"
    terminal_button = "Terminal"
    ping_osci_button = "Ping osci"
    reset_osci_button = "Factory reset oscilloscope"
    set_average_pts_button = "set avg pts"
    set_points_button = "set points"
    run_button = "RUN"
    single_button = "SINGLE"
    new_config_button = "New cfg"
    edit_config_button = "Edit cfg"
    load_config_button = "Load cfg"
    curr_path = "curr path"
    config_file_combo = "cfg file"
    is_data_reinterpreted = True
    
    # other stuff
    color_red = "maroon"
    color_green = "dark green"

    def __init__(self):
        sg.theme("DarkGrey9")
        sg.set_options(icon="assets/icon/icon.ico")
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
        left_column_width = int(self.WIDTH * 1.8 / 5)
        right_column_width = int(self.WIDTH * 3.2 / 5)

        col_gpib = sg.Col(
            [
                [sg.Text("Address number:", pad=(5, 10)), sg.InputText(size=(12, 1), key=self.address, default_text="7")],
                [
                    sg.Button(self.connect_button, size=button_size, pad=(10, 10)),
                    sg.Button(self.disconnect_button, size=button_size),
                ],
                [
                    sg.Button(self.terminal_button, size=button_size, pad=(10, 10)),
                    sg.Button(self.ping_osci_button, size=button_size)
                ]
            ],
            size=(left_column_width, 150),
            pad=(0, 0),
            element_justification="c"
        )

        col_osci = sg.Col(
            [
                [sg.Checkbox("Averaging", enable_events=True, default=False, key=self.averaging_check)],
                [sg.Text("Average No.")],
                [
                    sg.InputText("", size=(15, 1), key=self.average_pts_input),
                    sg.Button("Set", size=(5, 1), key=self.set_average_pts_button),
                ],
                [sg.Text("Points")],
                [
                    sg.InputText("", size=(15, 1), key=self.curr_points_input),
                    sg.Button("Set", size=(5, 1), key=self.set_points_button),
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
                        key=self.trimmed_check,
                        default=False,
                    )
                ],
                [sg.Button(self.reset_osci_button)],
            ],
            pad=(0, 0),
            size=(left_column_width, 280),
        )

        col_run = sg.Col(
            [
                [sg.Text("Directory in which the measurements will be saved:")],
                [
                    sg.InputText(
                        key=self.curr_path, default_text="assets/measurements", enable_events=True, size=(34, 1)
                    ),
                    sg.FolderBrowse("Browse", initial_folder="assets", change_submits=True, enable_events=True)
                ],
                [
                    sg.Button(self.run_button, size=button_size, disabled=True, pad=(1, 10)),
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
            size=(right_column_width, 150),
            pad=(0, 0),
            element_justification="c"
        )

        config_files = [f for f in listdir(ospath.join("assets", "config"))]
        col_cfg = sg.Col(
            [
                [
                    sg.Button(self.new_config_button),
                    sg.Button(self.edit_config_button),
                    sg.Button(self.load_config_button),
                    sg.Combo(
                        values=config_files,
                        default_value=config_files[0] if config_files else "",
                        key=self.config_file_combo,
                        size=(15, 1)
                    ),
                ],
                [sg.Text("Info")],
                [sg.Multiline(key="info", disabled=True, size=(43, 13))]
            ],
            key="cfg_col",
            pad=(0, 0),
            size=(right_column_width, 280),
            element_justification="c"
        )

        return [
            [sg.Frame("GPIB Settings", [[col_gpib]]), sg.Frame("Run and save", [[col_run]])],
            [sg.Frame("Oscilloscope settings", [[col_osci]]), sg.Frame("Config and set values", [[col_cfg]])]
        ]

    def add_set_value_key(self, key, value):
        if isinstance(value, str):
            value = value.lower()
        if isinstance(key, str):
            key = key.lower()
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
        self.add_set_value_key(self.trimmed_check, True)

        self.set_gui_values_to_set_values()
        self.update_info()

    def open_config_creation(self, file=None):
        # opens a new window for creating a new configuration file
        if file:
            filename = file.split(sep)[-1]
            cfg_content = open(file).read()
        else:
            filename = ""
            cfg_content = ""
        layout = [
            [sg.Multiline(cfg_content, key="cfg_input", size=(50, 20))],
            [sg.Text("Config name:"), sg.InputText(filename, key="cfg_name", size=(20,1))],
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
                    sg.popup_no_border("Config name is empty", background_color=self.color_red)
                else:
                    config_content = values["cfg_input"]
                    config_name = values["cfg_name"]
                    break
            elif event == "Help":
                sg.popup_no_border("""Write one command per line
Include 's' before a command
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
            sg.popup_no_border(f"No value in {cmd}", background_color=self.color_red)
            return
        CustomCmd(f"{cmd} {val}").do()
        if cmd.lower() in self._currently_set_values:
            self.add_set_value_key(cmd, val)
            self.update_info()

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
        
        self.input_ix = 0
        input_history = [""]
        def get_prev_input(self, event):
            if self.input_ix < len(input_history) - 1:
                self.input_ix += 1
            window[cmd_input].update(input_history[self.input_ix])
            
        def get_next_input(self, event):
            if self.input_ix > 0:
                self.input_ix -= 1
            window[cmd_input].update(input_history[self.input_ix])

        cmd_input, cmd_output, cmd_send = "cin", "cout", "csend"
        layout = [
            [sg.InputText(key=cmd_input, size=(50, 20)), sg.Button("Send", key=cmd_send, bind_return_key=True)],
            [sg.Multiline(key=cmd_output, disabled=True, size=(60, 450), autoscroll=True)],
        ]
        window = sg.Window("Terminal", layout, size=(450, 500), finalize=True)
        window[cmd_input].Widget.bind("<Up>", lambda e: get_prev_input(self, e))
        window[cmd_input].Widget.bind("<Down>", lambda e: get_next_input(self, e))
        while True:
            event, values = window.read()
            if event == cmd_send:
                window[cmd_input].update("")
                cmd_in = values[cmd_input]
                if cmd_in:
                    input_history.insert(1, cmd_in)
                self.input_ix = 0
                window[cmd_output].update(value=f">>> {cmd_in}\n", append=True)
                cmd_in_split = [i.lower().strip() for i in cmd_in.split()]
                if len(cmd_in_split) < 1:
                    continue
                if cmd_in.lower() in ("clr", "cls", "clear"):
                    window[cmd_output].update("")
                    continue
                if cmd_in_split[0] == "q":  # asking for output
                    try:
                        output = CustomCmdWithOutput(cmd_in).do()
                    except AdapterError as e:
                        sg.popup_no_border(e, background_color=self.color_red)
                        continue
                    window[cmd_output].update(value=output + "\n", append=True)
                else:
                    try:
                        CustomCmd(cmd_in).do()
                        cmd = " ".join(cmd_in_split[:-1])
                        val = cmd_in_split[-1]
                        if cmd in self._currently_set_values:
                            self.add_set_value_key(cmd, val)
                            self.update_info()
                    except AdapterError as e:
                        sg.popup_no_border(e, background_color=self.color_red)

            elif event in (sg.WIN_CLOSED, "Close"):
                break
        window.close()
        
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
            self.invoker.disengage_cmd()
            self.button_activation(True)
            self.add_set_value_key(self.address, 0)

        elif event == self.new_config_button:
            config_content, config_name = self.open_config_creation()
            self.create_config_file(config_content, config_name)
            
        elif event == self.edit_config_button:
            file_name = values[self.config_file_combo]
            full_path = ospath.join("assets", "config", file_name)
            if not ospath.isfile(full_path):
                sg.popup_no_border("File does not exist", background_color=self.color_red)
                return True
            config_content, config_name = self.open_config_creation(file=full_path)
            self.create_config_file(config_content, config_name)

        elif event == self.load_config_button:
            file_name = values[self.config_file_combo]
            full_path = ospath.join("assets", "config", file_name)
            if not ospath.isfile(full_path):
                sg.popup_no_border("File does not exist", background_color=self.color_red)
                return True
            if file_name:
                self.open_config_window(full_path)
            else:
                sg.popup_no_border("File not chosen", background_color=self.color_red)

        elif event == self.set_points_button:
            PointsCmd(values[self.curr_points_input]).check_and_do()
            self.add_set_value_key(self.curr_points_input, values[self.curr_points_input])

        elif event == self.set_average_pts_button:
            AverageNoCmd(values[self.average_pts_input]).check_and_do()
            self.add_set_value_key(self.average_pts_input, values[self.average_pts_input])

        elif event in self.channels_checkboxes:
            if values[event]:
                self._currently_set_values[self.channels].append(event)
                TurnOnChannel(event[2:]).do()
            else:
                self._currently_set_values[self.channels].remove(event)

        elif event == self.averaging_check:
            AverageCmd().do(values[self.averaging_check])
            self.add_set_value_key(self.averaging_check, values[self.averaging_check])

        elif event == self.trimmed_check:
            self.is_data_reinterpreted = values[self.trimmed_check]
            self.add_set_value_key(self.trimmed_check, self.is_data_reinterpreted)

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
            path = self.convert_path(values[self.curr_path])
            if channels:
                self.invoker.single_cmds(channels, path, self.is_data_reinterpreted)
            else:
                sg.popup_no_border("No channels were selected", background_color=self.color_red)

        elif event == self.run_button:
            mismatched = self.get_mismatched_inputboxes(values)
            if mismatched:
                self.mismatched_popup(mismatched)
                return True
            channels = self.get_set_value(self.channels)
            if not channels:
                sg.popup_no_border("No channels were selected", background_color=self.color_red)
                return True
            is_preamble = self.get_set_value(self.preamble_check)
            temp_file = self.convert_path("assets/measurements/temp.txt")
            self.invoker.start_run_cmds(temp_file, channels)
            sg.popup_no_border("stop", title="Running", keep_on_top=True, background_color=self.color_red)
            path = self.convert_path(values[self.curr_path])
            self.invoker.stop_run_cmds(temp_file, path, channels, is_preamble, self.is_data_reinterpreted)

        elif event == self.reset_osci_button:
            reset_message = "reset osci"
            if sg.popup_get_text(f"Type '{reset_message}' to factory reset", keep_on_top=True) == reset_message:
                FactoryResetCmd().do()
                return True
            sg.popup_no_border(f"Didn't reset, input wasn't '{reset_message}'", background_color=self.color_red)

        elif event == self.ping_osci_button:
            if CheckIfResponsiveCmd().do():
                sg.popup_no_border("ping successful", background_color=self.color_green)
            else:
                sg.popup_no_border("couldn't ping", background_color=self.color_red)

        elif event == self.terminal_button:
            self.open_terminal_window()
            
        elif event == "Browse":
            self.window[self.curr_path].update(values["Browse"])

        elif event == sg.WIN_CLOSED:
            return False

        return True

    def main_loop(self):
        while True:
            try:
                if not self.event_check():
                    break
                self.update_info()
            except (CommandError, AdapterError) as e:
                sg.popup_no_border(e, background_color=self.color_red)
            except Exception as e:
                print(e)

        self.invoker.disengage_cmd()
        self.window.close()

    def convert_path(self, path):
        return path.replace("/", sep)