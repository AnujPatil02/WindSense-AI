# dashboard/page_modules/9_drift_monitor.py
"""Model Drift Monitor — Elite UI"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import streamlit as st
import json
import numpy as np
import plotly.graph_objects as go
from dashboard.ui.theme import COLORS
from dashboard.ui.components import section_header, kpi_card, alert_banner

_PT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94A3B8", size=12),
    margin=dict(l=16, r=16, t=44, b=16),
)

FALLBACK = {
    "drift_detected": True,
    "n_drifted_columns": 3,
    "drift_share": 0.30,
    "dataset_drift": True,
    "column_results": {
        "vibration_mms":  {"drift_detected": True,  "stattest": "ks",    "p_value": 0.012, "drift_score": 0.421},
        "gearbox_temp_c": {"drift_detected": True,  "stattest": "ks",    "p_value": 0.031, "drift_score": 0.318},
        "bearing_wear":   {"drift_detected": True,  "stattest": "ks",    "p_value": 0.048, "drift_score": 0.287},
        "oil_quality":    {"drift_detected": False, "stattest": "ks",    "p_value": 0.142, "drift_score": 0.089},
        "rotor_rpm":      {"drift_detected": False, "stattest": "ks",    "p_value": 0.287, "drift_score": 0.054},
        "power_output_kw":{"drift_detected": False, "stattest": "ks",    "p_value": 0.412, "drift_score": 0.031},
        "wind_speed_ms":  {"drift_detected": False, "stattest": "ks",    "p_value": 0.531, "drift_score": 0.021},
    }
}

# ── Header ─────────────────────────────────────────────────
st.markdown(
    '<div class="ws-stagger-1" style="margin-bottom:24px;">'
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">'
    '<h1 style="font-size:28px;font-weight:800;margin:0;'
    "font-family:'Space Grotesk',sans-serif;color:" + COLORS["text_primary"] + ';letter-spacing:-1px;">'
    '📈 Model Drift Monitor</h1>'
    '<span style="font-size:10px;font-weight:700;color:' + COLORS["cyan"] + ';'
    'letter-spacing:2px;background:rgba(0,212,255,0.08);'
    'border:1px solid rgba(0,212,255,0.22);border-radius:20px;padding:4px 12px;">EVIDENTLY AI</span>'
    '</div>'
    '<p style="color:' + COLORS["text_muted"] + ';font-size:13px;margin:0;">'
    'Sensor distribution drift detection · model performance monitoring · retraining alerts</p>'
    '</div>',
    unsafe_allow_html=True
)

# ── Run button ─────────────────────────────────────────────
if st.button("🔄 Run Drift Detection Now", use_container_width=False):
    with st.spinner("Analyzing sensor distributions with Evidently AI..."):
        try:
            from mlops.drift_monitor import detect_drift
            result = detect_drift()
            st.session_state["drift_result"] = result
            st.success("✅ Drift detection complete!")
        except Exception as e:
            st.warning(f"Drift module unavailable — using demo data. ({e})")
            st.session_state["drift_result"] = FALLBACK

# ── Load result ────────────────────────────────────────────
summary_path = Path("outputs/reports/drift_summary.json")
result = st.session_state.get("drift_result")
if not result and summary_path.exists():
    try:
        with open(summary_path) as f:
            result = json.load(f)
    except Exception:
        pass
if not result:
    result = FALLBACK
    st.markdown(alert_banner(
        "Using demo drift data — click Run Drift Detection for live analysis",
        "python -m mlops.drift_monitor", "info"
    ), unsafe_allow_html=True)

drift        = result.get("drift_detected", False)
n_drifted    = result.get("n_drifted_columns", 0)
drift_share  = result.get("drift_share", 0)
col_results  = result.get("column_results", FALLBACK["column_results"])
total_cols   = len(col_results)

# ── Drift status banner ────────────────────────────────────
if drift:
    st.markdown(alert_banner(
        "DATA DRIFT DETECTED — Model retraining recommended",
        f"{n_drifted}/{total_cols} sensors drifted · {drift_share*100:.1f}% drift share",
        "critical"
    ), unsafe_allow_html=True)
else:
    st.markdown(alert_banner(
        "No Significant Drift — Models performing within tolerance",
        f"All {total_cols} sensors within distribution bounds",
        "info"
    ), unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────
cols = st.columns(4)
kpis = [
    ("Drift Status",    "DETECTED" if drift else "NORMAL",
     "Retraining needed" if drift else "All clear",
     "down" if drift else "up",
     COLORS["critical"] if drift else COLORS["healthy"], "📉"),
    ("Drifted Sensors", str(n_drifted),
     f"of {total_cols} monitored", "down" if n_drifted else "up",
     COLORS["critical"] if n_drifted else COLORS["healthy"], "📡"),
    ("Drift Share",     f"{drift_share*100:.1f}%",
     "Affected sensors", "warn" if drift_share>0.2 else "up",
     COLORS["warning"] if drift_share>0.2 else COLORS["healthy"], "📊"),
    ("Model Action",    "RETRAIN" if drift else "MONITOR",
     "Recommended action", "down" if drift else "neutral",
     COLORS["critical"] if drift else COLORS["cyan"], "🤖"),
]
for col, (label, val, delta, dtype, color, icon) in zip(cols, kpis):
    with col:
        st.markdown(kpi_card(label, val, delta, dtype, icon, color), unsafe_allow_html=True)

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

# ── Two-column: drift score bars + p-value chart ───────────
c1, c2 = st.columns(2)

with c1:
    st.markdown(section_header("Drift Score by Sensor",
                "Higher = more drift from training distribution"),
                unsafe_allow_html=True)

    sensors = list(col_results.keys())
    scores  = [col_results[s].get("drift_score",0) for s in sensors]
    drifted = [col_results[s].get("drift_detected",False) for s in sensors]
    bar_c   = [COLORS["critical"] if d else COLORS["healthy"] for d in drifted]
    labels  = [s.replace("_"," ").title() for s in sensors]

    fig1 = go.Figure(go.Bar(
        x=scores, y=labels, orientation="h",
        marker=dict(color=bar_c, line=dict(width=0)),
        text=[f"{v:.3f}" for v in scores],
        textposition="outside",
        textfont=dict(color=COLORS["text_secondary"], size=11, family="JetBrains Mono"),
    ))
    fig1.add_vline(x=0.15, line_dash="dash", line_color=COLORS["warning"], line_width=1.5,
                  annotation_text="Drift threshold (0.15)",
                  annotation_font_color=COLORS["warning"], annotation_font_size=10)
    fig1.update_layout(
        height=340, showlegend=False, bargap=0.3,
        xaxis=dict(title="Drift Score", range=[0, max(scores)*1.3],
                   gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(autorange="reversed"),
        **_PT,
    )
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.markdown(section_header("Statistical Test p-values",
                "KS test — lower p = stronger evidence of drift"),
                unsafe_allow_html=True)

    pvals  = [col_results[s].get("p_value", 0.5) for s in sensors]
    pval_c = [COLORS["critical"] if p < 0.05 else
              COLORS["warning"]  if p < 0.10 else
              COLORS["healthy"]  for p in pvals]

    fig2 = go.Figure(go.Bar(
        x=pvals, y=labels, orientation="h",
        marker=dict(color=pval_c, line=dict(width=0)),
        text=[f"{v:.3f}" for v in pvals],
        textposition="outside",
        textfont=dict(color=COLORS["text_secondary"], size=11, family="JetBrains Mono"),
    ))
    fig2.add_vline(x=0.05, line_dash="dash", line_color=COLORS["critical"], line_width=1.5,
                  annotation_text="α = 0.05",
                  annotation_font_color=COLORS["critical"], annotation_font_size=10)
    fig2.add_vline(x=0.10, line_dash="dot", line_color=COLORS["warning"], line_width=1,
                  annotation_text="α = 0.10",
                  annotation_font_color=COLORS["warning"], annotation_font_size=10)
    fig2.update_layout(
        height=340, showlegend=False, bargap=0.3,
        xaxis=dict(title="p-value", range=[0, max(pvals)*1.3],
                   gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(autorange="reversed"),
        **_PT,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Simulated distribution comparison ─────────────────────
st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
st.markdown(section_header("Distribution Comparison",
            "Training vs production sensor distributions — top drifted sensors"),
            unsafe_allow_html=True)

drifted_sensors = [s for s in sensors if col_results[s].get("drift_detected", False)]
if not drifted_sensors:
    drifted_sensors = sensors[:3]

dist_cols = st.columns(min(len(drifted_sensors), 3))
np.random.seed(42)

for col, sensor in zip(dist_cols, drifted_sensors[:3]):
    score = col_results[sensor].get("drift_score", 0.2)
    train_mean = np.random.uniform(3, 6)
    prod_mean  = train_mean + score * 4
    train_data = np.random.normal(train_mean, 1.0, 200)
    prod_data  = np.random.normal(prod_mean,  1.3, 200)

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=train_data, name="Training", nbinsx=25,
        marker_color="rgba(0,212,255,0.6)",
        opacity=0.75,
    ))
    fig.add_trace(go.Histogram(
        x=prod_data, name="Production", nbinsx=25,
        marker_color="rgba(239,68,68,0.6)",
        opacity=0.75,
    ))
    fig.update_layout(
        title="<b>" + sensor.replace("_"," ").title() + "</b>",
        barmode="overlay", height=240,
        legend=dict(bgcolor="rgba(0,0,0,0)",
                   font=dict(color=COLORS["text_secondary"], size=10)),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        **_PT,
    )
    col.plotly_chart(fig, use_container_width=True)

# ── Detailed table ─────────────────────────────────────────
st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
st.markdown(section_header("Sensor Drift Detail Table"), unsafe_allow_html=True)

import pandas as pd
rows = []
for s, data in col_results.items():
    d = data.get("drift_detected", False)
    rows.append({
        "Sensor":          s.replace("_"," ").title(),
        "Drift Detected":  "⚠️ YES" if d else "✅ NO",
        "Drift Score":     round(data.get("drift_score", 0), 4),
        "p-value":         round(data.get("p_value", 1.0), 4),
        "Test":            data.get("stattest", "ks").upper(),
        "Status":          "RETRAIN" if d else "OK",
    })

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
             column_config={
                 "Drift Score": st.column_config.ProgressColumn(
                     "Drift Score", min_value=0, max_value=1, format="%.3f"),
             })

# ── HTML report embed ──────────────────────────────────────
html_report = Path("outputs/reports/drift_report.html")
if html_report.exists():
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown(section_header("📄 Full Evidently Report"), unsafe_allow_html=True)
    with open(html_report, encoding="utf-8", errors="ignore") as f:
        st.components.v1.html(f.read(), height=600, scrolling=True)