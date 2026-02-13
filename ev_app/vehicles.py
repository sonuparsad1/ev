from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
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
        self.type_box.addItems(["Slow", "Fast"])
        form.addRow("Owner", self.owner)
        form.addRow("Vehicle #", self.number)
        form.addRow("Battery kWh", self.capacity)
        form.addRow("Charging", self.type_box)

        actions = QHBoxLayout()
        add_btn = QPushButton("Register Vehicle")
        add_btn.clicked.connect(self.add_vehicle)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search vehicle...")
        self.search.textChanged.connect(self.load_data)
        actions.addWidget(add_btn)
        actions.addWidget(self.search)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Owner", "Vehicle", "Capacity", "Type", "Sessions", "Created"]
        )
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)

        root.addLayout(form)
        root.addLayout(actions)
        root.addWidget(self.table)

    def add_vehicle(self):
        owner = self.owner.text().strip()
        number = self.number.text().strip().upper()
        cap = float(self.capacity.text() or 0)
        ctype = self.type_box.currentText()
        if not owner or not number or cap <= 0:
            return
        execute(
            "INSERT INTO vehicles(owner_name,vehicle_number,battery_capacity,charging_type) VALUES(?,?,?,?)",
            (owner, number, cap, ctype),
        )
        self.engine.register_vehicle(number, cap, ctype)
        self.engine.enqueue_vehicle(number)
        self.engine.start_charging()
        self.load_data()

    def load_data(self):
        keyword = f"%{self.search.text().strip()}%"
        rows = query(
            """
            SELECT v.*, COALESCE(COUNT(s.id),0) as sessions
            FROM vehicles v LEFT JOIN sessions s ON s.vehicle_number=v.vehicle_number
            WHERE v.vehicle_number LIKE ? OR v.owner_name LIKE ?
            GROUP BY v.id ORDER BY v.id DESC
            """,
            (keyword, keyword),
        )
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            vals = [
                row["owner_name"],
                row["vehicle_number"],
                f"{row['battery_capacity']:.1f}",
                row["charging_type"],
                str(row["sessions"]),
                row["created_at"],
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)
