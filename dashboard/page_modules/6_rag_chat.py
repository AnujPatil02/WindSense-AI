# dashboard/page_modules/6_rag_chat.py
"""WindSense AI Assistant — Elite Chat UI"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
import ollama
import numpy as np
from dashboard.ui.theme import COLORS
from dashboard.ui.components import section_header
from dashboard.utils.data_loader import load_decisions

MODEL = "tinyllama"

# ── Fleet data (loaded once) ───────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def _fleet_df():
    return load_decisions()

@st.cache_data(ttl=60, show_spinner=False)
def _fleet_context() -> str:
    try:
        df = _fleet_df()
        lines = [
            "You are WindSense-AI Assistant for a 5-turbine 2MW onshore wind farm.",
            "EXACT fleet data:",
        ]
        for _, r in df.iterrows():
            lines.append(
                f"{r['turbine_id']}: priority={r['priority']}, "
                f"RUL={float(r['rul_hours']):.0f}h, "
                f"health={float(r['health_score'])*100:.0f}%, "
                f"anomaly={float(r['anomaly_score']):.3f}, "
                f"action={r['action']}, "
                f"net_saving=${float(r['net_saving_usd']):,.0f}"
            )
        lines += [
            "Each turbine: rated 2000 kW (2 MW). Power curve: 0 kW below 3 m/s, "
            "2000×((v-3)/9)^2.6 for 3-12 m/s, 2000 kW above 12 m/s.",
            "Revenue: $0.075/kWh. Failure cost: $50,000/turbine.",
            "CRITICAL threshold: RUL<40h. HIGH: RUL 40-80h. MEDIUM: 80-100h. LOW: >100h.",
            "Answer ONLY using the data above. Never invent values.",
        ]
        return " ".join(lines)
    except Exception:
        return "WindSense fleet: 5 × 2MW wind turbines WT-001 to WT-005."

# Keywords that mean we should answer from data directly (bypass LLM)
DATA_KEYWORDS = [
    "wt-001","wt-002","wt-003","wt-004","wt-005",
    "power generation","total power","kwh","mwh","how much power",
    "revenue","saving","cost","financial","dollar","$",
    "rul of","health of","status of","priority of","anomaly of",
    "fleet status","all turbine","which turbine","fleet health",
    "schedule","maintenance window","crew","work order",
]

def _is_data_question(q: str) -> bool:
    q_low = q.lower()
    return any(k in q_low for k in DATA_KEYWORDS)


def _data_answer(q: str) -> str:
    """Answer data-specific questions directly from fleet data — no LLM."""
    q_low = q.lower()
    df = _fleet_df()

    # Power generation for specific turbine
    turbine_mentioned = None
    for tid in ["wt-001","wt-002","wt-003","wt-004","wt-005"]:
        if tid in q_low:
            turbine_mentioned = tid.upper()
            break

    if turbine_mentioned and any(w in q_low for w in
                                  ["power","kwh","mwh","generate","generation"]):
        row = df[df["turbine_id"]==turbine_mentioned].iloc[0]
        hs   = float(row["health_score"])
        pri  = row["priority"]
        rul  = float(row["rul_hours"])
        anom = float(row["anomaly_score"])

        # Parse hours from question
        hours = 10
        import re
        m = re.search(r'(\d+)\s*h', q_low)
        if m: hours = int(m.group(1))
        elif "peak" in q_low: hours = 1
        elif "72" in q_low: hours = 72
        elif "24" in q_low: hours = 24
        elif "48" in q_low: hours = 48

        # Power calc — CRITICAL = 0 (shutdown), others derated by health
        if pri == "CRITICAL":
            avg_power = 0
            note = "⚠️ WT is under EMERGENCY SHUTDOWN — zero power output."
        else:
            # Assume avg wind ~9 m/s → P = 2000×((9-3)/9)^2.6 ≈ 1,127 kW
            base_power = 2000 * ((9-3)/9)**2.6
            avg_power  = base_power * hs  # derate by health score
            note = f"Derated by health score ({hs*100:.0f}%)."

        total_kwh = avg_power * hours
        total_mwh = total_kwh / 1000
        revenue   = total_kwh * 0.075

        return (
            f"**{turbine_mentioned} Power Generation ({hours}h):**\n\n"
            f"| Parameter | Value |\n|---|---|\n"
            f"| Rated Capacity | 2,000 kW (2 MW) |\n"
            f"| Priority | {pri} |\n"
            f"| Health Score | {hs*100:.0f}% |\n"
            f"| RUL | {rul:.0f}h |\n"
            f"| Anomaly Score | {anom:.3f} |\n"
            f"| Avg Power (derated) | **{avg_power:.0f} kW** |\n"
            f"| Total over {hours}h | **{total_kwh:.0f} kWh ({total_mwh:.2f} MWh)** |\n"
            f"| Revenue @ $0.075/kWh | **${revenue:,.0f}** |\n\n"
            f"*{note}*"
        )

    # Multi-turbine power
    if any(w in q_low for w in ["wt-001","wt-002","wt-003","wt-004","wt-005"]) and \
       any(w in q_low for w in ["power","generate","kwh","mwh"]):
        mentioned = [t.upper() for t in ["wt-001","wt-002","wt-003","wt-004","wt-005"]
                     if t in q_low]
        hours = 72
        import re
        m = re.search(r'(\d+)\s*h', q_low)
        if m: hours = int(m.group(1))
        lines = [f"**Power Generation for {', '.join(mentioned)} ({hours}h):**\n"]
        total_all = 0
        for tid in mentioned:
            row = df[df["turbine_id"]==tid].iloc[0]
            hs  = float(row["health_score"])
            pri = row["priority"]
            if pri == "CRITICAL":
                avg_p = 0
            else:
                avg_p = 2000 * ((9-3)/9)**2.6 * hs
            total = avg_p * hours
            total_all += total
            lines.append(f"- **{tid}** ({pri}, health {hs*100:.0f}%): "
                         f"{avg_p:.0f} kW avg → {total:.0f} kWh")
        lines.append(f"\n**Combined total: {total_all:.0f} kWh "
                     f"({total_all/1000:.2f} MWh) | "
                     f"Revenue: ${total_all*0.075:,.0f}**")
        return "\n".join(lines)

    # Fleet status
    if any(w in q_low for w in ["fleet status","all turbine","status","fleet health"]):
        lines = ["**Current Fleet Status:**\n",
                 "| Turbine | Priority | RUL | Health | Anomaly | Action |",
                 "|---|---|---|---|---|---|"]
        for _, r in df.iterrows():
            lines.append(
                f"| {r['turbine_id']} | {r['priority']} | {float(r['rul_hours']):.0f}h | "
                f"{float(r['health_score'])*100:.0f}% | {float(r['anomaly_score']):.3f} | "
                f"{r['action'].replace('_',' ')} |"
            )
        return "\n".join(lines)

    # Specific turbine status
    if turbine_mentioned:
        row = df[df["turbine_id"]==turbine_mentioned].iloc[0]
        return (
            f"**{turbine_mentioned} Status:**\n\n"
            f"| Field | Value |\n|---|---|\n"
            f"| Priority | **{row['priority']}** |\n"
            f"| RUL | **{float(row['rul_hours']):.0f}h** |\n"
            f"| Health Score | **{float(row['health_score'])*100:.0f}%** |\n"
            f"| Anomaly Score | **{float(row['anomaly_score']):.3f}** |\n"
            f"| Action | **{row['action'].replace('_',' ')}** |\n"
            f"| Assigned Crew | **{row.get('assigned_crew','N/A')}** |\n"
            f"| Revenue Loss | **${float(row['revenue_loss_usd']):,.0f}** |\n"
            f"| Net Saving | **${float(row['net_saving_usd']):,.0f}** |"
        )

    # Financial
    if any(w in q_low for w in ["saving","cost","revenue","financial","dollar","$"]):
        total_ns = df["net_saving_usd"].sum()
        lines = ["**Fleet Financial Summary:**\n"]
        for _, r in df.iterrows():
            lines.append(
                f"- {r['turbine_id']}: Net saving ${float(r['net_saving_usd']):,.0f} "
                f"(loss ${float(r['revenue_loss_usd']):,.0f})"
            )
        lines.append(f"\n**Total fleet net saving: ${total_ns:,.0f}**")
        lines.append("*(vs $50,000/turbine unplanned failure cost)*")
        return "\n".join(lines)

    return None  # No data match — fall through to LLM or general template


def _general_template(q: str) -> str:
    q_low = q.lower()
    if any(w in q_low for w in ["bearing","gearbox"]):
        return ("**Gearbox/Bearing Failure Causes:**\n"
                "- Lubrication failure (oil degradation)\n"
                "- Overloading during high wind events\n"
                "- Rotor imbalance increasing radial load\n"
                "- Fatigue from cyclic stress\n\n"
                "**WindSense indicators:**\n"
                "- vibration_mms > 6 mm/s → Stage 3 (critical)\n"
                "- gearbox_temp_c > 85°C → Stage 2 (high)\n"
                "- bearing_wear > 0.7 → accelerated degradation mode\n"
                "Reference: Gearbox Manual Section 3.")
    if any(w in q_low for w in ["rul","remaining useful"]):
        return ("**Remaining Useful Life (RUL):**\n"
                "Hours until predicted component failure.\n\n"
                "**WindSense models:**\n"
                "- XGBoost: RMSE ~18.4h (winner)\n"
                "- LSTM: RMSE ~21.2h\n"
                "- Conformal prediction: 90% CI\n\n"
                "Trained on NASA CMAPSS (turbofan engine degradation, 21 sensors).")
    if any(w in q_low for w in ["anomaly","score","detection"]):
        return ("**Anomaly Score (0.0 → 1.0):**\n"
                "- 0.0-0.5: Normal\n- 0.5-0.7: Monitor\n"
                "- 0.7-0.85: Schedule maintenance\n- >0.85: CRITICAL\n\n"
                "**WindSense models:**\n"
                "- Isolation Forest: F1=0.82 (winner)\n"
                "- LSTM Autoencoder: F1=0.79")
    if any(w in q_low for w in ["maintenance","schedule","window"]):
        return ("**Maintenance Scheduling (Agent 3):**\n"
                "Selects low-wind windows to minimize revenue loss.\n"
                "Best windows: 02:00-06:00 IST (historically lowest wind).\n"
                "Notifies grid operator 48h in advance for outages >4h.")
    if any(w in q_low for w in ["critical","priority"]):
        return ("**Priority Levels:**\n"
                "🔴 CRITICAL: RUL<40h → Immediate shutdown ($8,000 maintenance)\n"
                "🟠 HIGH: RUL 40-80h → Within 48h ($5,000)\n"
                "🟡 MEDIUM: RUL 80-100h → Within 7 days ($3,000)\n"
                "🟢 LOW: RUL>100h → Monitor ($1,500)")
    if any(w in q_low for w in ["lstm","autoencoder"]):
        return ("**LSTM Autoencoder:**\n"
                "Trained on normal sensor patterns.\n"
                "High reconstruction error at inference = anomaly.\n"
                "Compared vs Isolation Forest — IF won by F1 score.")
    if any(w in q_low for w in ["conformal"]):
        return ("**Conformal Prediction:**\n"
                "Wraps XGBoost RUL with statistically guaranteed 90% CI.\n"
                "Example: RUL=93h → CI [75h, 111h] for WT-001.")
    if any(w in q_low for w in ["shap","xai","explainab"]):
        return ("**SHAP Explainability:**\n"
                "Shows which sensors most influence predictions.\n\n"
                "Top features (anomaly): vibration (0.312), temp (0.278), rpm (0.201)\n"
                "Top features (RUL): bearing_wear (0.341), gearbox_temp (0.289)\n"
                "View full plots in the Explainability Viewer page.")
    if any(w in q_low for w in ["rotor","imbalance"]):
        return ("**Rotor Imbalance:**\n"
                "Signs: 1P vibration spike, asymmetric blade loading, tower oscillation.\n"
                "Threshold: rotor_imbalance > 0.3 → HIGH alert.\n"
                "Fix: blade rebalancing at next low-wind window.")
    return ("I'm WindSense-AI Assistant.\n\n"
            "Ask me about:\n"
            "- Specific turbine: *'Status of WT-002'*\n"
            "- Power: *'Power generation from WT-003 for 24h'*\n"
            "- Financials: *'Net savings for the fleet'*\n"
            "- AI models: *'Explain anomaly detection'*\n"
            "- Maintenance: *'When to schedule WT-001 repair?'*")


SUGGESTIONS = [
    "Status of WT-001?",
    "Power generation from WT-002 for 10 hours",
    "Fleet status summary",
    "What causes gearbox bearing failure?",
    "Explain anomaly score thresholds",
    "Net savings for the fleet",
    "What does CRITICAL priority mean?",
    "Power generation from WT-003 and WT-005 for 72h",
]

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_processing" not in st.session_state:
    st.session_state.chat_processing = False

# ── Header ─────────────────────────────────────────────────
st.markdown(
    '<div class="ws-stagger-1" style="margin-bottom:24px;">'
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">'
    '<h1 style="font-size:28px;font-weight:800;margin:0;'
    "font-family:'Space Grotesk',sans-serif;color:" + COLORS["text_primary"] + ';letter-spacing:-1px;">'
    '🤖 WindSense AI Assistant</h1>'
    '<span style="font-size:10px;font-weight:700;color:' + COLORS["purple"] + ';'
    'letter-spacing:2px;background:rgba(139,92,246,0.08);'
    'border:1px solid rgba(139,92,246,0.22);border-radius:20px;padding:4px 12px;">'
    'OLLAMA · TINYLLAMA</span>'
    '</div>'
    '<p style="color:' + COLORS["text_muted"] + ';font-size:13px;margin:0;">'
    'Ask about turbine status, power generation, maintenance costs, or AI models</p>'
    '</div>',
    unsafe_allow_html=True
)

# ── Ollama check ───────────────────────────────────────────
def _ollama_ok() -> bool:
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return True
    except Exception:
        return False

ollama_live = _ollama_ok()
if not ollama_live:
    st.markdown(
        '<div style="background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.2);'
        'border-radius:12px;padding:14px 16px;margin-bottom:16px;'
        'display:flex;align-items:center;gap:12px;">'
        '<span style="font-size:20px;">⚠️</span>'
        '<div>'
        '<div style="font-size:13px;font-weight:700;color:' + COLORS["warning"] + ';">'
        'Ollama not running — answering from fleet data directly</div>'
        '<div style="font-size:12px;color:' + COLORS["text_secondary"] + ';margin-top:2px;'
        "font-family:'JetBrains Mono',monospace;\">Start: ollama serve</div>"
        '</div></div>',
        unsafe_allow_html=True
    )

# ── Suggested questions ────────────────────────────────────
st.markdown(section_header("💡 Quick Questions"), unsafe_allow_html=True)
sg_cols = st.columns(4)
for i, q in enumerate(SUGGESTIONS):
    if sg_cols[i % 4].button(q, key=f"sug_{i}", use_container_width=True):
        if not st.session_state.chat_processing:
            st.session_state.chat_messages.append({"role":"user","content":q})
            st.session_state.chat_processing = True
            st.rerun()

st.markdown(
    '<div style="height:1px;background:linear-gradient(to right,transparent,'
    + COLORS["border"] + ',transparent);margin:16px 0;"></div>',
    unsafe_allow_html=True
)

# ── Chat history ───────────────────────────────────────────
for msg in st.session_state.chat_messages:
    avatar = "🧑" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Response generation ────────────────────────────────────
if (st.session_state.chat_messages
        and st.session_state.chat_messages[-1]["role"] == "user"
        and st.session_state.chat_processing):

    user_q = st.session_state.chat_messages[-1]["content"]

    with st.chat_message("assistant", avatar="🤖"):
        placeholder   = st.empty()
        full_response = ""

        # Step 1: Check if data question — answer directly, bypass LLM
        data_resp = _data_answer(user_q)
        if data_resp:
            full_response = data_resp
            placeholder.markdown(full_response)

        # Step 2: General knowledge — try Ollama, fallback to template
        elif ollama_live:
            try:
                ollama_msgs = [{"role":"system","content":_fleet_context()}]
                for m in st.session_state.chat_messages[-4:]:
                    ollama_msgs.append({"role":m["role"],"content":m["content"]})
                stream = ollama.chat(
                    model=MODEL, messages=ollama_msgs, stream=True,
                    options={"temperature":0.1,"num_predict":300,"num_ctx":2048},
                )
                for chunk in stream:
                    token = chunk["message"]["content"]
                    full_response += token
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
            except Exception:
                full_response = _general_template(user_q)
                placeholder.markdown(full_response)

        # Step 3: Offline fallback
        else:
            full_response = _general_template(user_q)
            placeholder.markdown(full_response)

    st.session_state.chat_messages.append({"role":"assistant","content":full_response})
    st.session_state.chat_processing = False
    st.rerun()

# ── Chat input ─────────────────────────────────────────────
if prompt := st.chat_input("Ask: 'Status of WT-001' or 'Power from WT-002 for 24h'..."):
    if not st.session_state.chat_processing:
        st.session_state.chat_messages.append({"role":"user","content":prompt})
        st.session_state.chat_processing = True
        st.rerun()

# ── Controls ───────────────────────────────────────────────
st.markdown(
    '<div style="height:1px;background:linear-gradient(to right,transparent,'
    + COLORS["border"] + ',transparent);margin:16px 0;"></div>',
    unsafe_allow_html=True
)
c1, c2, c3 = st.columns([1,1,4])
if c1.button("🗑️ Clear Chat", use_container_width=True):
    st.session_state.chat_messages   = []
    st.session_state.chat_processing = False
    st.rerun()
c2.markdown(
    '<div style="padding:8px;font-size:11px;color:' + COLORS["text_muted"] + ';'
    "font-family:'JetBrains Mono',monospace;\">Model: " + MODEL + '</div>',
    unsafe_allow_html=True
)