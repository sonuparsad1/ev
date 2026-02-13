@echo off
echo Building EV Charging App...
gcc main.c gui.c auth.c vehicle.c queue.c charging.c billing.c storage.c chart.c -o EVChargingApp.exe -mwindows -lcomctl32
if %errorlevel%==0 (
    echo Build Successful!
) else (
    echo Build Failed!
)
pause
