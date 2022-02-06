#!/bin/sh

folder=".venv"

rm -rf "$folder"
python3 -m venv "$folder"
. "$folder"/bin/activate
python -m pip install -r requirements.txt