from os import listdir, path as ospath, sep
import PySimpleGUI as sg
from backend.command import *


class CustomConfig:
    # cache[file_name] = []Cmd()
    cache = {}
    input_char = "#"

    def __init__(self, gui):
        self.gui = gui

    class Cmd:
        def __init__(self, line, input_char):
            self.key = line
            self.edit_key = self.key + "_edit"
            self.input_from_user = ""
            self.layout = []
            self.input_char = input_char
            self.is_editable = self.input_char in line

        def __str__(self):
            if self.is_editable:
                return self.key.replace(self.input_char, self.input_from_user, 1)
            return self.key

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
's ' will be automatically included before every command
use '#' in a command for a variable input
\nExample:
:example:command 20
:another:example #"""
                )
            elif event == sg.WIN_CLOSED:
                break
        window.close()
        return (config_content, config_name)

    def create_layout(self, file_name):
        def parse_line(line, edit_key, input_from_user=""):
            res = []
            input_size = (10, 1)
            try:
                pos = line.index(self.input_char)
                res.append(sg.Text(line[:pos]))
                res.append(sg.InputText(input_from_user, size=input_size, key=edit_key))
                res.append(sg.Text(line[pos + 1 :]))
            except ValueError:
                res.append(sg.Text(line))
            res.append(sg.Button("Set", key=line))
            return res

        rows = []
        cmds = []

        # get from cache
        try:
            cmds = self.cache[file_name]
            for cmd in cmds:
                rows.append(parse_line(cmd.key, cmd.edit_key, cmd.input_from_user))
        except KeyError:
            lines = [" ".join(line.split()) for line in open(file_name).readlines()]
            for line in lines:
                cmd = self.Cmd(line, self.input_char)
                cmds.append(cmd)
                rows.append(parse_line(line, cmd.edit_key))
            self.cache[file_name] = cmds

        rows.append([sg.Button("Set all"), sg.Button("Close")])

        column_height = 500
        scroll = True
        rows_height = len(rows) * 35
        if rows_height < 500:
            column_height = rows_height
            scroll = False

        return sg.Column(rows, scrollable=scroll, vertical_scroll_only=True, size=(400, column_height))

    def run_command(self, cmd):
        CustomCmd("s " + str(cmd)).do()
        self.gui.add_set_value_key(cmd, "")
        self.gui.update_info()

    def open_window(self, file_name):
        layout = self.create_layout(file_name)
        cmds = self.cache[file_name]

        window = sg.Window("Run config", [[layout]])
        while True:
            event, values = window.read()

            if event in (sg.WIN_CLOSED, "Close"):
                break
            else:
                _cmds = cmds if event == "Set all" else [next(cmd for cmd in cmds if cmd.key == event)]
                for cmd in _cmds:
                    if cmd.is_editable:
                        cmd.input_from_user = values[cmd.edit_key]
                    self.run_command(cmd)

        window.close()

    def create_file(self, config_content, file_name):
        # purge cache
        try:
            del self.cache[file_name]
        except KeyError:
            pass

        if config_content:
            open(ospath.join("assets", "config", file_name), "w").write(config_content)
            self.gui.window[self.gui.config_file_combo].update(values=list(listdir(ospath.join("assets", "config"))))
