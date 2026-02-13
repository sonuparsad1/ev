# EV Charging Station Management Desktop Application

Production-focused EV charging station management software with:
- **C core engine** for queue, slot allocation, charging simulation, and billing logic.
- **Python + PyQt6** professional dark-dashboard desktop UI.
- **Global exception handling + file logging** (`ev_app/logs/error.log`).
- **SQLite persistence** for users, vehicles, charging sessions, rate history, revenue history, and settings.
- **PyInstaller packaging** for installable Windows executables.

## Project structure

```text
ev_app/
    main.py
    login.py
    dashboard.py
    vehicles.py
    charging.py
    report.py
    settings.py
    queue.py
    database.py
    core.c
    core.h
    style.qss
    logs/
        error.log
    ui/
        dashboard.py
        vehicles.py
        charging.py
        analytics.py
        settings.py
    backend/
        database.py
        logic.py
        rate_manager.py
    assets/
        icons/
        styles/
```

## Windows build (single EXE)

From inside `ev_app`:

```bat
pyinstaller --onefile --windowed --icon=app.ico main.py
```

Recommended command including native engine and stylesheet:

```bat
pyinstaller --onefile --windowed --icon=app.ico --add-data "style.qss;." --add-binary "core.dll;." main.py --name EVChargingApp
```

## Linux run

```bash
cd ev_app
python3 -m pip install PyQt6 matplotlib bcrypt
gcc -shared -fPIC -o core.so core.c
python3 main.py
```

## Default admin
- Username: `admin`
- Password: `admin123`
