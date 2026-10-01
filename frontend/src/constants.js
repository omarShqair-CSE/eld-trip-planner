export const COLORS = {
  start: "#2563eb",
  pickup: "#16a34a",
  dropoff: "#dc2626",
  fuel: "#f59e0b",
  rest: "#7c3aed",
  break: "#0891b2",
  restart: "#be185d",
};

export const KIND = {
  start: "Start",
  pickup: "Pickup",
  dropoff: "Drop-off",
  fuel: "Fuel stop",
  rest: "10-hr rest",
  break: "30-min break",
  restart: "34-hr restart",
};

// 13.5 -> "1:30 PM"
export function fmtHour(h) {
  const total = Math.round(h * 60);
  const hh = Math.floor(total / 60) % 24;
  const mm = total % 60;
  const h12 = hh % 12 === 0 ? 12 : hh % 12;
  return `${h12}:${String(mm).padStart(2, "0")} ${hh >= 12 ? "PM" : "AM"}`;
}

export function fmtDateTime(iso) {
  return new Date(iso).toLocaleString([], {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
