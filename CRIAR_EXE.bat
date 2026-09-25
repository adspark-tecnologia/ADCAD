@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt
py -m PyInstaller --noconfirm --onefile --windowed --name ADCAD main.py
pause
