from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database import execute, get_setting, set_setting


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self.load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        form = QFormLayout()
        self.base_rate = QLineEdit()
        self.peak_rate = QLineEdit()
        self.offpeak_rate = QLineEdit()
        self.total_slots = QLineEdit()
        self.peak_enabled = QCheckBox("Enable peak pricing")
        self.theme_toggle = QCheckBox("Light theme")

        form.addRow("Base rate (₹/kWh)", self.base_rate)
        form.addRow("Peak rate (₹/kWh)", self.peak_rate)
        form.addRow("Off-peak rate (₹/kWh)", self.offpeak_rate)
        form.addRow("Total slots", self.total_slots)
        form.addRow(self.peak_enabled)
        form.addRow(self.theme_toggle)

        actions = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save)
        reset_btn = QPushButton("Reset System Data")
        reset_btn.clicked.connect(self.reset_system)
        actions.addWidget(save_btn)
        actions.addWidget(reset_btn)

        root.addLayout(form)
        root.addLayout(actions)

    def load(self):
        self.base_rate.setText(get_setting("base_rate", "12.5"))
        self.peak_rate.setText(get_setting("peak_rate", "18.0"))
        self.offpeak_rate.setText(get_setting("offpeak_rate", "9.5"))
        self.total_slots.setText(get_setting("total_slots", "6"))
        self.peak_enabled.setChecked(get_setting("peak_enabled", "1") == "1")
        self.theme_toggle.setChecked(get_setting("theme", "dark") == "light")

    def save(self):
        try:
            base = float(self.base_rate.text())
            peak = float(self.peak_rate.text())
            offpeak = float(self.offpeak_rate.text())
            slots = int(self.total_slots.text())
            if min(base, peak, offpeak) <= 0 or slots < 1:
                raise ValueError("Values must be positive.")
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Settings", str(exc))
            return

        set_setting("base_rate", base)
        set_setting("peak_rate", peak)
        set_setting("offpeak_rate", offpeak)
        set_setting("total_slots", slots)
        set_setting("peak_enabled", "1" if self.peak_enabled.isChecked() else "0")
        set_setting("theme", "light" if self.theme_toggle.isChecked() else "dark")
        QMessageBox.information(self, "Saved", "Settings updated")

    def reset_system(self):
        execute("DELETE FROM sessions")
        execute("DELETE FROM vehicles")
        QMessageBox.information(self, "Reset", "System data cleared")
