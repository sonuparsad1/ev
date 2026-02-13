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
        daily = query("SELECT substr(charged_at,1,10) day, SUM(cost) revenue, SUM(energy) energy FROM sessions GROUP BY day ORDER BY day DESC LIMIT 7")
        daily = list(reversed(daily)) or [{"day": f"D{i}", "revenue": random.randint(2_000, 9_000), "energy": random.randint(140, 380)} for i in range(1, 8)]
        monthly = query("SELECT substr(charged_at,1,7) month, SUM(cost) revenue FROM sessions GROUP BY month ORDER BY month")
        monthly = monthly or [{"month": f"M{i}", "revenue": random.randint(40_000, 95_000)} for i in range(1, 7)]
        type_mix = query("SELECT charging_type, COUNT(*) c FROM vehicles GROUP BY charging_type")
        totals = query("SELECT COUNT(*) cnt, COALESCE(AVG(duration),0) avgd, COALESCE(AVG(energy),0) avge, COALESCE(SUM(cost),0) rev FROM sessions", one=True)
        active_vehicle = query("SELECT vehicle_number, COUNT(*) c FROM sessions GROUP BY vehicle_number ORDER BY c DESC LIMIT 1", one=True)

        recent = daily[-1]["revenue"] if daily else 0
        old = daily[0]["revenue"] if daily else 1
        growth = ((recent - old) / max(1, old)) * 100
        slot_use = min(100, sum(self.live_points) / 2)
        peak_idx = self.live_points.index(max(self.live_points))

        self.kpi.setText(
            f"Avg Session Duration: {totals['avgd']:.1f} min • Avg Energy/session: {totals['avge']:.2f} kWh • "
            f"Most Active Vehicle: {(active_vehicle['vehicle_number'] if active_vehicle else 'N/A')} • "
            f"Revenue Growth: {growth:.1f}% • Slot Utilization: {slot_use:.1f}% • Peak Demand Prediction: {16 + peak_idx}:00"
        )

        self.figure.clear()
        ax1 = self.figure.add_subplot(321)
        ax2 = self.figure.add_subplot(322)
        ax3 = self.figure.add_subplot(323)
        ax4 = self.figure.add_subplot(324)
        ax5 = self.figure.add_subplot(325)
        ax6 = self.figure.add_subplot(326)

        ax1.plot([d["day"] for d in daily], [d["revenue"] for d in daily], color="#43e0b7", marker="o")
        ax1.fill_between([d["day"] for d in daily], [d["revenue"] for d in daily], alpha=0.2, color="#43e0b7")
        ax1.set_title("Daily Revenue", color="white")

        ax2.bar([m["month"] for m in monthly], [m["revenue"] for m in monthly], color="#5d93ff")
        ax2.set_title("Monthly Revenue", color="white")

        labels = [r["charging_type"] for r in type_mix] or ["Normal", "Fast"]
        sizes = [r["c"] for r in type_mix] or [60, 40]
        ax3.pie(sizes, labels=labels, autopct="%1.0f%%", colors=["#43e0b7", "#f6aa54"])
        ax3.set_title("Charging Type Distribution", color="white")

        energy_vals = [d["energy"] for d in daily]
        ax4.pie([sum(energy_vals), max(1, 2000 - sum(energy_vals))], labels=["Used", "Remaining"],
                colors=["#61dafb", "#314156"], autopct="%1.0f%%")
        ax4.set_title("Energy Distribution", color="white")

        ax5.plot(range(len(self.live_points)), self.live_points, color="#ff79c6", linewidth=2)
        ax5.fill_between(range(len(self.live_points)), self.live_points, color="#ff79c6", alpha=0.2)
        ax5.set_title("Peak Usage Time Graph", color="white")

        weekly = [sum([d["revenue"] for d in daily])] * 4
        monthly_comp = [m["revenue"] for m in monthly][-4:]
        ax6.plot(["W1", "W2", "W3", "W4"], weekly, label="Weekly Run Rate", color="#7df9ff")
        ax6.plot([f"M{i+1}" for i in range(len(monthly_comp))], monthly_comp, label="Monthly", color="#8bff6c")
        ax6.legend(facecolor="#111b2e", labelcolor="white")
        ax6.set_title("Weekly vs Monthly Comparison", color="white")

        for ax in (ax1, ax2, ax5, ax6):
            self._apply_dark(ax)

        self.figure.tight_layout()
        self.canvas.draw_idle()
