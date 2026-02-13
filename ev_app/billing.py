from database import query


class BillingService:
    RATE = 15.0
    TAX = 0.05

    @classmethod
    def breakdown(cls, energy):
        base = energy * cls.RATE
        tax = base * cls.TAX
        return {"energy": energy, "base": base, "tax": tax, "total": base + tax}

    @staticmethod
    def recent_sessions(limit=20):
        return query(
            "SELECT vehicle_number, energy, cost, duration, charged_at FROM sessions ORDER BY id DESC LIMIT ?",
            (limit,),
        )
