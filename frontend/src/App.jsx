import { useState } from "react";
import TripForm from "./components/TripForm";
import MapView from "./components/MapView";
import LogSheet from "./components/LogSheet";
import { planTrip } from "./api";
import { COLORS, KIND, fmtDateTime } from "./constants";

export default function App() {
  const [result, setResult] = useState(null);
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handle({ payload, details }) {
    setLoading(true);
    setError("");
    try {
      setResult(await planTrip(payload));
      setDetails(details);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <header className="hero no-print">
        <h1>ELD Trip Planner</h1>
        <p>Enter a trip. Get the route, every required stop, and filled-out driver's daily logs (70 hr / 8 day).</p>
      </header>

      <main className="wrap">
        <div className="layout no-print">
          <div className="col">
            <TripForm onSubmit={handle} loading={loading} />
            {error && <div className="error">{error}</div>}
          </div>

          <div className="col">
            {result ? (
              <>
                <div className="summary">
                  <div className="stat"><b>{result.summary.miles}</b><span>miles</span></div>
                  <div className="stat"><b>{result.summary.driving_hours}</b><span>driving hrs</span></div>
                  <div className="stat"><b>{result.summary.days}</b><span>log sheets</span></div>
                  <div className="stat"><b>{fmtDateTime(result.summary.finish)}</b><span>finish</span></div>
                </div>
                <div className="card nopad"><MapView route={result.route} stops={result.stops} /></div>
                <div className="card">
                  <h2>Stops & rests</h2>
                  <ol className="stops">
                    {result.stops.map((s, i) => (
                      <li key={i}>
                        <span className="dot" style={{ background: COLORS[s.kind] }}>{i + 1}</span>
                        <div>
                          <b>{KIND[s.kind]}</b> - {s.label}
                          <small>{fmtDateTime(s.arrive)}{s.hours ? ` - ${s.hours} h` : ""}</small>
                        </div>
                      </li>
                    ))}
                  </ol>
                </div>
              </>
            ) : (
              <div className="card empty">
                <h2>Your route will appear here</h2>
                <p>Fill in the trip on the left and press <b>Plan trip</b>.</p>
              </div>
            )}
          </div>
        </div>

        {result && (
          <section className="logs">
            <div className="logs-head no-print">
              <h2>Daily log sheets</h2>
              <button className="btn ghost" onClick={() => window.print()}>Print / Save PDF</button>
            </div>
            {result.logs.map((log) => (
              <LogSheet key={log.date} log={log} details={details} />
            ))}
          </section>
        )}
      </main>
    </>
  );
}