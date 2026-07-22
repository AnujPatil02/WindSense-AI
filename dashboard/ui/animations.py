# dashboard/ui/animations.py
"""WindSense-AI — Elite Animations & Dynamic Components"""

from dashboard.ui.theme import COLORS, PRIORITY_COLORS


def animated_counter(value: float, label: str,
                     suffix: str = "", color: str = None) -> str:
    c = color or COLORS["cyan"]
    return (
        '<div style="text-align:center;padding:20px;border-radius:16px;'
        'background:linear-gradient(145deg,rgba(13,20,36,0.95),rgba(5,8,22,0.90));'
        'border:1px solid rgba(255,255,255,0.06);">'
        '<div style="font-size:40px;font-weight:800;line-height:1;'
        "font-family:'JetBrains Mono',monospace;color:" + c + ';">'
        + f'{value:,.0f}' + suffix + '</div>'
        '<div style="margin-top:8px;font-size:11px;text-transform:uppercase;'
        'letter-spacing:1.6px;color:' + COLORS["text_muted"] + ';font-weight:700;">'
        + label + '</div></div>'
    )


def spinning_turbine(size: int = 60, speed: str = "3s", color: str = None) -> str:
    c  = color or COLORS["cyan"]
    bg = COLORS.get("bg_primary", "#050816")
    br = COLORS.get("border", "#1E2D45")
    return (
        '<style>@keyframes wsSpin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}'
        '@keyframes wsTurbineGlow{0%,100%{filter:drop-shadow(0 0 4px ' + c + ');}50%{filter:drop-shadow(0 0 12px ' + c + ');}}'
        '</style>'
        '<div style="display:flex;justify-content:center;align-items:center;padding:10px;">'
        '<svg width="' + str(size) + '" height="' + str(size) + '" viewBox="0 0 100 100" '
        'style="overflow:visible;animation:wsTurbineGlow 3s ease-in-out infinite;">'
        '<circle cx="50" cy="50" r="34" fill="' + c + '0D" style="filter:blur(10px);"/>'
        '<rect x="47" y="56" width="6" height="36" rx="3" fill="' + br + '"/>'
        '<ellipse cx="50" cy="52" rx="8" ry="5" fill="' + c + '"/>'
        '<g style="transform-origin:50px 52px;animation:wsSpin ' + speed + ' linear infinite;">'
        '<line x1="50" y1="52" x2="50" y2="10" stroke="' + c + '" stroke-width="4" stroke-linecap="round"/>'
        '<line x1="50" y1="52" x2="84" y2="74" stroke="' + c + '" stroke-width="4" stroke-linecap="round"/>'
        '<line x1="50" y1="52" x2="16" y2="74" stroke="' + c + '" stroke-width="4" stroke-linecap="round"/>'
        '</g>'
        '<circle cx="50" cy="52" r="5" fill="' + bg + '"/>'
        '<circle cx="50" cy="52" r="3" fill="' + c + '"/>'
        '</svg></div>'
    )


def fleet_map(turbine_data: list) -> str:
    default_positions = [(18,30),(38,22),(60,28),(80,38),(28,62),(52,68),(76,60)]

    # Connection lines between adjacent turbines
    connection_lines = ""
    for i in range(len(turbine_data) - 1):
        x1 = turbine_data[i].get("x", default_positions[i % len(default_positions)][0])
        y1 = turbine_data[i].get("y", default_positions[i % len(default_positions)][1])
        x2 = turbine_data[i+1].get("x", default_positions[(i+1) % len(default_positions)][0])
        y2 = turbine_data[i+1].get("y", default_positions[(i+1) % len(default_positions)][1])
        connection_lines += (
            f'<line x1="{x1}%" y1="{y1}%" x2="{x2}%" y2="{y2}%" '
            f'stroke="{COLORS["cyan"]}" stroke-width="0.35" '
            f'stroke-dasharray="2,3" opacity="0.28"/>'
        )

    turbine_svg = ""
    for i, t in enumerate(turbine_data):
        x        = t.get("x", default_positions[i % len(default_positions)][0])
        y        = t.get("y", default_positions[i % len(default_positions)][1])
        priority = t.get("priority", "LOW")
        color    = PRIORITY_COLORS.get(priority, COLORS["healthy"])
        tid      = t.get("id", f"WT-{i+1:03d}")
        rul      = t.get("rul_hours", 100)
        health   = t.get("health_score", 0.85)
        health_pct = health * 100
        spd      = "2s" if priority == "CRITICAL" else "4s" if priority == "HIGH" else "6s"

        ping = ""
        if priority in ["CRITICAL","HIGH"]:
            ping = (
                f'<circle cx="{x}%" cy="{y}%" r="4.5%" fill="none" '
                f'stroke="{color}" stroke-width="0.4" opacity="0.55">'
                f'<animate attributeName="r" values="3;8;3" dur="2s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.7;0;0.7" dur="2s" repeatCount="indefinite"/>'
                f'</circle>'
            )

        turbine_svg += (
            f'{ping}'
            f'<circle cx="{x}%" cy="{y}%" r="3.2%" fill="{color}18" stroke="{color}" stroke-width="1.2"/>'
            f'<g style="transform-origin:{x}% {y}%;animation:wsMiniSpin {spd} linear infinite;">'
            f'<line x1="{x}%" y1="{y}%" x2="{x}%" y2="{y-1.8}%" stroke="{color}" stroke-width="0.35"/>'
            f'<line x1="{x}%" y1="{y}%" x2="{x+1.5}%" y2="{y+1.2}%" stroke="{color}" stroke-width="0.35"/>'
            f'<line x1="{x}%" y1="{y}%" x2="{x-1.5}%" y2="{y+2}%" stroke="{color}" stroke-width="0.35"/>'
            f'</g>'
            f'<circle cx="{x}%" cy="{y}%" r="0.7%" fill="{color}"/>'
            f'<text x="{x}%" y="{y+7.8}%" text-anchor="middle" '
            f'fill="{COLORS["text_primary"]}" font-size="3" font-weight="600" font-family="Inter">'
            f'{tid}</text>'
            f'<text x="{x}%" y="{y+10.5}%" text-anchor="middle" '
            f'fill="{COLORS["text_muted"]}" font-size="2.2" font-family="JetBrains Mono">'
            f'HS {health_pct:.0f}% RUL {rul:.0f}h</text>'
        )

    css = (
        '<style>'
        '@keyframes wsMiniSpin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}'
        '@keyframes wsFadeFleet{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}'
        '</style>'
    )
    svg = (
    f'<svg viewBox="0 0 100 100" width="100%" height="630" preserveAspectRatio="xMidYMid meet">'
    f'<defs><linearGradient id="fleetBg" x1="0%" y1="0%" x2="100%" y2="100%">'
    f'<stop offset="0%" stop-color="#0f172a"/><stop offset="100%" stop-color="#111827"/>'
    f'</linearGradient></defs>'
    f'<rect width="100%" height="100%" rx="6" fill="url(#fleetBg)"/>'
    # Grid
    f'<g opacity="0.07">'
    f'<path d="M0 20 H100 M0 40 H100 M0 60 H100 M0 80 H100" stroke="#94a3b8" stroke-width="0.3"/>'
    f'<path d="M20 0 V100 M40 0 V100 M60 0 V100 M80 0 V100" stroke="#94a3b8" stroke-width="0.3"/>'
    f'</g>'
    # Wind streams — multiple horizontal dashed lines at different y positions
    f'<g opacity="0.18">'
    # Stream 1 — top area
    f'<line x1="-20" y1="12" x2="80" y2="10" stroke="{COLORS["cyan"]}" stroke-width="0.5" stroke-dasharray="4,6">'
    f'<animateTransform attributeName="transform" type="translate" values="-10,0;110,0;-10,0" dur="14s" repeatCount="indefinite"/>'
    f'</line>'
    # Stream 2 — upper mid
    f'<line x1="-20" y1="28" x2="90" y2="26" stroke="{COLORS["cyan"]}" stroke-width="0.4" stroke-dasharray="6,8">'
    f'<animateTransform attributeName="transform" type="translate" values="-20,0;100,0;-20,0" dur="13s" repeatCount="indefinite"/>'
    f'</line>'
    # Stream 3 — mid
    f'<line x1="-10" y1="45" x2="110" y2="43" stroke="{COLORS["cyan"]}" stroke-width="0.5" stroke-dasharray="4,6">'
    f'<animateTransform attributeName="transform" type="translate" values="-15,0;105,0;-15,0" dur="15s" repeatCount="indefinite"/>'
    f'</line>'
    # Stream 4 — lower mid
    f'<line x1="-20" y1="62" x2="85" y2="60" stroke="{COLORS["purple"]}" stroke-width="0.35" stroke-dasharray="3,9">'
    f'<animateTransform attributeName="transform" type="translate" values="-10,0;115,0;-10,0" dur="11s" repeatCount="indefinite"/>'
    f'</line>'
    # Stream 5 — lower
    f'<line x1="-15" y1="76" x2="95" y2="74" stroke="{COLORS["cyan"]}" stroke-width="0.4" stroke-dasharray="5,7">'
    f'<animateTransform attributeName="transform" type="translate" values="-25,0;100,0;-25,0" dur="14s" repeatCount="indefinite"/>'
    f'</line>'
    # Stream 6 — bottom
    f'<line x1="-20" y1="90" x2="80" y2="88" stroke="{COLORS["cyan"]}" stroke-width="0.3" stroke-dasharray="3,10">'
    f'<animateTransform attributeName="transform" type="translate" values="-5,0;120,0;-5,0" dur="15s" repeatCount="indefinite"/>'
    f'</line>'
    # Extra short gusts
    f'<line x1="-20" y1="35" x2="50" y2="34" stroke="{COLORS["cyan"]}" stroke-width="0.25" stroke-dasharray="2,12">'
    f'<animateTransform attributeName="transform" type="translate" values="0,0;130,0;0,0" dur="12s" repeatCount="indefinite"/>'
    f'</line>'
    f'<line x1="-20" y1="55" x2="60" y2="53" stroke="{COLORS["purple"]}" stroke-width="0.25" stroke-dasharray="2,14">'
    f'<animateTransform attributeName="transform" type="translate" values="-30,0;110,0;-30,0" dur="15s" repeatCount="indefinite"/>'
    f'</line>'
    f'</g>'
    # Connection lines
    f'{connection_lines}'
    # Turbines
    f'{turbine_svg}'
    f'</svg>'
)
    return (
        f'<div style="border-radius:22px;overflow:hidden;'
        f'border:1px solid rgba(255,255,255,0.05);'
        f'background:linear-gradient(145deg,rgba(15,23,42,0.95),rgba(17,24,39,0.85));'
        f'box-shadow:0 0 30px rgba(0,0,0,0.35);animation:wsFadeFleet 0.5s ease;">'
        f'{svg}</div>{css}'
    )


def glowing_status_dot(status: str = "healthy") -> str:
    status_map = {
        "healthy":  COLORS.get("healthy",  "#10B981"),
        "warning":  COLORS.get("warning",  "#F59E0B"),
        "critical": COLORS.get("critical", "#EF4444"),
        "offline":  COLORS.get("text_muted","#64748B"),
        "active":   COLORS.get("cyan",     "#00D4FF"),
    }
    color = status_map.get(status.lower(), COLORS["cyan"])
    return (
        '<div style="width:12px;height:12px;border-radius:50%;background:' + color + ';'
        'box-shadow:0 0 10px ' + color + ';animation:wsDotPulse 2s infinite;"></div>'
        '<style>@keyframes wsDotPulse{0%,100%{transform:scale(1);opacity:1;box-shadow:0 0 6px ' + color + ';}'
        '50%{transform:scale(1.35);opacity:0.7;box-shadow:0 0 14px ' + color + ';}}</style>'
    )


def loading_wave(text: str = "Loading WindSense AI...") -> str:
    letters = "".join(f"<span>{c}</span>" for c in text)
    delays  = "".join(
        f".ws-loader-text span:nth-child({i}){{animation-delay:{i*0.05:.2f}s;}}"
        for i in range(2, min(len(text)+1, 20))
    )
    return (
        '<div style="width:100%;padding:20px;text-align:center;">'
        '<div style="display:flex;gap:1px;justify-content:center;flex-wrap:wrap;'
        'margin-bottom:14px;" class="ws-loader-text">' + letters + '</div>'
        '<div style="width:100%;height:4px;border-radius:999px;'
        'background:rgba(255,255,255,0.06);overflow:hidden;">'
        '<div style="width:40%;height:100%;border-radius:999px;'
        'background:linear-gradient(90deg,' + COLORS["cyan"] + ',' + COLORS["purple"] + ');'
        'animation:wsProgress 1.8s infinite ease-in-out;"></div>'
        '</div></div>'
        '<style>'
        '.ws-loader-text span{color:' + COLORS["cyan"] + ';font-weight:700;font-size:14px;'
        "font-family:'Space Grotesk',sans-serif;animation:wsWave 1.2s infinite;}"
        + delays +
        '@keyframes wsWave{0%,100%{transform:translateY(0);opacity:0.6;}'
        '50%{transform:translateY(-5px);opacity:1;}}'
        '@keyframes wsProgress{0%{transform:translateX(-100%);}100%{transform:translateX(350%);}}'
        '</style>'
    )


def agent_pipeline_visual(agents: list) -> str:
    """Animated agent pipeline with neural connection lines."""
    n = len(agents)
    items = ""
    for i, (aid, role, color) in enumerate(agents):
        connector = ""
        if i < n - 1:
            connector = (
                '<div style="display:flex;align-items:center;padding:0 6px;">'
                '<div style="height:2px;width:32px;background:linear-gradient(to right,'
                + color + ',' + COLORS["purple"] + ');opacity:0.6;border-radius:999px;'
                'position:relative;overflow:hidden;">'
                '<div style="position:absolute;top:0;left:0;height:100%;width:12px;'
                'background:white;opacity:0.4;border-radius:999px;'
                'animation:wsFlowPulse 1.5s ' + str(i*0.3) + 's linear infinite;"></div>'
                '</div></div>'
            )
        items += (
            '<div style="display:flex;flex-direction:column;align-items:center;gap:6px;">'
            '<div style="width:52px;height:52px;border-radius:50%;'
            'background:' + color + '15;border:2px solid ' + color + ';'
            'display:flex;align-items:center;justify-content:center;'
            'font-size:20px;box-shadow:0 0 16px ' + color + '40;'
            'animation:wsAgentPulse 3s ' + str(i*0.5) + 's ease-in-out infinite;">'
            '🤖</div>'
            '<div style="font-size:10px;font-weight:700;color:' + color + ';'
            'letter-spacing:0.5px;text-align:center;">' + aid + '</div>'
            '<div style="font-size:9px;color:' + COLORS["text_muted"] + ';'
            'text-align:center;max-width:60px;line-height:1.3;">' + role + '</div>'
            '</div>'
            + connector
        )

    return (
        '<div style="display:flex;align-items:center;justify-content:center;'
        'padding:20px;background:rgba(5,8,22,0.7);border-radius:16px;'
        'border:1px solid ' + COLORS["border"] + ';gap:4px;">'
        + items +
        '</div>'
        '<style>'
        '@keyframes wsAgentPulse{0%,100%{box-shadow:0 0 12px rgba(0,212,255,0.3);}'
        '50%{box-shadow:0 0 24px rgba(0,212,255,0.6);}}'
        '@keyframes wsFlowPulse{0%{transform:translateX(-100%);}100%{transform:translateX(400%);}}'
        '</style>'
    )


def scan_line_effect() -> str:
    """Subtle CRT scan-line ambient effect for page backgrounds."""
    return (
        '<style>'
        '@keyframes wsScanLine{'
        '0%{top:-2%;opacity:0.04;}'
        '100%{top:102%;opacity:0;}'
        '}'
        '.ws-scan-overlay::before{'
        'content:"";position:fixed;top:0;left:0;right:0;height:2px;'
        'background:linear-gradient(to right,transparent,' + COLORS["cyan"] + ',transparent);'
        'pointer-events:none;z-index:9998;'
        'animation:wsScanLine 6s linear infinite;'
        '}'
        '</style>'
        '<div class="ws-scan-overlay"></div>'
    )


def metric_flip_card(label: str, value: str, sub: str = "",
                     color: str = None) -> str:
    """Animated flip-style metric display."""
    c = color or COLORS["cyan"]
    return (
        '<div style="background:rgba(13,20,36,0.9);border:1px solid ' + COLORS["border"] + ';'
        'border-top:2px solid ' + c + ';border-radius:14px;padding:18px;text-align:center;'
        'transition:all 0.3s cubic-bezier(0.22,1,0.36,1);cursor:default;'
        'box-shadow:0 4px 20px rgba(0,0,0,0.3);"'
        'onmouseover="this.style.transform=\'translateY(-4px)\';this.style.boxShadow=\'0 12px 36px rgba(0,0,0,0.4)\'"'
        'onmouseout="this.style.transform=\'translateY(0)\';this.style.boxShadow=\'0 4px 20px rgba(0,0,0,0.3)\'">'
        '<div style="font-size:10px;color:' + COLORS["text_muted"] + ';'
        'text-transform:uppercase;letter-spacing:1.5px;font-weight:700;margin-bottom:8px;">'
        + label + '</div>'
        '<div style="font-size:32px;font-weight:800;color:' + c + ';'
        "font-family:'Space Grotesk',sans-serif;line-height:1;letter-spacing:-1px;\">"
        + value + '</div>'
        + (f'<div style="font-size:11px;color:{COLORS["text_muted"]};margin-top:6px;">{sub}</div>' if sub else '') +
        '</div>'
    )


def telemetry_stream_bar(sensors: list) -> str:
    """
    Animated telemetry bar showing live sensor values.
    sensors: list of (name, value, max_val, color)
    """
    bars = ""
    for i, (name, val, max_val, color) in enumerate(sensors):
        pct = min(100, max(0, (val / max_val) * 100)) if max_val else 0
        bars += (
            '<div style="margin-bottom:10px;">'
            '<div style="display:flex;justify-content:space-between;'
            'align-items:center;margin-bottom:4px;">'
            '<span style="font-size:11px;color:' + COLORS["text_secondary"] + ';font-weight:600;">' + name + '</span>'
            '<span style="font-size:11px;color:' + color + ';'
            "font-family:'JetBrains Mono',monospace;font-weight:700;\">" + f"{val:.1f}" + '</span>'
            '</div>'
            '<div style="height:5px;background:rgba(255,255,255,0.06);border-radius:999px;overflow:hidden;">'
            '<div style="height:100%;width:' + f"{pct:.1f}" + '%;background:' + color + ';'
            'border-radius:999px;box-shadow:0 0 8px ' + color + ';'
            'animation:wsBarGrow 0.8s ' + f"{i*0.1:.1f}" + 's cubic-bezier(0.22,1,0.36,1) both;'
            'transition:width 0.5s ease;"></div>'
            '</div></div>'
        )

    return (
        '<div style="background:rgba(5,8,22,0.7);border:1px solid ' + COLORS["border"] + ';'
        'border-radius:14px;padding:16px;">' + bars + '</div>'
        '<style>@keyframes wsBarGrow{from{width:0;}}</style>'
    )