import csv
from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from database import query


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.summary = QLabel("Generate investor-ready operational reports.")
        self.csv_btn = QPushButton("Download CSV")
        self.pdf_btn = QPushButton("Download PDF Summary")
        self.rev_btn = QPushButton("Revenue Summary")
        self.energy_btn = QPushButton("Energy Usage Report")
        self.session_btn = QPushButton("Session Breakdown")

        self.csv_btn.clicked.connect(self.export_csv)
        self.pdf_btn.clicked.connect(self.export_pdf)
        self.rev_btn.clicked.connect(self.refresh_summary)
        self.energy_btn.clicked.connect(self.refresh_summary)
        self.session_btn.clicked.connect(self.refresh_summary)

        for widget in [self.summary, self.csv_btn, self.pdf_btn, self.rev_btn, self.energy_btn, self.session_btn]:
            layout.addWidget(widget)
        self.refresh_summary()

    def refresh_summary(self):
        totals = query(
            "SELECT COUNT(*) sessions, COALESCE(SUM(energy),0) energy, COALESCE(SUM(cost),0) revenue, COALESCE(AVG(duration),0) avg_duration FROM sessions",
            one=True,
        )
        self.summary.setText(
            f"Revenue ₹{totals['revenue']:.2f} • Energy {totals['energy']:.2f} kWh • Sessions {totals['sessions']} • Avg Duration {totals['avg_duration']:.1f} min"
        )

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save report", str(Path.home() / "ev_report.csv"), "CSV (*.csv)")
        if not path:
            return
        rows = query("SELECT vehicle_number, energy, cost, duration, charged_at FROM sessions ORDER BY id DESC")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Vehicle", "Energy", "Cost", "Duration", "Charged At"])
            for row in rows:
                writer.writerow([row["vehicle_number"], row["energy"], row["cost"], row["duration"], row["charged_at"]])

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", str(Path.home() / "ev_report.pdf"), "PDF (*.pdf)")
        if not path:
            return
        totals = query(
            "SELECT COUNT(*) sessions, COALESCE(SUM(energy),0) energy, COALESCE(SUM(cost),0) revenue, COALESCE(AVG(duration),0) avg_duration FROM sessions",
            one=True,
        )
        with PdfPages(path) as pdf:
            fig = Figure(figsize=(8, 5), facecolor="#0b1220")
            ax = fig.add_subplot(111)
            ax.axis("off")
            lines = [
                "VoltOS EV Charging Report",
                f"Sessions: {totals['sessions']}",
                f"Revenue: ₹{totals['revenue']:.2f}",
                f"Energy Delivered: {totals['energy']:.2f} kWh",
                f"Average Session Duration: {totals['avg_duration']:.1f} minutes",
            ]
            ax.text(0.08, 0.85, "\n".join(lines), color="white", fontsize=14, va="top")
            pdf.savefig(fig)
