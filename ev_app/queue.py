import ctypes
import sys
from pathlib import Path


class CoreEngine:
    def __init__(self):
        base = Path(__file__).resolve().parent
        if sys.platform.startswith("win"):
            lib = base / "core.dll"
        else:
            lib = base / "core.so"
        self.core = ctypes.CDLL(str(lib))
        self._configure()

    def _configure(self):
        self.core.register_vehicle.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_int]
        self.core.enqueue_vehicle.argtypes = [ctypes.c_char_p]
        self.core.enqueue_vehicle.restype = ctypes.c_int
        self.core.start_charging.restype = ctypes.c_int
        self.core.update_charging.argtypes = [ctypes.c_double]
        self.core.calculate_bill.argtypes = [ctypes.c_double]
        self.core.calculate_bill.restype = ctypes.c_double
        self.core.get_total_revenue.restype = ctypes.c_double
        self.core.get_total_vehicles.restype = ctypes.c_int
        self.core.get_active_sessions.restype = ctypes.c_int
        self.core.get_slot_count.restype = ctypes.c_int
        self.core.get_slot_status.argtypes = [ctypes.c_int]
        self.core.get_slot_status.restype = ctypes.c_int
        self.core.get_slot_vehicle.argtypes = [ctypes.c_int]
        self.core.get_slot_vehicle.restype = ctypes.c_char_p
        self.core.get_slot_energy.argtypes = [ctypes.c_int]
        self.core.get_slot_energy.restype = ctypes.c_double
        self.core.get_slot_percent.argtypes = [ctypes.c_int]
        self.core.get_slot_percent.restype = ctypes.c_double

    def register_vehicle(self, vehicle_number, capacity, charging_type):
        ct = 1 if charging_type.lower() == "fast" else 0
        self.core.register_vehicle(vehicle_number.encode(), float(capacity), ct)

    def enqueue_vehicle(self, vehicle_number):
        return bool(self.core.enqueue_vehicle(vehicle_number.encode()))

    def start_charging(self):
        return self.core.start_charging()

    def update_charging(self, minutes=0.75):
        self.core.update_charging(minutes)

    def calculate_bill(self, energy):
        return self.core.calculate_bill(energy)

    def stats(self):
        slots = []
        count = self.core.get_slot_count()
        for i in range(count):
            slots.append(
                {
                    "slot": i + 1,
                    "active": bool(self.core.get_slot_status(i)),
                    "vehicle": self.core.get_slot_vehicle(i).decode() or "-",
                    "energy": self.core.get_slot_energy(i),
                    "percent": self.core.get_slot_percent(i),
                }
            )
        return {
            "total_revenue": self.core.get_total_revenue(),
            "total_vehicles": self.core.get_total_vehicles(),
            "active_sessions": self.core.get_active_sessions(),
            "slots": slots,
        }
