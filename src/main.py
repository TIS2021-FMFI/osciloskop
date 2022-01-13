import os
import sys
import PySimpleGUI as sg
from frontend.gui import GUI
from dotenv import load_dotenv

env_path = ".enva"

def make_dirs():
    paths = [os.getenv("OSCI_MEASUREMENTS_DIR"),
        os.getenv("OSCI_CONFIG_DIR"),
        os.getenv("OSCI_HPCTRL_DIR")]
    for path in paths:
        os.makedirs(path)


if __name__ == "__main__":
    if not os.path.isfile(env_path):
        error_message = f"{env_path} file not found"
        sg.PopupError(error_message)
        sys.exit(error_message)
    load_dotenv(env_path)
    try:
        make_dirs()
    except FileExistsError:
        pass
    gui = GUI()
    gui.main_loop()
