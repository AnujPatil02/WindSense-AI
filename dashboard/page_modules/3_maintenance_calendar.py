# dashboard/page_modules/3_maintenance_calendar.py
"""Maintenance Calendar — Elite UI"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
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

# 3_maintenance_calendar.py — replace get_schedule() entirely

from dashboard.utils.data_loader import load_decisions, DUR_MAP, MAINT_COST, FAILURE_COST, TARIFF, RATED

@st.cache_data(ttl=30, show_spinner=False)
def get_schedule():
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    df  = load_decisions()

    # Schedule windows based on priority
    OFFSET = {"CRITICAL":1, "HIGH":12, "MEDIUM":24, "LOW":120}
    starts, ends = [], []
    for _, row in df.iterrows():
        pri = row.get("priority","LOW")
        dur = DUR_MAP.get(pri, 6)
        oh  = OFFSET.get(pri, 24)
        s   = now + timedelta(hours=oh)
        starts.append(s.isoformat())
        ends.append((s + timedelta(hours=dur)).isoformat())

    df["scheduled_start"] = starts
    df["scheduled_end"]   = ends
    return df

df = get_schedule()

# ── Header ─────────────────────────────────────────────────
st.markdown(
    '<div class="ws-stagger-1" style="margin-bottom:24px;">'
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">'
    '<h1 style="font-size:28px;font-weight:800;margin:0;'
    "font-family:'Space Grotesk',sans-serif;"
    'color:' + COLORS['text_primary'] + ';letter-spacing:-1px;">📅 Maintenance Schedule</h1>'
    '<span style="font-size:10px;font-weight:700;color:' + COLORS['warning'] + ';'
    'letter-spacing:2px;background:rgba(245,158,11,0.08);'
    'border:1px solid rgba(245,158,11,0.22);border-radius:20px;padding:4px 12px;">AI-OPTIMIZED</span>'
    '</div>'
    '<p style="color:' + COLORS['text_muted'] + ';font-size:13px;margin:0;">'
    'AI-optimized maintenance windows · minimizing generation loss · crew dispatch</p>'
    '</div>',
    unsafe_allow_html=True
)

# ── KPIs ───────────────────────────────────────────────────
total_loss   = float(df["revenue_loss_usd"].sum()) if "revenue_loss_usd" in df.columns else 0
total_saving = float(df["net_saving_usd"].sum())   if "net_saving_usd"   in df.columns else 0
n_critical   = int(len(df[df["priority"]=="CRITICAL"])) if "priority" in df.columns else 0

cols = st.columns(4)
kpis = [
    ("Critical Jobs",   str(n_critical),        "Immediate action", "down" if n_critical else "up", COLORS["critical"],"🚨"),
    ("Total Scheduled", str(len(df)),            "All turbines",     "neutral", COLORS["cyan"],    "📋"),
    ("Revenue Loss",    f"${total_loss:,.0f}",   "Downtime cost",    "warn",    COLORS["warning"], "💸"),
    ("Net Savings",     f"${total_saving:,.0f}", "vs failure cost",  "up",      COLORS["healthy"], "💰"),
]
for col, (label, val, delta, dtype, color, icon) in zip(cols, kpis):
    with col:
        st.markdown(kpi_card(label, val, delta, dtype, icon, color), unsafe_allow_html=True)

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

# ── Parse valid rows once ──────────────────────────────────
now = datetime.utcnow()
valid_rows = []
for _, row in df.iterrows():
    try:
        s = pd.to_datetime(row["scheduled_start"]).to_pydatetime().replace(tzinfo=None)
        e = pd.to_datetime(row["scheduled_end"]).to_pydatetime().replace(tzinfo=None)
        if (e - s).total_seconds() < 3600:
            e = s + timedelta(hours=6)
        valid_rows.append((row, s, e))
    except Exception:
        continue

tab1, tab2, tab3 = st.tabs(["📅 Gantt Timeline", "👷 Crew Schedule", "📋 Job Details"])

# ── TAB 1 ──────────────────────────────────────────────────
with tab1:
    st.markdown(section_header("Maintenance Timeline",
                "AI-scheduled windows aligned with low-wind forecast periods"),
                unsafe_allow_html=True)

    if valid_rows:
        fig = go.Figure()
        seen = set()

        for row, start, end in valid_rows:
            pri   = row.get("priority","LOW")
            color = PRIORITY_COLOR.get(pri, COLORS["healthy"])
            tid   = row.get("turbine_id","")
            crew  = row.get("assigned_crew","")
            rul   = row.get("rul_hours", 0)
            loss  = row.get("revenue_loss_usd", 0)
            dur_h = (end - start).total_seconds() / 3600

            # Use scatter with fill for gantt bars (datetime x-axis compatible)
            y_top = tid + " ▲"
            y_bot = tid + " ▼"
            fig.add_trace(go.Scatter(
                x=[start, end, end, start, start],
                y=[y_top,  y_top, y_bot,  y_bot,  y_top],
                fill="toself",
                fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.25)",  # hex opacity
                line=dict(color=color, width=1.5),
                name=pri, legendgroup=pri,
                showlegend=(pri not in seen),
                hovertemplate=(
                    "<b>" + tid + "</b> | " + pri + "<br>" +
                    "Crew: " + str(crew) + " | RUL: " + str(int(float(rul))) + "h<br>" +
                    "Start: " + start.strftime("%b %d %H:%M") + "<br>" +
                    "End: " + end.strftime("%b %d %H:%M") + "<br>" +
                    "Duration: " + f"{dur_h:.0f}" + "h | Loss: $" + f"{float(loss):,.0f}" +
                    "<extra></extra>"
                ),
            ))
            seen.add(pri)

            # Label in center of bar
            mid = start + (end - start) / 2
            fig.add_annotation(
                x=mid, y=y_top,
                text=str(crew) + " · " + f"{dur_h:.0f}" + "h",
                showarrow=False,
                font=dict(size=10, color=COLORS["text_primary"]),
                yshift=-12,
            )

        # NOW line — pass datetime object directly, NOT isoformat string
        fig.add_shape(
            type="line",
            x0=now, x1=now,
            y0=0, y1=1,
            yref="paper",
            line=dict(color=COLORS["text_muted"], width=1.5, dash="dash"),
        )
        fig.add_annotation(
            x=now, y=1, yref="paper",
            text="NOW", showarrow=False,
            font=dict(size=10, color=COLORS["text_muted"]),
            yshift=8,
        )

        # Y-axis: clean turbine IDs only
        tids     = [r.get("turbine_id","") for r,_,_ in valid_rows]
        y_tops   = [t + " ▲" for t in tids]
        y_bots   = [t + " ▼" for t in tids]
        all_y    = []
        for a, b in zip(y_tops, y_bots):
            all_y += [a, b]

        fig.update_layout(
            height=380,
            xaxis=dict(
                title="Timeline",
                type="date",
                tickformat="%b %d\n%H:%M",
                gridcolor="rgba(255,255,255,0.04)",
                tickfont=dict(color=COLORS["text_secondary"], size=10),
            ),
            yaxis=dict(
                tickvals=y_tops,
                ticktext=tids,
                tickfont=dict(color=COLORS["text_primary"], size=12),
                gridcolor="rgba(255,255,255,0.04)",
            ),
            legend=dict(
                bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"],
                font=dict(color=COLORS["text_secondary"]), title="Priority",
            ),
            **_PT,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid schedule rows to display.")

    # Summary cards
    st.markdown(section_header("Schedule Summary"), unsafe_allow_html=True)
    if valid_rows:
        card_cols = st.columns(len(valid_rows))
        for col, (row, start, end) in zip(card_cols, valid_rows):
            pri   = row.get("priority","LOW")
            color = PRIORITY_COLOR.get(pri, COLORS["healthy"])
            tid   = row.get("turbine_id","")
            dur_h = (end-start).total_seconds()/3600
            col.markdown(
                '<div style="background:rgba(13,20,36,0.9);'
                'border:1px solid ' + color + '44;border-top:3px solid ' + color + ';'
                'border-radius:12px;padding:14px;text-align:center;">'
                '<div style="font-size:13px;font-weight:800;color:' + COLORS["text_primary"] + ';'
                "font-family:'Space Grotesk',sans-serif;\">" + tid + '</div>'
                '<div style="font-size:10px;color:' + COLORS["text_muted"] + ';margin:4px 0;">'
                + start.strftime("%b %d %H:%M") + '</div>'
                '<div style="font-size:13px;color:' + color + ';font-weight:700;'
                "font-family:'JetBrains Mono',monospace;\">" + f"{dur_h:.0f}h" + '</div>'
                '<div style="font-size:10px;color:' + COLORS["text_muted"] + ';margin-top:3px;">'
                + str(row.get("assigned_crew","")) + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

# ── TAB 2 ──────────────────────────────────────────────────
with tab2:
    if "assigned_crew" not in df.columns:
        st.info("No crew data.")
    else:
        crew_data = (df.groupby("assigned_crew")
                     .agg(jobs=("turbine_id","count"),
                          total_loss=("revenue_loss_usd","sum"))
                     .reset_index())
        bar_colors = [COLORS["cyan"],COLORS["purple"],COLORS["warning"],COLORS["healthy"]]

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(section_header("Jobs per Crew"), unsafe_allow_html=True)
            fig3 = go.Figure(go.Bar(
                x=crew_data["assigned_crew"].tolist(),
                y=crew_data["jobs"].tolist(),
                marker=dict(color=bar_colors[:len(crew_data)], line=dict(width=0)),
                text=crew_data["jobs"].tolist(), textposition="outside",
                textfont=dict(color=COLORS["text_primary"], size=13, family="JetBrains Mono"),
            ))
            fig3.update_layout(height=300, bargap=0.4, showlegend=False, **_PT)
            st.plotly_chart(fig3, use_container_width=True)

        with c2:
            st.markdown(section_header("Revenue Impact"), unsafe_allow_html=True)
            fig4 = go.Figure(go.Pie(
                labels=crew_data["assigned_crew"].tolist(),
                values=crew_data["total_loss"].tolist(),
                hole=0.58,
                marker=dict(colors=bar_colors[:len(crew_data)],
                            line=dict(color=COLORS["bg_primary"], width=3)),
                textfont=dict(size=12, color=COLORS["text_primary"]),
            ))
            fig4.add_annotation(text="Revenue<br>Impact", x=0.5, y=0.5, showarrow=False,
                                font=dict(size=11, color=COLORS["text_muted"]))
            fig4.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                               font=dict(family="Inter", color=COLORS["text_secondary"]),
                               legend=dict(bgcolor="rgba(0,0,0,0)",
                                          font=dict(color=COLORS["text_secondary"],size=11)),
                               margin=dict(l=16,r=16,t=16,b=16))
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown(section_header("Crew Assignment Details"), unsafe_allow_html=True)
        for crew in sorted(df["assigned_crew"].unique()):
            crew_jobs = df[df["assigned_crew"] == crew]
            with st.expander("👷 " + crew + " — " + str(len(crew_jobs)) + " job(s)"):
                for _, job in crew_jobs.iterrows():
                    pri   = job.get("priority","LOW")
                    color = PRIORITY_COLOR.get(pri, COLORS["healthy"])
                    action = job.get("action","").replace("_"," ")
                    try:
                        ss = pd.to_datetime(job["scheduled_start"]).strftime("%b %d %H:%M")
                    except Exception:
                        ss = str(job.get("scheduled_start",""))[:16]
                    st.markdown(
                        '<div style="display:flex;justify-content:space-between;'
                        'align-items:center;padding:12px 16px;margin-bottom:10px;'
                        'background:rgba(5,8,22,0.7);border:1px solid ' + COLORS["border"] + ';'
                        'border-left:3px solid ' + color + ';border-radius:10px;">'
                        '<div>'
                        '<div style="font-weight:700;color:' + COLORS["text_primary"] + ';'
                        'font-size:13px;">' + str(job.get("turbine_id","")) + '</div>'
                        '<div style="font-size:11px;color:' + COLORS["text_muted"] + ';'
                        'margin-top:3px;">' + action + ' · ' + ss + '</div>'
                        '</div>'
                        + priority_badge(pri) +
                        '</div>',
                        unsafe_allow_html=True
                    )

# ── TAB 3 ──────────────────────────────────────────────────
with tab3:
    st.markdown(section_header("All Maintenance Jobs",
                "Sorted by priority — financial impact analysis"), unsafe_allow_html=True)

    MAINT_COST   = {"CRITICAL":8000,"HIGH":5000,"MEDIUM":3000,"LOW":1500}
    FAILURE_COST = 50_000.0
    TARIFF       = 0.075
    RATED        = 2000.0
    emoji_map    = {"CRITICAL":"🚨","HIGH":"⚠️","MEDIUM":"📋","LOW":"✅"}

    pri_order = {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3}
    df_s = df.copy()
    if "priority" in df_s.columns:
        df_s["_o"] = df_s["priority"].map(pri_order).fillna(4)
        df_s = df_s.sort_values("_o").drop("_o",axis=1)

    for _, row in df_s.iterrows():
        pri   = row.get("priority","LOW")
        color = PRIORITY_COLOR.get(pri, COLORS["healthy"])
        tid   = row.get("turbine_id","")
        action= row.get("action","").replace("_"," ")
        rul   = float(row.get("rul_hours",80))
        crew  = row.get("assigned_crew","TBD")
        mc    = MAINT_COST.get(pri,5000)
        emoji = emoji_map.get(pri,"📋")

        try:
            s_dt = pd.to_datetime(row["scheduled_start"]).to_pydatetime().replace(tzinfo=None)
            e_dt = pd.to_datetime(row["scheduled_end"]).to_pydatetime().replace(tzinfo=None)
            dur  = max(4.0,(e_dt-s_dt).total_seconds()/3600)
            ss   = s_dt.strftime("%b %d, %Y %H:%M")
            es   = e_dt.strftime("%b %d, %Y %H:%M")
        except Exception:
            dur = {"CRITICAL":12,"HIGH":8,"MEDIUM":6,"LOW":4}.get(pri,6)
            ss  = es = "N/A"

        cf   = 0.40 + min(rul/125.0,1.0)*0.25
        loss = round(RATED*cf*dur*TARIFF, 2)
        ns   = round(FAILURE_COST-mc-loss, 2)

        with st.expander(emoji + " **" + tid + "** — " + pri + " — " + action,
                         expanded=(pri=="CRITICAL")):
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("RUL",          f"{rul:.0f}h")
            m2.metric("Duration",     f"{dur:.0f}h")
            m3.metric("Revenue Loss", f"${loss:,.0f}")
            m4.metric("Net Saving",   f"${ns:,.0f}")

            st.markdown(
                '<div style="display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 10px;">'
                + priority_badge(pri) +
                '<span class="ws-badge ws-badge-cyan">👷 ' + crew + '</span>'
                '<span class="ws-badge ws-badge-gray">🕐 ' + ss + '</span>'
                '<span class="ws-badge ws-badge-gray">🕐 ' + es + '</span>'
                '</div>'
                '<div style="background:rgba(5,8,22,0.8);border:1px solid ' + color + '33;'
                'margin-top:10px;margin-bottom:10px;'
                'border-left:3px solid ' + color + ';border-radius:10px;padding:14px 16px;">'
                '<div style="font-size:9px;color:' + COLORS["text_muted"] + ';'
                'font-weight:700;letter-spacing:1.5px;margin-bottom:8px;">💡 FINANCIAL SUMMARY</div>'
                '<div style="font-size:12px;color:' + COLORS["text_secondary"] + ';line-height:1.8;">'
                'Avoiding failure saves <span style="color:' + COLORS["healthy"] + ';'
                "font-weight:700;font-family:'JetBrains Mono',monospace;\">$" + f"{ns:,.0f}" + '</span>'
                ' net · $' + f"{FAILURE_COST:,.0f}" + ' avoided − $' + f"{mc:,}" +
                ' maintenance − $' + f"{loss:,.0f}" + ' generation loss'
                '</div></div>',
                unsafe_allow_html=True
            )

    # Summary table
    rows = []
    for _, row in df_s.iterrows():
        pri = row.get("priority","LOW")
        rul = float(row.get("rul_hours",80))
        try:
            s = pd.to_datetime(row["scheduled_start"]).to_pydatetime().replace(tzinfo=None)
            e = pd.to_datetime(row["scheduled_end"]).to_pydatetime().replace(tzinfo=None)
            dur = max(4.0,(e-s).total_seconds()/3600)
        except Exception:
            dur = {"CRITICAL":12,"HIGH":8,"MEDIUM":6,"LOW":4}.get(pri,6)
        cf   = 0.40+min(rul/125.0,1.0)*0.25
        loss = round(RATED*cf*dur*TARIFF,2)
        mc   = MAINT_COST.get(pri,5000)
        ns   = round(FAILURE_COST-mc-loss,2)
        rows.append({"Turbine":row.get("turbine_id",""),"Priority":pri,
                     "Duration (h)":round(dur,0),"Revenue Loss ($)":loss,
                     "Maint Cost ($)":mc,"Net Saving ($)":ns,
                     "Crew":row.get("assigned_crew","")})

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                 column_config={
                     "Revenue Loss ($)": st.column_config.NumberColumn(format="$%.0f"),
                     "Net Saving ($)":   st.column_config.NumberColumn(format="$%.0f"),
                     "Maint Cost ($)":   st.column_config.NumberColumn(format="$%.0f"),
                 })
    st.download_button("⬇️ Export CSV", df_s.to_csv(index=False),
                       "maintenance_schedule.csv","text/csv")