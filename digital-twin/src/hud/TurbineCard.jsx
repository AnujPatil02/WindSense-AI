const STATUS_COLOR = { HEALTHY: "#10D97A", WARNING: "#F5A623", CRITICAL: "#FF3B3B" };

export default function TurbineCard({ turbine }) {
  if (!turbine) return null;
  const color = STATUS_COLOR[turbine.status];

  return (
    <div style={{
      position: "absolute", top: 150, left: 16, width: 220,
      background: "rgba(10, 16, 30, 0.65)", backdropFilter: "blur(14px)",
      border: `1px solid ${color}55`, borderRadius: 12, padding: 14,
      color: "#e8ecf1", fontFamily: "'Inter', sans-serif",
      boxShadow: `0 0 24px ${color}33`,
    }}>
      <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 15, marginBottom: 6 }}>
        {turbine.id}
      </div>
      <Stat label="Health Score" value={`${turbine.healthScore}%`} />
      <Stat label="RUL" value={`${turbine.rul} Hours`} />
      <Stat label="Anomaly Score" value={turbine.anomalyScore.toFixed(2)} />
      <Stat label="Power Output" value={`${Math.round(turbine.power * 1000)} kW`} />
      <Stat label="Wind Speed" value={`${turbine.windSpeed} m/s`} />
      <div style={{ marginTop: 6, fontSize: 11, fontWeight: 700, color }}>
        Status: {turbine.status}
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11.5, marginBottom: 3 }}>
      <span style={{ opacity: 0.7 }}>{label}</span>
      <span style={{ fontFamily: "monospace" }}>{value}</span>
    </div>
  );
}
