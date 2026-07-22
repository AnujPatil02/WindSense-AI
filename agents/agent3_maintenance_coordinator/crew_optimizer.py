"""Crew Dispatch Optimizer — Agent 3"""

from datetime import datetime
from typing import List, Dict
from loguru import logger

CREWS = [
    {"id": "CREW_A", "skills": ["bearing","gearbox","electrical"], "available": True},
    {"id": "CREW_B", "skills": ["rotor","hydraulics","pitch","gearbox"], "available": True},
    {"id": "CREW_C", "skills": ["bearing","rotor","gearbox","electrical"], "available": True},
]

FAULT_SKILL_MAP = {
    "sensor_2" : "gearbox",
    "sensor_7" : "gearbox",
    "sensor_11": "electrical",
    "sensor_4" : "hydraulics",
    "sensor_3" : "bearing",
    "sensor_15": "rotor",
    "sensor_20": "gearbox",
    "sensor_9" : "bearing",
    "sensor_14": "electrical",
    "default"  : "gearbox",
}


def assign_crews(decisions: List[Dict]) -> List[Dict]:
    """Assign crew to each decision — always assign, never leave PENDING."""
    # Track crew end times
    crew_end_times = {c["id"]: None for c in CREWS}

    # Sort by priority first
    priority_order = {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3}
    sorted_decisions = sorted(
        decisions,
        key=lambda x: priority_order.get(x.get("priority","LOW"), 3)
    )

    for decision in sorted_decisions:
        if decision.get("priority") == "LOW":
            # Still assign a crew for LOW
            pass

        required_skill = FAULT_SKILL_MAP.get(
            decision.get("primary_cause","default"),
            FAULT_SKILL_MAP["default"]
        )

        sched_start = decision.get("scheduled_start","")

        # Find best available crew with required skill
        best_crew = None
        for crew in CREWS:
            cid = crew["id"]
            # Check if crew is free
            is_free = (
                crew_end_times[cid] is None or
                crew_end_times[cid] <= sched_start
            )
            if is_free and required_skill in crew["skills"]:
                best_crew = cid
                break

        # Fallback 1: any crew with skill, ignore timing
        if not best_crew:
            for crew in CREWS:
                if required_skill in crew["skills"]:
                    best_crew = crew["id"]
                    break

        # Fallback 2: least busy crew (always assign someone)
        if not best_crew:
            best_crew = min(CREWS, key=lambda c: crew_end_times[c["id"]] or "")["id"]

        decision["assigned_crew"]  = best_crew
        decision["required_skill"] = required_skill
        crew_end_times[best_crew]  = decision.get("scheduled_end", sched_start)

    return decisions


def get_crew_schedule(decisions: List[Dict]) -> Dict:
    schedule = {c["id"]: [] for c in CREWS}
    for d in decisions:
        crew = d.get("assigned_crew","CREW_A")
        if crew in schedule:
            schedule[crew].append({
                "turbine" : d["turbine_id"],
                "priority": d["priority"],
                "start"   : d["scheduled_start"],
                "end"     : d["scheduled_end"],
            })
    return schedule


if __name__ == "__main__":
    sample = [
        {"turbine_id": f"WT-00{i}", "priority": p,
         "primary_cause": "sensor_7",
         "scheduled_start": "2024-01-01T06:00:00",
         "scheduled_end"  : "2024-01-01T12:00:00"}
        for i, p in enumerate(["CRITICAL","HIGH","HIGH","MEDIUM","LOW"], 1)
    ]
    result = assign_crews(sample)
    for r in result:
        print(f"{r['turbine_id']} → {r['assigned_crew']}")