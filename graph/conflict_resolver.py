"""Conflict Resolver — safety-first agent decision arbitration."""
from loguru import logger


def resolve(anomaly_msg: dict, rul_msg: dict,
            rl_action: dict, rule_action: dict) -> dict:

    priority_rank = {
        "IMMEDIATE_SHUTDOWN_AND_REPAIR": 0,
        "IMMEDIATE_SHUTDOWN"           : 0,
        "SCHEDULE_WITHIN_48H"          : 1,
        "REDUCE_LOAD_50PCT"            : 1,
        "SCHEDULE_WITHIN_7_DAYS"       : 2,
        "DERATE_TO_75PCT"              : 2,
        "MONITOR"                      : 3,
        "MONITOR_AND_LOG"              : 3,
        "NORMAL_OPERATION"             : 4,
    }

    rule_str = rule_action.get("action", "MONITOR_AND_LOG")
    rl_str   = rl_action.get("action",   "MONITOR_AND_LOG")
    rule_rank = priority_rank.get(rule_str, 3)
    rl_rank   = priority_rank.get(rl_str,   3)

    if rule_rank <= rl_rank:
        chosen, chosen_by = rule_str, "rule_based"
        reason = "Rule-based took more conservative action"
    else:
        chosen, chosen_by = rl_str, "rl_agent"
        reason = "RL agent recommended more urgent intervention"

    # Safety override — use POINT ESTIMATE only, not lower_bound
    rul_point = float(rul_msg.get("rul_hours", 999))
    if rul_point < 5:   # only truly critical
        chosen    = "IMMEDIATE_SHUTDOWN_AND_REPAIR"
        chosen_by = "safety_override"
        reason    = f"RUL critically low ({rul_point:.1f}h) — safety override"

    result = {
        "final_action"  : chosen,
        "chosen_by"     : chosen_by,
        "rule_suggested": rule_str,
        "rl_suggested"  : rl_str,
        "reason"        : reason,
        "rul_lower_h"   : rul_msg.get("lower_hours", 0),
        "rul_hours"     : rul_point,
    }
    logger.info(f"Conflict resolved: {chosen} (by {chosen_by})")
    return result