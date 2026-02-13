import logging
from datetime import datetime

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, QVariantAnimation, Qt
from PyQt6.QtGui import QColor, QCloseEvent, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
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
from reports import ReportsPage
from settings import SettingsPage
from vehicles import VehiclePage


class CircularProgress(QWidget):
    def __init__(self):
        super().__init__()
        self.value = 0
        self.setMinimumSize(130, 130)

    def set_value(self, value):
        self.value = max(0, min(100, int(value)))
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(14, 14, -14, -14)
        painter.setPen(QPen(QColor("#223149"), 12))
        painter.drawArc(rect, 0, 360 * 16)
        painter.setPen(QPen(QColor("#4fa3ff"), 12))
        painter.drawArc(rect, 90 * 16, -int((360 * self.value / 100) * 16))
        painter.setPen(QColor("#dbe5ff"))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.value}%")


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
        body = f"{self._value:.2f}".rstrip("0").rstrip(".")
        self.setText(f"{self.prefix}{body}{self.suffix}")


class StatCard(QFrame):
    def __init__(self, title, prefix="", suffix="", sub="Live"):
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)
        self.value = AnimatedValueLabel(prefix, suffix)
        self.title = QLabel(title)
        self.title.setWordWrap(True)
        self.sub = QLabel(sub)
        self.sub.setObjectName("subtle")
        layout.addWidget(self.value)
        layout.addWidget(self.title)
        layout.addWidget(self.sub)


class OverviewPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(14)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        self.total_vehicles = StatCard("Total Vehicles")
        self.active = StatCard("Active Charging Sessions", sub="● Live")
        self.available = StatCard("Available Slots")
        self.revenue = StatCard("Total Revenue", prefix="₹")
        self.energy = StatCard("Today's Energy", suffix=" kWh")
        self.rate = StatCard("Current Rate", prefix="₹", suffix="/kWh")
        cards = [self.total_vehicles, self.active, self.available, self.revenue, self.energy, self.rate]
        for idx, card in enumerate(cards):
            grid.addWidget(card, idx // 3, idx % 3)
        for i in range(3):
            grid.setColumnStretch(i, 1)
        root.addLayout(grid)

        monitor = QFrame()
        monitor.setObjectName("panel")
        m_layout = QHBoxLayout(monitor)
        left = QVBoxLayout()
        self.live_title = QLabel("Real-time Charging Monitor")
        self.live_title.setObjectName("sectionTitle")
        self.battery = QLabel("Battery: 0%")
        self.speed = QLabel("Speed: 0.0 kW")
        self.eta = QLabel("ETA: --")
        self.session_timer = QLabel("Session Timer: 00:00")
        self.live_cost = QLabel("Live Cost: ₹0.00")
        self.live_progress = QProgressBar()
        self.live_progress.setFormat("Slot Usage %p%")
        for w in [self.live_title, self.battery, self.speed, self.eta, self.session_timer, self.live_cost, self.live_progress]:
            left.addWidget(w)
        m_layout.addLayout(left, 2)
        self.circular = CircularProgress()
        m_layout.addWidget(self.circular, 1)
        root.addWidget(monitor)


class RevenuePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.badge = QLabel("Rate Mode")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Vehicle", "Energy (kWh)", "Rate", "Cost (₹)", "Time"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.badge)
        layout.addWidget(self.table)

    def refresh(self, mode, rate):
        self.badge.setText(f"{mode} • ₹{rate:.2f}/kWh")
        self.badge.setObjectName("badgePeak" if "Peak" in mode else "badgeOffpeak")
        rows = query("SELECT vehicle_number, energy, cost, charged_at FROM sessions ORDER BY id DESC LIMIT 20")
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            vals = [row["vehicle_number"], f"{row['energy']:.2f}", f"₹{(row['cost']/max(0.1,row['energy'])):.2f}", f"{row['cost']:.2f}", row["charged_at"]]
            for c, val in enumerate(vals):
                self.table.setItem(r, c, QTableWidgetItem(val))


class DashboardWindow(QMainWindow):
    def __init__(self, engine, user):
        super().__init__()
        self.engine = engine
        self.user = user
        self.rates = RateService()
        self.sidebar_expanded = True
        self.blink = False
        self.elapsed_session = 0
        self.setWindowTitle("VoltOS • EV Infrastructure Cloud")
        self.setMinimumSize(1200, 760)
        self.resize(1500, 900)
        self._build_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def closeEvent(self, event: QCloseEvent) -> None:
        answer = QMessageBox.question(self, "Exit", "Do you want to safely close VoltOS?")
        if answer == QMessageBox.StandardButton.Yes:
            try:
                self.timer.stop()
                self.charging.stop_sim()
            except Exception:
                logging.exception("Error during graceful shutdown")
            event.accept()
        else:
            event.ignore()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(12, 12, 12, 12)
        shell.setSpacing(12)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMaximumWidth(280)
        side = QVBoxLayout(self.sidebar)
        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        self.avatar = QLabel("⚡")
        self.avatar.setObjectName("avatar")
        self.profile = QLabel(f"{self.user['username']}\n{self.user['role']}")
        self.profile.setObjectName("profile")
        self.status = QLabel("● Station Online")
        self.status.setObjectName("online")
        self.clock = QLabel("--:--:--")
        self.energy_badge = QLabel("Energy Today: 0.0 kWh")
        self.energy_badge.setObjectName("miniBadge")
        for widget in [self.toggle_btn, self.avatar, self.profile, self.status, self.clock, self.energy_badge]:
            side.addWidget(widget)

        self.menu_buttons = []
        for text, icon in [
            ("Dashboard", "⌁"),
            ("Vehicles", "◈"),
            ("Charging Sessions", "⚡"),
            ("Revenue", "₹"),
            ("Analytics", "◔"),
            ("Reports", "☷"),
            ("Settings", "⚙"),
        ]:
            btn = QPushButton(f"{icon}  {text}")
            btn.clicked.connect(lambda _=False, t=text: self.switch_page(t))
            btn.setObjectName("menuBtn")
            self.menu_buttons.append(btn)
            side.addWidget(btn)
        side.addStretch(1)
        logout = QPushButton("Logout")
        logout.setObjectName("logout")
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
        self.reports = ReportsPage()
        self.settings = SettingsPage()
        for page in [self.overview, self.vehicles, self.charging, self.revenue_page, self.analytics, self.reports, self.settings]:
            self.pages.addWidget(page)
        body.addWidget(self.pages)
        shell.addLayout(body, 1)

        self.switch_page("Dashboard")
        self.refresh_summary(self.engine.stats())

    def toggle_sidebar(self):
        w = self.sidebar.width()
        target = 96 if self.sidebar_expanded else 280
        self.sidebar_expanded = not self.sidebar_expanded
        self.anim = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.anim.setDuration(280)
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
            "Reports": 5,
            "Settings": 6,
        }
        self.pages.setCurrentIndex(mapping[text])
        for b in self.menu_buttons:
            b.setProperty("active", "true" if text in b.text() else "false")
            b.style().unpolish(b)
            b.style().polish(b)
        effect = QGraphicsOpacityEffect(self.pages.currentWidget())
        self.pages.currentWidget().setGraphicsEffect(effect)
        fade = QPropertyAnimation(effect, b"opacity")
        fade.setDuration(240)
        fade.setStartValue(0.1)
        fade.setEndValue(1.0)
        fade.start()
        self._fade = fade

    def tick(self):
        try:
            now = datetime.now()
            self.clock.setText(now.strftime("%d %b %Y  %H:%M:%S"))
            self.blink = not self.blink
            self.overview.active.sub.setText("● Live" if self.blink else "◌ Live")
            self.refresh_summary(self.engine.stats())
        except Exception:
            logging.exception("Tick refresh failed")

    def refresh_summary(self, stats):
        try:
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
            self.overview.live_progress.setValue(used_percent)
            self.overview.circular.set_value(used_percent)

            active_slots = [slot for slot in stats["slots"] if slot["active"]]
            if active_slots:
                live = active_slots[0]
                pct = int(live["percent"])
                self.elapsed_session += 1
                self.overview.battery.setText(f"Battery: {pct}%")
                self.overview.speed.setText(f"Speed: {18 + (pct % 24):.1f} kW")
                self.overview.eta.setText(f"ETA: {max(1, int((100 - pct) * 0.8))} mins")
                self.overview.live_cost.setText(f"Live Cost: ₹{live['energy'] * rate:.2f}")
                self.overview.session_timer.setText(f"Session Timer: {self.elapsed_session//60:02d}:{self.elapsed_session%60:02d}")
            else:
                self.elapsed_session = 0
                self.overview.battery.setText("Battery: 0%")
                self.overview.speed.setText("Speed: 0.0 kW")
                self.overview.eta.setText("ETA: --")
                self.overview.live_cost.setText("Live Cost: ₹0.00")
                self.overview.session_timer.setText("Session Timer: 00:00")

            self.energy_badge.setText(f"Energy Today: {total_energy:.2f} kWh")
            self.revenue_page.refresh(mode, rate)
        except Exception:
            logging.exception("Summary refresh failed")
