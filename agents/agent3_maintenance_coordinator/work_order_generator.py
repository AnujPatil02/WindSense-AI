"""Auto-generate PDF Work Orders — Agent 3"""

from pathlib import Path
from datetime import datetime
from typing import Dict
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from loguru import logger

WORK_ORDERS = Path("outputs/work_orders")


def generate(decision: Dict, rul_result: Dict,
             anomaly_result: Dict, llm_explanation: str = "") -> Path:
    """
    Generate a PDF maintenance work order.
    Returns path to created PDF.
    """
    WORK_ORDERS.mkdir(exist_ok=True)

    turbine_id = decision["turbine_id"]
    timestamp  = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    pdf_path   = WORK_ORDERS / f"WO_{turbine_id}_{timestamp}.pdf"

    doc    = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                                topMargin=2*cm, bottomMargin=2*cm,
                                leftMargin=2.5*cm, rightMargin=2.5*cm)
    styles = getSampleStyleSheet()
    story  = []

    # ── Header ────────────────────────────────────────────────────────────
    title_style = ParagraphStyle("title", parent=styles["Title"],
                                  textColor=colors.HexColor("#1a3c5e"),
                                  fontSize=18)
    story.append(Paragraph("WINDSENSE-AI MAINTENANCE WORK ORDER", title_style))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor("#1a3c5e")))
    story.append(Spacer(1, 0.3*cm))

    # ── Work Order Info ───────────────────────────────────────────────────
    wo_number = f"WO-{turbine_id}-{timestamp}"
    info_data = [
        ["Work Order #",   wo_number,
         "Priority",       _priority_label(decision["priority"])],
        ["Turbine ID",     turbine_id,
         "Generated",      datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["Scheduled Start",decision.get("scheduled_start", "TBD")[:19],
         "Scheduled End",  decision.get("scheduled_end", "TBD")[:19]],
        ["Assigned Crew",  decision.get("assigned_crew", "TBD"),
         "Action",         decision.get("action", "TBD").replace("_", " ")],
    ]

    info_table = Table(info_data, colWidths=[4*cm, 5.5*cm, 3.5*cm, 4*cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), colors.HexColor("#f0f4f8")),
        ("TEXTCOLOR",   (0,0), (0,-1), colors.HexColor("#1a3c5e")),
        ("TEXTCOLOR",   (2,0), (2,-1), colors.HexColor("#1a3c5e")),
        ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",    (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.grey),
        ("PADDING",     (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Sensor Data ───────────────────────────────────────────────────────
    story.append(Paragraph("DIAGNOSTIC DATA", styles["Heading2"]))
    sensor_data = [
        ["Parameter",          "Value",        "Status"],
        ["Anomaly Score",      f"{decision.get('anomaly_score', 0):.4f}",
         _flag("HIGH" if decision.get("anomaly_score",0) > 0.7 else "OK")],
        ["RUL Estimate",       f"{rul_result.get('rul_hours',0):.1f} hours",
         _flag("CRITICAL" if rul_result.get('rul_hours',99) < 24 else "OK")],
        ["RUL Lower Bound",    f"{rul_result.get('lower_hours',0):.1f} hours", ""],
        ["RUL Upper Bound",    f"{rul_result.get('upper_hours',0):.1f} hours", ""],
        ["Primary Fault Sensor", anomaly_result.get("primary_cause","N/A"), ""],
        ["Recommended Load",   f"{decision.get('recommended_load_pct',100)}%", ""],
    ]

    s_table = Table(sensor_data, colWidths=[6*cm, 5*cm, 6*cm])
    s_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#1a3c5e")),
        ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.white, colors.HexColor("#f9fbfc")]),
        ("PADDING",     (0,0), (-1,-1), 6),
    ]))
    story.append(s_table)
    story.append(Spacer(1, 0.4*cm))

    # ── AI Reasoning ──────────────────────────────────────────────────────
    story.append(Paragraph("AI DECISION REASONING", styles["Heading2"]))
    reasoning = llm_explanation or decision.get("reasoning", "N/A")
    story.append(Paragraph(reasoning, styles["BodyText"]))
    story.append(Spacer(1, 0.3*cm))

    # ── Safety Checklist ─────────────────────────────────────────────────
    story.append(Paragraph("SAFETY CHECKLIST (Technician must complete)", styles["Heading2"]))
    checklist = [
        "☐  Work permit obtained and signed",
        "☐  Turbine de-energized and LOTO applied",
        "☐  Rotor lock pin inserted and tagged",
        "☐  PPE: harness, hard hat, petroleum-rated gloves",
        "☐  Wind speed confirmed < 8 m/s before tower access",
        "☐  Two-person crew confirmed on site",
        "☐  Emergency contact numbers verified",
    ]
    for item in checklist:
        story.append(Paragraph(item, styles["BodyText"]))

    story.append(Spacer(1, 0.4*cm))

    # ── Sign-off ──────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    sign_data = [
        ["Technician Signature", "________________",
         "Supervisor Approval",  "________________"],
        ["Date / Time",          "________________",
         "Date / Time",          "________________"],
    ]
    sign_table = Table(sign_data, colWidths=[4*cm, 5*cm, 4*cm, 5*cm])
    sign_table.setStyle(TableStyle([
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("PADDING",   (0,0), (-1,-1), 8),
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
    ]))
    story.append(sign_table)

    doc.build(story)
    logger.success(f"Work order generated: {pdf_path}")
    return pdf_path


def _priority_label(priority: str) -> str:
    labels = {
        "CRITICAL": "🔴 CRITICAL",
        "HIGH"    : "🟠 HIGH",
        "MEDIUM"  : "🟡 MEDIUM",
        "LOW"     : "🟢 LOW",
    }
    return labels.get(priority, priority)


def _flag(status: str) -> str:
    return {"HIGH": "⚠ HIGH", "CRITICAL": "🔴 CRITICAL", "OK": "✓ OK"}.get(status, status)


if __name__ == "__main__":
    decision = {
        "turbine_id": "WT-003", "priority": "HIGH",
        "anomaly_score": 0.82, "action": "SCHEDULE_WITHIN_48H",
        "scheduled_start": "2024-06-01T06:00:00",
        "scheduled_end":   "2024-06-01T12:00:00",
        "assigned_crew": "CREW_A", "primary_cause": "sensor_7",
        "recommended_load_pct": 50,
        "reasoning": "High anomaly score detected on gearbox sensor. RUL critically low.",
    }
    rul    = {"rul_hours": 38.0, "lower_hours": 22.0, "upper_hours": 55.0}
    anomaly= {"primary_cause": "sensor_7", "anomaly_score": 0.82}
    path   = generate(decision, rul, anomaly,
                      llm_explanation="Gearbox bearing degradation confirmed by Agent 1.")
    print(f"✅ PDF: {path}")