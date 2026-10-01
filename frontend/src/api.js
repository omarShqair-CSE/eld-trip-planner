const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function planTrip(payload) {
  const res = await fetch(`${API}/api/plan/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(
      data.error || Object.values(data).flat().join(" ") || "Request failed",
    );
  }
  return data;
}
