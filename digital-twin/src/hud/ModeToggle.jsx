export default function ModeToggle({ isNight, onToggleNight }) {
  const btn = (active) => ({
    background: active ? "rgba(0, 212, 255, 0.25)" : "rgba(10, 16, 30, 0.55)",
    border: `1px solid ${active ? "#00D4FF" : "rgba(0, 212, 255, 0.25)"}`,
    color: "#e8ecf1",
    borderRadius: 8,
    padding: "8px 14px",
    fontFamily: "'Inter', sans-serif",
    fontSize: 12,
    cursor: "pointer",
    backdropFilter: "blur(12px)",
    marginRight: 8,
  });

  return (
    <div style={{ position: "absolute", top: 90, left: 16, display: "flex" }}>
      <button style={btn(isNight)} onClick={onToggleNight}>
        {isNight ? "🌙 Night" : "☀ Day"}
      </button>
    </div>
  );
}
