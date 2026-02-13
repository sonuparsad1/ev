from datetime import datetime

from database import execute, get_setting


class RateService:
    def __init__(self):
        self.refresh()

    def refresh(self):
        self.base_rate = float(get_setting("base_rate", 12.5))
        self.peak_rate = float(get_setting("peak_rate", 18.0))
        self.offpeak_rate = float(get_setting("offpeak_rate", 9.5))
        self.peak_enabled = get_setting("peak_enabled", "1") == "1"
        self.peak_start = int(get_setting("peak_start", 17))
        self.peak_end = int(get_setting("peak_end", 22))

    def current(self):
        self.refresh()
        hour = datetime.now().hour
        if self.peak_enabled and self.peak_start <= hour < self.peak_end:
            return self.peak_rate, "Peak Hours Active"
        if hour < 6 or hour >= 22:
            return self.offpeak_rate, "Off-Peak Rate"
        return self.base_rate, "Base Rate"

    def calculate(self, energy_kwh):
        rate, mode = self.current()
        execute(
            "INSERT INTO rate_history(hour, applied_rate, mode) VALUES(?,?,?)",
            (datetime.now().hour, rate, mode),
        )
        return energy_kwh * rate, rate, mode
