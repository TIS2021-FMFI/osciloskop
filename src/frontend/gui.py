import PySimpleGUI as sg
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from backend import functions as f

sg.theme("DarkAmber")

# Elements inside the window
layout = [
    [sg.Button("Connect"), sg.Button("Disconnect")],
    [sg.InputText("", key="terminal")],
    [sg.Radio("Channel 1", 1, default=True), sg.Radio("Channel 2", 1), sg.Radio("Channel 3", 1), sg.Radio("Channel 4", 1)],
    [sg.Input(), sg.SaveAs()],
    [sg.Listbox(values=["RAW", "average", "histogram H/V", "versus"], size=(15, 4))]
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