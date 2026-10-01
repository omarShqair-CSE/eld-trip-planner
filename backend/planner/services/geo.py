"""Map helpers: geocoding (Nominatim), routing (OSRM), reverse geocoding, polyline math."""
import bisect
import math
import time
from functools import lru_cache

import requests

NOMINATIM = "https://nominatim.openstreetmap.org"
OSRM = "https://router.project-osrm.org"
HEADERS = {"User-Agent": "eld-trip-planner/1.0 (contact: omarshqair731@gmail.com)"}
METERS_PER_MILE = 1609.344
MAX_AVG_MPH = 55.0  # OSRM uses a car profile; cap the average speed for a loaded truck


class GeoError(Exception):
    """A user-facing problem (unknown place, no route...)."""


@lru_cache(maxsize=256)
def geocode(query):
    resp = requests.get(
        f"{NOMINATIM}/search",
        params={"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "us"},
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    time.sleep(1)  # Nominatim policy: max 1 request per second
    if not data:
        raise GeoError(f"Could not find the location: {query}")
    return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"])}


def get_route(points):
    """points = [current, pickup, dropoff] -> legs, geometry, totals."""
    coords = ";".join(f"{p['lng']},{p['lat']}" for p in points)
    resp = requests.get(
        f"{OSRM}/route/v1/driving/{coords}",
        params={"overview": "simplified", "geometries": "geojson", "steps": "false"},
        headers=HEADERS,
        timeout=25,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise GeoError("No driving route found between these locations.")
    route = data["routes"][0]
    legs = []
    for leg in route["legs"]:
        miles = leg["distance"] / METERS_PER_MILE
        hours = max(leg["duration"] / 3600, miles / MAX_AVG_MPH)
        legs.append({"miles": miles, "hours": hours})
    geometry = [[lat, lng] for lng, lat in route["geometry"]["coordinates"]]
    return {
        "legs": legs,
        "geometry": geometry,
        "miles": sum(l["miles"] for l in legs),
        "hours": sum(l["hours"] for l in legs),
    }


@lru_cache(maxsize=512)
def reverse_geocode(lat, lng):
    """Return 'City, ST' for a coordinate (falls back to the raw coordinate)."""
    try:
        resp = requests.get(
            f"{NOMINATIM}/reverse",
            params={"lat": lat, "lon": lng, "format": "jsonv2", "zoom": 10},
            headers=HEADERS,
            timeout=8,
        )
        resp.raise_for_status()
        addr = resp.json().get("address", {})
        time.sleep(1)
        place = (
            addr.get("city") or addr.get("town") or addr.get("village")
            or addr.get("hamlet") or addr.get("county")
        )
        state = (addr.get("ISO3166-2-lvl4") or "").split("-")[-1]
        if place:
            return f"{place}, {state}" if state else place
    except requests.RequestException:
        pass
    return f"{lat:.2f}, {lng:.2f}"


def haversine_miles(a, b):
    r = 3958.8
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dphi = p2 - p1
    dl = math.radians(b[1] - a[1])
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


class Polyline:
    """Find the coordinate that sits X% of the way along the route."""

    def __init__(self, pts):
        self.pts = pts
        self.cum = [0.0]
        for i in range(1, len(pts)):
            self.cum.append(self.cum[-1] + haversine_miles(pts[i - 1], pts[i]))
        self.length = self.cum[-1]

    def point_at_fraction(self, f):
        if len(self.pts) == 1 or self.length == 0:
            return list(self.pts[0])
        target = min(max(f, 0.0), 1.0) * self.length
        i = bisect.bisect_left(self.cum, target)
        if i == 0:
            return list(self.pts[0])
        if i >= len(self.pts):
            return list(self.pts[-1])
        seg = self.cum[i] - self.cum[i - 1]
        t = (target - self.cum[i - 1]) / seg if seg else 0.0
        a, b = self.pts[i - 1], self.pts[i]
        return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]