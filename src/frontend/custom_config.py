import os
import PySimpleGUI as sg
import backend.command as cm


class CustomConfig:
    # cache[file_name] = []Cmd()
    cache = {}
    input_char = "#"

    def __init__(self, gui):
        self.gui = gui
        self.window = None
        self.window_name = None

    class Cmd:
        def __init__(self, line, input_char):
            self.key = "s " + line
            self.edit_key = self.key + "_edit"
            self.input_from_user = ""
            self.layout = []
            self.input_char = input_char
            self.is_editable = self.input_char in line

        def __str__(self):
            if self.is_editable:
                return self.key.replace(self.input_char, self.input_from_user, 1)
            return self.key

    def open_creation_window(self, file=None):
        # opens a new window for creating a new configuration file
        if self.window:
            return
        if file:
            filename = file.split(os.sep)[-1]
            with open(file) as f:
                self.cfg_content = f.read()
        else:
            filename = ""
            self.cfg_content = ""
        layout = [
            [sg.Multiline(self.cfg_content, key="cfg_input", size=(50, 20))],
            [sg.Text("Config name:"), sg.InputText(filename, key="cfg_name", size=(20, 1))],
            [sg.Button("Save"), sg.Button("Discard changes"), sg.Button("Help")],
        ]
        self.window_name = "Config"
        self.window = sg.Window(self.window_name, [[sg.Col(layout, element_justification="c")]], finalize=True)
    
    def check_creation_event(self, event, values):
        config_content = ""
        config_name = ""
        if event == "Discard changes":
            if values["cfg_input"] != self.cfg_content:  # ask only if nothing is written
                ans = sg.popup_yes_no("Are you sure you want to discard current changes?")
                if ans == "Yes":
                    self.close_window()
            else:
                self.close_window()
        elif event == "Save":
            if not values["cfg_name"]:
                sg.popup_no_border("Config name is empty", background_color=self.gui.color_red)
            else:
                config_content = values["cfg_input"]
                config_name = values["cfg_name"]
                self.close_window()
                self.create_file(config_content, config_name)
                if config_name:
                    self.gui.window[self.gui.config_file_combo].update(value=config_name)
        elif event == "Help":
            sg.popup_no_border(
                """Write one command per line.
's ' will be automatically included before every command.
Use '#' in a command for a variable input.
\nExample:
:example:command 20
:another:example #"""
            )
        elif event == sg.WIN_CLOSED:
            self.close_window()

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
            cmds = self.cache[os.path.basename(file_name)]
            for cmd in cmds:
                rows.append(parse_line(cmd.key, cmd.edit_key, cmd.input_from_user))
        except KeyError:
            with open(file_name) as f:
                lines = [" ".join(line.split()) for line in f.readlines()]
            for line in lines:
                cmd = self.Cmd(line, self.input_char)
                cmds.append(cmd)
                rows.append(parse_line(cmd.key, cmd.edit_key))
            self.cache[os.path.basename(file_name)] = cmds

        rows.append([sg.Button("Set all"), sg.Button("Close")])

        column_height = 500
        scroll = True
        rows_height = len(rows) * 35
        if rows_height < 500:
            column_height = rows_height
            scroll = False

        return sg.Column(rows, scrollable=scroll, vertical_scroll_only=True, size=(400, column_height))

    def run_command(self, cmd):
        cm.CustomCmd(str(cmd)).do()
        self.gui.add_set_value_key(cmd, "")
        self.gui.update_info()

    def open_config_window(self, file_name):
        if self.window:
            return
        layout = self.create_layout(file_name)
        self.cmds = self.cache[os.path.basename(file_name)]
        self.window_name = "Run config"
        self.window = sg.Window(self.window_name, [[layout]], finalize=True)

    def check_config_event(self, event, values):
        if event in (sg.WIN_CLOSED, "Close"):
            self.close_window()
            return
        _cmds = self.cmds if event == "Set all" else [next(cmd for cmd in self.cmds if cmd.key == event)]
        for cmd in _cmds:
            if cmd.is_editable:
                cmd.input_from_user = values[cmd.edit_key].strip()
                if not cmd.input_from_user:
                    sg.popup_no_border(
                        f"'{cmd}' has no input",
                        background_color=self.gui.color_red,
                    )
                    break
            self.run_command(cmd)

    def create_file(self, config_content, file_name):
        # purge cache
        try:
            del self.cache[os.path.basename(file_name)]
        except KeyError:
            pass

        if config_content:
            with open(os.path.join("assets", "config", file_name), "w") as f:
                f.write(config_content)
            self.gui.window[self.gui.config_file_combo].update(values=list(os.listdir(os.path.join("assets", "config"))))
            
    def close_window(self):
        self.window.close()
        self.window = None
        self.window_name = None
        
    def check_event(self, event, values):
        if self.window_name == "Config":
            self.check_creation_event(event, values)
        elif self.window_name == "Run config":
            self.check_config_event(event, values)
