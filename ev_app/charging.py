from datetime import datetime

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QGridLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from database import execute


class ChargingCard(QWidget):
    def __init__(self, slot_id):
        super().__init__()
        self.slot_id = slot_id
        layout = QVBoxLayout(self)
        self.title = QLabel(f"Slot {slot_id}")
        self.status = QLabel("Available")
        self.vehicle = QLabel("Vehicle: -")
        self.energy = QLabel("Energy: 0.0 kWh")
        self.progress = QProgressBar()
        layout.addWidget(self.title)
        layout.addWidget(self.status)
        layout.addWidget(self.vehicle)
        layout.addWidget(self.energy)
        layout.addWidget(self.progress)


class ChargingPage(QWidget):
    def __init__(self, engine, on_stats_update):
        super().__init__()
        self.engine = engine
        self.on_stats_update = on_stats_update
        self.last_seen = {}
        self.cards = []
        self._build_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def _build_ui(self):
        root = QGridLayout(self)
        for i in range(6):
            card = ChargingCard(i + 1)
            self.cards.append(card)
            root.addWidget(card, i // 3, i % 3)

    def tick(self):
        self.engine.update_charging(0.75)
        stats = self.engine.stats()
        for data, card in zip(stats["slots"], self.cards):
            active = data["active"]
            card.status.setText("Charging" if active else "Available")
            card.vehicle.setText(f"Vehicle: {data['vehicle']}")
            card.energy.setText(f"Energy: {data['energy']:.2f} kWh")
            card.progress.setValue(int(data["percent"]))

            prev = self.last_seen.get(card.slot_id)
            if prev and prev["vehicle"] != "-" and not active:
                energy = prev["energy"]
                cost = self.engine.calculate_bill(energy)
                execute(
                    "INSERT INTO sessions(vehicle_number,energy,cost,duration,charged_at) VALUES(?,?,?,?,?)",
                    (prev["vehicle"], energy, cost, 45.0, datetime.now().isoformat(timespec="seconds")),
                )
            self.last_seen[card.slot_id] = data

        self.on_stats_update(stats)
