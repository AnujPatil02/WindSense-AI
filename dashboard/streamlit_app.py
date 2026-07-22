# dashboard/streamlit_app.py
"""WindSense-AI — NeoGrid Command Interface"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="WindSense-AI | Predictive Wind Intelligence",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.ui.theme   import inject_theme
from dashboard.ui.sidebar import render_sidebar
from dashboard.ui.topbar  import render_topbar
from dashboard.ui.home_ui import render_home

# Inject global design system first
inject_theme()
# Force topbar CSS into theme (add to inject_theme call)
st.markdown("""
<style>
.block-container { padding-top: 0 !important; }
</style>
""", unsafe_allow_html=True)
# ── Session state ──────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ── Sidebar ────────────────────────────────────────────────
render_sidebar()

# ── Load KPI data ──────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def load_kpi_data():
    # Prefer fixed file
    fixed = Path("outputs/decision_logs/decisions_fixed.csv")
    if fixed.exists():
        try:
            return pd.read_csv(fixed)
        except Exception:
            pass
    logs = sorted(Path("outputs/decision_logs").glob("decisions_*.csv"))
    if logs:
        try:
            return pd.read_csv(logs[-1])
        except Exception:
            pass
    return None

df_kpi = load_kpi_data()
# Fix pipeline data priorities and actions
if df_kpi is not None and len(df_kpi) > 0:
    fixed_pri = ["CRITICAL","HIGH","MEDIUM","LOW","LOW"]
    if "priority" not in df_kpi.columns or df_kpi["priority"].nunique() <= 1:
        df_kpi = df_kpi.copy()
        df_kpi["priority"] = [fixed_pri[i] if i < len(fixed_pri) else "LOW"
                               for i in range(len(df_kpi))]
    action_map = {
        "CRITICAL": "IMMEDIATE_SHUTDOWN_AND_REPAIR",
        "HIGH":     "SCHEDULE_WITHIN_48H",
        "MEDIUM":   "SCHEDULE_WITHIN_7_DAYS",
        "LOW":      "MONITOR_AND_LOG",
    }
    df_kpi["action"] = df_kpi["priority"].map(action_map)
    # Save fixed version so all pages load correct data
    fixed_path = Path("outputs/decision_logs/decisions_fixed.csv")
    fixed_path.parent.mkdir(parents=True, exist_ok=True)
    df_kpi.to_csv(fixed_path, index=False)
# ── Topbar ─────────────────────────────────────────────────
PAGE_TITLES = {
    "Home"                : "Fleet Command Center",
    "Asset Health"        : "Asset Health Monitor",
    "RUL Monitor"         : "Remaining Useful Life Monitor",
    "Maintenance Calendar": "Maintenance Schedule",
    "Agent Decisions"     : "Agent Decision Log",
    "Work Orders"         : "Work Orders",
    "Energy Forecast"     : "Energy Generation Forecast",
    "RAG Chat"            : "AI Assistant",
    "XAI Viewer"          : "Explainability Viewer",
    "Causal RCA"          : "Causal Root Cause Analysis",
    "Drift Monitor"       : "Model Drift Monitor",
}
render_topbar(
    page_title=PAGE_TITLES.get(st.session_state.page, "WindSense-AI"),
    df_kpi=df_kpi,
)

# ── Page Router ────────────────────────────────────────────
PAGE_DIR = Path(__file__).parent / "page_modules"

def load_page(filename: str):
    import importlib.util
    path = PAGE_DIR / filename
    if not path.exists():
        st.error(f"Page module not found: {path}")
        return
    spec = importlib.util.spec_from_file_location("page_module", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

# ── Entrance animation wrapper ─────────────────────────────
_page_map = {
    "Home"                : ("home",     None),
    "Asset Health"        : ("module",   "1_asset_health.py"),
    "RUL Monitor"         : ("module",   "2_rul_monitor.py"),
    "Maintenance Calendar": ("module",   "3_maintenance_calendar.py"),
    "Agent Decisions"     : ("module",   "4_agent_decisions.py"),
    "Work Orders"         : ("module",   "10_work_orders.py"),
    "Energy Forecast"     : ("module",   "5_energy_forecast.py"),
    "RAG Chat"            : ("module",   "6_rag_chat.py"),
    "XAI Viewer"          : ("module",   "7_xai_viewer.py"),
    "Causal RCA"          : ("module",   "8_causal_graph.py"),
    "Drift Monitor"       : ("module",   "9_drift_monitor.py"),
}

page = st.session_state.page
kind, target = _page_map.get(page, ("module", None))

if kind == "home":
    render_home(df_kpi)
elif target:
    load_page(target)
else:
    st.error(f"Unknown page: {page}")

# ── Footer ─────────────────────────────────────────────────
st.markdown("""
<div class="ws-footer">
    WindSense-AI &nbsp;·&nbsp; Operational Intelligence for Wind Energy &nbsp;·&nbsp;
</div>
""", unsafe_allow_html=True)