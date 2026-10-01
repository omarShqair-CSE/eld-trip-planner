import { fmtHour } from "../constants";

const ROWS = [
  ["OFF", "Off Duty"],
  ["SB", "Sleeper Berth"],
  ["D", "Driving"],
  ["ON", "On Duty (not driving)"],
];
const X0 = 160;   // left edge of the grid
const HW = 30;    // width of one hour
const Y0 = 44;    // top edge of the grid
const RH = 38;    // height of one row
const GRID_BOTTOM = Y0 + ROWS.length * RH;

const x = (h) => X0 + h * HW;
const rowY = (status) => Y0 + ROWS.findIndex((r) => r[0] === status) * RH + RH / 2;

function Field({ label, value }) {
  return (
    <div className="field">
      <div className="v">{value || "\u00A0"}</div>
      <div className="l">{label}</div>
    </div>
  );
}

export default function LogSheet({ log, details }) {
  // One continuous line: horizontal along each status, vertical where the status changes
  const points = log.segments.flatMap((s) => [`${x(s.start)},${rowY(s.status)}`, `${x(s.end)},${rowY(s.status)}`]);
  const [yyyy, mm, dd] = log.date.split("-");

  return (
    <section className="sheet">
      <div className="sheet-title">
        <h3>Driver's Daily Log</h3>
        <span>(24 hours) - Original: file at home terminal</span>
      </div>

      <div className="fields">
        <Field label="Date (month / day / year)" value={`${mm} / ${dd} / ${yyyy}`} />
        <Field label="Total miles driving today" value={log.miles} />
        <Field label="Truck / trailer numbers" value={details.vehicles} />
        <Field label="Name of carrier" value={details.carrier} />
        <Field label="Main office address" value={details.office} />
        <Field label="Shipping documents / commodity" value={details.shipping} />
      </div>

      <svg viewBox="0 0 960 235" className="grid" role="img" aria-label="Duty status graph">
        {Array.from({ length: 25 }, (_, h) => (
          <text key={h} x={x(h)} y={Y0 - 10} textAnchor="middle" className="hl">
            {h === 0 || h === 24 ? "Mid" : h === 12 ? "Noon" : h % 12}
          </text>
        ))}

        {ROWS.map(([key, label], i) => (
          <g key={key}>
            <rect x={X0} y={Y0 + i * RH} width={24 * HW} height={RH} className="cell" />
            <text x={X0 - 8} y={Y0 + i * RH + RH / 2 + 4} textAnchor="end" className="rl">{label}</text>
            <text x={x(24) + 10} y={Y0 + i * RH + RH / 2 + 4} className="tot">{log.totals[key].toFixed(2)}</text>
          </g>
        ))}

        {Array.from({ length: 97 }, (_, q) => {
          const px = X0 + (q * HW) / 4;
          if (q % 4 === 0) {
            return <g key={q}><line x1={px} x2={px} y1={Y0} y2={GRID_BOTTOM} className="hr" /></g>;
          }
          const len = q % 2 === 0 ? 12 : 7;
          return (
            <g key={q}>
              {ROWS.map((_, i) => (
                <line key={i} x1={px} x2={px} y1={Y0 + (i + 1) * RH - len} y2={Y0 + (i + 1) * RH} className="tk" />
              ))}
            </g>
          );
        })}

        <polyline points={points.join(" ")} className="duty" />

        {log.remarks.map((r, i) => (
          <g key={i}>
            <line x1={x(r.hour)} x2={x(r.hour)} y1={GRID_BOTTOM} y2={GRID_BOTTOM + 10} className="mk" />
            <circle cx={x(r.hour)} cy={GRID_BOTTOM + 18} r="8" className="mkc" />
            <text x={x(r.hour)} y={GRID_BOTTOM + 22} textAnchor="middle" className="mkt">{i + 1}</text>
          </g>
        ))}
        <text x={x(24) + 10} y={GRID_BOTTOM + 22} className="tot">= 24.00</text>
      </svg>

      <h4>Remarks</h4>
      <ol className="remarks">
        {log.remarks.map((r, i) => (
          <li key={i}><b>{fmtHour(r.hour)}</b> - {r.location}: {r.note}</li>
        ))}
      </ol>
      <p className="recap">
        Recap: on-duty hours today (lines 3 + 4) = <b>{(log.totals.D + log.totals.ON).toFixed(2)} h</b>
      </p>
    </section>
  );
}