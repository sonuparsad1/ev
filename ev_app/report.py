from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from database import query


class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.figure = Figure(facecolor="#141824")
        self.canvas = FigureCanvas(self.figure)
        self.kpi = QLabel()
        layout = QVBoxLayout(self)
        layout.addWidget(self.kpi)
        layout.addWidget(self.canvas)
        self.refresh()

    def refresh(self):
        daily = query(
            "SELECT substr(charged_at,1,10) day, SUM(cost) revenue FROM sessions GROUP BY day ORDER BY day"
        )
        monthly = query(
            "SELECT substr(charged_at,1,7) month, SUM(cost) revenue FROM sessions GROUP BY month ORDER BY month"
        )
        totals = query("SELECT COUNT(*) cnt, COALESCE(AVG(cost),0) avgv FROM sessions", one=True)
        self.kpi.setText(
            f"Total Sessions: {totals['cnt']}    Average Session Value: ₹{totals['avgv']:.2f}"
        )

        self.figure.clear()
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)

        ax1.bar([d["day"] for d in daily], [d["revenue"] for d in daily], color="#3dd9b3")
        ax1.set_title("Daily Revenue", color="white")
        ax2.plot([m["month"] for m in monthly], [m["revenue"] for m in monthly], color="#4fa3ff", marker="o")
        ax2.set_title("Monthly Revenue", color="white")

        for ax in (ax1, ax2):
            ax.set_facecolor("#1c2233")
            ax.tick_params(colors="white")
            for spine in ax.spines.values():
                spine.set_color("#617195")

        self.figure.tight_layout()
        self.canvas.draw_idle()
