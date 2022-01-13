# HP83480A oscilloscope GUI application

## Requirements
Install Python modules: `pip install -r requirements.txt`

[hpctrl](https://github.com/TIS2020-FMFI/hpctrl): put `connect.ini` in the [root folder](/) and `hpctrl.exe`, `winvfx.16.dll`, `gpiblib.dll` in [tools/hpctrl](tools/hpctrl)

Application won't launch without `.env` in the [root folder](/).

## Binary compilation
`
pyinstaller --noconfirm --onefile --noconsole --windowed --hidden-import "pysimplegui" --hidden-import "python-dotenv" --icon "assets\icon\icon.ico" --name "OscilloscopeCtrl" "src\main.py"
`

## Screenshots
Main window  
![Main window](assets/screenshots/main.png)

Terminal  
![Terminal](assets/screenshots/terminal.png)

Creating config  
![Creating config](assets/screenshots/config_new.png)

Loading config  
![Loading config](assets/screenshots/config_load.png)