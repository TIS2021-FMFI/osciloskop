from os import listdir, path as ospath, sep
import PySimpleGUI as sg
from backend.command import *


class CustomConfig:
    def __init__(self, gui):
        self.gui = gui

    def open_creation(self, file=None):
        # opens a new window for creating a new configuration file
        if file:
            filename = file.split(sep)[-1]
            cfg_content = open(file).read()
        else:
            filename = ""
            cfg_content = ""
        layout = [
            [sg.Multiline(cfg_content, key="cfg_input", size=(50, 20))],
            [sg.Text("Config name:"), sg.InputText(filename, key="cfg_name", size=(20, 1))],
            [sg.Button("Save"), sg.Button("Discard changes"), sg.Button("Help")],
        ]
        window = sg.Window("Config", [[sg.Col(layout, element_justification="c")]])
        config_content = ""
        config_name = ""
        while True:
            event, values = window.read()
            if event == "Discard changes":
                if values["cfg_input"]:  # ask only if nothing is written
                    ans = sg.popup_yes_no("Are you sure you want to discard current changes?")
                    if ans == "No":
                        continue
                break
            elif event == "Save":
                if not values["cfg_name"]:
                    sg.popup_no_border("Config name is empty", background_color=self.gui.color_red)
                else:
                    config_content = values["cfg_input"]
                    config_name = values["cfg_name"]
                    break
            elif event == "Help":
                sg.popup_no_border(
                    """Write one command per line
Include 's' before a command
'#' at the end of a command for a variable input
\nExample:
s :acquire:points 20
s :acquire:count #"""
                )
            elif event == sg.WIN_CLOSED:
                break
        window.close()
        return (config_content, config_name)

    def _create_layout(self, file_name):
        def parse_line(line):
            if "#" in line:
                return " ".join(line.split()[:-1]), True
            return line, False

        rows = []  # layout rows
        buttons = {}  # command: <input> (None if no input #)
        txt_size = (30, 1)
        lines = [line.strip() for line in open(file_name).readlines()]
        for line in lines:
            if not line:
                continue
            input_key = None
            cmd, has_input = parse_line(line)
            rows.append([sg.Text(cmd, size=txt_size), sg.Button("Set", key=cmd)])
            if has_input:  # hashtag in line, add input element
                input_key = f"input {len(rows)-1}"
                # input_default = self.get_set_value(cmd) if cmd.lower() in self._currently_set_values else ""
                input_default = None
                rows[-1].insert(1, sg.InputText(input_default, size=(10, 1), key=input_key))
            buttons[cmd] = input_key
        rows.append([sg.Button("Set all"), sg.Button("Close")])
        column_height = 500
        scroll = True
        rows_height = len(rows) * 35
        if rows_height < 500:
            column_height = rows_height
            scroll = False
        return (
            sg.Column(rows, scrollable=scroll, vertical_scroll_only=True, size=(400, column_height)),
            buttons,
        )

    def _run_command(self, values, cmd, input_key):
        if input_key is not None:
            val = values[input_key]
        else:
            cmd, val = " ".join(cmd.split()[:-1]), cmd.split()[-1]
        if not val:
            sg.popup_no_border(f"No value in {cmd}", background_color=self.gui.color_red)
            return
        if not cmd:
            cmd, val = val, cmd
        if not val:
            val = "set"
        CustomCmd(f"{cmd} {val}").do()
        self.gui.add_set_value_key(cmd, val)
        self.gui.update_info()

    def open_window(self, file_name):
        layout, button_input_map = self._create_layout(file_name)
        window = sg.Window("Run config", [[layout]])
        while True:  # button key - button_input_map.key (command), input key - button_input_map[command]
            event, values = window.read()
            if event == "Set all":
                for cmd, input_key in button_input_map.items():
                    self._run_command(values, cmd, input_key)
            elif event in button_input_map.keys():
                self._run_command(values, event, button_input_map[event])
            elif event in (sg.WIN_CLOSED, "Close"):
                break
        window.close()

    def create_file(self, config_content, file_name, window):
        if config_content:
            open(ospath.join("assets", "config", file_name), "w").write(config_content)
            self.gui.window[self.gui.config_file_combo].update(values=[f for f in listdir(ospath.join("assets", "config"))])
