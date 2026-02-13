from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database import execute, query


class VehiclePage(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        form = QFormLayout()
        self.owner = QLineEdit()
        self.number = QLineEdit()
        self.capacity = QLineEdit()
        self.type_box = QComboBox()
        self.type_box.addItems(["Normal", "Fast"])
        form.addRow("Owner", self.owner)
        form.addRow("Vehicle #", self.number)
        form.addRow("Battery kWh", self.capacity)
        form.addRow("Charging", self.type_box)

        actions = QHBoxLayout()
        add_btn = QPushButton("Register Vehicle")
        add_btn.clicked.connect(self.add_vehicle)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search owner / vehicle")
        self.search.textChanged.connect(self.load_data)
        self.filter_status = QComboBox()
        self.filter_status.addItems(["All", "Charging", "Idle", "Completed"])
        self.filter_status.currentTextChanged.connect(self.load_data)
        self.sort_box = QComboBox()
        self.sort_box.addItems(["Newest", "Owner", "Capacity"])
        self.sort_box.currentTextChanged.connect(self.load_data)
        for w in [add_btn, self.search, self.filter_status, self.sort_box]:
            actions.addWidget(w)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            ["Owner", "Vehicle", "Capacity", "Type", "Status", "Sessions", "Created", "History", "Edit", "Delete"]
        )
        self.table.horizontalHeader().setStretchLastSection(False)

        root.addLayout(form)
        root.addLayout(actions)
        root.addWidget(self.table)

    def add_vehicle(self):
        owner = self.owner.text().strip()
        number = self.number.text().strip().upper()
        cap = float(self.capacity.text() or 0)
        ctype = self.type_box.currentText()
        if not owner or not number or cap <= 0:
            QMessageBox.warning(self, "Invalid", "Please fill all fields")
            return
        execute(
            "INSERT INTO vehicles(owner_name,vehicle_number,battery_capacity,charging_type) VALUES(?,?,?,?)",
            (owner, number, cap, ctype),
        )
        self.engine.register_vehicle(number, cap, ctype)
        self.engine.enqueue_vehicle(number)
        self.engine.start_charging()
        self.load_data()

    def _status_for(self, vehicle_number):
        for slot in self.engine.stats()["slots"]:
            if slot["vehicle"] == vehicle_number and slot["active"]:
                return "Charging"
        sessions = query("SELECT COUNT(*) c FROM sessions WHERE vehicle_number=?", (vehicle_number,), one=True)["c"]
        return "Completed" if sessions else "Idle"

    def load_data(self):
        keyword = f"%{self.search.text().strip()}%"
        order_by = "v.id DESC"
        if self.sort_box.currentText() == "Owner":
            order_by = "v.owner_name ASC"
        elif self.sort_box.currentText() == "Capacity":
            order_by = "v.battery_capacity DESC"

        rows = query(
            f"""
            SELECT v.*, COALESCE(COUNT(s.id),0) as sessions
            FROM vehicles v LEFT JOIN sessions s ON s.vehicle_number=v.vehicle_number
            WHERE v.vehicle_number LIKE ? OR v.owner_name LIKE ?
            GROUP BY v.id ORDER BY {order_by}
            """,
            (keyword, keyword),
        )

        filtered = []
        for row in rows:
            status = self._status_for(row["vehicle_number"])
            if self.filter_status.currentText() != "All" and status != self.filter_status.currentText():
                continue
            filtered.append((row, status))

        self.table.setRowCount(len(filtered))
        for r, (row, status) in enumerate(filtered):
            vals = [
                row["owner_name"],
                row["vehicle_number"],
                f"{row['battery_capacity']:.1f}",
                row["charging_type"],
                status,
                str(row["sessions"]),
                row["created_at"],
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)

            history_btn = QPushButton("History")
            history_btn.clicked.connect(lambda _=False, v=row["vehicle_number"]: self.show_history(v))
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda _=False, v=row: self.edit_vehicle(v))
            del_btn = QPushButton("Delete")
            del_btn.clicked.connect(lambda _=False, vid=row["id"]: self.delete_vehicle(vid))
            self.table.setCellWidget(r, 7, history_btn)
            self.table.setCellWidget(r, 8, edit_btn)
            self.table.setCellWidget(r, 9, del_btn)

    def show_history(self, vehicle_number):
        history = query(
            "SELECT energy, cost, duration, charged_at FROM sessions WHERE vehicle_number=? ORDER BY id DESC LIMIT 8",
            (vehicle_number,),
        )
        text = "\n".join(
            [f"{h['charged_at']} | {h['energy']:.2f} kWh | ₹{h['cost']:.2f} | {h['duration']:.1f} min" for h in history]
        ) or "No sessions yet"
        QMessageBox.information(self, f"{vehicle_number} Session History", text)

    def edit_vehicle(self, row):
        dialog = QDialog(self)
        dialog.setWindowTitle("Vehicle details")
        layout = QFormLayout(dialog)
        owner = QLineEdit(row["owner_name"])
        cap = QLineEdit(str(row["battery_capacity"]))
        ctype = QComboBox()
        ctype.addItems(["Normal", "Fast"])
        ctype.setCurrentText(row["charging_type"])
        layout.addRow("Owner", owner)
        layout.addRow("Capacity", cap)
        layout.addRow("Type", ctype)
        save = QPushButton("Save")
        save.clicked.connect(dialog.accept)
        layout.addRow(save)
        if dialog.exec():
            execute(
                "UPDATE vehicles SET owner_name=?, battery_capacity=?, charging_type=? WHERE id=?",
                (owner.text().strip(), float(cap.text() or 0), ctype.currentText(), row["id"]),
            )
            self.load_data()

    def delete_vehicle(self, vehicle_id):
        execute("DELETE FROM vehicles WHERE id=?", (vehicle_id,))
        self.load_data()
