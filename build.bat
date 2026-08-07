@echo off
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Guga --icon "assets\guga.ico" --add-data "assets\actions;assets\actions" --add-data "assets\guga.ico;assets" --add-data "config;config" main.py

echo.
echo Build complete: dist\Guga.exe

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
  "%ISCC%" installer.iss
  echo Installer complete: installer-output\Guga-Desktop-Pet-Setup.exe
) else (
  echo Inno Setup 6 was not found. Guga.exe was built, but the installer was skipped.
)
endlocal
