import os
from frontend.gui import GUI


def make_dirs():
    paths = ["assets/measurements", "assets/config", "tools/hpctrl"]
    for path in paths:
        os.makedirs(path)


if __name__ == "__main__":
    try:
        make_dirs()
    except FileExistsError:
        pass
    gui = GUI()
    gui.main_loop()
