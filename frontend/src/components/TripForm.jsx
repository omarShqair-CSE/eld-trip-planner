import { useState } from "react";

const pad = (n) => String(n).padStart(2, "0");
const toInput = (d) =>
  `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;

function defaultStart() {
  const d = new Date();
  d.setHours(8, 0, 0, 0);
  return toInput(d);
}

export default function TripForm({ onSubmit, loading }) {
  const [f, setF] = useState({
    current: "",
    pickup: "",
    dropoff: "",
    cycle: "0",
    start: defaultStart(),
    carrier: "Demo Freight Co.",
    office: "Richmond, VA",
    vehicles: "Truck 101 / Trailer 2044",
    shipping: "BOL 88213 - General freight",
  });
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  function submit(e) {
    e.preventDefault();
    onSubmit({
      payload: {
        current_location: f.current,
        pickup_location: f.pickup,
        dropoff_location: f.dropoff,
        cycle_used: Number(f.cycle),
        start_time: f.start,
      },
      details: { carrier: f.carrier, office: f.office, vehicles: f.vehicles, shipping: f.shipping },
    });
  }

  return (
    <form className="card form" onSubmit={submit}>
      <h2>Trip details</h2>

      <label>
        Current location
        <input required value={f.current} onChange={set("current")} placeholder="e.g. Richmond, VA" />
      </label>
      <label>
        Pickup location
        <input required value={f.pickup} onChange={set("pickup")} placeholder="e.g. Chicago, IL" />
      </label>
      <label>
        Drop-off location
        <input required value={f.dropoff} onChange={set("dropoff")} placeholder="e.g. Dallas, TX" />
      </label>

      <div className="row">
        <label>
          Cycle used (hrs)
          <input type="number" min="0" max="70" step="0.25" required value={f.cycle} onChange={set("cycle")} />
        </label>
        <label>
          Start time
          <input type="datetime-local" required value={f.start} onChange={set("start")} />
        </label>
      </div>

      <details>
        <summary>Log sheet details (optional)</summary>
        <label>Carrier name<input value={f.carrier} onChange={set("carrier")} /></label>
        <label>Main office address<input value={f.office} onChange={set("office")} /></label>
        <label>Truck / trailer numbers<input value={f.vehicles} onChange={set("vehicles")} /></label>
        <label>Shipping doc / commodity<input value={f.shipping} onChange={set("shipping")} /></label>
      </details>

      <button className="btn" disabled={loading}>
        {loading ? <><span className="spinner" /> Planning trip...</> : "Plan trip & draw logs"}
      </button>
    </form>
  );
}