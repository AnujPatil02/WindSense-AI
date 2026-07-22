"""Inter-Agent Message Schema — LangGraph"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class SensorReading:
    turbine_id     : str
    timestamp      : str
    wind_speed_ms  : float
    power_kw       : float
    vibration_mms  : float
    gearbox_temp_c : float
    bearing_wear   : float
    oil_quality    : float
    health_score   : float
    cmapss_rul     : float = 125.0
    anomaly_score  : float = 0.0


@dataclass
class AnomalyMessage:
    turbine_id     : str
    anomaly_flag   : int
    anomaly_score  : float
    primary_cause  : str
    top_sensors    : List[Dict]
    shap_top       : Dict      = field(default_factory=dict)
    timestamp      : str       = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class RULMessage:
    turbine_id     : str
    rul_hours      : float
    lower_hours    : float
    upper_hours    : float
    model_used     : str
    timestamp      : str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class MaintenanceDecision:
    turbine_id          : str
    priority            : str
    action              : str
    scheduled_start     : str
    scheduled_end       : str
    assigned_crew       : str
    recommended_load_pct: int
    revenue_loss_usd    : float
    reasoning           : str
    llm_explanation     : str  = ""
    work_order_path     : str  = ""
    timestamp           : str  = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class AgentState:
    """Shared state passed between agents in LangGraph."""
    readings    : List[SensorReading]   = field(default_factory=list)
    anomalies   : List[AnomalyMessage]  = field(default_factory=list)
    rul_results : List[RULMessage]      = field(default_factory=list)
    decisions   : List[MaintenanceDecision] = field(default_factory=list)
    forecast_72h: List[float]           = field(default_factory=list)
    causal_report: Dict                 = field(default_factory=dict)
    errors      : List[str]             = field(default_factory=list)
    run_id      : str                   = field(default_factory=lambda: datetime.utcnow().strftime("%Y%m%d_%H%M%S"))

    def to_dict(self):
        return asdict(self)