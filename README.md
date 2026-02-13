# EV Charging Station Management Desktop Application

Professional offline EV charging station management software with:
- **C core engine** for queue, slot allocation, charging simulation, and billing logic.
- **Python + PyQt6** SaaS-style desktop UI.
- **ctypes bridge** between UI and C engine.
- **SQLite** persistence for users, vehicles, and sessions.
- **Matplotlib analytics** in-app (daily + monthly revenue).

## Project structure

```text
ev_app/
    core.c
    core.h
    main.py
    login.py
    dashboard.py
    vehicles.py
    queue.py
    charging.py
    billing.py
    report.py
    database.py
    style.qss
build_app.bat
```

## One-command build (Windows EXE)

Run this from repository root:

```bat
build_app.bat
```

This single command will:
1. Install required Python packages.
2. Compile `core.c` to `core.dll`.
3. Build `EVChargingApp.exe` with PyInstaller.

Output:
- `ev_app\dist\EVChargingApp.exe`

## Manual steps (if preferred)

### 1) Compile C core
```bash
cd ev_app
gcc -shared -o core.dll core.c
```

### 2) Install dependencies
```bash
pip install PyQt6 matplotlib pyinstaller bcrypt
```

### 3) Start app
```bash
cd ev_app
python main.py
```

### 4) Build Windows EXE
```bash
cd ev_app
pyinstaller --onefile --windowed main.py --name EVChargingApp
```

## Default admin
- Username: `admin`
- Password: `admin123`
