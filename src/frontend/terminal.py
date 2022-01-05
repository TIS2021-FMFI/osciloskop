import PySimpleGUI as sg
from backend.command import *
from backend.adapter import AdapterError


class Terminal:
    def __init__(self, gui):
        self.gui = gui

    def open_window(self):
        input_ix = 0
        input_history = [""]

        def get_prev_input(self, event):
            nonlocal input_ix
            if input_ix < len(input_history) - 1:
                input_ix += 1
            window[cmd_input].update(input_history[input_ix])

        def get_next_input(self, event):
            nonlocal input_ix
            if input_ix > 0:
                input_ix -= 1
            window[cmd_input].update(input_history[input_ix])

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
                input_ix = 0
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
                        sg.popup_no_border(e, background_color=self.gui.color_red)
                        continue
                    window[cmd_output].update(value=output + "\n", append=True)
                else:
                    try:
                        CustomCmd(cmd_in).do()
                        cmd = " ".join(cmd_in_split[:-1])
                        val = cmd_in_split[-1]
                        if cmd in self.gui._currently_set_values:
                            self.gui.add_set_value_key(cmd, val)
                            self.gui.update_info()
                    except AdapterError as e:
                        sg.popup_no_border(e, background_color=self.gui.color_red)

            elif event in (sg.WIN_CLOSED, "Close"):
                break
        window.close()
