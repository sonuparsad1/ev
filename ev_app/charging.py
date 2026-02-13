import logging
import random
from datetime import datetime

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

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
        self.timer = QLabel("Timer: 00:00")
        self.eta = QLabel("ETA: --")
        self.cost = QLabel("Cost: ₹0.00")
        self.progress = QProgressBar()
        for w in [self.title, self.status, self.vehicle, self.energy, self.speed, self.timer, self.eta, self.cost, self.progress]:
            layout.addWidget(w)


class ChargingPage(QWidget):
    def __init__(self, engine, on_stats_update):
        super().__init__()
        self.engine = engine
        self.on_stats_update = on_stats_update
        self.last_seen = {}
        self.cards = []
        self.seconds = {}
        self.rates = RateService()
        self.running = True
        self._build_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.start_btn = QPushButton("Start Simulation")
        self.stop_btn = QPushButton("Stop Simulation")
        self.start_btn.clicked.connect(self.start_sim)
        self.stop_btn.clicked.connect(self.stop_sim)
        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)
        root.addLayout(controls)
        grid = QGridLayout()
        grid.setSpacing(12)
        for i in range(6):
            card = ChargingCard(i + 1)
            self.cards.append(card)
            grid.addWidget(card, i // 3, i % 3)
        root.addLayout(grid)

    def start_sim(self):
        self.running = True

    def stop_sim(self):
        self.running = False

    def tick(self):
        try:
            if self.running:
                self.engine.update_charging(0.75)
                self.engine.start_charging()
            stats = self.engine.stats()
            rate, mode = self.rates.current()
            for data, card in zip(stats["slots"], self.cards):
                active = data["active"] and self.running
                pct = int(data["percent"])
                vid = data["vehicle"]
                card.status.setText("● Charging" if active else "Idle")
                card.status.setObjectName("chargingLive" if active else "")
                card.vehicle.setText(f"Vehicle: {vid}")
                card.energy.setText(f"Energy: {data['energy']:.2f} kWh")
                speed = random.uniform(18.0, 60.0) if active else 0.0
                card.speed.setText(f"Speed: {speed:.1f} kW")
                eta = max(0, int((100 - pct) * 0.9)) if active else 0
                card.eta.setText(f"ETA: {eta} mins" if active else "ETA: --")
                card.cost.setText(f"Cost: ₹{data['energy'] * rate:.2f} ({mode})")
                card.progress.setValue(pct)
                self.seconds[card.slot_id] = self.seconds.get(card.slot_id, 0) + (1 if active else 0)
                s = self.seconds[card.slot_id]
                card.timer.setText(f"Timer: {s//60:02d}:{s%60:02d}")

                prev = self.last_seen.get(card.slot_id)
                if prev and prev["vehicle"] != "-" and not active and prev["active"]:
                    energy = prev["energy"]
                    cost, _, _ = self.rates.calculate(energy)
                    execute(
                        "INSERT INTO sessions(vehicle_number,energy,cost,duration,charged_at) VALUES(?,?,?,?,?)",
                        (prev["vehicle"], energy, cost, max(1, s / 60), datetime.now().isoformat(timespec="seconds")),
                    )
                    self.seconds[card.slot_id] = 0
                self.last_seen[card.slot_id] = {**data, "active": active}

            self.on_stats_update(stats)
        except Exception:
            logging.exception("Charging tick failed")
