import bcrypt
from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database import execute, query

MAX_ATTEMPTS = 5


class LoginWidget(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 40, 80, 40)
        title = QLabel("EV Charging Cloud")
        title.setObjectName("title")

        form = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.role = QComboBox()
        self.role.addItems(["Admin", "Operator"])

        form.addRow("Username", self.username)
        form.addRow("Password", self.password)
        form.addRow("Role", self.role)

        buttons = QHBoxLayout()
        login_btn = QPushButton("Login")
        reg_btn = QPushButton("Register")
        login_btn.clicked.connect(self.login)
        reg_btn.clicked.connect(self.register)
        buttons.addWidget(login_btn)
        buttons.addWidget(reg_btn)

        layout.addWidget(title)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def register(self):
        username = self.username.text().strip()
        password = self.password.text().strip()
        role = self.role.currentText()
        if not username or not password:
            return
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            execute(
                "INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                (username, pw_hash, role),
            )
            QMessageBox.information(self, "Done", "Registered.")
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))

    def shake_error(self):
        anim = QPropertyAnimation(self, b"pos")
        p = self.pos()
        anim.setDuration(280)
        anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        anim.setKeyValueAt(0.0, QPoint(p.x(), p.y()))
        anim.setKeyValueAt(0.25, QPoint(p.x() - 14, p.y()))
        anim.setKeyValueAt(0.5, QPoint(p.x() + 14, p.y()))
        anim.setKeyValueAt(1.0, QPoint(p.x(), p.y()))
        anim.start()
        self._anim = anim

    def login(self):
        username = self.username.text().strip()
        password = self.password.text().strip()
        role = self.role.currentText()
        user = query("SELECT * FROM users WHERE username=?", (username,), one=True)

        if not user or user["role"] != role or user["is_locked"]:
            self.shake_error()
            QMessageBox.warning(self, "Denied", "Invalid account.")
            return

        if bcrypt.checkpw(password.encode(), user["password_hash"]):
            execute("UPDATE users SET failed_attempts=0 WHERE id=?", (user["id"],))
            self.on_success(dict(user))
            return

        failed = user["failed_attempts"] + 1
        locked = 1 if failed >= MAX_ATTEMPTS else 0
        execute(
            "UPDATE users SET failed_attempts=?, is_locked=? WHERE id=?",
            (failed, locked, user["id"]),
        )
        self.shake_error()
        QMessageBox.warning(self, "Denied", "Wrong password.")
