import { useState, useEffect } from "react";

const MOCK_ALERTS = [
  "WT-003 vibration anomaly detected",
  "Gearbox degradation probability increased",
  "AI recommends inspection within 48h",
  "WT-005 RUL dropped below 12h threshold",
  "Maintenance Coordinator scheduling crew dispatch",
];

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
  right: 16,
  width: 280,
  maxHeight: 150,
  overflow: "hidden",
};

export default function AlertFeed() {
  const [visible, setVisible] = useState([MOCK_ALERTS[0]]);

  useEffect(() => {
    let i = 0;
    const t = setInterval(() => {
      i = (i + 1) % MOCK_ALERTS.length;
      setVisible((prev) => [MOCK_ALERTS[i], ...prev].slice(0, 4));
    }, 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={glass}>
      <div style={{ fontSize: 10, opacity: 0.6, letterSpacing: 1, marginBottom: 8 }}>LIVE ALERTS</div>
      {visible.map((a, i) => (
        <div key={i} style={{
          fontSize: 11.5, padding: "5px 0", borderTop: i > 0 ? "1px solid rgba(255,255,255,0.08)" : "none",
          opacity: 1 - i * 0.15,
        }}>
          <span style={{ color: "#F5A623", marginRight: 6 }}>●</span>{a}
        </div>
      ))}
    </div>
  );
}
