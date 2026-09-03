# dashboard/ui/sidebar.py
"""WindSense-AI — Elite NeoGrid Sidebar"""

import streamlit as st
import base64
from dashboard.ui.theme import COLORS

def _logo_b64(path="assets/logo.png") -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

NAV_SECTIONS = {
    "OVERVIEW": [
        ("🖥️",  "Command Center",      "Home"),
    ],
    "MONITORING": [
        ("📡",  "Health Monitor",      "Asset Health"),
        ("⏳",  "Failure Predictor",   "RUL Monitor"),
    ],
    "OPERATIONS": [
        ("🗓️",  "Maintenance Planner", "Maintenance Calendar"),
        ("🧠",  "AI Decision Log",     "Agent Decisions"),
        ("📝",  "Work Orders",         "Work Orders"),
    ],
    "ANALYTICS": [
        ("⚡",  "Power Forecast",      "Energy Forecast"),
        ("🤖",  "RAG Assistant",       "RAG Chat"),
        ("🔬",  "Explainability",      "XAI Viewer"),
        ("🕸️",  "Root Cause Analysis", "Causal RCA"),
    ],
    "MLOPS": [
        ("📈",  "Model Monitor",       "Drift Monitor"),
    ],
}
_SECTION_ACCENT = {
    "OVERVIEW":    COLORS["cyan"],
    "MONITORING":  COLORS["healthy"],
    "OPERATIONS":  COLORS["warning"],
    "ANALYTICS":   COLORS["purple"],
    "MLOPS":       COLORS["orange"],
}

_SERVICES = [
    ("MQTT Broker", COLORS["healthy"], "ONLINE"),
    ("InfluxDB",    COLORS["healthy"], "ONLINE"),
    ("LangGraph",   COLORS["purple"],  "ACTIVE"),
    ("Ollama LLM",  COLORS["cyan"],    "RUNNING"),
    ("FAISS RAG",   COLORS["cyan"],    "INDEXED"),
]


def render_sidebar():
    # Initialize session state FIRST — before any access
    if "page" not in st.session_state:
        st.session_state.page = "Home"

    _LOGO = _logo_b64()

    with st.sidebar:

        # Logo
        if _LOGO:
            st.markdown(
                '<div style="display:flex;justify-content:center;'
                'align-items:center;padding:20px 16px 10px;">'
                '<img src="data:image/png;base64,' + _LOGO + '" '
                'style="width:150px;filter:drop-shadow(0 0 14px rgba(0,212,255,0.25));"></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="padding:20px 16px 10px;text-align:center;">'
                '<div style="font-size:17px;font-weight:800;'
                "font-family:'Space Grotesk',sans-serif;"
                'background:linear-gradient(135deg,#00D4FF,#8B5CF6);'
                '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
                'WindSense-AI</div>'
                '<div style="font-size:9px;color:' + COLORS["text_muted"] + ';">'
                'NEOGRID COMMAND</div>'
                '</div>',
                unsafe_allow_html=True
            )

        # Divider
        st.markdown(
            '<div style="height:1px;background:linear-gradient(to right,transparent,'
            + COLORS["border"] + ',transparent);margin:4px 16px 14px;"></div>',
            unsafe_allow_html=True
        )

        # System Status
        rows_html = "".join([
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;">'
            '<span style="font-size:11px;color:' + COLORS["text_secondary"] + ';font-weight:500;">' + svc + '</span>'
            '<span style="display:flex;align-items:center;gap:6px;">'
            '<span style="width:6px;height:6px;border-radius:50%;background:' + col + ';'
            'box-shadow:0 0 6px ' + col + ';display:inline-block;"></span>'
            '<span style="font-size:10px;color:' + col + ';font-weight:700;letter-spacing:0.5px;">' + lbl + '</span>'
            '</span></div>'
            for svc, col, lbl in _SERVICES
        ])
        st.markdown(
            '<div style="margin:0 8px 14px;padding:12px 14px;'
            'background:rgba(5,8,22,0.7);border:1px solid ' + COLORS["border"] + ';'
            'border-radius:12px;backdrop-filter:blur(8px);">'
            '<div style="font-size:9px;color:' + COLORS["text_muted"] + ';font-weight:700;'
            'letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;">SYSTEM STATUS</div>'
            + rows_html +
            '</div>',
            unsafe_allow_html=True
        )

        # Navigation
        for section, pages in NAV_SECTIONS.items():
            accent = _SECTION_ACCENT.get(section, COLORS["cyan"])
            st.markdown(
                '<div style="font-size:9px;font-weight:700;color:' + COLORS["text_muted"] + ';'
                'letter-spacing:2px;padding:10px 16px 5px;text-transform:uppercase;'
                'display:flex;align-items:center;gap:6px;">'
                '<span style="display:inline-block;width:16px;height:1px;'
                'background:' + accent + ';opacity:0.6;"></span>' + section + '</div>',
                unsafe_allow_html=True
            )

            for icon, label, target in pages:
                if st.button(
                    f"{icon}  {label}",
                    key=f"nav_{target}",
                    use_container_width=True,
                ):
                    st.session_state.page = target
                    st.rerun()

        # External tools
        st.markdown(
            '<div style="height:1px;background:linear-gradient(to right,transparent,'
            + COLORS["border"] + ',transparent);margin:14px 16px 10px;"></div>'
            '<div style="font-size:9px;font-weight:700;color:' + COLORS["text_muted"] + ';'
            'letter-spacing:2px;padding:0 16px 8px;text-transform:uppercase;">EXTERNAL TOOLS</div>',
            unsafe_allow_html=True
        )
        c1, c2 = st.columns(2)
        c1.link_button("Grafana",  "http://localhost:3000", use_container_width=True)
        c2.link_button("MLflow", "http://127.0.0.1:5001", use_container_width=True)
        st.link_button("InfluxDB", "http://localhost:8086", use_container_width=True)

        # Footer
        st.markdown(
            '<div style="margin-top:18px;padding:10px 16px;text-align:center;'
            'border-top:1px solid rgba(255,255,255,0.04);">'
            '<div style="font-size:10px;color:' + COLORS["text_muted"] + ';'
            'letter-spacing:1px;line-height:1.9;font-weight:500;">'
            'WindSense-AI <br>'
            '<span style="font-size:9px;opacity:0.7;">Predictive Wind Intelligence</span>'
            '</div></div>',
            unsafe_allow_html=True
        )