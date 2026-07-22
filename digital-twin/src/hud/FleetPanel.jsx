import { turbines } from "../data/mockTelemetry.js";

const glass = {
  background: "rgba(10, 16, 30, 0.55)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(0, 212, 255, 0.25)",
  borderRadius: 10,
  padding: "12px 16px",
  color: "#e8ecf1",
  fontFamily: "'Inter', sans-serif",
  position: "absolute",
  bottom: 16,
  left: 16,
  minWidth: 180,
};

export default function FleetPanel() {
  const avgHealth = Math.round(turbines.reduce((s, t) => s + t.healthScore, 0) / turbines.length);
  const totalPower = turbines.reduce((s, t) => s + t.power, 0).toFixed(1);
  const critical = turbines.filter((t) => t.status === "CRITICAL").length;

  return (
    <div style={glass}>
      <div style={{ fontSize: 10, opacity: 0.6, letterSpacing: 1, marginBottom: 8 }}>FLEET STATUS</div>
      <Row label="Fleet Health" value={`${avgHealth}%`} color="#10D97A" />
      <Row label="Total Power" value={`${totalPower} MW`} color="#00D4FF" />
      <Row label="Critical Assets" value={critical} color={critical > 0 ? "#FF3B3B" : "#10D97A"} />
    </div>
  );
}

function Row({ label, value, color }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
      <span style={{ opacity: 0.75 }}>{label}</span>
      <span style={{ fontFamily: "monospace", color, fontWeight: 600 }}>{value}</span>
    </div>
  );
}
