import PySimpleGUI as sg
from backend import functions as f

sg.theme("DarkAmber")

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

layout = [
    [sg.Frame(layout=win_1, title='', element_justification="c")],
    [sg.Frame(layout=win_2, title='', element_justification="c")],
    [sg.Frame(layout=win_3, title='', element_justification="c")]
]

# Create the window
window = sg.Window("GUI application", layout, size=(500, 400), element_justification="center")

def run():
    # Event loop
    while True:
        event, values = window.read()
        if event == "Connect":
            f.connect()
        if event == "Disconnect":
            f.disconnect()
        if event == sg.WIN_CLOSED:
            break

    window.close()