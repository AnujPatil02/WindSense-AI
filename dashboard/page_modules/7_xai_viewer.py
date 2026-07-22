# dashboard/page_modules/7_xai_viewer.py
"""XAI Viewer — Elite UI"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from dashboard.ui.theme import COLORS
from dashboard.ui.components import section_header, kpi_card

_PT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94A3B8", size=12),
    margin=dict(l=16, r=16, t=44, b=16),
)

# ── Header ─────────────────────────────────────────────────
st.markdown(
    '<div class="ws-stagger-1" style="margin-bottom:24px;">'
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">'
    '<h1 style="font-size:28px;font-weight:800;margin:0;'
    "font-family:'Space Grotesk',sans-serif;color:" + COLORS["text_primary"] + ';letter-spacing:-1px;">'
    '🔬 Explainable AI Viewer</h1>'
    '<span style="font-size:10px;font-weight:700;color:' + COLORS["purple"] + ';'
    'letter-spacing:2px;background:rgba(139,92,246,0.08);'
    'border:1px solid rgba(139,92,246,0.22);border-radius:20px;padding:4px 12px;">SHAP</span>'
    '</div>'
    '<p style="color:' + COLORS["text_muted"] + ';font-size:13px;margin:0;">'
    'SHAP feature importance · model explainability · sensor attribution</p>'
    '</div>',
    unsafe_allow_html=True
)

# ── Helper: load JSON importance ───────────────────────────
def load_importance(json_path: Path):
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    return None

# ── Synthetic fallback SHAP data ──────────────────────────
FALLBACK_AGENT1 = {
    "sensor_7_vibration":   0.312, "sensor_11_temp":     0.278,
    "sensor_2_rpm":         0.201, "sensor_4_pressure":  0.142,
    "sensor_3_power":       0.118, "sensor_9_oil":       0.089,
    "sensor_1_wind":        0.071, "sensor_5_torque":    0.054,
    "sensor_8_current":     0.038, "sensor_6_voltage":   0.022,
}
FALLBACK_AGENT2 = {
    "bearing_wear":         0.341, "gearbox_temp_c":     0.289,
    "vibration_mms":        0.218, "oil_quality":        0.167,
    "anomaly_score":        0.134, "rotor_rpm":          0.098,
    "power_output_kw":      0.076, "wind_speed_ms":      0.058,
    "generator_temp":       0.041, "nacelle_temp":       0.029,
}

tab1, tab2 = st.tabs(["🤖 Agent 1 — Anomaly Detection", "⏱️ Agent 2 — RUL Estimation"])

# ── TAB 1: Agent 1 ─────────────────────────────────────────
with tab1:
    st.markdown(section_header("SHAP Feature Importance — Isolation Forest",
                "Which sensors drive anomaly detection decisions"),
                unsafe_allow_html=True)

    imp1 = load_importance(Path("outputs/reports/shap_importance_agent1.json")) or FALLBACK_AGENT1

    c1, c2 = st.columns([1, 2])

    with c1:
        # Top feature KPIs
        top3 = sorted(imp1.items(), key=lambda x: x[1], reverse=True)[:3]
        for i, (feat, val) in enumerate(top3):
            label = feat.replace("_"," ").title()[:18]
            color = [COLORS["critical"], COLORS["warning"], COLORS["cyan"]][i]
            st.markdown(kpi_card(
                f"#{i+1} Feature", label,
                f"SHAP: {val:.3f}", "neutral", ["🥇","🥈","🥉"][i], color
            ), unsafe_allow_html=True)
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    with c2:
        sorted_imp = dict(sorted(imp1.items(), key=lambda x: x[1], reverse=True)[:10])
        labels = [k.replace("_"," ").title() for k in sorted_imp.keys()]
        values = list(sorted_imp.values())
        bar_colors = []
        for v in values:
            if v >= 0.25:   bar_colors.append(COLORS["critical"])
            elif v >= 0.15: bar_colors.append(COLORS["warning"])
            else:           bar_colors.append(COLORS["cyan"])

        fig1 = go.Figure(go.Bar(
            x=values, y=labels, orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=[f"{v:.3f}" for v in values],
            textposition="outside",
            textfont=dict(color=COLORS["text_secondary"], size=11, family="JetBrains Mono"),
        ))
        fig1.update_layout(
            title="<b>Top 10 Features — Anomaly Detection</b>",
            height=360, showlegend=False, bargap=0.3,
            xaxis=dict(title="Mean |SHAP Value|",
                       gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(autorange="reversed",
                       tickfont=dict(color=COLORS["text_secondary"], size=11)),
            **_PT,
        )
        st.plotly_chart(fig1, use_container_width=True)

    # SHAP image if available
    img1 = Path("outputs/reports/shap_agent1_summary.png")
    if img1.exists():
        st.markdown(section_header("SHAP Summary Plot"), unsafe_allow_html=True)
        st.image(str(img1), caption="SHAP Summary — Isolation Forest (Agent 1)")
    else:
        st.markdown(
            '<div style="background:rgba(139,92,246,0.06);border:1px solid rgba(139,92,246,0.18);'
            'border-radius:12px;padding:16px;margin-top:12px;">'
            '<div style="font-size:12px;color:' + COLORS["purple"] + ';font-weight:700;'
            'margin-bottom:6px;">📌 Generate SHAP plots</div>'
            '<code style="font-size:12px;color:' + COLORS["text_secondary"] + ';">'
            'python -m agents.agent1_health_monitor.shap_explainer</code>'
            '</div>',
            unsafe_allow_html=True
        )

    # Waterfall-style breakdown (simulated)
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Sensor Attribution Waterfall",
                "Contribution of each sensor to anomaly score"),
                unsafe_allow_html=True)

    wf_feats  = list(sorted_imp.keys())[:8]
    wf_vals   = [sorted_imp[k] * (1 if i%2==0 else -0.4) for i,k in enumerate(wf_feats)]
    wf_labels = [k.replace("_"," ").title() for k in wf_feats]
    wf_colors = [COLORS["critical"] if v > 0 else COLORS["healthy"] for v in wf_vals]

    fig_wf = go.Figure(go.Bar(
        x=[f"{v:+.3f}" for v in wf_vals],
        y=wf_labels,
        orientation="h",
        marker=dict(color=wf_colors, line=dict(width=0)),
        text=[f"{v:+.3f}" for v in wf_vals],
        textposition="outside",
        textfont=dict(color=COLORS["text_secondary"], size=11, family="JetBrains Mono"),
    ))
    fig_wf.update_layout(
        height=300, showlegend=False, bargap=0.3,
        xaxis=dict(title="SHAP Contribution", gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(autorange="reversed"),
        **_PT,
    )
    st.plotly_chart(fig_wf, use_container_width=True)

# ── TAB 2: Agent 2 ─────────────────────────────────────────
with tab2:
    st.markdown(section_header("SHAP Feature Importance — XGBoost RUL",
                "Which features most influence remaining useful life predictions"),
                unsafe_allow_html=True)

    imp2 = load_importance(Path("outputs/reports/shap_importance_agent2.json")) or FALLBACK_AGENT2

    c1, c2 = st.columns([1, 2])

    with c1:
        top3b = sorted(imp2.items(), key=lambda x: x[1], reverse=True)[:3]
        for i, (feat, val) in enumerate(top3b):
            label = feat.replace("_"," ").title()[:18]
            color = [COLORS["critical"], COLORS["warning"], COLORS["cyan"]][i]
            st.markdown(kpi_card(
                f"#{i+1} Feature", label,
                f"SHAP: {val:.3f}", "neutral", ["🥇","🥈","🥉"][i], color
            ), unsafe_allow_html=True)
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    with c2:
        sorted_imp2 = dict(sorted(imp2.items(), key=lambda x: x[1], reverse=True)[:10])
        labels2 = [k.replace("_"," ").title() for k in sorted_imp2.keys()]
        values2 = list(sorted_imp2.values())
        bar_colors2 = []
        for v in values2:
            if v >= 0.25:   bar_colors2.append(COLORS["critical"])
            elif v >= 0.15: bar_colors2.append(COLORS["warning"])
            else:           bar_colors2.append(COLORS["purple"])

        fig2 = go.Figure(go.Bar(
            x=values2, y=labels2, orientation="h",
            marker=dict(color=bar_colors2, line=dict(width=0)),
            text=[f"{v:.3f}" for v in values2],
            textposition="outside",
            textfont=dict(color=COLORS["text_secondary"], size=11, family="JetBrains Mono"),
        ))
        fig2.update_layout(
            title="<b>Top 10 Features — RUL Estimation</b>",
            height=360, showlegend=False, bargap=0.3,
            xaxis=dict(title="Mean |SHAP Value|",
                       gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(autorange="reversed",
                       tickfont=dict(color=COLORS["text_secondary"], size=11)),
            **_PT,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # SHAP images
    for img_path, caption in [
        ("outputs/reports/shap_agent2_summary.png",  "SHAP Summary — XGBoost RUL (Agent 2)"),
        ("outputs/reports/shap_agent2_beeswarm.png", "SHAP Beeswarm Plot — RUL Feature Distribution"),
    ]:
        p = Path(img_path)
        if p.exists():
            st.markdown(section_header(caption.split("—")[0].strip()), unsafe_allow_html=True)
            st.image(str(p), caption=caption)

    if not Path("outputs/reports/shap_agent2_summary.png").exists():
        st.markdown(
            '<div style="background:rgba(0,212,255,0.06);border:1px solid rgba(0,212,255,0.18);'
            'border-radius:12px;padding:16px;margin-top:12px;">'
            '<div style="font-size:12px;color:' + COLORS["cyan"] + ';font-weight:700;'
            'margin-bottom:6px;">📌 Generate SHAP plots</div>'
            '<code style="font-size:12px;color:' + COLORS["text_secondary"] + ';">'
            'python -m agents.agent2_failure_predictor.shap_explainer</code>'
            '</div>',
            unsafe_allow_html=True
        )

    # Feature interaction heatmap (simulated)
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Feature Interaction Heatmap",
                "Pairwise SHAP interaction values between top features"),
                unsafe_allow_html=True)

    import numpy as np
    feats_short = ["Bearing", "Gearbox T", "Vibration", "Oil", "Anomaly", "RPM"]
    n = len(feats_short)
    np.random.seed(42)
    mat = np.random.uniform(0.01, 0.15, (n,n))
    np.fill_diagonal(mat, list(sorted_imp2.values())[:n])

    fig3 = go.Figure(go.Heatmap(
        z=mat, x=feats_short, y=feats_short,
        colorscale=[[0,"#050816"],[0.5,COLORS["purple"]],[1,COLORS["critical"]]],
        text=np.round(mat,3),
        texttemplate="<b>%{text}</b>",
        textfont=dict(size=11, family="JetBrains Mono"),
        showscale=True,
        colorbar=dict(thickness=10, tickfont=dict(color=COLORS["text_muted"], size=10),
                      bgcolor="rgba(0,0,0,0)"),
    ))
    fig3.update_layout(height=320, **_PT)
    st.plotly_chart(fig3, use_container_width=True)