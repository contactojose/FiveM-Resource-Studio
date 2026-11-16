#!/bin/bash
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --clean --windowed --name "FiveM Resource Studio" FiveM_Resource_Studio.py
echo "App generada en dist/FiveM Resource Studio.app"
