# dashboard/ui/components.py
"""WindSense-AI — Elite Reusable UI Components"""

from dashboard.ui.theme import COLORS, PRIORITY_COLORS


def kpi_card(label: str, value: str, delta: str = "",
             delta_type: str = "neutral", icon: str = "",
             accent: str = None) -> str:
    color     = accent or COLORS["cyan"]
    # derive glow rgba from accent
    glow      = f"rgba({','.join(str(int(color.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.12)" \
                if color.startswith("#") else "rgba(0,212,255,0.12)"
    d_cls     = f"ws-delta-{delta_type}"
    delta_html = f'<span class="ws-kpi-delta {d_cls}">{delta}</span>' if delta else ""
    icon_html  = f'<div class="ws-kpi-icon">{icon}</div>' if icon else ""
    return f"""
    <div class="ws-kpi-card ws-stagger-1"
         style="--accent:{color};--accent-glow:{glow};">
        {icon_html}
        <div class="ws-kpi-label">{label}</div>
        <div class="ws-kpi-value">{value}</div>
        {delta_html}
    </div>"""


def section_header(title: str, subtitle: str = "") -> str:
    sub = (f'<div style="font-size:12px;color:{COLORS["text_muted"]};'
           f'font-weight:400;margin-top:2px;">{subtitle}</div>') if subtitle else ""
    return f'<div class="ws-section-header">{title}{sub}</div>'


def glass_panel(content: str, padding: str = "20px") -> str:
    return f'<div class="ws-panel" style="padding:{padding};">{content}</div>'


def status_badge(text: str, level: str = "gray") -> str:
    dot_map = {
        "critical": "●", "high": "●", "medium": "●",
        "low": "●", "cyan": "●", "purple": "●", "gray": "●",
    }
    dot = dot_map.get(level.lower(), "●")
    return f'<span class="ws-badge ws-badge-{level.lower()}">{dot} {text}</span>'


def priority_badge(priority: str) -> str:
    level_map = {"CRITICAL":"critical","HIGH":"high","MEDIUM":"medium","LOW":"low"}
    return status_badge(priority, level_map.get(priority, "gray"))


def turbine_card(turbine_id: str, health_pct: int, priority: str,
                 rul_hours: float, power_kw: float) -> str:
    color = PRIORITY_COLORS.get(priority, COLORS["healthy"])
    pct   = max(0, min(100, health_pct))
    badge = priority_badge(priority)
    try:
        r,g,b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
        glow  = f"rgba({r},{g},{b},0.12)"
    except Exception:
        glow = "rgba(0,212,255,0.12)"
    return f"""
    <div class="ws-kpi-card"
         style="--accent:{color};--accent-glow:{glow};padding:16px;min-height:auto;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span style="font-size:14px;font-weight:800;color:{COLORS['text_primary']};
                         font-family:'Space Grotesk',sans-serif;">{turbine_id}</span>
            {badge}
        </div>
        <div style="font-size:32px;font-weight:800;color:{color};
                    font-family:'Space Grotesk',sans-serif;line-height:1;
                    letter-spacing:-1px;">{pct}%</div>
        <div style="margin:10px 0 8px;height:4px;background:rgba(255,255,255,0.06);
                    border-radius:999px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:{color};
                        border-radius:999px;
                        box-shadow:0 0 8px {color};
                        transition:width 0.6s cubic-bezier(0.22,1,0.36,1);"></div>
        </div>
        <div style="display:flex;justify-content:space-between;
                    font-size:11px;color:{COLORS['text_muted']};">
            <span>RUL <span style="color:{COLORS['text_secondary']};
                font-family:'JetBrains Mono',monospace;font-weight:700;">{rul_hours:.0f}h</span></span>
            <span><span style="color:{COLORS['text_secondary']};
                font-family:'JetBrains Mono',monospace;font-weight:700;">{power_kw:.0f}</span> kW</span>
        </div>
    </div>"""


def alert_banner(message: str, detail: str = "", level: str = "critical") -> str:
    icons  = {"critical":"🚨","warning":"⚠️","info":"ℹ️"}
    icon   = icons.get(level, "⚠️")
    cls    = f"ws-alert-{level}"
    color  = {"critical":COLORS["critical"],"warning":COLORS["warning"],
               "info":COLORS["cyan"]}.get(level, COLORS["warning"])
    detail_html = (f'<div style="font-size:12px;color:{COLORS["text_secondary"]};'
                   f'margin-top:3px;">{detail}</div>') if detail else ""
    return f"""
    <div class="{cls}">
        <span style="font-size:20px;line-height:1;">{icon}</span>
        <div>
            <div style="font-size:13px;font-weight:700;color:{color};">{message}</div>
            {detail_html}
        </div>
    </div>"""


def styled_table(headers: list, rows: list) -> str:
    th_html   = "".join(f"<th>{h}</th>" for h in headers)
    rows_html = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f"""
    <div style="background:rgba(13,20,36,0.9);border:1px solid {COLORS['border']};
                border-radius:14px;overflow:hidden;
                box-shadow:0 4px 20px rgba(0,0,0,0.25);">
        <table class="ws-table">
            <thead><tr>{th_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>"""


def metric_row(label: str, value: str, value_color: str = None, unit: str = "") -> str:
    vc       = value_color or COLORS["text_primary"]
    unit_html = (f' <span style="color:{COLORS["text_muted"]};font-size:11px;">'
                 f'{unit}</span>') if unit else ""
    return f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:10px 14px;background:rgba(5,8,22,0.6);
                border:1px solid {COLORS['border']};
                border-radius:10px;margin-bottom:6px;
                transition:background 0.15s ease;">
        <span style="color:{COLORS['text_secondary']};font-size:13px;">{label}</span>
        <span style="color:{vc};font-weight:700;
                     font-family:'JetBrains Mono',monospace;font-size:13px;">
            {value}{unit_html}
        </span>
    </div>"""


def financial_card(rows: list) -> str:
    content = "".join(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:10px 14px;background:rgba(5,8,22,0.5);
                border-radius:8px;margin-bottom:6px;">
        <span style="color:{COLORS['text_secondary']};font-size:13px;">{label}</span>
        <span style="color:{color};font-weight:700;
                     font-family:'JetBrains Mono',monospace;">{value}</span>
    </div>""" for label, value, color in rows)
    return f"""
    <div style="background:rgba(13,20,36,0.9);border:1px solid {COLORS['border']};
                border-radius:14px;padding:16px;
                box-shadow:0 4px 20px rgba(0,0,0,0.25);">{content}</div>"""


def pulse_indicator(color: str = None, size: int = 8) -> str:
    c = color or COLORS["healthy"]
    return (
        f'<span style="position:relative;display:inline-flex;'
        f'align-items:center;justify-content:center;'
        f'width:{size+8}px;height:{size+8}px;">'
        f'<span style="position:absolute;width:{size+6}px;height:{size+6}px;'
        f'border-radius:50%;background:{c};opacity:0.2;'
        f'animation:wsPulseRing 2s infinite;"></span>'
        f'<span style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:{c};box-shadow:0 0 6px {c};display:inline-block;'
        f'z-index:1;"></span></span>'
    )


def live_indicator(label: str = "LIVE") -> str:
    return f"""
    <span style="display:inline-flex;align-items:center;gap:6px;
                 background:rgba(16,185,129,0.08);
                 border:1px solid rgba(16,185,129,0.22);
                 border-radius:20px;padding:3px 10px;">
        {pulse_indicator(COLORS['healthy'], 6)}
        <span style="font-size:10px;font-weight:700;
                     color:{COLORS['healthy']};letter-spacing:1.2px;">{label}</span>
    </span>"""


def agent_card(agent_id: str, role: str, model: str,
               color: str, perf: str) -> str:
    return f"""
    <div style="display:flex;align-items:center;gap:10px;
                padding:12px 14px;margin-bottom:6px;
                background:rgba(13,20,36,0.85);
                border:1px solid {COLORS['border']};
                border-left:3px solid {color};
                border-radius:12px;
                transition:all 0.2s cubic-bezier(0.22,1,0.36,1);">
        <div style="flex:1;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:13px;font-weight:700;
                             color:{COLORS['text_primary']};
                             font-family:'Space Grotesk',sans-serif;">{agent_id}</span>
                <span style="font-size:10px;color:{color};
                             font-family:'JetBrains Mono',monospace;
                             font-weight:700;">{perf}</span>
            </div>
            <div style="font-size:12px;font-weight:600;
                        color:{COLORS['text_secondary']};margin:3px 0 2px;">{role}</div>
            <div style="font-size:10px;color:{COLORS['text_muted']};
                        letter-spacing:0.3px;">{model}</div>
        </div>
        {pulse_indicator(color, 8)}
    </div>"""


def nav_button(icon: str, label: str, is_active: bool = False) -> str:
    if is_active:
        style = (f"background:rgba(0,212,255,0.08);color:{COLORS['cyan']};"
                 f"border-left:3px solid {COLORS['cyan']};")
    else:
        style = f"color:{COLORS['text_muted']};border-left:3px solid transparent;"
    return f"""
    <div style="{style}display:flex;align-items:center;gap:10px;
                padding:9px 14px;margin:1px 0;cursor:pointer;
                border-radius:0 8px 8px 0;font-size:13px;font-weight:500;
                transition:all 0.18s cubic-bezier(0.22,1,0.36,1);">
        <span style="font-size:15px;">{icon}</span>
        <span>{label}</span>
    </div>"""