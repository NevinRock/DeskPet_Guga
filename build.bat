@echo off
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Guga --add-data "assets;assets" --add-data "config;config" main.py

echo.
echo Build complete: dist\Guga.exe
endlocal
