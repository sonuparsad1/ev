from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from charging import ChargingPage
from report import AnalyticsPage
from vehicles import VehiclePage


class SummaryCard(QWidget):
    def __init__(self, title):
        super().__init__()
        layout = QVBoxLayout(self)
        self.value = QLabel("0")
        self.value.setObjectName("metricValue")
        self.title = QLabel(title)
        layout.addWidget(self.value)
        layout.addWidget(self.title)


class DashboardWindow(QMainWindow):
    def __init__(self, engine, user):
        super().__init__()
        self.engine = engine
        self.user = user
        self.setWindowTitle("EV Charging Station Management")
        self.resize(1400, 850)
        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        side_layout = QVBoxLayout(self.sidebar)
        toggle_btn = QPushButton("☰")
        toggle_btn.clicked.connect(self.toggle_sidebar)
        self.menu = QListWidget()
        self.menu.addItems(["Dashboard", "Vehicles", "Charging", "Analytics"])
        self.menu.currentRowChanged.connect(self.switch_page)
        side_layout.addWidget(toggle_btn)
        side_layout.addWidget(QLabel(f"{self.user['username']} ({self.user['role']})"))
        side_layout.addWidget(self.menu)
        shell.addWidget(self.sidebar)

        main = QVBoxLayout()
        cards = QHBoxLayout()
        self.card_total_vehicles = SummaryCard("Total Vehicles")
        self.card_active = SummaryCard("Active Sessions")
        self.card_revenue = SummaryCard("Total Revenue")
        self.card_slots = SummaryCard("Available Slots")
        for card in [self.card_total_vehicles, self.card_active, self.card_revenue, self.card_slots]:
            cards.addWidget(card)

        self.pages = QStackedWidget()
        self.home = QWidget()
        self.home.setLayout(QVBoxLayout())
        self.home.layout().addWidget(QLabel("Welcome to modern EV operations center"))
        self.vehicles_page = VehiclePage(self.engine)
        self.charging_page = ChargingPage(self.engine, self.refresh_summary)
        self.analytics = AnalyticsPage()
        self.pages.addWidget(self.home)
        self.pages.addWidget(self.vehicles_page)
        self.pages.addWidget(self.charging_page)
        self.pages.addWidget(self.analytics)

        main.addLayout(cards)
        main.addWidget(self.pages)
        shell.addLayout(main, 1)

        self.menu.setCurrentRow(0)
        self.refresh_summary(self.engine.stats())

    def toggle_sidebar(self):
        w = self.sidebar.width()
        target = 72 if w > 120 else 240
        anim = QPropertyAnimation(self.sidebar, b"maximumWidth")
        anim.setDuration(240)
        anim.setStartValue(w)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.start()
        self._sidebar_anim = anim

    def switch_page(self, idx):
        self.pages.setCurrentIndex(max(0, idx))
        if idx == 3:
            self.analytics.refresh()

    def refresh_summary(self, stats):
        self.card_total_vehicles.value.setText(str(stats["total_vehicles"]))
        self.card_active.value.setText(str(stats["active_sessions"]))
        self.card_revenue.value.setText(f"₹{stats['total_revenue']:.2f}")
        available = len([s for s in stats["slots"] if not s["active"]])
        self.card_slots.value.setText(str(available))
        if stats["active_sessions"] == 0:
            return
        for s in stats["slots"]:
            if s["active"] and s["percent"] >= 99:
                QMessageBox.information(self, "Charging Complete", f"{s['vehicle']} completed charging")
                break
