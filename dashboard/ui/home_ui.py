# dashboard/ui/home_ui.py
"""WindSense-AI — Elite Home Page"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
from dashboard.ui.theme import COLORS, PRIORITY_COLORS
from dashboard.ui.components import (
    kpi_card, section_header, priority_badge,
    styled_table, pulse_indicator, agent_card,
)
from dashboard.ui.animations import fleet_map
from dashboard.digital_twin_embed import render_digital_twin


def render_home(df_kpi=None):
    
    # ── Parse KPI data ─────────────────────────────────────
# In home_ui.py render_home(), replace the fleet_health calculation:

    if df_kpi is not None and len(df_kpi) > 0:
        n_turbines   = len(df_kpi)
        n_anomalies  = int(df_kpi["anomaly_flag"].sum()) if "anomaly_flag" in df_kpi.columns else 0
        min_rul      = float(df_kpi["rul_hours"].min()) if "rul_hours" in df_kpi.columns else 0
        min_rul_tid  = str(df_kpi.loc[df_kpi["rul_hours"].idxmin(), "turbine_id"]) \
                   if "rul_hours" in df_kpi.columns else "N/A"
        total_saving = float(df_kpi["net_saving_usd"].sum()) if "net_saving_usd" in df_kpi.columns else 0
        n_critical   = int(len(df_kpi[df_kpi["priority"] == "CRITICAL"])) if "priority" in df_kpi.columns else 0

    # Fleet health — same fallback logic as topbar
        if "health_score" in df_kpi.columns and df_kpi["health_score"].sum() > 0:
            fleet_health = float(df_kpi["health_score"].mean() * 100)
        elif "priority" in df_kpi.columns:
            pri_health_map = {"CRITICAL": 0.30, "HIGH": 0.55, "MEDIUM": 0.72, "LOW": 0.90}
            fleet_health = float(df_kpi["priority"].map(pri_health_map).fillna(0.85).mean() * 100)
        else:
            fleet_health = 85.0
    else:
        n_turbines = 5; n_anomalies = 0; min_rul = 0
        min_rul_tid = "N/A"; total_saving = 0
        n_critical = 0; fleet_health = 85.0

    n_work_orders = len(list(Path("outputs/work_orders").glob("*.pdf")))

    # ── Page header ────────────────────────────────────────
    st.markdown(f"""
    <div class="ws-stagger-1" style="margin-bottom:24px;">
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:6px;">
            <h1 style="font-size:28px;font-weight:800;margin:0;
                       font-family:'Space Grotesk',sans-serif;
                       color:{COLORS['text_primary']};letter-spacing:-1px;">
                🖥️ Fleet Command Center
            </h1>
            <span style="font-size:10px;font-weight:700;color:{COLORS['cyan']};
                         letter-spacing:2px;background:rgba(0,212,255,0.08);
                         border:1px solid rgba(0,212,255,0.22);
                         border-radius:20px;padding:6px 12px;">
                Predicitve Wind Intelligence
            </span>
        </div>
        <p style="color:{COLORS['text_muted']};font-size:13px;margin:0;letter-spacing:0.3px;">
            Real-time predictive maintenance intelligence — 2MW onshore wind turbine fleet
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ────────────────────────────────────────────
    kpi_defs = [
        ("Fleet Health",   f"{fleet_health:.0f}%",    "1 Critical Unit",
         "up" if fleet_health > 75 else "warn", COLORS["healthy"],  "🏭"),
        ("Active Alerts",  str(n_anomalies),           "Anomalies Detected",
         "down" if n_anomalies > 0 else "up",
         COLORS["critical"] if n_anomalies > 0 else COLORS["healthy"], "⚠️"),
        ("Critical Units", str(n_critical),            "Immediate Action Required",
         "down" if n_critical > 0 else "up",
         COLORS["critical"] if n_critical > 0 else COLORS["healthy"], "🚨"),
        ("Min RUL",        f"{min_rul:.0f}h",          f"⚠ {min_rul_tid}",
         "warn" if min_rul < 50 else "up",       COLORS["warning"],  "⏱️"),
        ("Net Savings",    f"${total_saving:,.0f}",    "vs Unplanned Failure",
         "up",                                    COLORS["cyan"],    "💰"),
        ("Work Orders",    str(n_work_orders),         "Generated PDFs",
         "neutral",                               COLORS["purple"],  "📋"),
    ]
    cols = st.columns(6)
    for i, (col, (label, val, delta, dtype, color, icon)) in enumerate(zip(cols, kpi_defs)):
        with col:
            st.markdown(
                kpi_card(label, val, delta, dtype, icon, color).replace(
                    'ws-stagger-1', f'ws-stagger-{min(i+1,5)}'
                ),
                unsafe_allow_html=True
            )

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Fleet Map + Agent Pipeline ─────────────────────────
    col_map, col_right = st.columns([3, 2], gap="medium")

    with col_map:
        st.markdown(section_header("🗺️ Digital Twin Fleet Map",
                    "Live turbine health topology — offshore grid"), unsafe_allow_html=True)
        positions = [(18,32),(38,22),(62,28),(80,40),(48,64)]
        turbine_data = []
        if df_kpi is not None:
            for i, (_, row) in enumerate(df_kpi.iterrows()):
                turbine_data.append({
                    "id":           row.get("turbine_id", f"WT-{i+1:03d}"),
                    "x":            positions[i % len(positions)][0],
                    "y":            positions[i % len(positions)][1],
                    "priority":     row.get("priority", "LOW"),
                    "health_score": float(row.get("health_score", 0.85)),
                    "rul_hours":    float(row.get("rul_hours", 100)),
                })
        else:
            for i in range(5):
                turbine_data.append({
                    "id": f"WT-00{i+1}", "x": positions[i][0], "y": positions[i][1],
                    "priority": "LOW", "health_score": 0.85, "rul_hours": 100,
                })
        st.markdown(fleet_map(turbine_data), unsafe_allow_html=True)

    with col_right:
        # Agent Pipeline
        st.markdown(section_header("🤖 Agent Pipeline", "4 autonomous AI agents active"),
                    unsafe_allow_html=True)
        agents = [
            ("Agent 1", "Health Monitor",     "LSTM AE + Isolation Forest", COLORS["cyan"],    "F1: 0.82"),
            ("Agent 2", "Failure Predictor",  "XGBoost + LSTM + Conformal", COLORS["purple"],  "RMSE: ~18h"),
            ("Agent 3", "Maintenance Coord",  "Rule-based + PPO RL",        COLORS["healthy"], "5 decisions"),
            ("Agent 4", "Energy Forecaster",  "Prophet + LSTM",             COLORS["warning"], "CF: 35-45%"),
        ]
        for args in agents:
            st.markdown(agent_card(*args), unsafe_allow_html=True)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # Tech Stack
        st.markdown(section_header("📦 Tech Stack"), unsafe_allow_html=True)
        stack = [
            ("IoT + Digital Twin", "MQTT · InfluxDB · ODE Sim",  COLORS["cyan"]),
            ("ML Models",          "TF · XGBoost · Scikit-learn", COLORS["purple"]),
            ("LLM + RAG",          "Ollama TinyLlama · FAISS",    COLORS["healthy"]),
            ("Orchestration",      "LangGraph · 4 Agents",        COLORS["warning"]),
            ("MLOps",              "MLflow · Evidently AI",        "#60A5FA"),
        ]
        for name, desc, color in stack:
            st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:space-between;
                        padding:9px 14px;margin-bottom:5px;
                        background:rgba(5,8,22,0.6);
                        border:1px solid {COLORS['border']};
                        border-left:3px solid {color};
                        border-radius:10px;
                        transition:all 0.18s ease;">
                <span style="font-size:12px;font-weight:700;
                             color:{COLORS['text_primary']};
                             font-family:'Space Grotesk',sans-serif;">{name}</span>
                <span style="font-size:11px;color:{COLORS['text_muted']};
                             text-align:right;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Fleet Table + Quick Nav ────────────────────────────
    col_tbl, col_nav = st.columns([3, 2], gap="medium")

    with col_tbl:
        st.markdown(section_header("📡 Live Fleet Status", "Real-time asset telemetry"),
                    unsafe_allow_html=True)
        if df_kpi is not None:
            rows = []
            for _, row in df_kpi.iterrows():
                pri   = row.get("priority", "LOW")
                rul   = float(row.get("rul_hours", 0))
                anom  = float(row.get("anomaly_score", 0))
                action = str(row.get("action", "")).replace("_", " ")
                rul_c  = COLORS["critical"] if rul < 30 else COLORS["warning"] if rul < 60 else COLORS["text_primary"]
                anom_c = COLORS["critical"] if anom > 0.8 else COLORS["warning"] if anom > 0.6 else COLORS["text_secondary"]
                rows.append([
                    f'<span style="color:{COLORS["cyan"]};font-weight:700;'
                    f'font-family:\'JetBrains Mono\',monospace;">{row.get("turbine_id","")}</span>',
                    priority_badge(pri),
                    f'<span style="font-family:\'JetBrains Mono\',monospace;color:{rul_c};font-weight:700;">{rul:.0f}h</span>',
                    f'<span style="font-family:\'JetBrains Mono\',monospace;color:{anom_c};">{anom:.3f}</span>',
                    f'<span style="font-size:11px;color:{COLORS["text_muted"]};">{action}</span>',
                ])
            st.markdown(styled_table(["Turbine","Priority","RUL","Anomaly","Action"], rows),
                        unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:rgba(13,20,36,0.85);border:1px solid {COLORS['border']};
                        border-radius:14px;padding:32px;text-align:center;">
                <div style="font-size:36px;margin-bottom:10px;">🤖</div>
                <div style="color:{COLORS['text_secondary']};font-size:14px;font-weight:700;
                            font-family:'Space Grotesk',sans-serif;">No pipeline data yet</div>
                <div style="color:{COLORS['text_muted']};font-size:12px;margin-top:6px;
                            font-family:'JetBrains Mono',monospace;">
                    python -m graph.langgraph_orchestrator
                </div>
            </div>
            """, unsafe_allow_html=True)

                # ── 3D Digital Twin (toggle button → opens inline below) ──
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    st.markdown(section_header("🌍 3D Operations View",
                "Immersive digital twin — full fleet visualization"), unsafe_allow_html=True)

    if "show_3d_twin" not in st.session_state:
        st.session_state.show_3d_twin = False

    def _toggle_3d_twin():
        st.session_state.show_3d_twin = not st.session_state.show_3d_twin

    btn_label = "▼ Close 3D View" if st.session_state.show_3d_twin else "▶ Open 3D Digital Twin"
    st.button(btn_label, key="toggle_3d_twin", use_container_width=False, on_click=_toggle_3d_twin)

    if st.session_state.show_3d_twin:
        render_digital_twin(height=850)



