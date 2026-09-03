# dashboard/ui/topbar.py
"""WindSense-AI — Elite Topbar with live IST clock"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timezone, timedelta
from dashboard.ui.theme import COLORS
import base64

IST = timezone(timedelta(hours=5, minutes=30))

def _logo_b64(path="assets/logo1.png") -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

_LOGO1 = _logo_b64()


def render_topbar(page_title: str = "Fleet Command Center", df_kpi=None, latency: str = "24ms"):

    if df_kpi is not None and len(df_kpi) > 0:
        n_turbines = len(df_kpi)
        n_anomalies = int(df_kpi["anomaly_flag"].sum()) if "anomaly_flag" in df_kpi.columns else 0
        min_rul = float(df_kpi["rul_hours"].min()) if "rul_hours" in df_kpi.columns else 0
        n_critical = int(len(df_kpi[df_kpi["priority"] == "CRITICAL"])) if "priority" in df_kpi.columns else 0

        # Fleet health — use health_score if valid, else derive from priority mix
        if "health_score" in df_kpi.columns and df_kpi["health_score"].sum() > 0:
            fleet_health = float(df_kpi["health_score"].mean() * 100)
        elif "priority" in df_kpi.columns:
            # Derive health from priority distribution as fallback
            pri_health_map = {"CRITICAL": 0.30, "HIGH": 0.55, "MEDIUM": 0.72, "LOW": 0.90}
            fleet_health = float(df_kpi["priority"].map(pri_health_map).fillna(0.85).mean() * 100)
        else:
            fleet_health = 85.0
    else:
        n_turbines = 5; n_anomalies = 0; min_rul = 0; n_critical = 0; fleet_health = 85.0

    alert_color  = COLORS["critical"] if n_critical > 0 else COLORS["healthy"]
    rul_color    = COLORS["critical"] if min_rul < 20 else COLORS["warning"] if min_rul < 50 else COLORS["healthy"]
    health_color = COLORS["critical"] if fleet_health < 50 else COLORS["warning"] if fleet_health < 75 else COLORS["healthy"]

    def chip(label, value, vc, dot_c):
        return (
            '<div style="display:flex;flex-direction:column;align-items:center;'
            'justify-content:center;gap:3px;width:88px;height:64px;'
            'background:rgba(255,255,255,0.03);'
            'border:1px solid ' + COLORS["border"] + ';border-radius:12px;'
            'box-sizing:border-box;flex-shrink:0;flex-grow:0;">'
            '<span style="font-size:9px;color:' + COLORS["text_muted"] + ';'
            'letter-spacing:1.2px;text-transform:uppercase;font-weight:700;'
            'white-space:nowrap;text-align:center;">' + label + '</span>'
            '<span style="font-size:16px;font-weight:800;color:' + vc + ';'
            "font-family:'JetBrains Mono',monospace;line-height:1;white-space:nowrap;\">"
            + value + '</span>'
            '<span style="width:5px;height:5px;border-radius:50%;background:' + dot_c + ';'
            'box-shadow:0 0 6px ' + dot_c + ';display:inline-block;flex-shrink:0;"></span>'
            '</div>'
        )

    chips_html = (
        chip("TURBINES",   str(n_turbines)+"/5",    COLORS["cyan"],   COLORS["healthy"]) +
        chip("FLEET HLTH", f"{fleet_health:.0f}%",  health_color,     health_color) +
        chip("ALERTS",     str(n_anomalies),         alert_color,      alert_color) +
        chip("MIN RUL",    f"{min_rul:.0f}h",        rul_color,        rul_color) +
        chip("AGENTS",     "4/4",                    COLORS["purple"], COLORS["purple"])
    )

    logo_src  = ("data:image/png;base64," + _LOGO1) if _LOGO1 else ""
    logo_html = (
        '<img src="' + logo_src + '" style="width:50px;height:50px;object-fit:contain;'
        'filter:drop-shadow(0 0 12px rgba(0,212,255,0.5));">'
    )

    now_ist = datetime.now(IST).strftime("%d %b %Y · %H:%M:%S IST")

    topbar_html = (
        '<div style="position:relative;top:auto;z-index:1;'
        'background:linear-gradient(180deg,rgba(5,8,22,0.99),rgba(11,17,32,0.97));'
        'border-bottom:1px solid ' + COLORS["border"] + ';'
        'backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);'
        'padding:14px 28px;margin:0 0 1.6rem 0;border-radius:12px;'
        'display:flex;align-items:center;justify-content:space-between;'
        'box-shadow:0 6px 40px rgba(0,0,0,0.5);'
        'min-height:80px;box-sizing:border-box;">'

        '<div style="display:flex;align-items:center;gap:16px;">'
        + logo_html +
        '<div>'
        '<div style="font-size:17px;font-weight:800;'
        "font-family:'Space Grotesk',sans-serif;"
        'background:linear-gradient(135deg,#00D4FF,#8B5CF6);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1;">'
        'WindSense-AI</div>'
        '<div style="font-size:10px;color:' + COLORS["text_muted"] + ';'
        'letter-spacing:2.5px;font-weight:600;margin-top:2px;">Predictive Wind Intelligence</div>'
        '</div>'
        '<div style="width:1px;height:36px;background:rgba(255,255,255,0.07);"></div>'
        '<span style="display:inline-flex;align-items:center;gap:6px;'
        'background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.22);'
        'border-radius:20px;padding:5px 12px;white-space:nowrap;">'
        '<span style="width:7px;height:7px;border-radius:50%;background:' + COLORS["healthy"] + ';'
        'box-shadow:0 0 7px ' + COLORS["healthy"] + ';display:inline-block;"></span>'
        '<span style="font-size:10px;font-weight:700;color:' + COLORS["healthy"] + ';'
        'letter-spacing:1.2px;">LIVE</span></span>'
        '<span style="display:inline-flex;align-items:center;gap:6px;'
        'background:rgba(139,92,246,0.08);border:1px solid rgba(139,92,246,0.22);'
        'border-radius:20px;padding:5px 12px;white-space:nowrap;">'
        '<span style="width:7px;height:7px;border-radius:50%;background:' + COLORS["purple"] + ';'
        'box-shadow:0 0 7px ' + COLORS["purple"] + ';display:inline-block;"></span>'
        '<span style="font-size:10px;font-weight:700;color:' + COLORS["purple"] + ';'
        'letter-spacing:1.2px;">AI ACTIVE</span></span>'
        '<div style="width:1px;height:36px;background:rgba(255,255,255,0.07);"></div>'
        '<div>'
        '<div style="color:' + COLORS["text_primary"] + ';font-size:15px;font-weight:700;'
        'letter-spacing:-0.3px;">' + page_title + '</div>'
        '<div style="font-size:10px;color:' + COLORS["text_muted"] + ';margin-top:2px;">'
        'Predictive Wind Intelligence</div>'
        '</div></div>'

        '<div style="display:flex;align-items:center;gap:8px;">'
        + chips_html +
        '</div>'

        '<div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;margin-left:24px;">'
        '<span id="ws-ist-clock" style="font-size:13px;font-weight:700;'
        'color:' + COLORS["text_secondary"] + ';'
        "font-family:'JetBrains Mono',monospace;white-space:nowrap;\">"
        + now_ist + '</span>'
        '<span style="font-size:10px;color:' + COLORS["text_muted"] + ';letter-spacing:1px;">'
        'LATENCY · ' + latency + '</span>'
        '</div>'
        '</div>'
    )

    st.markdown(topbar_html, unsafe_allow_html=True)

    components.html(
        """
        <script>
        function wsTickClock() {
            var now = new Date();
            var istOffset = (5 * 60 + 30) * 60000;
            var ist = new Date(now.getTime() + istOffset);
            var months = ["Jan","Feb","Mar","Apr","May","Jun",
                          "Jul","Aug","Sep","Oct","Nov","Dec"];
            var d  = String(ist.getUTCDate()).padStart(2,"0");
            var mo = months[ist.getUTCMonth()];
            var y  = ist.getUTCFullYear();
            var h  = String(ist.getUTCHours()).padStart(2,"0");
            var mi = String(ist.getUTCMinutes()).padStart(2,"0");
            var s  = String(ist.getUTCSeconds()).padStart(2,"0");
            var txt = d + " " + mo + " " + y + " · " + h + ":" + mi + ":" + s + " IST";
            var el = window.parent.document.getElementById("ws-ist-clock");
            if (el) el.textContent = txt;
        }
        wsTickClock();
        if (!window._wsClockStarted) {
            window._wsClockStarted = true;
            setInterval(wsTickClock, 1000);
        }
        </script>
        """,
        height=0,
        scrolling=False,
    )