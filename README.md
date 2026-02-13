# EV Charging Station Management App (WinAPI, C)

## Build command
Use the following command in a Windows MinGW/MSYS shell:

```bat
gcc main.c gui.c auth.c vehicle.c queue.c charging.c billing.c storage.c chart.c -o EVChargingApp.exe -mwindows -lcomctl32
```

## One-click build
You can also run:

```bat
build.bat
```

This compiles the app and generates `EVChargingApp.exe`.


## Login credentials
- **Admin login:** `admin` / `admin123`
- **Vehicle owner login:** Username = Owner Name, Password = Vehicle Number
