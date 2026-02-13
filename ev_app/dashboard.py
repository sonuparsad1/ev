from datetime import datetime

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, QVariantAnimation
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from charging import ChargingPage
from database import query
from rates import RateService
from report import AnalyticsPage
from settings import SettingsPage
from vehicles import VehiclePage


class AnimatedValueLabel(QLabel):
    def __init__(self, prefix="", suffix=""):
        super().__init__("0")
        self.prefix = prefix
        self.suffix = suffix
        self._value = 0.0
        self.setObjectName("metricValue")

    def setAnimatedValue(self, value):
        anim = QVariantAnimation(self)
        anim.setDuration(700)
        anim.setStartValue(self._value)
        anim.setEndValue(float(value))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.valueChanged.connect(self._set_value)
        anim.start()
        self.anim = anim

    def _set_value(self, v):
        self._value = float(v)
        body = f"{self._value:.2f}"
        if body.endswith(".00"):
            body = body[:-3]
        self.setText(f"{self.prefix}{body}{self.suffix}")


class StatCard(QFrame):
    def __init__(self, title, prefix="", suffix=""):
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        self.value = AnimatedValueLabel(prefix, suffix)
        self.title = QLabel(title)
        self.sub = QLabel("Live")
        self.sub.setObjectName("subtle")
        layout.addWidget(self.value)
        layout.addWidget(self.title)
        layout.addWidget(self.sub)


class OverviewPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        grid = QGridLayout()
        self.total_vehicles = StatCard("Total Vehicles")
        self.active = StatCard("Active Charging Sessions")
        self.available = StatCard("Available Slots")
        self.revenue = StatCard("Total Revenue", prefix="₹")
        self.energy = StatCard("Today's Energy Delivered", suffix=" kWh")
        self.rate = StatCard("Current Electricity Rate", prefix="₹", suffix="/kWh")
        cards = [self.total_vehicles, self.active, self.available, self.revenue, self.energy, self.rate]
        for idx, card in enumerate(cards):
            grid.addWidget(card, idx // 3, idx % 3)

        self.slot_progress = QProgressBar()
        self.slot_progress.setFormat("Slot Usage %p%")
        self.blink = QLabel("● Live Charging")
        self.blink.setObjectName("chargingLive")
        root.addLayout(grid)
        root.addWidget(self.slot_progress)
        root.addWidget(self.blink)


class RevenuePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.badge = QLabel("Rate Mode")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Vehicle", "Energy (kWh)", "Cost (₹)", "Time"])
        layout.addWidget(self.badge)
        layout.addWidget(self.table)

    def refresh(self, mode):
        self.badge.setText(mode)
        self.badge.setObjectName("badgePeak" if "Peak" in mode else "badgeOffpeak")
        rows = query("SELECT vehicle_number, energy, cost, charged_at FROM sessions ORDER BY id DESC LIMIT 20")
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            vals = [row["vehicle_number"], f"{row['energy']:.2f}", f"{row['cost']:.2f}", row["charged_at"]]
            for c, val in enumerate(vals):
                self.table.setItem(r, c, QTableWidgetItem(val))


class DashboardWindow(QMainWindow):
    def __init__(self, engine, user):
        super().__init__()
        self.engine = engine
        self.user = user
        self.rates = RateService()
        self.setWindowTitle("VoltOS • EV SaaS Dashboard")
        self.resize(1500, 900)
        self._build_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMaximumWidth(280)
        side = QVBoxLayout(self.sidebar)
        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        self.avatar = QLabel("⚡")
        self.avatar.setObjectName("avatar")
        self.profile = QLabel(f"{self.user['username']}\n{self.user['role']}")
        self.status = QLabel("Station: Online")
        self.clock = QLabel("--:--:--")
        self.energy_badge = QLabel("Today's Energy: 0.0 kWh")
        side.addWidget(self.toggle_btn)
        side.addWidget(self.avatar)
        side.addWidget(self.profile)
        side.addWidget(self.status)
        side.addWidget(self.clock)
        side.addWidget(self.energy_badge)

        self.menu_buttons = []
        for text, icon in [
            ("Dashboard", "🏠"),
            ("Vehicles", "🚘"),
            ("Charging Sessions", "🔌"),
            ("Revenue", "💰"),
            ("Analytics", "📈"),
            ("Settings", "⚙️"),
        ]:
            btn = QPushButton(f"{icon}  {text}")
            btn.clicked.connect(lambda _=False, t=text: self.switch_page(t))
            btn.setObjectName("menuBtn")
            self.menu_buttons.append(btn)
            side.addWidget(btn)
        side.addStretch(1)
        logout = QPushButton("Logout")
        logout.clicked.connect(self.close)
        side.addWidget(logout)
        shell.addWidget(self.sidebar)

        body = QVBoxLayout()
        self.pages = QStackedWidget()
        self.overview = OverviewPage()
        self.vehicles = VehiclePage(self.engine)
        self.charging = ChargingPage(self.engine, self.refresh_summary)
        self.revenue_page = RevenuePage()
        self.analytics = AnalyticsPage()
        self.settings = SettingsPage()
        for page in [self.overview, self.vehicles, self.charging, self.revenue_page, self.analytics, self.settings]:
            self.pages.addWidget(page)
        body.addWidget(self.pages)
        shell.addLayout(body, 1)

        self.switch_page("Dashboard")
        self.refresh_summary(self.engine.stats())

    def toggle_sidebar(self):
        w = self.sidebar.width()
        target = 92 if w > 120 else 280
        self.anim = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.anim.setDuration(260)
        self.anim.setStartValue(w)
        self.anim.setEndValue(target)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.anim.start()

    def switch_page(self, text):
        mapping = {
            "Dashboard": 0,
            "Vehicles": 1,
            "Charging Sessions": 2,
            "Revenue": 3,
            "Analytics": 4,
            "Settings": 5,
        }
        idx = mapping[text]
        self.pages.setCurrentIndex(idx)
        for b in self.menu_buttons:
            b.setProperty("active", "true" if text in b.text() else "false")
            b.style().unpolish(b)
            b.style().polish(b)
        effect = QGraphicsOpacityEffect(self.pages.currentWidget())
        self.pages.currentWidget().setGraphicsEffect(effect)
        fade = QPropertyAnimation(effect, b"opacity")
        fade.setDuration(220)
        fade.setStartValue(0.15)
        fade.setEndValue(1.0)
        fade.start()
        self._fade = fade

    def tick(self):
        now = datetime.now()
        self.clock.setText(now.strftime("%d %b %Y  %H:%M:%S"))
        self.refresh_summary(self.engine.stats())

    def refresh_summary(self, stats):
        rate, mode = self.rates.current()
        total_energy = query("SELECT COALESCE(SUM(energy),0) e FROM sessions WHERE substr(charged_at,1,10)=date('now')", one=True)["e"]

        self.overview.total_vehicles.value.setAnimatedValue(stats["total_vehicles"])
        self.overview.active.value.setAnimatedValue(stats["active_sessions"])
        available = len([s for s in stats["slots"] if not s["active"]])
        self.overview.available.value.setAnimatedValue(available)
        self.overview.revenue.value.setAnimatedValue(stats["total_revenue"])
        self.overview.energy.value.setAnimatedValue(total_energy)
        self.overview.rate.value.setAnimatedValue(rate)
        used_percent = int(((len(stats["slots"]) - available) / max(1, len(stats["slots"]))) * 100)
        self.overview.slot_progress.setValue(used_percent)

        self.energy_badge.setText(f"Today's Energy: {total_energy:.2f} kWh")
        self.revenue_page.refresh(mode)
