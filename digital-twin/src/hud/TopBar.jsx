import { useState, useEffect } from "react";

const glass = {
  background: "rgba(10, 16, 30, 0.55)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(0, 212, 255, 0.25)",
  borderRadius: 10,
  padding: "10px 16px",
  color: "#e8ecf1",
  fontFamily: "'Inter', sans-serif",
};

export default function TopBar({ agentsActive = 3 }) {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <>
      <div style={{ ...glass, position: "absolute", top: 16, left: 16 }}>
        <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 18, fontWeight: 700, color: "#00D4FF" }}>
          WindSense-AI
        </div>
        <div style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>Predictive Wind Intelligence</div>
      </div>

      <div style={{ ...glass, position: "absolute", top: 16, right: 16, textAlign: "right" }}>
        <div style={{ fontSize: 12, fontFamily: "monospace" }}>
          {time.toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour12: false })} IST
        </div>
        <div style={{ fontSize: 11, color: "#10D97A", marginTop: 2 }}>● System Online</div>
        <div style={{ fontSize: 11, opacity: 0.7 }}>{agentsActive} AI Agents Active</div>
      </div>
    </>
  );
}
