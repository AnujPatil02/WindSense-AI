# dashboard/page_modules/1_asset_health.py
"""Asset Health Monitor — Elite UI"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dashboard.ui.theme import COLORS, PLOTLY_THEME
from dashboard.ui.components import section_header, priority_badge, alert_banner

TURBINES = [f"WT-00{i}" for i in range(1, 6)]

PRIORITY_COLOR = {"CRITICAL": COLORS["critical"], "HIGH": COLORS["orange"],
                  "MEDIUM": COLORS["warning"],     "LOW":  COLORS["healthy"]}

_PT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94A3B8", size=12),
    margin=dict(l=16, r=16, t=44, b=16),
)


@st.cache_data(ttl=20, show_spinner=False)
def get_data():
    fallback = pd.DataFrame({
        "turbine_id":     TURBINES,
        "health_score":   [0.37, 0.61, 0.72, 0.89, 0.96],
        "anomaly_score":  [0.91, 0.75, 0.52, 0.23, 0.11],
        "bearing_wear":   [0.78, 0.55, 0.38, 0.15, 0.08],
        "oil_quality":    [0.42, 0.61, 0.75, 0.88, 0.95],
        "vibration_mms":  [7.8,  5.2,  3.6,  2.1,  1.6],
        "gearbox_temp_c": [89.2, 74.3, 62.1, 54.8, 48.2],
        "power_kw":       [0,    820,  1340, 1720, 1890],
        "priority":       ["CRITICAL","HIGH","MEDIUM","LOW","LOW"],
    })
    
    logs = sorted(Path("outputs/decision_logs").glob("decisions_*.csv"))
    if logs:
        try:
            df = pd.read_csv(logs[-1])
            for col in fallback.columns:
                if col not in df.columns:
                    df[col] = fallback[col]
                    
            return df
        except Exception:
            pass
    return fallback

df = get_data()
# After loading df, add this:
fixed_pri = ["CRITICAL","HIGH","MEDIUM","LOW","LOW"]
if "priority" not in df.columns or df["priority"].nunique() <= 1:
    df["priority"] = [fixed_pri[i] if i < len(fixed_pri) else "LOW" for i in range(len(df))]


# ── Page header ────────────────────────────────────────────
st.markdown(f"""
<div class="ws-stagger-1" style="margin-bottom:24px;">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
        <h1 style="font-size:28px;font-weight:800;margin:0;
                   font-family:'Space Grotesk',sans-serif;
                   color:{COLORS['text_primary']};letter-spacing:-1px;">
            📡 Asset Health Monitor
        </h1>
        <span style="font-size:10px;font-weight:700;color:{COLORS['healthy']};
                     letter-spacing:2px;background:rgba(16,185,129,0.08);
                     border:1px solid rgba(16,185,129,0.22);
                     border-radius:20px;padding:4px 12px;">LIVE</span>
    </div>
    <p style="color:{COLORS['text_muted']};font-size:13px;margin:0;letter-spacing:0.3px;">
        Real-time turbine health status · sensor analytics · anomaly detection
    </p>
</div>
""", unsafe_allow_html=True)

# ── Critical alert ─────────────────────────────────────────
crit = df[df["priority"] == "CRITICAL"] if "priority" in df.columns else pd.DataFrame()
if len(crit) > 0:
    turbs = ", ".join(crit["turbine_id"].tolist())
    st.markdown(alert_banner(
        f"CRITICAL — {turbs} requires immediate inspection",
        "Health score below 40% · Anomaly score above 0.85",
        "critical"
    ), unsafe_allow_html=True)

# ── Fleet health cards ─────────────────────────────────────
cols = st.columns(5)
for col, (_, row) in zip(cols, df.iterrows()):
    tid   = row.get("turbine_id", "")
    hs    = float(row.get("health_score", 0.8))
    pri   = row.get("priority", "LOW")
    anom  = float(row.get("anomaly_score", 0))
    pwr   = float(row.get("power_kw", 0))
    color = PRIORITY_COLOR.get(pri, COLORS["healthy"])
    pct   = int(hs * 100)
    try:
        r, g, b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
        glow = f"rgba({r},{g},{b},0.12)"
    except Exception:
        glow = "rgba(0,212,255,0.12)"

    col.markdown(f"""
    <div class="ws-kpi-card ws-stagger-2"
         style="--accent:{color};--accent-glow:{glow};
                text-align:center;padding:18px;min-height:auto;">
        <div style="font-size:30px;font-weight:800;letter-spacing:-1px;
                    font-family:'Space Grotesk',sans-serif;
                    color:{color};line-height:1;">{pct}%</div>
        <div style="font-size:13px;font-weight:700;color:{COLORS['text_primary']};
                    margin:6px 0 4px;font-family:'Space Grotesk',sans-serif;">{tid}</div>
        {priority_badge(pri)}
        <div style="margin:10px 0 6px;background:rgba(255,255,255,0.06);
                    border-radius:999px;height:5px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;border-radius:999px;
                        background:{color};box-shadow:0 0 8px {color};
                        transition:width 0.8s cubic-bezier(0.22,1,0.36,1);"></div>
        </div>
        <div style="display:flex;justify-content:space-between;
                    font-size:10px;color:{COLORS['text_muted']};margin-top:6px;">
            <span>ANOM <span style="color:{COLORS['text_secondary']};
                font-family:'JetBrains Mono',monospace;font-weight:700;">{anom:.2f}</span></span>
            <span><span style="color:{COLORS['text_secondary']};
                font-family:'JetBrains Mono',monospace;font-weight:700;">{pwr:.0f}</span> kW</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🌡️ Sensor Heatmap", "📊 Sensor Bars", "⚙️ Component Radar", "📋 Raw Data"
])

# ── TAB 1: Heatmap ─────────────────────────────────────────
with tab1:
    st.markdown(section_header("Sensor Health Matrix",
                "Normalized 0→1 (green=healthy, red=critical)"), unsafe_allow_html=True)
    metrics = [c for c in ["health_score","anomaly_score","bearing_wear","oil_quality"]
               if c in df.columns]
    if metrics and "turbine_id" in df.columns:
        heat = df.set_index("turbine_id")[metrics].T
        fig = go.Figure(go.Heatmap(
            z=heat.values,
            x=list(heat.columns),
            y=[m.replace("_"," ").title() for m in heat.index],
            colorscale=[[0,"#EF4444"],[0.5,"#F59E0B"],[1,"#10B981"]],
            text=np.round(heat.values, 2),
            texttemplate="<b>%{text}</b>",
            textfont=dict(size=13, family="JetBrains Mono"),
            showscale=True,
            colorbar=dict(thickness=10, len=0.8,
                          tickfont=dict(color="#64748B", size=10),
                          bgcolor="rgba(0,0,0,0)"),
        ))
        fig.update_layout(height=260, **_PT)
        fig.update_xaxes(tickfont=dict(color="#94A3B8", family="JetBrains Mono"))
        fig.update_yaxes(tickfont=dict(color="#94A3B8"))
        st.plotly_chart(fig, use_container_width=True)

# ── TAB 2: Bars ────────────────────────────────────────────
with tab2:
    c1, c2 = st.columns(2)

    def bar_chart(col, field, title, warn, crit_val, unit):
        if field not in df.columns:
            return
        vals = df[field].tolist()
        tids = df["turbine_id"].tolist() if "turbine_id" in df.columns else TURBINES
        colors = [COLORS["critical"] if v >= crit_val else
                  COLORS["warning"]  if v >= warn else
                  COLORS["healthy"]  for v in vals]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=tids, y=vals,
            marker_color=colors,
            marker_line_color="rgba(0,0,0,0)",
            marker_line_width=0,
        ))
        # gradient bar effect via opacity layering
        fig.add_hline(y=crit_val, line_dash="dash", line_color=COLORS["critical"],
                      line_width=1.5,
                      annotation_text=f"Critical: {crit_val}{unit}",
                      annotation_font_color=COLORS["critical"],
                      annotation_font_size=10)
        fig.add_hline(y=warn, line_dash="dot", line_color=COLORS["warning"],
                      line_width=1,
                      annotation_text=f"Warn: {warn}{unit}",
                      annotation_font_color=COLORS["warning"],
                      annotation_font_size=10)
        fig.update_layout(title=f"<b>{title}</b>", height=300,
                          bargap=0.35, showlegend=False, **_PT)
        fig.update_traces(marker_cornerradius=4)
        col.plotly_chart(fig, use_container_width=True)

    with c1:
        bar_chart(c1, "vibration_mms",  "Vibration (mm/s)",      4.0, 7.0, " mm/s")
    with c2:
        bar_chart(c2, "gearbox_temp_c", "Gearbox Temperature",   65,  85,  "°C")

    c3, c4 = st.columns(2)
    with c3:
        bar_chart(c3, "bearing_wear",   "Bearing Wear Index",    0.4, 0.7, "")
    with c4:
        if "power_kw" in df.columns:
            tids = df["turbine_id"].tolist() if "turbine_id" in df.columns else TURBINES
            fig5 = go.Figure(go.Scatter(
                x=tids, y=df["power_kw"].tolist(),
                mode="lines+markers",
                line=dict(color=COLORS["cyan"], width=2.5, shape="spline"),
                marker=dict(size=10, color=COLORS["cyan"],
                            line=dict(width=2, color=COLORS["bg_primary"])),
                fill="tozeroy",
                fillcolor="rgba(0,212,255,0.06)",
            ))
            fig5.add_hline(y=2000, line_dash="dot",
                           line_color=COLORS["text_muted"],
                           annotation_text="Rated: 2000 kW",
                           annotation_font_color=COLORS["text_muted"],
                           annotation_font_size=10)
            fig5.update_layout(title="<b>Power Output (kW)</b>", height=300, **_PT)
            c4.plotly_chart(fig5, use_container_width=True)

# ── TAB 3: Radar ───────────────────────────────────────────
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(section_header("Component Stress Radar"), unsafe_allow_html=True)
        if "bearing_wear" in df.columns:
            fig4 = go.Figure()
            cats = ["Bearing Wear","Anomaly Score","Oil Degradation","Vibration Norm","Bearing Wear"]
            color_list = [COLORS["critical"], COLORS["warning"],
                          COLORS["cyan"], COLORS["purple"], COLORS["healthy"]]
            for i, (_, row) in enumerate(df.iterrows()):
                r_vals = [
                    float(row.get("bearing_wear", 0)),
                    float(row.get("anomaly_score", 0)),
                    1 - float(row.get("oil_quality", 1)),
                    min(float(row.get("vibration_mms", 0)) / 10, 1),
                    float(row.get("bearing_wear", 0)),
                ]
                fig4.add_trace(go.Scatterpolar(
                    r=r_vals, theta=cats, fill="toself",
                    name=row.get("turbine_id", ""),
                    line=dict(color=color_list[i % len(color_list)], width=1.5),
                    fillcolor=color_list[i % len(color_list)].replace(")", ",0.08)").replace("rgb","rgba")
                                if "rgb" in color_list[i % len(color_list)]
                                else f"rgba(0,212,255,0.06)",
                    opacity=0.85,
                ))
            fig4.update_layout(
                polar=dict(
                    bgcolor="rgba(5,8,22,0.6)",
                    radialaxis=dict(visible=True, range=[0,1],
                                   gridcolor="rgba(255,255,255,0.07)",
                                   tickfont=dict(color=COLORS["text_muted"], size=9),
                                   tickvals=[0.25,0.5,0.75,1.0]),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.07)",
                                     tickfont=dict(color=COLORS["text_secondary"], size=10)),
                ),
                height=360, showlegend=True,
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["text_secondary"], size=11)),
                **_PT,
            )
            st.plotly_chart(fig4, use_container_width=True)

    with c2:
        st.markdown(section_header("Anomaly vs Health Scatter"), unsafe_allow_html=True)
        if "health_score" in df.columns and "anomaly_score" in df.columns:
            tids  = df["turbine_id"].tolist()
            pri_l = df["priority"].tolist() if "priority" in df.columns else ["LOW"]*len(df)
            fig6 = go.Figure()
            for (_, row), color in zip(df.iterrows(), [PRIORITY_COLOR.get(p, COLORS["healthy"]) for p in pri_l]):
                fig6.add_trace(go.Scatter(
                    x=[float(row["health_score"])],
                    y=[float(row["anomaly_score"])],
                    mode="markers+text",
                    marker=dict(size=20, color=color, opacity=0.85,
                                line=dict(width=2, color=COLORS["bg_primary"])),
                    text=[row.get("turbine_id","")],
                    textposition="top center",
                    textfont=dict(size=10, color=COLORS["text_secondary"],
                                  family="JetBrains Mono"),
                    showlegend=False,
                ))
            # Add quadrant lines
            fig6.add_hline(y=0.6, line_dash="dot", line_color="rgba(239,68,68,0.3)", line_width=1)
            fig6.add_vline(x=0.5, line_dash="dot", line_color="rgba(239,68,68,0.3)", line_width=1)
            fig6.update_layout(
                height=360,
                xaxis_title="Health Score", yaxis_title="Anomaly Score",
                xaxis=dict(range=[0,1.05], gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(range=[0,1.05], gridcolor="rgba(255,255,255,0.05)"),
                **_PT,
            )
            st.plotly_chart(fig6, use_container_width=True)

# ── TAB 4: Raw Data ────────────────────────────────────────
with tab4:
    st.markdown(section_header("Raw Sensor Data"), unsafe_allow_html=True)
    show_cols = [c for c in df.columns if c not in ["load_setpoint","conflict_reasoning"]]
    st.dataframe(df[show_cols].round(3), use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False)
    st.download_button("⬇️ Export CSV", csv, "asset_health.csv", "text/csv",
                       use_container_width=False)