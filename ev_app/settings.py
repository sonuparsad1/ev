import csv
from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database import execute, get_setting, query, set_setting


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
        self.peak_enabled = QCheckBox("Enable peak hours")
        form.addRow("Base rate (₹/kWh)", self.base_rate)
        form.addRow("Peak rate (₹/kWh)", self.peak_rate)
        form.addRow("Off-peak rate (₹/kWh)", self.offpeak_rate)
        form.addRow("Total slots", self.total_slots)
        form.addRow(self.peak_enabled)

        actions = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save)
        export_btn = QPushButton("Export Report CSV")
        export_btn.clicked.connect(self.export_csv)
        reset_btn = QPushButton("Reset System")
        reset_btn.clicked.connect(self.reset_system)
        actions.addWidget(save_btn)
        actions.addWidget(export_btn)
        actions.addWidget(reset_btn)

        root.addLayout(form)
        root.addLayout(actions)

    def load(self):
        self.base_rate.setText(get_setting("base_rate", "12.5"))
        self.peak_rate.setText(get_setting("peak_rate", "18.0"))
        self.offpeak_rate.setText(get_setting("offpeak_rate", "9.5"))
        self.total_slots.setText(get_setting("total_slots", "6"))
        self.peak_enabled.setChecked(get_setting("peak_enabled", "1") == "1")

    def save(self):
        set_setting("base_rate", self.base_rate.text())
        set_setting("peak_rate", self.peak_rate.text())
        set_setting("offpeak_rate", self.offpeak_rate.text())
        set_setting("total_slots", self.total_slots.text())
        set_setting("peak_enabled", "1" if self.peak_enabled.isChecked() else "0")
        QMessageBox.information(self, "Saved", "Settings updated")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save report", str(Path.home() / "ev_report.csv"), "CSV (*.csv)")
        if not path:
            return
        rows = query("SELECT vehicle_number, energy, cost, duration, charged_at FROM sessions ORDER BY id DESC")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Vehicle", "Energy", "Cost", "Duration", "Charged At"])
            for r in rows:
                w.writerow([r["vehicle_number"], r["energy"], r["cost"], r["duration"], r["charged_at"]])
        QMessageBox.information(self, "Exported", f"CSV saved to {path}")

    def reset_system(self):
        execute("DELETE FROM sessions")
        execute("DELETE FROM vehicles")
        QMessageBox.information(self, "Reset", "System data cleared")
