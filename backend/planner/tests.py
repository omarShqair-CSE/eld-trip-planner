from datetime import datetime

from django.test import SimpleTestCase

from .services.hos import plan_trip
from .services.logs import build_daily_logs


def hrs(ev):
    return (ev["end"] - ev["start"]).total_seconds() / 3600


class HosRulesTest(SimpleTestCase):
    def setUp(self):
        legs = [{"miles": 120, "hours": 2.2}, {"miles": 1900, "hours": 34.5}]
        self.events = plan_trip(legs, cycle_used=25, start=datetime(2026, 10, 1, 8, 0))

    def test_no_driving_block_over_8_hours(self):
        self.assertTrue(all(hrs(e) <= 8 + 1e-6 for e in self.events if e["status"] == "D"))

    def test_daily_driving_never_exceeds_11(self):
        total = 0
        for e in self.events:
            if e["kind"] in ("rest", "restart"):
                total = 0
            elif e["status"] == "D":
                total += hrs(e)
                self.assertLessEqual(total, 11 + 1e-6)

    def test_fuel_at_least_every_1000_miles(self):
        miles_since = 0
        for e in self.events:
            if e["kind"] == "fuel":
                miles_since = 0
            miles_since += e["miles"]
            self.assertLessEqual(miles_since, 1000 + 1e-6)

    def test_every_log_day_has_24_hours(self):
        for log in build_daily_logs([dict(e, location="X") for e in self.events]):
            self.assertAlmostEqual(sum(log["totals"].values()), 24, delta=0.05)