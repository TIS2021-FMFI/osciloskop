import PySimpleGUI as sg
import backend.command as cm
from backend.adapter import AdapterError


class Terminal:
    def __init__(self, gui):
        self.gui = gui
        self.window = None

    def open_window(self):
        self.input_ix = 0
        self.input_history = [""]

        def get_prev_input(self, event):
            if self.input_ix < len(self.input_history) - 1:
                self.input_ix += 1
            self.window[self.cmd_input].update(self.input_history[self.input_ix])

        def get_next_input(self, event):
            if self.input_ix > 0:
                self.input_ix -= 1
            self.window[self.cmd_input].update(self.input_history[self.input_ix])

        self.cmd_input, self.cmd_output, self.cmd_send = "cin", "cout", "csend"
        layout = [
            [sg.InputText(key=self.cmd_input, size=(50, 20)), sg.Button("Send", key=self.cmd_send, bind_return_key=True)],
            [sg.Multiline(key=self.cmd_output, disabled=True, size=(60, 450), autoscroll=True)],
        ]
        self.window = sg.Window("Terminal", layout, size=(450, 500), finalize=True)
        self.window[self.cmd_input].Widget.bind("<Up>", lambda e: get_prev_input(self, e))
        self.window[self.cmd_input].Widget.bind("<Down>", lambda e: get_next_input(self, e))
    
    def check_event(self, event, values):
        if event == sg.WIN_CLOSED:
            self.window.close()
            self.window = None
        if event != self.cmd_send:
            return
        self.window[self.cmd_input].update("")
        cmd_in = values[self.cmd_input]
        if cmd_in:
            self.input_history.insert(1, cmd_in)
        self.input_ix = 0
        self.window[self.cmd_output].update(value=f">>> {cmd_in}\n", append=True)
        cmd_in_split = [i.lower().strip() for i in cmd_in.split()]
        if not cmd_in_split:
            return
        if cmd_in.lower() in ("clr", "cls", "clear"):
            self.window[self.cmd_output].update("")
            return
        if cmd_in_split[0] == "q":  # asking for output
            try:
                output = cm.CustomCmdWithOutput(cmd_in).do()
            except AdapterError as e:
                sg.popup_no_border(e, background_color=self.gui.color_red)
                return
            self.window[self.cmd_output].update(value=output + "\n", append=True)
        else:
            try:
                cm.CustomCmd(cmd_in).do()
                cmd = " ".join(cmd_in_split[:-1])
                val = cmd_in_split[-1]
                if cmd in self.gui._currently_set_values:
                    self.gui.add_set_value_key(cmd, val)
                    self.gui.update_info()
            except AdapterError as e:
                sg.popup_no_border(e, background_color=self.gui.color_red)

