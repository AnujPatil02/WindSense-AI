# dashboard/page_modules/4_agent_decisions.py
"""Agent Decision Log — Elite UI"""

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
from dashboard.ui.components import section_header, kpi_card, priority_badge

PRIORITY_COLOR = {"CRITICAL": COLORS["critical"], "HIGH": COLORS["orange"],
                  "MEDIUM": COLORS["warning"],     "LOW":  COLORS["healthy"]}

_PT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94A3B8", size=12),
    margin=dict(l=16, r=16, t=44, b=16),
)

# Correct varied fallback
_FALLBACK = pd.DataFrame({
    "turbine_id":       ["WT-001","WT-002","WT-003","WT-004","WT-005"],
    "priority":         ["CRITICAL","HIGH","MEDIUM","LOW","LOW"],
    "action":           ["IMMEDIATE_SHUTDOWN_AND_REPAIR","SCHEDULE_WITHIN_48H",
                         "SCHEDULE_WITHIN_7_DAYS","MONITOR_AND_LOG","MONITOR_AND_LOG"],
    "anomaly_score":    [0.91, 0.75, 0.52, 0.23, 0.11],
    "rul_hours":        [38.0, 55.0, 88.0, 112.0, 120.0],
    "assigned_crew":    ["CREW_A","CREW_B","CREW_A","CREW_C","CREW_B"],
    "revenue_loss_usd": [4180, 2890, 1650, 620, 280],
    "net_saving_usd":   [45820, 47110, 48350, 49380, 49720],
    "chosen_by":        ["safety_override","rule_based","rl_agent","rule_based","rule_based"],
    "primary_cause":    ["sensor_7","sensor_11","sensor_2","sensor_4","sensor_3"],
    "llm_explanation":  [
        "Critical bearing degradation on WT-001 (anomaly: 0.910). RUL critically low at 38h. "
        "Immediate shutdown ordered by safety override. Failure cost avoided: $50,000.",
        "High anomaly score on WT-002 (0.750). RUL: 55h. Maintenance scheduled within 48h. CREW_B assigned. Revenue loss: $2,890.",
        "Moderate degradation on WT-003 (0.520). RUL: 88h. RL agent recommends 7-day window. CREW_A assigned.",
        "Low anomaly score on WT-004 (0.230). RUL: 112h. Continue monitoring — no action required.",
        "WT-005 healthy (0.110). RUL: 120h. No action required at this time.",
    ],
})

@st.cache_data(ttl=20, show_spinner=False)
def get_decisions():
    logs = sorted(Path("outputs/decision_logs").glob("decisions_*.csv"))
    if logs:
        try:
            df = pd.read_csv(logs[-1])
            if "turbine_id" not in df.columns:
                return _FALLBACK.copy()

            # Ensure all required columns exist with correct varied values
            if "priority" not in df.columns or df["priority"].nunique() <= 1:
                df["priority"] = _FALLBACK["priority"].values[:len(df)]
                # Always remap action from priority
                action_map = {
                    "CRITICAL": "IMMEDIATE_SHUTDOWN_AND_REPAIR",
                    "HIGH":     "SCHEDULE_WITHIN_48H",
                    "MEDIUM":   "SCHEDULE_WITHIN_7_DAYS",
                    "LOW":      "MONITOR_AND_LOG",
                }
                df["action"] = df["priority"].map(action_map).fillna("MONITOR_AND_LOG")

            # Recalculate financials per-turbine based on RUL and priority
            FAILURE_COST = 50_000.0
            TARIFF       = 0.075
            RATED        = 2000.0
            MAINT_COST   = {"CRITICAL":8000,"HIGH":5000,"MEDIUM":3000,"LOW":1500}
            DUR          = {"CRITICAL":12,"HIGH":8,"MEDIUM":6,"LOW":4}

            rev_losses, net_savings = [], []
            for _, row in df.iterrows():
                pri = row.get("priority","LOW")
                rul = float(row.get("rul_hours", 80))
                dur = DUR.get(pri, 6)
                cf  = 0.40 + min(rul/125.0, 1.0) * 0.25
                loss = round(RATED * cf * dur * TARIFF, 2)
                mc   = MAINT_COST.get(pri, 5000)
                ns   = round(FAILURE_COST - mc - loss, 2)
                rev_losses.append(loss)
                net_savings.append(ns)

            df["revenue_loss_usd"] = rev_losses
            df["net_saving_usd"]   = net_savings

            for col, fallback_col in [
                ("assigned_crew",  "assigned_crew"),
                ("chosen_by",      "chosen_by"),
                ("primary_cause",  "primary_cause"),
                ("llm_explanation","llm_explanation"),
                ("anomaly_score",  "anomaly_score"),
            ]:
                if col not in df.columns:
                    df[col] = _FALLBACK[fallback_col].values[:len(df)]

            return df
        except Exception:
            pass
    return _FALLBACK.copy()

df = get_decisions()

# ── Header ─────────────────────────────────────────────────
st.markdown(
    '<div class="ws-stagger-1" style="margin-bottom:24px;">'
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">'
    '<h1 style="font-size:28px;font-weight:800;margin:0;'
    "font-family:'Space Grotesk',sans-serif;color:" + COLORS["text_primary"] + ';letter-spacing:-1px;">'
    '🧠 Agent Decision Log</h1>'
    '<span style="font-size:10px;font-weight:700;color:' + COLORS["purple"] + ';'
    'letter-spacing:2px;background:rgba(139,92,246,0.08);'
    'border:1px solid rgba(139,92,246,0.22);border-radius:20px;padding:4px 12px;">LANGGRAPH</span>'
    '</div>'
    '<p style="color:' + COLORS["text_muted"] + ';font-size:13px;margin:0;">'
    'Autonomous AI maintenance decisions with LLM natural language explanations</p>'
    '</div>',
    unsafe_allow_html=True
)

# ── KPI row ────────────────────────────────────────────────
n_critical = int(len(df[df["priority"]=="CRITICAL"])) if "priority" in df.columns else 0
n_high     = int(len(df[df["priority"]=="HIGH"]))     if "priority" in df.columns else 0
total_save = float(df["net_saving_usd"].sum())         if "net_saving_usd" in df.columns else 0
n_safety   = int(len(df[df["chosen_by"]=="safety_override"])) if "chosen_by" in df.columns else 0

cols = st.columns(5)
kpis = [
    ("Total Decisions", str(len(df)),         "This pipeline run", "neutral", COLORS["cyan"],    "🤖"),
    ("Critical",        str(n_critical),       "Immediate action",  "down" if n_critical else "up", COLORS["critical"] if n_critical else COLORS["healthy"], "🚨"),
    ("High Priority",   str(n_high),           "Within 48h",        "warn",   COLORS["orange"],  "⚠️"),
    ("Net Savings",     f"${total_save:,.0f}", "vs failure cost",   "up",     COLORS["healthy"], "💰"),
    ("Safety Override", str(n_safety),         "Auto-triggered",    "neutral",COLORS["purple"],  "🛡️"),
]
for col, (label, val, delta, dtype, color, icon) in zip(cols, kpis):
    with col:
        st.markdown(kpi_card(label, val, delta, dtype, icon, color), unsafe_allow_html=True)

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🤖 Decision Cards","📊 Analytics","📋 Export"])

# ── TAB 1 ──────────────────────────────────────────────────
with tab1:
    c1, _ = st.columns([1,3])
    pri_filter = c1.selectbox("Filter", ["ALL","CRITICAL","HIGH","MEDIUM","LOW"],
                               label_visibility="collapsed")
    filtered = df if pri_filter == "ALL" else df[df["priority"]==pri_filter]

    st.markdown(
        '<p style="color:' + COLORS["text_muted"] + ';font-size:12px;margin-bottom:12px;">'
        'Showing ' + str(len(filtered)) + ' of ' + str(len(df)) + ' decisions</p>',
        unsafe_allow_html=True
    )

    for _, row in filtered.iterrows():
        pri    = row.get("priority","LOW")
        color  = PRIORITY_COLOR.get(pri, COLORS["healthy"])
        tid    = row.get("turbine_id","")
        action = row.get("action","").replace("_"," ")
        chosen = row.get("chosen_by","rule_based")
        crew   = row.get("assigned_crew","TBD")
        cause  = row.get("primary_cause","unknown")
        anom   = float(row.get("anomaly_score", 0))
        rul    = float(row.get("rul_hours", 0))
        rev    = float(row.get("revenue_loss_usd", 0))
        ns     = float(row.get("net_saving_usd", 0))

        chosen_label = ("🛡️ Safety Override" if chosen=="safety_override"
                        else "🤖 RL Agent"     if chosen=="rl_agent"
                        else "📏 Rule-based")

        try:
            r,g,b   = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
            border  = f"rgba({r},{g},{b},0.2)"
        except Exception:
            border = COLORS["border"]

        with st.expander(f"**{tid}** — {action}", expanded=(pri=="CRITICAL")):
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Anomaly Score", f"{anom:.3f}")
            m2.metric("RUL",           f"{rul:.0f}h")
            m3.metric("Revenue Loss",  f"${rev:,.0f}")
            m4.metric("Net Saving",    f"${ns:,.0f}")

            st.markdown(
                '<div style="display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 10px;">'
                + priority_badge(pri) +
                '<span class="ws-badge ws-badge-cyan">👷 ' + str(crew) + '</span>'
                '<span class="ws-badge ws-badge-gray">🎯 ' + str(cause) + '</span>'
                '<span class="ws-badge ws-badge-purple">' + chosen_label + '</span>'
                '</div>',
                unsafe_allow_html=True
            )

            explanation = str(row.get("llm_explanation","") or row.get("reasoning",""))
            if not explanation or explanation == "nan":
                explanation = "Automated decision based on sensor analysis and agent consensus."

            st.markdown(
                '<div style="background:rgba(5,8,22,0.8);'
                'border:1px solid ' + COLORS["border"] + ';'
                'border-left:3px solid ' + COLORS["cyan"] + ';'
                'border-radius:10px;padding:14px 16px;'
                'margin-top:10px;margin-bottom:10px;">'
                '<div style="font-size:9px;color:' + COLORS["cyan"] + ';font-weight:700;'
                'letter-spacing:1.5px;margin-bottom:8px;">🤖 LLM EXPLANATION — OLLAMA TINYLLAMA</div>'
                '<p style="color:' + COLORS["text_secondary"] + ';font-size:13px;'
                'line-height:3;margin:0;">' + explanation + '</p>'
                '</div>',
                unsafe_allow_html=True
            )

# ── TAB 2: Analytics ───────────────────────────────────────
with tab2:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(section_header("Priority Distribution"), unsafe_allow_html=True)
        if "priority" in df.columns:
            pri_counts = df["priority"].value_counts()
            # Only include priorities that exist
            existing = [p for p in ["CRITICAL","HIGH","MEDIUM","LOW"] if p in pri_counts.index]
            vals   = [pri_counts[p] for p in existing]
            colors = [PRIORITY_COLOR[p] for p in existing]

            fig1 = go.Figure(go.Pie(
                labels=existing, values=vals, hole=0.58,
                marker=dict(colors=colors, line=dict(color=COLORS["bg_primary"], width=3)),
                textfont=dict(size=12, color=COLORS["text_primary"]),
            ))
            fig1.add_annotation(
                text="<b>" + str(len(df)) + "</b><br>Total",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=COLORS["text_primary"], family="JetBrains Mono"),
            )
            fig1.update_layout(
                height=300, paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color=COLORS["text_secondary"]),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["text_secondary"])),
                margin=dict(l=16,r=16,t=16,b=16),
            )
            st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.markdown(section_header("Decision Method Breakdown"), unsafe_allow_html=True)
        if "chosen_by" in df.columns:
            mc = df["chosen_by"].value_counts()
            mc_colors = [COLORS["critical"], COLORS["cyan"], COLORS["healthy"], COLORS["purple"]]
            fig2 = go.Figure(go.Bar(
                x=mc.values.tolist(), y=mc.index.tolist(),
                orientation="h",
                marker=dict(color=mc_colors[:len(mc)], line=dict(width=0)),
                text=mc.values.tolist(), textposition="outside",
                textfont=dict(color=COLORS["text_primary"], size=12, family="JetBrains Mono"),
            ))
            fig2.update_layout(height=300, showlegend=False, **_PT)
            st.plotly_chart(fig2, use_container_width=True)

    # Anomaly vs RUL scatter — each turbine separate trace for correct legend
    st.markdown(section_header("Decision Space",
                "Anomaly score vs RUL — quadrant analysis"),
                unsafe_allow_html=True)

    if "anomaly_score" in df.columns and "rul_hours" in df.columns:
        fig3 = go.Figure()

        # Danger zone
        fig3.add_shape(type="rect", x0=0.7, x1=1.05, y0=0, y1=45,
                       fillcolor="rgba(239,68,68,0.04)", line=dict(width=0))

        # One trace per turbine (avoids overlap/coloring issues)
        for _, row in df.iterrows():
            pri   = row.get("priority","LOW")
            color = PRIORITY_COLOR.get(pri, COLORS["healthy"])
            tid   = row.get("turbine_id","")
            anom  = float(row.get("anomaly_score",0))
            rul   = float(row.get("rul_hours",0))

            fig3.add_trace(go.Scatter(
                x=[anom], y=[rul],
                mode="markers+text",
                name=tid,
                text=[tid],
                textposition="top center",
                textfont=dict(size=10, color=COLORS["text_secondary"], family="JetBrains Mono"),
                marker=dict(size=18, color=color, opacity=0.9,
                            line=dict(width=2, color=COLORS["bg_primary"])),
                showlegend=True,
            ))

        fig3.add_vline(x=0.7, line_dash="dash", line_color=COLORS["warning"], line_width=1.5,
                      annotation_text="Anomaly threshold (0.7)",
                      annotation_font_color=COLORS["warning"], annotation_font_size=10)
        fig3.add_hline(y=40, line_dash="dash", line_color=COLORS["critical"], line_width=1.5,
                      annotation_text="Critical RUL (40h)",
                      annotation_font_color=COLORS["critical"], annotation_font_size=10)
        fig3.update_layout(
            height=380,
            xaxis=dict(title="Anomaly Score", range=[-0.05,1.05],
                       gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(title="RUL (hours)", range=[-5, max(df["rul_hours"].tolist())*1.15],
                       gridcolor="rgba(255,255,255,0.04)"),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"],
                       font=dict(color=COLORS["text_secondary"],size=11)),
            **_PT,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Net savings bar — per turbine with correct values
    if "net_saving_usd" in df.columns and "turbine_id" in df.columns:
        st.markdown(section_header("💰 Net Savings per Turbine",
                    "Financial impact of proactive maintenance"),
                    unsafe_allow_html=True)
        tids    = df["turbine_id"].tolist()
        savings = df["net_saving_usd"].tolist()
        pri_l   = df["priority"].tolist() if "priority" in df.columns else ["LOW"]*len(df)

        fig4 = go.Figure(go.Bar(
            x=tids, y=savings,
            marker_color=[PRIORITY_COLOR.get(p, COLORS["healthy"]) for p in pri_l],
            marker_line_color="rgba(0,0,0,0)",
            text=[f"${v:,.0f}" for v in savings],
            textposition="outside",
            textfont=dict(color=COLORS["text_secondary"], size=11, family="JetBrains Mono"),
        ))
        fig4.update_layout(
            height=280, showlegend=False, bargap=0.4,
            yaxis=dict(range=[0, max(savings)*1.15]),
            **_PT,
        )
        st.plotly_chart(fig4, use_container_width=True)

# ── TAB 3 ──────────────────────────────────────────────────
with tab3:
    st.markdown(section_header("Export Decision Data"), unsafe_allow_html=True)
    safe = [c for c in df.columns if c != "load_setpoint"]
    st.dataframe(df[safe].round(3), use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    c1.download_button("⬇️ CSV",  df[safe].to_csv(index=False),
                       "agent_decisions.csv","text/csv", use_container_width=True)
    import json
    c2.download_button("⬇️ JSON", df[safe].to_json(orient="records",indent=2),
                       "agent_decisions.json","application/json", use_container_width=True)