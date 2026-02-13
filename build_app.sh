#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$REPO_DIR/ev_app"
cd "$APP_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

check_shared_python() {
  "$PYTHON_BIN" - <<'PY'
import sysconfig, pathlib
libname = sysconfig.get_config_var("LDLIBRARY")
libdir = sysconfig.get_config_var("LIBDIR")
if not libname or not libdir:
    raise SystemExit(1)
if not (pathlib.Path(libdir) / libname).exists():
    raise SystemExit(1)
print(pathlib.Path(libdir) / libname)
PY
}

if ! SHARED_LIB_PATH="$(check_shared_python 2>/dev/null)"; then
  echo "ERROR: Current Python ($PYTHON_BIN) has no visible shared libpython; PyInstaller cannot build on Linux with this interpreter."
  echo
  echo "Fix (Ubuntu/Debian) - run exactly:"
  echo "  sudo apt update && sudo apt install -y python3 python3-venv python3-dev build-essential"
  echo "  cd $REPO_DIR && python3 -m venv .venv && . .venv/bin/activate && ./build_app.sh"
  echo
  echo "Or point to another Python that has libpython:"
  echo "  PYTHON_BIN=/usr/bin/python3 ./build_app.sh"
  exit 1
fi

echo "Using Python: $PYTHON_BIN"
echo "Detected shared library: $SHARED_LIB_PATH"

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install PyQt6 matplotlib pyinstaller bcrypt

gcc -shared -fPIC -o core.so core.c

if [[ ! -f core.so ]]; then
  echo "ERROR: core.so build failed."
  exit 1
fi

"$PYTHON_BIN" -m PyInstaller --onefile --windowed --add-data "style.qss:." --add-binary "core.so:." main.py --name EVChargingApp

echo
printf 'Build complete: %s\n' "$APP_DIR/dist/EVChargingApp"
