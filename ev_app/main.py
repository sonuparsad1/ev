import atexit
import logging
import sys
import traceback
from pathlib import Path

from PyQt6.QtCore import QLockFile, Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

from dashboard import DashboardWindow
from database import init_db, query
from login import LoginWidget
from queue import CoreEngine


APP_NAME = "VoltOS EV Charging Station"
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "error.log"
LOCK_FILE = Path(__file__).resolve().parent / "ev_app.lock"


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def resource_path(name: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")) / name
    return Path(__file__).resolve().parent / name


def apply_styles(app: QApplication) -> None:
    qss = resource_path("style.qss")
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))


def ensure_default_admin() -> None:
    import bcrypt
    from database import execute

    existing = query("SELECT id FROM users WHERE username='admin'", one=True)
    if not existing:
        execute(
            "INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
            ("admin", bcrypt.hashpw(b"admin123", bcrypt.gensalt()), "Admin"),
        )


def show_fatal_error(message: str) -> None:
    QMessageBox.critical(None, "Unexpected Error", message)


def install_exception_hooks() -> None:
    def handle_exception(exc_type, exc_value, exc_traceback):
        details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.error("Unhandled exception\n%s", details)
        show_fatal_error("The application hit an unexpected error. Details were written to logs/error.log.")

    sys.excepthook = handle_exception


def main() -> int:
    configure_logging()
    logging.info("Starting %s", APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(True)

    lock = QLockFile(str(LOCK_FILE))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.warning(None, "Already Running", "An instance of VoltOS is already running.")
        return 1

    atexit.register(lock.unlock)

    install_exception_hooks()
    try:
        init_db()
        ensure_default_admin()
        apply_styles(app)

        engine = CoreEngine()
        state = {}

        def on_success(user):
            try:
                win = DashboardWindow(engine, user)
                win.show()
                state["dashboard"] = win
                state["login"].close()
            except Exception:
                logging.exception("Failed to open dashboard window")
                show_fatal_error("Unable to open dashboard. Please check logs/error.log.")

        login = LoginWidget(on_success)
        login.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        state["login"] = login
        login.show()
        return app.exec()
    except Exception:
        logging.exception("Fatal startup failure")
        show_fatal_error("Startup failed. Please review logs/error.log.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
