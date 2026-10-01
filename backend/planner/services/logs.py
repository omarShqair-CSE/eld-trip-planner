"""Turn the flat list of duty events into one log sheet per calendar day."""
from datetime import timedelta

STATUSES = ("OFF", "SB", "D", "ON")


def _hour(dt):
    return dt.hour + dt.minute / 60 + dt.second / 3600


def split_by_day(events):
    """Cut events that cross midnight so every piece belongs to one day."""
    pieces = []
    for ev in events:
        total = (ev["end"] - ev["start"]).total_seconds()
        cur, first = ev["start"], True
        while cur < ev["end"]:
            midnight = (cur + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = min(ev["end"], midnight)
            secs = (end - cur).total_seconds()
            start_h = _hour(cur)
            pieces.append({
                "date": cur.date(),
                "status": ev["status"],
                "start_h": start_h,
                "end_h": 24.0 if end == midnight else start_h + secs / 3600,
                "miles": ev["miles"] * secs / total,
                "location": ev["location"],
                "note": ev["note"],
                "first": first,          # only the first piece gets a "Remarks" entry
            })
            first, cur = False, end
    return pieces


def _merge(segments):
    merged = []
    for s in segments:
        if merged and merged[-1]["status"] == s["status"] and abs(merged[-1]["end"] - s["start"]) < 1e-6:
            merged[-1]["end"] = s["end"]
        else:
            merged.append(dict(s))
    return merged


def build_daily_logs(events):
    by_day = {}
    for p in split_by_day(events):
        by_day.setdefault(p["date"], []).append(p)

    logs = []
    for day in sorted(by_day):
        pieces = by_day[day]
        segments, cursor = [], 0.0
        for p in pieces:
            if p["start_h"] - cursor > 1e-6:          # before the trip starts: off duty
                segments.append({"status": "OFF", "start": cursor, "end": p["start_h"]})
            segments.append({"status": p["status"], "start": p["start_h"], "end": p["end_h"]})
            cursor = p["end_h"]
        if 24 - cursor > 1e-6:                         # after the trip ends: off duty
            segments.append({"status": "OFF", "start": cursor, "end": 24.0})
        segments = _merge(segments)

        totals = {s: 0.0 for s in STATUSES}
        for s in segments:
            totals[s["status"]] += s["end"] - s["start"]

        logs.append({
            "date": day.isoformat(),
            "miles": round(sum(p["miles"] for p in pieces if p["status"] == "D")),
            "segments": [{"status": s["status"], "start": round(s["start"], 4), "end": round(s["end"], 4)} for s in segments],
            "totals": {k: round(v, 2) for k, v in totals.items()},
            "remarks": [
                {"hour": round(p["start_h"], 4), "location": p["location"], "note": p["note"]}
                for p in pieces if p["first"]
            ],
        })
    return logs