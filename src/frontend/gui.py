import os
import platform
import PySimpleGUI as sg
import backend.command as cm
from backend.adapter import AdapterError
from frontend.custom_config import CustomConfig
from frontend.terminal import Terminal
class GUI:

    class IsInCustomConfig():
        def __init__(self, value):
            self.value = value
        def __eq__(self, other):
            return self.value == other.value
        def __hash__(self):
            return hash(self.value)

    WIDTH, HEIGHT = 600, 500
    if platform.system() != "Windows":
        WIDTH = 700

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
        self.invoker = cm.Invoker()
        self._currently_set_values = {self.channels: []}
        self.custom_config = CustomConfig(self)
        self.terminal = Terminal(self)
        self.layout = self._create_layout()
        self.window = sg.Window(
            "Oscilloscope control",
            self.layout,
            size=(self.WIDTH, self.HEIGHT),
            element_justification="c",
            finalize=True
        )
        self.start_adapter()

    def start_adapter(self):
        try:
            cm.start_adapter()
            if os.getenv("OSCI_IN_PRODUCTION") != "true":
                sg.popup_no_border("Launched in testing mode", background_color=self.color_red, auto_close=True)
        except AdapterError as e:
            sg.popup_no_border(e, background_color=self.color_red)
            self.window.close()

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

        self.saving_text = sg.Text("Saving...", visible=False, justification="c")
        col_run = sg.Col(
            [
                [sg.Text("Directory in which the measurements will be saved:")],
                [
                    sg.InputText(
                        key=self.curr_path, default_text=os.getenv("OSCI_MEASUREMENTS_DIR"), enable_events=True, size=(34, 1)
                    ),
                    sg.FolderBrowse("Browse", initial_folder="assets", change_submits=True, enable_events=True)
                ],
                [
                    sg.Button(self.run_button, size=button_size, disabled=True, pad=(1, 10)),
                    sg.Button(self.single_button, size=button_size, disabled=True),
                    self.saving_text
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

        config_files = list(os.listdir(os.path.join("assets", "config")))
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
        elif isinstance(key, self.custom_config.Cmd):
            key, value = self.IsInCustomConfig(key.key), str(key)
        self._currently_set_values[key] = value
        
    def get_set_value(self, key):
        return self._currently_set_values[key.lower()]

    def set_gui_values_to_set_values(self):
        for key, value in self._currently_set_values.items():
            if key in self.window.AllKeysDict:
                self.window[key].update(value)

    def initialize_set_values(self):
        self._currently_set_values = {self.channels: []}
        self.add_set_value_key(self.average_pts_input, cm.AverageNoCmd().get_set_value())
        self.add_set_value_key(self.curr_points_input, cm.PointsCmd().get_set_value())
        self.add_set_value_key(self.averaging_check, cm.AverageCmd().get_set_value())
        self.add_set_value_key(self.preamble_check, False)
        self.add_set_value_key(self.trimmed_check, True)

        self._currently_set_values[self.channels] = []
        for channel in self.channels_checkboxes:
            enabled = cm.ChannelCmd(self.channel_number(channel)).get_set_value()
            if enabled:
                self._currently_set_values[self.channels].append(channel)
            self.window[channel].update(enabled)

        self.set_gui_values_to_set_values()
        self.update_info()

    def update_info(self):
        info_content = [
            value if isinstance(key, self.IsInCustomConfig) else f"{key} = {value}"
            for key, value in self._currently_set_values.items()
            if value
        ]
        self.window["info"].update("\n".join(info_content))

    def button_activation(self, disable):
        for button in self.single_button, self.run_button:
            self.window[button].update(disabled=disable)
        
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
        window, event, values = sg.read_all_windows()
        if window is None:
            return False
        if window == self.terminal.window:
            self.terminal.check_event(event, values)
        
        elif window == self.custom_config.window:
            self.custom_config.check_event(event, values)

        elif event == self.connect_button:
            self.invoker.initialize_cmds(values[self.address])
            self.add_set_value_key(self.address, values[self.address])
            self.button_activation(False)
            self.initialize_set_values()

        elif event == self.disconnect_button:
            self.invoker.disengage_cmd()
            self.button_activation(True)
            self.add_set_value_key(self.address, 0)

        elif event == self.new_config_button:
            self.custom_config.open_creation_window()
            
        elif event == self.edit_config_button:
            file_name = values[self.config_file_combo]
            full_path = os.path.join("assets", "config", file_name)
            if not os.path.isfile(full_path):
                sg.popup_no_border("File does not exist", background_color=self.color_red)
                return True
            self.custom_config.open_creation_window(file=full_path)

        elif event == self.load_config_button:
            file_name = values[self.config_file_combo]
            full_path = os.path.join("assets", "config", file_name)
            if not os.path.isfile(full_path):
                sg.popup_no_border("File does not exist", background_color=self.color_red)
                return True
            if file_name:
                self.custom_config.open_config_window(full_path)
            else:
                sg.popup_no_border("File not chosen", background_color=self.color_red)

        elif event == self.set_points_button:
            cm.PointsCmd(values[self.curr_points_input]).check_and_do()
            self.add_set_value_key(self.curr_points_input, values[self.curr_points_input])

        elif event == self.set_average_pts_button:
            cm.AverageNoCmd(values[self.average_pts_input]).check_and_do()
            self.add_set_value_key(self.average_pts_input, values[self.average_pts_input])

        elif event in self.channels_checkboxes:
            if values[event]:
                cm.TurnOnChannelCmd(self.channel_number(event)).do()
                self._currently_set_values[self.channels].append(event)
            else:
                cm.TurnOffChannelCmd(self.channel_number(event)).do()
                self._currently_set_values[self.channels].remove(event)

        elif event == self.averaging_check:
            cm.AverageCmd().do(values[self.averaging_check])
            self.add_set_value_key(self.averaging_check, values[self.averaging_check])

        elif event == self.trimmed_check:
            self.is_data_reinterpreted = values[self.trimmed_check]
            self.add_set_value_key(self.trimmed_check, self.is_data_reinterpreted)

        elif event == self.preamble_check:
            if values[self.preamble_check]:
                cm.PreampleOnCmd().do()
            else:
                cm.PreambleOffCmd().do()
            self.add_set_value_key(self.preamble_check, values[self.preamble_check])

        elif event == self.single_button:
            mismatched = self.get_mismatched_inputboxes(values)
            if mismatched:
                self.mismatched_popup(mismatched)
                return True
            channels = self.get_set_value(self.channels)
            path = convert_path(values[self.curr_path])
            self.saving_text.update(visible=True, value="Saving...")
            if channels:
                self.invoker.single_cmds(channels, path, self.is_data_reinterpreted, self.saving_text)
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
            temp_file = convert_path(os.path.join(os.getenv("OSCI_MEASUREMENTS_DIR"), "temp.txt"))
            self.invoker.start_run_cmds(temp_file, channels)
            sg.popup_no_border("stop", title="Running", keep_on_top=True, background_color=self.color_red)
            self.saving_text.update(visible=True, value="Saving...")
            path = convert_path(values[self.curr_path])
            self.invoker.stop_run_cmds(temp_file, path, channels, is_preamble, self.is_data_reinterpreted, self.saving_text)

        elif event == self.reset_osci_button:
            reset_message = "reset osci"
            if sg.popup_get_text(f"Type '{reset_message}' to factory reset", keep_on_top=True) == reset_message:
                cm.FactoryResetCmd().do()
                return True
            sg.popup_no_border(f"Didn't reset, input wasn't '{reset_message}'", background_color=self.color_red)

        elif event == self.ping_osci_button:
            if cm.CheckIfResponsiveCmd().do():
                sg.popup_no_border("ping successful", background_color=self.color_green)
            else:
                sg.popup_no_border("couldn't ping", background_color=self.color_red)

        elif event == self.terminal_button:
            self.terminal.open_window()
            
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
            except (cm.CommandError, AdapterError) as error:
                sg.popup_no_border(error, background_color=self.color_red)

        if cm.adapter is not None:
            self.invoker.disengage_cmd()
        self.window.close()

    def channel_number(self, channel_string):
        return channel_string[2:]


def convert_path(path):
    return path.replace("/", os.sep)
