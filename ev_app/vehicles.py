import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
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
    PAGE_SIZE = 8

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.page = 0
        self.filtered = []
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
        self.sort_box.addItems(["Newest", "Owner", "Capacity", "Revenue"])
        self.sort_box.currentTextChanged.connect(self.load_data)
        for w in [add_btn, self.search, self.filter_status, self.sort_box]:
            actions.addWidget(w)

        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(
            ["Owner", "Vehicle", "Capacity", "Type", "Status", "Sessions", "Revenue", "Created", "History", "Edit", "Delete"]
        )
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        pager = QHBoxLayout()
        self.prev_btn = QPushButton("◀")
        self.prev_btn.clicked.connect(self.prev_page)
        self.page_label = QLabel("Page 1")
        self.next_btn = QPushButton("▶")
        self.next_btn.clicked.connect(self.next_page)
        pager.addWidget(self.prev_btn)
        pager.addWidget(self.page_label)
        pager.addWidget(self.next_btn)

        root.addLayout(form)
        root.addLayout(actions)
        root.addWidget(self.table)
        root.addLayout(pager)

    def add_vehicle(self):
        try:
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
            self.owner.clear()
            self.number.clear()
            self.capacity.clear()
            self.load_data()
        except Exception as exc:
            logging.exception("Failed to register vehicle")
            QMessageBox.critical(self, "Error", f"Could not register vehicle: {exc}")

    def _status_for(self, vehicle_number):
        for slot in self.engine.stats()["slots"]:
            if slot["vehicle"] == vehicle_number and slot["active"]:
                return "Charging"
        sessions = query("SELECT COUNT(*) c FROM sessions WHERE vehicle_number=?", (vehicle_number,), one=True)["c"]
        return "Completed" if sessions else "Idle"

    def _badge(self, text):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if text == "Charging":
            item.setBackground(Qt.GlobalColor.darkGreen)
        elif text == "Completed":
            item.setBackground(Qt.GlobalColor.darkBlue)
        else:
            item.setBackground(Qt.GlobalColor.darkGray)
        return item

    def load_data(self):
        self.page = 0
        keyword = f"%{self.search.text().strip()}%"
        order_by = "v.id DESC"
        if self.sort_box.currentText() == "Owner":
            order_by = "v.owner_name ASC"
        elif self.sort_box.currentText() == "Capacity":
            order_by = "v.battery_capacity DESC"
        elif self.sort_box.currentText() == "Revenue":
            order_by = "revenue DESC"

        rows = query(
            f"""
            SELECT v.*, COALESCE(COUNT(s.id),0) as sessions, COALESCE(SUM(s.cost),0) as revenue
            FROM vehicles v LEFT JOIN sessions s ON s.vehicle_number=v.vehicle_number
            WHERE v.vehicle_number LIKE ? OR v.owner_name LIKE ?
            GROUP BY v.id ORDER BY {order_by}
            """,
            (keyword, keyword),
        )

        self.filtered = []
        for row in rows:
            status = self._status_for(row["vehicle_number"])
            if self.filter_status.currentText() != "All" and status != self.filter_status.currentText():
                continue
            self.filtered.append((row, status))
        self.render_page()

    def render_page(self):
        start = self.page * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        items = self.filtered[start:end]
        self.table.setRowCount(len(items))
        for r, (row, status) in enumerate(items):
            vals = [
                row["owner_name"],
                row["vehicle_number"],
                f"{row['battery_capacity']:.1f}",
                row["charging_type"],
                status,
                str(row["sessions"]),
                f"₹{row['revenue']:.2f}",
                row["created_at"],
            ]
            for c, val in enumerate(vals):
                if c == 4:
                    item = self._badge(val)
                else:
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(r, c, item)

            history_btn = QPushButton("🕘")
            history_btn.clicked.connect(lambda _=False, v=row["vehicle_number"]: self.show_history(v))
            edit_btn = QPushButton("✎")
            edit_btn.clicked.connect(lambda _=False, v=row: self.edit_vehicle(v))
            del_btn = QPushButton("🗑")
            del_btn.clicked.connect(lambda _=False, vid=row["id"]: self.delete_vehicle(vid))
            self.table.setCellWidget(r, 8, history_btn)
            self.table.setCellWidget(r, 9, edit_btn)
            self.table.setCellWidget(r, 10, del_btn)

        total_pages = max(1, (len(self.filtered) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page_label.setText(f"Page {self.page + 1}/{total_pages}")
        self.prev_btn.setEnabled(self.page > 0)
        self.next_btn.setEnabled(self.page + 1 < total_pages)

    def prev_page(self):
        self.page = max(0, self.page - 1)
        self.render_page()

    def next_page(self):
        total_pages = max(1, (len(self.filtered) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page = min(total_pages - 1, self.page + 1)
        self.render_page()

    def show_history(self, vehicle_number):
        history = query(
            "SELECT energy, cost, duration, charged_at FROM sessions WHERE vehicle_number=? ORDER BY id DESC LIMIT 12",
            (vehicle_number,),
        )
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{vehicle_number} Session History")
        layout = QVBoxLayout(dialog)
        table = QTableWidget(len(history), 4)
        table.setHorizontalHeaderLabels(["Energy", "Cost", "Duration", "Time"])
        for r, row in enumerate(history):
            table.setItem(r, 0, QTableWidgetItem(f"{row['energy']:.2f} kWh"))
            table.setItem(r, 1, QTableWidgetItem(f"₹{row['cost']:.2f}"))
            table.setItem(r, 2, QTableWidgetItem(f"{row['duration']:.1f} min"))
            table.setItem(r, 3, QTableWidgetItem(row["charged_at"]))
        layout.addWidget(table)
        dialog.resize(700, 360)
        dialog.exec()

    def edit_vehicle(self, row):
        dialog = QDialog(self)
        dialog.setWindowTitle("Vehicle details")
        layout = QFormLayout(dialog)
        owner = QLineEdit(row["owner_name"])
        cap = QLineEdit(str(row["battery_capacity"]))
        ctype = QComboBox()
        ctype.addItems(["Normal", "Fast"])
        ctype.setCurrentText(row["charging_type"])
        save = QPushButton("Save")

        def do_save():
            try:
                execute(
                    "UPDATE vehicles SET owner_name=?, battery_capacity=?, charging_type=? WHERE id=?",
                    (owner.text().strip(), float(cap.text() or 0), ctype.currentText(), row["id"]),
                )
                dialog.accept()
                self.load_data()
            except Exception as exc:
                QMessageBox.warning(dialog, "Invalid", f"Could not update: {exc}")

        save.clicked.connect(do_save)
        layout.addRow("Owner", owner)
        layout.addRow("Battery", cap)
        layout.addRow("Type", ctype)
        layout.addRow(save)
        dialog.exec()

    def delete_vehicle(self, vehicle_id):
        execute("DELETE FROM vehicles WHERE id=?", (vehicle_id,))
        self.load_data()
