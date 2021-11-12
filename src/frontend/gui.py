import PySimpleGUI as sg
import backend.functions as f
import threading

class GUI:

    def __init__(self):
        self.func = f.Functions()
        sg.theme("DarkAmber")
        self.layout = self.create_layout()
        self.window = sg.Window("GUI application", self.layout, size=(500, 500), element_justification="center")

    def create_layout(self): 
        button_size = (10, 1)
        # Elements inside the window
        win_1 = [
            [sg.InputText("Address No.", key="terminal", size=(12, 1)), sg.Button("Connect", size=button_size)],
            [sg.Button("Terminal", size=button_size), sg.Button("Disconnect", size=button_size)]
        ]
        win_2 = [
            [sg.InputText("Average No.", size=(15, 1), key="average")],
            [sg.InputText("Points 16-4096", size=(15, 1), key="points")],
            [sg.Button("RESET", size=(12, 1))]
        ]
        win_3 = [
            [sg.Checkbox("Channel 1"), sg.Checkbox("Channel 2")],
            [sg.Checkbox("Channel 3"), sg.Checkbox("Channel 4")],
            [sg.Combo(values=["RAW", "average", "histogram H/V", "versus"], default_value="RAW")],
            [sg.InputText("FILE_NAME", size=(25, 1)), sg.SaveAs("PATH/")],
            [sg.Button("SAVE", size=button_size), sg.Checkbox("AutoSave")],
            [sg.Button("SINGLE", size=button_size), sg.Button("STOP", size=button_size), sg.Button("SINGLE", size=button_size)]
        ]
        win_4 = [
            [sg.Button("Send custom", size=button_size), sg.InputText("AAA", size=(15, 1), key="custom")],
            [sg.Button("Quit GUI", size=button_size)],
            [sg.Button("FREEZE BUTTON", size=button_size)]
        ]

        return [
            [sg.Frame(layout=win, title='', element_justification="c")]
            for win in (win_1, win_2, win_3, win_4)
        ]

    def run(self):
        # Event loop
        while True:
            event, values = self.window.read()
            if event == "Connect":
                threading.Thread(target=self.func.connect).start()
            if event == "Disconnect":
                threading.Thread(target=self.func.disconnect).start()
            if event == "Send custom":
                threading.Thread(target=self.func.send_custom, args=(values["custom"],)).start()
            if event == "FREEZE BUTTON":
                threading.Thread(target=self.func._freeze_test).start()
            if event in (sg.WIN_CLOSED, "Quit GUI"):
                break

        self.window.close()