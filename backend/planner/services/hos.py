"""Hours-of-Service planner: property-carrying driver, 70 hours / 8 days, no adverse conditions."""
from datetime import timedelta

MAX_DRIVE = 11.0      # max driving hours after 10 consecutive hours off
WINDOW = 14.0         # driving window (hours) that starts when you come on duty
BREAK_AFTER = 8.0     # 30-min break needed after 8 cumulative driving hours
BREAK_LEN = 0.5
REST_LEN = 10.0       # 10 consecutive hours off (we log it as sleeper berth)
RESTART_LEN = 34.0    # 34-hour restart resets the 70-hour cycle
CYCLE_LIMIT = 70.0
FUEL_EVERY = 1000.0   # miles
FUEL_LEN = 0.5        # assumption: a fuel stop takes 30 min (on duty, not driving)
PICKUP_LEN = 1.0      # given in the assessment
DROPOFF_LEN = 1.0     # given in the assessment
EPS = 1e-6


def _hours(td):
    return td.total_seconds() / 3600


class Planner:
    def __init__(self, start, cycle_used):
        self.clock = start
        self.cycle_used = cycle_used      # on-duty hours already used in the 8-day cycle
        self.driving_today = 0.0          # driving hours since the last 10h rest
        self.since_break = 0.0            # driving hours since the last 30+ min break
        self.window_start = None          # when the current 14h window started
        self.miles_since_fuel = 0.0
        self.miles_done = 0.0
        self.events = []

    # ---- helpers -------------------------------------------------------
    def window_left(self):
        if self.window_start is None:
            return WINDOW
        return WINDOW - _hours(self.clock - self.window_start)

    def _add(self, status, hours, kind, note, miles=0.0):
        end = self.clock + timedelta(hours=hours)
        self.events.append({
            "status": status,        # OFF | SB | D | ON
            "kind": kind,            # drive | pickup | dropoff | fuel | break | rest | restart
            "start": self.clock,
            "end": end,
            "note": note,
            "miles": miles,
            "marker": self.miles_done,   # miles driven so far when this event starts
        })
        self.clock = end

    def _reset_daily(self):
        self.driving_today = 0.0
        self.since_break = 0.0
        self.window_start = None

    # ---- duty changes --------------------------------------------------
    def on_duty(self, hours, kind, note):
        if self.window_start is None:
            self.window_start = self.clock
        self._add("ON", hours, kind, note)
        self.cycle_used += hours
        if hours >= BREAK_LEN - EPS:      # 30+ consecutive minutes not driving = a valid break
            self.since_break = 0.0

    def rest(self):
        self._add("SB", REST_LEN, "rest", "10-hour rest (sleeper berth)")
        self._reset_daily()

    def restart(self):
        self._add("OFF", RESTART_LEN, "restart", "34-hour restart (cycle reset)")
        self._reset_daily()
        self.cycle_used = 0.0

    def short_break(self):
        self._add("OFF", BREAK_LEN, "break", "30-minute break")
        self.since_break = 0.0

    # ---- driving -------------------------------------------------------
    def drive(self, miles, hours, note):
        if miles <= EPS or hours <= EPS:
            return
        speed = miles / hours
        remaining = hours
        while remaining > EPS:
            # 1) mandatory stops first (order matters)
            if self.cycle_used >= CYCLE_LIMIT - EPS:
                self.restart()
                continue
            if self.driving_today >= MAX_DRIVE - EPS or self.window_left() <= EPS:
                self.rest()
                continue
            if self.since_break >= BREAK_AFTER - EPS:
                self.short_break()
                continue
            if self.miles_since_fuel >= FUEL_EVERY - EPS:
                self.on_duty(FUEL_LEN, "fuel", "Fueling")
                self.miles_since_fuel = 0.0
                continue

            # 2) drive until the first limit is reached
            if self.window_start is None:
                self.window_start = self.clock
            chunk = min(
                remaining,
                MAX_DRIVE - self.driving_today,
                BREAK_AFTER - self.since_break,
                self.window_left(),
                CYCLE_LIMIT - self.cycle_used,
                (FUEL_EVERY - self.miles_since_fuel) / speed,
            )
            chunk_miles = chunk * speed
            self._add("D", chunk, "drive", note, miles=chunk_miles)
            self.miles_done += chunk_miles
            self.miles_since_fuel += chunk_miles
            self.driving_today += chunk
            self.since_break += chunk
            self.cycle_used += chunk
            remaining -= chunk


def plan_trip(legs, cycle_used, start):
    """legs = [current->pickup, pickup->dropoff], each {'miles','hours'}."""
    p = Planner(start, cycle_used)
    p.drive(legs[0]["miles"], legs[0]["hours"], "Driving to pickup")
    p.on_duty(PICKUP_LEN, "pickup", "Pickup - loading")
    p.drive(legs[1]["miles"], legs[1]["hours"], "Driving to drop-off")
    p.on_duty(DROPOFF_LEN, "dropoff", "Drop-off - unloading")
    return p.events