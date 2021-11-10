#!/bin/sh

folder=".venv"

python3 -m venv "$folder"
. "$folder"/bin/activate
python -m pip install -r src/requirements.txt