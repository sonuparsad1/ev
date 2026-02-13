import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from dashboard import DashboardWindow
from database import init_db, query
from login import LoginWidget
from queue import CoreEngine


def ensure_default_admin():
    import bcrypt
    from database import execute

    existing = query("SELECT id FROM users WHERE username='admin'", one=True)
    if existing:
        return
    execute(
        "INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
        ("admin", bcrypt.hashpw(b"admin123", bcrypt.gensalt()), "Admin"),
    )


def apply_styles(app):
    qss = Path(__file__).resolve().parent / "style.qss"
    app.setStyleSheet(qss.read_text(encoding="utf-8"))


def main():
    init_db()
    ensure_default_admin()
    app = QApplication(sys.argv)
    apply_styles(app)

    engine = CoreEngine()

    state = {}

    def on_success(user):
        win = DashboardWindow(engine, user)
        win.show()
        state["dashboard"] = win
        state["login"].close()

    login = LoginWidget(on_success)
    state["login"] = login
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
