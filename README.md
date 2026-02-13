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
build_app.sh
build_app.bat
```

## One-command build (Linux)

Run this from repository root:

```bash
./build_app.sh
```

Output:
- `ev_app/dist/EVChargingApp`

## One full Linux command (no script)

```bash
cd /workspace/ev/ev_app && python3 -m pip install --upgrade pip && python3 -m pip install PyQt6 matplotlib pyinstaller bcrypt && gcc -shared -fPIC -o core.so core.c && python3 -m PyInstaller --onefile --windowed main.py --name EVChargingApp
```

## Linux fix for "Python was built without a shared library"

If you get this PyInstaller error, use a distro Python with shared `libpython`:

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-dev build-essential && cd /workspace/ev && python3 -m venv .venv && . .venv/bin/activate && ./build_app.sh
```

Or explicitly choose another Python interpreter:

```bash
PYTHON_BIN=/usr/bin/python3 ./build_app.sh
```

## One-command build (Windows EXE)

Run this from repository root:

```bat
build_app.bat
```

Output:
- `ev_app\dist\EVChargingApp.exe`

## Manual run (Linux)

```bash
cd ev_app
python3 -m pip install PyQt6 matplotlib bcrypt
gcc -shared -fPIC -o core.so core.c
python3 main.py
```

## Default admin
- Username: `admin`
- Password: `admin123`
