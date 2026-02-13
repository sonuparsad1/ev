@echo off
setlocal
cd /d %~dp0\ev_app
python -m pip install --upgrade pip
python -m pip install PyQt6 matplotlib pyinstaller bcrypt
gcc -shared -o core.dll core.c
pyinstaller --onefile --windowed main.py --name EVChargingApp
echo.
echo Build complete: %~dp0ev_app\dist\EVChargingApp.exe
endlocal
