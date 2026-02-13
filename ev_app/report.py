import random

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from database import query


class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.figure = Figure(facecolor="#0b1220")
        self.canvas = FigureCanvas(self.figure)
        self.kpi = QLabel()
        self.live_points = [8, 10, 14, 13, 15, 16, 18]
        layout = QVBoxLayout(self)
        layout.addWidget(self.kpi)
        layout.addWidget(self.canvas)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_live)
        self.timer.start(2000)
        self.refresh()

    def _apply_dark(self, ax):
        ax.set_facecolor("#111b2e")
        ax.tick_params(colors="#d5def5")
        ax.grid(color="#2c3d61", alpha=0.35)
        for spine in ax.spines.values():
            spine.set_color("#617195")

    def _update_live(self):
        self.live_points = self.live_points[1:] + [max(4, self.live_points[-1] + random.randint(-3, 4))]
        self.refresh()

    def refresh(self):
        daily = query(
            "SELECT substr(charged_at,1,10) day, SUM(cost) revenue FROM sessions GROUP BY day ORDER BY day DESC LIMIT 7"
        )
        daily = list(reversed(daily))
        monthly = query(
            "SELECT substr(charged_at,1,7) month, SUM(cost) revenue FROM sessions GROUP BY month ORDER BY month"
        )
        energy_mix = query(
            "SELECT charging_type, COUNT(*) c FROM vehicles GROUP BY charging_type"
        )
        totals = query("SELECT COUNT(*) cnt, COALESCE(AVG(duration),0) avgd, COALESCE(AVG(energy),0) avge FROM sessions", one=True)
        active_user = query(
            "SELECT owner_name, COUNT(*) c FROM vehicles GROUP BY owner_name ORDER BY c DESC LIMIT 1",
            one=True,
        )

        most_used_type = energy_mix[0]["charging_type"] if energy_mix else "N/A"
        self.kpi.setText(
            f"Avg Session Duration: {totals['avgd']:.1f} min | Avg Energy/Vehicle: {totals['avge']:.2f} kWh | "
            f"Most Active User: {(active_user['owner_name'] if active_user else 'N/A')} | Most Used Type: {most_used_type}"
        )

        self.figure.clear()
        ax1 = self.figure.add_subplot(321)
        ax2 = self.figure.add_subplot(322)
        ax3 = self.figure.add_subplot(323)
        ax4 = self.figure.add_subplot(324)
        ax5 = self.figure.add_subplot(325)

        ax1.plot([d["day"] for d in daily], [d["revenue"] for d in daily], color="#43e0b7", marker="o")
        ax1.set_title("Daily Revenue (7d)", color="white")

        ax2.bar([m["month"] for m in monthly], [m["revenue"] for m in monthly], color="#5d93ff")
        ax2.set_title("Monthly Revenue", color="white")

        labels = [r["charging_type"] for r in energy_mix] or ["Normal", "Fast"]
        sizes = [r["c"] for r in energy_mix] or [1, 1]
        ax3.pie(sizes, labels=labels, autopct="%1.0f%%", colors=["#43e0b7", "#f6aa54"])
        ax3.set_title("Charging Type Distribution", color="white")

        ax4.pie([sum(self.live_points), max(1, 180 - sum(self.live_points))], labels=["Energy Used", "Remaining"],
                colors=["#61dafb", "#314156"], autopct="%1.0f%%")
        ax4.set_title("Energy Consumption", color="white")

        ax5.plot(range(len(self.live_points)), self.live_points, color="#ff79c6", linewidth=2)
        ax5.fill_between(range(len(self.live_points)), self.live_points, color="#ff79c6", alpha=0.2)
        ax5.set_title("Live Usage (2s)", color="white")

        for ax in (ax1, ax2, ax5):
            self._apply_dark(ax)

        self.figure.tight_layout()
        self.canvas.draw_idle()
