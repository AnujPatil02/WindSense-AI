"""
WindSense-AI — Synthetic Data Generator
Generates:
  1. maintenance_logs.csv     — fault history for RAG
  2. Equipment manual PDFs    — knowledge base documents
"""

import pandas as pd
import numpy as np
import random
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

random.seed(42)
np.random.seed(42)

SYNTHETIC_DIR = Path("data/synthetic")
MANUALS_DIR   = SYNTHETIC_DIR / "equipment_manuals"
RAG_DOCS_DIR  = Path("data/rag_docs")
MANUALS_DIR.mkdir(exist_ok=True)
RAG_DOCS_DIR.mkdir(exist_ok=True)

# ── 1. Maintenance Logs ─────────────────────────────────────────────────────

FAULT_TYPES = [
    "Gearbox bearing wear",
    "Rotor blade imbalance",
    "Generator overheating",
    "Hydraulic system pressure drop",
    "Pitch control failure",
    "Yaw system misalignment",
    "Main shaft fatigue crack",
    "Cooling fan failure",
    "Oil contamination",
    "Vibration sensor drift",
]

ACTIONS_TAKEN = [
    "Replaced bearing assembly. Torqued to 280 Nm. Test run 2 hours normal.",
    "Balanced rotor blades. Vibration reduced from 8.2 to 1.1 mm/s.",
    "Cleaned cooling fins, replaced thermal paste. Temperature normal after 30 min.",
    "Replaced hydraulic seals and refilled fluid to 210 bar. System stable.",
    "Recalibrated pitch actuator. Pitch angle error reduced to ±0.2°.",
    "Realigned yaw motor encoder. Yaw error <1° across all wind directions.",
    "Welded fatigue crack with ER70S-6 rod. NDT confirmed structural integrity.",
    "Replaced cooling fan motor. Airflow restored to rated 850 CFM.",
    "Drained and replaced ISO VG 320 gear oil. Particle count within spec.",
    "Replaced MEMS vibration sensor. Calibrated against reference accelerometer.",
]

TECHNICIANS = ["Ravi Kumar", "Priya Sharma", "Amit Patel", "Neha Singh", "Rahul Gupta"]
TURBINES    = [f"WT-{str(i).zfill(3)}" for i in range(1, 16)]

records = []
start_date = pd.Timestamp("2020-01-01")

for i in range(500):
    fault_idx  = random.randint(0, len(FAULT_TYPES) - 1)
    fault      = FAULT_TYPES[fault_idx]
    action     = ACTIONS_TAKEN[fault_idx]
    turbine    = random.choice(TURBINES)
    technician = random.choice(TECHNICIANS)
    date       = start_date + pd.Timedelta(days=random.randint(0, 1460))
    severity   = random.choice(["Low", "Medium", "High", "Critical"])
    downtime_h = round(random.uniform(1.0, 72.0), 1)
    cost_usd   = round(random.uniform(500, 25000), 2)
    sensor_val = round(random.uniform(0.5, 9.8), 2)

    records.append({
        "log_id"         : f"LOG-{str(i+1).zfill(4)}",
        "date"           : date.strftime("%Y-%m-%d"),
        "turbine_id"     : turbine,
        "fault_type"     : fault,
        "severity"       : severity,
        "anomaly_score"  : round(random.uniform(0.5, 1.0), 3),
        "sensor_reading" : sensor_val,
        "sensor_unit"    : random.choice(["mm/s", "°C", "bar", "RPM"]),
        "action_taken"   : action,
        "technician"     : technician,
        "downtime_hours" : downtime_h,
        "repair_cost_usd": cost_usd,
        "resolution"     : random.choice(["Resolved", "Resolved", "Resolved", "Monitoring"]),
    })

logs_df = pd.DataFrame(records).sort_values("date").reset_index(drop=True)
logs_df.to_csv(SYNTHETIC_DIR / "maintenance_logs.csv", index=False)
logs_df.to_csv(RAG_DOCS_DIR  / "maintenance_logs.csv", index=False)
print(f"✅ maintenance_logs.csv — {len(logs_df)} records")

# ── 2. Equipment Manual PDFs ─────────────────────────────────────────────────

MANUALS = {
    "gearbox_maintenance_manual": {
        "title": "WindSense Gearbox Maintenance Manual — Rev 4.2",
        "sections": [
            ("1. Safety Precautions",
             "Always de-energize the turbine and engage rotor lock before any gearbox inspection. "
             "Use PPE including safety harness, hard hat, and gloves rated for petroleum products. "
             "Minimum two-person crew required for gearbox work above ground level."),
            ("2. Inspection Intervals",
             "Perform visual inspection every 3 months. Oil sampling every 6 months. "
             "Full bearing inspection every 12 months or after any anomaly score exceeding 0.75. "
             "Replace bearing assembly when vibration exceeds 7.0 mm/s RMS sustained over 4 hours."),
            ("3. Gearbox Bearing Replacement Procedure",
             "Step 1: Lock out rotor and confirm zero energy state.\n"
             "Step 2: Drain gear oil into approved container (ISO VG 320, capacity 180L).\n"
             "Step 3: Remove gearbox access panel (M16 bolts, 32 Nm torque).\n"
             "Step 4: Extract old bearing using hydraulic puller tool P/N WSN-HP-003.\n"
             "Step 5: Clean bearing seat with lint-free cloth and isopropyl alcohol.\n"
             "Step 6: Press new bearing (SKF 23134 CCK/W33) using induction heater at 110°C.\n"
             "Step 7: Torque retaining bolts to 280 Nm in star pattern.\n"
             "Step 8: Refill with fresh ISO VG 320 oil to sight glass midpoint.\n"
             "Step 9: Run turbine at 30% rated speed for 2 hours. Monitor vibration and temperature."),
            ("4. Oil Analysis Thresholds",
             "Water content: <200 ppm. Viscosity at 40°C: 288–352 cSt. "
             "ISO cleanliness code: 16/14/11 maximum. Particle count >4µm: <500 particles/mL. "
             "If any threshold exceeded: drain and replace oil immediately."),
            ("5. Fault Codes",
             "GBX-001: High vibration — check bearing preload and alignment.\n"
             "GBX-002: Oil temperature >95°C — check cooling system and oil level.\n"
             "GBX-003: Oil pressure <1.5 bar — check pump and filter condition.\n"
             "GBX-004: Gear mesh frequency anomaly — inspect gear teeth for pitting or spalling."),
        ]
    },
    "bearing_failure_guide": {
        "title": "WindSense Bearing Failure Diagnosis Guide — Rev 2.1",
        "sections": [
            ("1. Early Warning Indicators",
             "Stage 1 (RUL 80–100 hours): High frequency vibration peaks at bearing defect frequencies. "
             "Anomaly score 0.5–0.65. Action: increase monitoring frequency to daily.\n"
             "Stage 2 (RUL 40–80 hours): Audible bearing noise during low-wind inspection. "
             "Temperature rise of 5–10°C above baseline. Anomaly score 0.65–0.80.\n"
             "Stage 3 (RUL <40 hours): Significant vibration increase >6 mm/s. "
             "Temperature >85°C. Anomaly score >0.80. Action: schedule immediate replacement."),
            ("2. Vibration Signature Analysis",
             "Ball pass frequency outer race (BPFO) = n/2 × RPM/60 × (1 - d/D × cos α).\n"
             "Ball pass frequency inner race (BPFI) = n/2 × RPM/60 × (1 + d/D × cos α).\n"
             "n=number of balls, d=ball diameter, D=pitch diameter, α=contact angle.\n"
             "For SKF 23134: BPFO = 8.4× shaft RPM. BPFI = 11.6× shaft RPM."),
            ("3. Root Cause Categories",
             "Lubrication failure (35% of cases): Identified by spalling on rolling elements.\n"
             "Contamination (25% of cases): Metal particles or water ingress.\n"
             "Overload (20% of cases): Brinelling marks on raceway.\n"
             "Misalignment (15% of cases): Uneven wear pattern across raceway width.\n"
             "Manufacturing defect (5% of cases): Identified by premature failure <6 months."),
        ]
    },
    "safety_and_operations_manual": {
        "title": "WindSense Turbine Safety and Operations Manual — Section 4",
        "sections": [
            ("4.1 Emergency Shutdown Procedure",
             "Step 1: Press red E-STOP button on SCADA terminal or turbine base.\n"
             "Step 2: Confirm rotor brake engagement within 45 seconds (alarm if exceeded).\n"
             "Step 3: Confirm pitch set to feathered position (90° ± 2°).\n"
             "Step 4: Isolate grid connection via main circuit breaker.\n"
             "Step 5: Wait 10 minutes for rotor to fully stop before tower access."),
            ("4.2 Bearing Replacement Safety Protocol",
             "Pre-work permit required. Isolate and lock out: main circuit breaker, "
             "hydraulic power unit, pitch control battery backup. Verify zero energy with "
             "multimeter before entry. Rotor lock pin must be inserted and tagged. "
             "Maximum allowable wind speed during work: 8 m/s."),
            ("4.3 Maintenance Window Scheduling",
             "Schedule maintenance when wind forecast <4 m/s (below cut-in threshold) "
             "to minimize generation loss. Preferred windows: 02:00–06:00 local time "
             "(historically lowest wind in most European sites). "
             "Coordinate with grid operator 48 hours in advance for planned outages >4 hours."),
        ]
    },
}

styles = getSampleStyleSheet()

for filename, content in MANUALS.items():
    pdf_path = MANUALS_DIR / f"{filename}.pdf"
    doc      = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                                  topMargin=2*cm, bottomMargin=2*cm,
                                  leftMargin=2.5*cm, rightMargin=2.5*cm)
    story = []
    
    # Title
    story.append(Paragraph(content["title"], styles["Title"]))
    story.append(Spacer(1, 0.5*cm))
    
    # Sections
    for heading, body in content["sections"]:
        story.append(Paragraph(heading, styles["Heading2"]))
        story.append(Spacer(1, 0.2*cm))
        for line in body.split("\n"):
            story.append(Paragraph(line.strip(), styles["BodyText"]))
            story.append(Spacer(1, 0.1*cm))
        story.append(Spacer(1, 0.3*cm))
    
    doc.build(story)
    
    # Also copy to rag_docs for indexing
    import shutil
    shutil.copy(pdf_path, RAG_DOCS_DIR / f"{filename}.pdf")
    print(f"✅ {filename}.pdf created")

print("\n✅ All synthetic data generated successfully!")
print(f"   Maintenance logs : data/synthetic/maintenance_logs.csv")
print(f"   PDF manuals      : data/synthetic/equipment_manuals/")
print(f"   RAG source docs  : data/rag_docs/")