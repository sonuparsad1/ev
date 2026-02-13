import random
from datetime import datetime

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QGridLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from database import execute
from rates import RateService


class ChargingCard(QWidget):
    def __init__(self, slot_id):
        super().__init__()
        self.slot_id = slot_id
        layout = QVBoxLayout(self)
        self.title = QLabel(f"Slot {slot_id}")
        self.status = QLabel("Available")
        self.vehicle = QLabel("Vehicle: -")
        self.energy = QLabel("Energy: 0.0 kWh")
        self.speed = QLabel("Speed: 0.0 kW")
        self.eta = QLabel("ETA: --")
        self.cost = QLabel("Cost: ₹0.00")
        self.progress = QProgressBar()
        for w in [self.title, self.status, self.vehicle, self.energy, self.speed, self.eta, self.cost, self.progress]:
            layout.addWidget(w)


class ChargingPage(QWidget):
    def __init__(self, engine, on_stats_update):
        super().__init__()
        self.engine = engine
        self.on_stats_update = on_stats_update
        self.last_seen = {}
        self.cards = []
        self.rates = RateService()
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
        self.engine.start_charging()
        stats = self.engine.stats()
        rate, mode = self.rates.current()
        for data, card in zip(stats["slots"], self.cards):
            active = data["active"]
            pct = int(data["percent"])
            card.status.setText("● Charging" if active else "Idle")
            card.status.setObjectName("chargingLive" if active else "")
            card.vehicle.setText(f"Vehicle: {data['vehicle']}")
            card.energy.setText(f"Energy: {data['energy']:.2f} kWh")
            speed = random.uniform(18.0, 60.0) if active else 0.0
            card.speed.setText(f"Speed: {speed:.1f} kW")
            eta = max(0, int((100 - pct) * 0.9)) if active else 0
            card.eta.setText(f"ETA: {eta} mins" if active else "ETA: --")
            card.cost.setText(f"Cost: ₹{data['energy'] * rate:.2f} ({mode})")
            card.progress.setValue(pct)

            prev = self.last_seen.get(card.slot_id)
            if prev and prev["vehicle"] != "-" and not active and prev["active"]:
                energy = prev["energy"]
                cost, _, _ = self.rates.calculate(energy)
                execute(
                    "INSERT INTO sessions(vehicle_number,energy,cost,duration,charged_at) VALUES(?,?,?,?,?)",
                    (prev["vehicle"], energy, cost, 45.0, datetime.now().isoformat(timespec="seconds")),
                )
            self.last_seen[card.slot_id] = data

        self.on_stats_update(stats)
