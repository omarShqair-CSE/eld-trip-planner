import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { COLORS, KIND, fmtDateTime } from "../constants";

function pin(kind, n) {
  return L.divIcon({
    className: "",
    html: `<div class="pin" style="background:${COLORS[kind]}">${n}</div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
}

function popup(stop, i) {
  const box = document.createElement("div");
  const title = document.createElement("b");
  title.textContent = `${i + 1}. ${KIND[stop.kind]}`;
  const place = document.createElement("div");
  place.textContent = stop.label;
  const when = document.createElement("small");
  when.textContent = `${fmtDateTime(stop.arrive)}${stop.hours ? ` - ${stop.hours} h` : ""}`;
  box.append(title, place, when);
  return box;
}

export default function MapView({ route, stops }) {
  const el = useRef(null);
  const map = useRef(null);
  const layer = useRef(null);

  useEffect(() => {
    map.current = L.map(el.current).setView([39.5, -98.35], 4);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map.current);
    layer.current = L.layerGroup().addTo(map.current);
    return () => {
      map.current.remove();
      map.current = null;
    };
  }, []);

  useEffect(() => {
    if (!route || !map.current) return;
    layer.current.clearLayers();
    const line = L.polyline(route, { color: "#2563eb", weight: 5, opacity: 0.85 }).addTo(layer.current);
    stops.forEach((s, i) =>
      L.marker([s.lat, s.lng], { icon: pin(s.kind, i + 1) }).bindPopup(popup(s, i)).addTo(layer.current)
    );
    map.current.fitBounds(line.getBounds(), { padding: [30, 30] });
  }, [route, stops]);

  return <div ref={el} className="map" />;
}