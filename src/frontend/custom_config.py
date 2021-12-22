from os import listdir, path as ospath, sep
import PySimpleGUI as sg
import re
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

        input_char = "#"
        unit_char = "?"
        rows = []
        buttons = {}  # button_key: [key1, key2, key3, ..]
        txt_size=(30, 1)
        lines = [line.strip() for line in open(file_name).readlines()]
        for i, line in enumerate(lines):
            split_by_special = re.split(f"(\\{input_char}|\\{unit_char})", line)
            curr_row = []
            buttons[i] = []
            for j, x in enumerate(split_by_special):
                x = x.strip()
                curr_key = f"{i}/{j}"
                if x == input_char:
                    curr_row.append(sg.InputText("", size=(10, 1), key=curr_key))
                elif x == unit_char:
                    curr_row.append(
                        sg.Combo(values=["s", "ms", "µs", "ns", "ps"], default_value="ms", key=curr_key)
                    )
                else:
                    # todo idk how to read sg.Text, prolly window[text]? for now it's input
                    curr_row.append(sg.InputText(x, size=(10, 1), key=curr_key))
                buttons[i].append(curr_key)
            curr_row.append(sg.Button("Set", key=i))
            rows.append(list(curr_row))
        rows.append([sg.Button("Set all"), sg.Button("Close")])
        column_height = 500
        scroll = True
        rows_height = len(rows) * 35
        if rows_height < 500:
            column_height = rows_height
            scroll = False
        return (sg.Column(rows, scrollable=scroll, vertical_scroll_only=True, size=(400, column_height)), buttons)

    def _run_command(self, values):
        if "" in values:
            sg.Popup("Something is empty")
            return
        command = " ".join(values)
        print(command)
        # CustomCmd(command).do()

        # if input_key is not None:
        #     val = values[input_key]
        # else:
        #     cmd, val = " ".join(cmd.split()[:-1]), cmd.split()[-1]
        # if not val:
        #     sg.popup_no_border(f"No value in {cmd}", background_color=self.color_red)
        #     return
        # if not cmd:
        #     cmd, val = val, cmd
        # if not val:
        #     val = "set"
        # self.add_set_value_key(cmd, val)
        # self.update_info()


    def open_window(self, file_name):
        layout, button_input_map = self._create_layout(file_name)
        window = sg.Window("Run config", [[layout]])
        while True: # button key - button_input_map.key (command), input key - button_input_map[command]
            event, values = window.read()
            if event == "Set all":
                for keys in button_input_map.values():
                    self._run_command([values[x] for x in keys])
            elif event in button_input_map.keys():
                self._run_command([values[x] for x in button_input_map[event]])
            elif event in (sg.WIN_CLOSED, "Close"):
                break
        window.close()

    def create_file(self, config_content, file_name, window):
        if config_content:
            open(ospath.join("assets", "config", file_name), "w").write(config_content)
            self.gui.window[self.gui.config_file_combo].update(
                values=list(listdir(ospath.join("assets", "config")))
            )