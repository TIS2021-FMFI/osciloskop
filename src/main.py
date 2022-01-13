import os
import sys
import PySimpleGUI as sg
from frontend.gui import GUI
from dotenv import load_dotenv

ENV_PATH = ".env"

def make_dirs():
    paths = [os.getenv("OSCI_MEASUREMENTS_DIR"),
        os.getenv("OSCI_CONFIG_DIR"),
        os.getenv("OSCI_HPCTRL_DIR")]
    for path in paths:
        os.makedirs(path)


if __name__ == "__main__":
    if not os.path.isfile(ENV_PATH):
        error_message = f"{ENV_PATH} file not found"
        sg.PopupError(error_message)
        sys.exit(error_message)
    load_dotenv(ENV_PATH)
    try:
        make_dirs()
    except FileExistsError:
        pass
    gui = GUI()
    gui.main_loop()
