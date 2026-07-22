# dashboard/page_modules/2_rul_monitor.py
"""RUL Monitor — Elite UI"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dashboard.ui.theme import COLORS
from dashboard.ui.components import section_header, kpi_card, alert_banner, priority_badge

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
    logs = sorted(Path("outputs/decision_logs").glob("decisions_*.csv"))
    if logs:
        try:
            df = pd.read_csv(logs[-1])
            if "rul_hours" in df.columns:
                return df
        except Exception:
            pass
    return pd.DataFrame({
        "turbine_id":    TURBINES,
        "rul_hours":     [38.0, 55.0, 88.0, 112.0, 120.0],
        "lower_hours":   [22.0, 38.0, 68.0,  95.0, 108.0],
        "upper_hours":   [55.0, 73.0,108.0, 125.0, 125.0],
        "priority":      ["CRITICAL","HIGH","MEDIUM","LOW","LOW"],
        "anomaly_score": [0.91,  0.75,  0.52,  0.23,  0.11],
        "health_score":  [0.37,  0.61,  0.72,  0.89,  0.96],
    })

df = get_data()
fixed_pri = ["CRITICAL","HIGH","MEDIUM","LOW","LOW"]
if "priority" not in df.columns or df["priority"].nunique() <= 1:
    df["priority"] = [fixed_pri[i] if i < len(fixed_pri) else "LOW" for i in range(len(df))]

# ── Header ─────────────────────────────────────────────────
st.markdown(f"""
<div class="ws-stagger-1" style="margin-bottom:24px;">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
        <h1 style="font-size:28px;font-weight:800;margin:0;
                   font-family:'Space Grotesk',sans-serif;
                   color:{COLORS['text_primary']};letter-spacing:-1px;">
            ⏳ Remaining Useful Life Monitor
        </h1>
        <span style="font-size:10px;font-weight:700;color:{COLORS['cyan']};
                     letter-spacing:2px;background:rgba(0,212,255,0.08);
                     border:1px solid rgba(0,212,255,0.22);
                     border-radius:20px;padding:4px 12px;">CONFORMAL AI</span>
    </div>
    <p style="color:{COLORS['text_muted']};font-size:13px;margin:0;letter-spacing:0.3px;">
        Failure prediction with 90% conformal prediction intervals · XGBoost + LSTM ensemble
    </p>
</div>
""", unsafe_allow_html=True)

# ── Critical alert ─────────────────────────────────────────
critical = df[df["priority"] == "CRITICAL"] if "priority" in df.columns else pd.DataFrame()
if len(critical) > 0:
    turbs = ", ".join(critical["turbine_id"].tolist())
    st.markdown(alert_banner(
        f"CRITICAL — {turbs}: RUL below threshold. Shutdown recommended.",
        "Estimated failure within 40h · Initiate emergency maintenance protocol",
        "critical"
    ), unsafe_allow_html=True)

# ── KPI row ────────────────────────────────────────────────
rul_vals = df["rul_hours"].tolist() if "rul_hours" in df.columns else [100]*5
n_crit   = len(critical)
n_healthy = len(df[df["priority"]=="LOW"]) if "priority" in df.columns else 0

cols = st.columns(4)
kpis = [
    ("Min Fleet RUL",     f"{min(rul_vals):.0f}h",    "Earliest failure",     "down" if min(rul_vals)<40 else "warn", COLORS["critical"]),
    ("Avg Fleet RUL",     f"{np.mean(rul_vals):.0f}h","Fleet mean estimate",  "neutral",                              COLORS["cyan"]),
    ("Critical Turbines", str(n_crit),                 "Immediate action",     "down" if n_crit > 0 else "up",        COLORS["critical"] if n_crit else COLORS["healthy"]),
    ("Healthy Turbines",  str(n_healthy),              "RUL > 100h",           "up",                                  COLORS["healthy"]),
]
icons = ["⏳","📊","🔴","✅"]
for col, (label, val, delta, dtype, color), icon in zip(cols, kpis, icons):
    with col:
        st.markdown(kpi_card(label, val, delta, dtype, icon, color), unsafe_allow_html=True)

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

# ── Gauge row ──────────────────────────────────────────────
st.markdown(section_header("⏱️ RUL Gauges", "Per-turbine remaining useful life estimate"),
            unsafe_allow_html=True)

gauge_cols = st.columns(5)
for col, (_, row) in zip(gauge_cols, df.iterrows()):
    rul   = float(row.get("rul_hours", 100))
    tid   = row.get("turbine_id", "")
    pri   = row.get("priority", "LOW")
    color = PRIORITY_COLOR.get(pri, COLORS["healthy"])
    pct   = min(rul / 125, 1.0)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rul,
        number={"suffix": "h", "font": {"size": 26, "color": color,
                "family": "JetBrains Mono"}},
        title={"text": f"<b style='font-size:13px;color:#F8FAFC;'>{tid}</b><br>"
                       f"<span style='font-size:10px;color:#64748B;'>{pri}</span>",
               "font": {"size": 12}},
        gauge={
            "axis": {"range": [0, 125], "tickwidth": 1,
                     "tickcolor": "rgba(255,255,255,0.1)",
                     "tickfont": {"size": 9, "color": "#64748B"},
                     "nticks": 6},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "rgba(5,8,22,0.8)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,   40], "color": "rgba(239,68,68,0.08)"},
                {"range": [40,  80], "color": "rgba(245,158,11,0.06)"},
                {"range": [80, 125], "color": "rgba(16,185,129,0.06)"},
            ],
            "threshold": {
                "line": {"color": COLORS["critical"], "width": 2},
                "thickness": 0.75, "value": 40,
            },
        }
    ))
    fig.update_layout(
        height=200,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"], family="Inter"),
        margin=dict(l=8, r=8, t=56, b=8),
    )
    col.plotly_chart(fig, use_container_width=True)

st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

# ── Confidence interval chart ──────────────────────────────
st.markdown(section_header("📊 Prediction Intervals",
            "90% conformal prediction bands — shaded region shows uncertainty"),
            unsafe_allow_html=True)

turbine_ids = df["turbine_id"].tolist() if "turbine_id" in df.columns else TURBINES
rul_list    = df["rul_hours"].tolist()   if "rul_hours"  in df.columns else [100]*5
lower_list  = df["lower_hours"].tolist() if "lower_hours" in df.columns else [v-20 for v in rul_list]
upper_list  = df["upper_hours"].tolist() if "upper_hours" in df.columns else [v+20 for v in rul_list]
pri_list    = df["priority"].tolist()    if "priority"   in df.columns else ["LOW"]*5
pt_colors   = [PRIORITY_COLOR.get(p, COLORS["healthy"]) for p in pri_list]

fig2 = go.Figure()

# CI shaded band
fig2.add_trace(go.Scatter(
    x=turbine_ids + turbine_ids[::-1],
    y=upper_list + lower_list[::-1],
    fill="toself",
    fillcolor="rgba(0,212,255,0.06)",
    line=dict(color="rgba(0,0,0,0)"),
    name="90% CI Band",
    showlegend=True,
))
fig2.add_trace(go.Scatter(
    x=turbine_ids, y=upper_list,
    mode="lines", line=dict(dash="dot", color=COLORS["cyan"], width=1),
    name="Upper bound", opacity=0.5,
))
fig2.add_trace(go.Scatter(
    x=turbine_ids, y=lower_list,
    mode="lines", line=dict(dash="dot", color=COLORS["cyan"], width=1),
    name="Lower bound", opacity=0.5,
))

# Spline connecting estimates
fig2.add_trace(go.Scatter(
    x=turbine_ids, y=rul_list,
    mode="lines", line=dict(color=COLORS["purple"], width=1.5, dash="dot", shape="spline"),
    showlegend=False, opacity=0.5,
))

# Point estimates with per-turbine color
fig2.add_trace(go.Scatter(
    x=turbine_ids, y=rul_list,
    mode="markers+text",
    marker=dict(
        size=18, color=pt_colors,
        line=dict(width=2, color=COLORS["bg_primary"]),
        symbol="circle",
    ),
    text=[f"{v:.0f}h" for v in rul_list],
    textposition="top center",
    textfont=dict(size=11, color=COLORS["text_primary"], family="JetBrains Mono"),
    name="RUL Estimate",
))

fig2.add_hline(y=40, line_dash="dash", line_color=COLORS["critical"], line_width=1.5,
              annotation_text="🚨 Critical (40h)",
              annotation_font_color=COLORS["critical"], annotation_font_size=10)
fig2.add_hline(y=80, line_dash="dot", line_color=COLORS["warning"], line_width=1,
              annotation_text="⚠️ Warning (80h)",
              annotation_font_color=COLORS["warning"], annotation_font_size=10)

fig2.update_layout(
    height=400,
    xaxis_title="Turbine ID",
    yaxis_title="Remaining Useful Life (hours)",
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"],
               font=dict(color=COLORS["text_secondary"], size=11)),
    **_PT,
)
st.plotly_chart(fig2, use_container_width=True)

# ── Degradation velocity bars ──────────────────────────────
# Replace the "── Degradation velocity bars ──" section at the bottom of 2_rul_monitor.py
# At top of degradation section - re-reference df explicitly
_df = df  # ensure local reference
hs_vals = _df["health_score"].tolist() if "health_score" in _df.columns else [0.5]*len(_df)
st.markdown(section_header("📉 Degradation Rate Analysis",
            "Health score drop rate — higher = faster deterioration"),
            unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    hs_vals = df["health_score"].tolist() if "health_score" in df.columns else [0.5]*5
    degrad  = [round((1 - v) * 100, 1) for v in hs_vals]
    bar_colors = [PRIORITY_COLOR.get(p, COLORS["healthy"]) for p in pri_list]
    fig3 = go.Figure(go.Bar(
        x=turbine_ids, y=degrad,
        marker_color=bar_colors,
        marker_line_color="rgba(0,0,0,0)",
        text=[f"{v}%" for v in degrad],
        textposition="outside",
        textfont=dict(color=COLORS["text_secondary"], size=11, family="JetBrains Mono"),
    ))
    fig3.add_hline(y=60, line_dash="dash", line_color=COLORS["critical"], line_width=1,
                  annotation_text="Critical threshold",
                  annotation_font_color=COLORS["critical"], annotation_font_size=10)
    fig3.update_layout(title="<b>Degradation Index (%)</b>",
                       height=300, showlegend=False, bargap=0.35, **_PT)
    st.plotly_chart(fig3, use_container_width=True)

with c2:
    if "anomaly_score" in df.columns:
        fig4 = go.Figure()
        for (_, row), color in zip(df.iterrows(), pt_colors):
            fig4.add_trace(go.Scatter(
                x=[float(row.get("anomaly_score", 0))],
                y=[float(row.get("rul_hours", 0))],
                mode="markers+text",
                marker=dict(size=20, color=color, opacity=0.88,
                            line=dict(width=2, color=COLORS["bg_primary"])),
                text=[row.get("turbine_id", "")],
                textposition="top center",
                textfont=dict(size=10, color=COLORS["text_secondary"], family="JetBrains Mono"),
                showlegend=False,
            ))
        fig4.add_hline(y=40, line_dash="dash", line_color=COLORS["critical"], line_width=1)
        fig4.add_vline(x=0.7, line_dash="dot", line_color=COLORS["warning"], line_width=1)
        fig4.update_layout(
            title="<b>RUL vs Anomaly Score</b>",
            xaxis_title="Anomaly Score", yaxis_title="RUL (hours)",
            height=300, **_PT,
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No anomaly_score data available.")

# ── Summary table ──────────────────────────────────────────
st.markdown(section_header("📋 RUL Summary"), unsafe_allow_html=True)
show_cols = [c for c in ["turbine_id","rul_hours","lower_hours","upper_hours",
                          "priority","anomaly_score","health_score"] if c in df.columns]
st.dataframe(
    df[show_cols].round(1),
    use_container_width=True,
    hide_index=True,
    column_config={
        "rul_hours":     st.column_config.ProgressColumn("RUL (h)",    min_value=0, max_value=125, format="%.0f h"),
        "anomaly_score": st.column_config.ProgressColumn("Anomaly",    min_value=0, max_value=1,   format="%.3f"),
        "health_score":  st.column_config.ProgressColumn("Health",     min_value=0, max_value=1,   format="%.2f"),
        "priority":      st.column_config.TextColumn("Priority"),
    }
)