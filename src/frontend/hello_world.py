import PySimpleGUI as sg

sg.theme("DarkAmber")

# Elements inside the window
layout = [
    [sg.Button("Show text below")],
    [sg.InputText("Hello World", key="user_input")]
]

# Create the window
window = sg.Window("GUI application", layout, size=(200, 100), element_justification="center");

# Event loop
while True:
    event, values = window.read();
    if event == "Show text below":
        sg.popup(values["user_input"], no_titlebar=True, auto_close_duration=1, auto_close=True, background_color="black")
    if event == sg.WIN_CLOSED:
        break

window.close();