"""Glue: geocode -> route -> HOS schedule -> daily logs -> JSON for the frontend."""
from .geo import Polyline, geocode, get_route, reverse_geocode
from .hos import plan_trip
from .logs import build_daily_logs


def _locate(ev, poly, total, landmarks, pts, names):
    """Return (lat, lng, 'City, ST') for the place where an event starts."""
    if ev["kind"] == "pickup":
        idx = 1
    elif ev["kind"] == "dropoff":
        idx = 2
    else:
        idx = next((i for mile, i in landmarks if abs(ev["marker"] - mile) < 1.0), None)
    if idx is not None:
        return pts[idx]["lat"], pts[idx]["lng"], names[idx]
    lat, lng = poly.point_at_fraction(ev["marker"] / total)
    return lat, lng, reverse_geocode(round(lat, 2), round(lng, 2))


def build_plan(current, pickup, dropoff, cycle_used, start):
    pts = [geocode(current), geocode(pickup), geocode(dropoff)]
    names = [current.strip(), pickup.strip(), dropoff.strip()]
    route = get_route(pts)

    events = plan_trip(route["legs"], cycle_used, start)
    poly = Polyline(route["geometry"])
    total = max(route["miles"], 0.1)
    landmarks = [(0.0, 0), (route["legs"][0]["miles"], 1), (route["miles"], 2)]

    for ev in events:
        ev["lat"], ev["lng"], ev["location"] = _locate(ev, poly, total, landmarks, pts, names)

    stops = [{
        "kind": "start", "label": names[0], "note": "Trip start",
        "lat": pts[0]["lat"], "lng": pts[0]["lng"],
        "arrive": events[0]["start"].isoformat(), "hours": 0,
    }]
    for ev in events:
        if ev["kind"] == "drive":
            continue
        stops.append({
            "kind": ev["kind"], "label": ev["location"], "note": ev["note"],
            "lat": ev["lat"], "lng": ev["lng"],
            "arrive": ev["start"].isoformat(),
            "hours": round((ev["end"] - ev["start"]).total_seconds() / 3600, 2),
        })

    logs = build_daily_logs(events)
    return {
        "route": route["geometry"],
        "stops": stops,
        "logs": logs,
        "summary": {
            "miles": round(route["miles"]),
            "driving_hours": round(sum((e["end"] - e["start"]).total_seconds() / 3600 for e in events if e["kind"] == "drive"), 1),
            "days": len(logs),
            "finish": events[-1]["end"].isoformat(),
        },
    }