"""
WindSense-AI — Digital Twin
Physics-informed turbine model using ODE simulation.
Simulates realistic sensor degradation over time.
"""

import numpy as np
from scipy.integrate import solve_ivp
from dataclasses import dataclass, field
from typing import Dict
import json
from pathlib import Path


@dataclass
class TurbineState:
    """Represents the current physical state of one turbine."""
    turbine_id: str
    age_hours: float = 0.0           # Operating hours since last overhaul
    bearing_wear: float = 0.0        # 0.0 (new) → 1.0 (failed)
    gear_oil_quality: float = 1.0    # 1.0 (clean) → 0.0 (degraded)
    rotor_imbalance: float = 0.0     # 0.0 (balanced) → 1.0 (severe)
    temperature_bias: float = 0.0    # Additional heat from degradation (°C)
    fault_injected: bool = False      # Whether a fault has been injected


class DigitalTwin:
    """
    Physics-informed digital twin for a wind turbine.
    
    Uses simplified ODE model to simulate:
    - Bearing degradation dynamics
    - Thermal behavior under load
    - Vibration response to mechanical wear
    - Power curve derating under fault conditions
    """

    # ── Turbine nameplate parameters ─────────────────────────────────────
    RATED_POWER_KW     = 2000.0    # 2 MW rated power
    CUT_IN_SPEED       = 3.0       # m/s — below this, turbine is idle
    RATED_SPEED        = 12.0      # m/s — above this, power is constant
    CUT_OUT_SPEED      = 25.0      # m/s — above this, turbine shuts down
    RATED_RPM          = 16.5      # Generator RPM at rated wind
    GEARBOX_RATIO      = 90.0      # Gearbox ratio (rotor→generator)
    ROTOR_RPM_RATED    = 16.5      # Rotor RPM at rated wind
    BEARING_LIFE_HOURS = 8760.0    # Expected bearing life (1 year)
    OIL_CHANGE_HOURS   = 4380.0    # Oil change interval (6 months)

    _INIT_STATE = {
        "WT-001": {"bearing_wear": 0.78, "gear_oil_quality": 0.42, "rotor_imbalance": 0.15},
        "WT-002": {"bearing_wear": 0.55, "gear_oil_quality": 0.61, "rotor_imbalance": 0.08},
        "WT-003": {"bearing_wear": 0.38, "gear_oil_quality": 0.75, "rotor_imbalance": 0.04},
        "WT-004": {"bearing_wear": 0.15, "gear_oil_quality": 0.88, "rotor_imbalance": 0.01},
        "WT-005": {"bearing_wear": 0.08, "gear_oil_quality": 0.95, "rotor_imbalance": 0.00},
    }

    def __init__(self, turbine_id: str, age_hours: float = 0.0,
                 degradation_rate: float = 1.0):
        """
        Args:
            turbine_id       : Unique ID e.g. 'WT-001'
            age_hours        : Starting age in operating hours
            degradation_rate : Multiplier — >1 degrades faster (for simulation)
        """
        self.state = TurbineState(
            turbine_id=turbine_id,
            age_hours=age_hours
        )
        
        self.degradation_rate = degradation_rate
        self.rng = np.random.default_rng(seed=hash(turbine_id) % 2**31)

        if turbine_id in self._INIT_STATE:
            s = self._INIT_STATE[turbine_id]
            self.state.bearing_wear      = s["bearing_wear"]
            self.state.gear_oil_quality  = s["gear_oil_quality"]
            self.state.rotor_imbalance   = s["rotor_imbalance"]
            self.state.temperature_bias  = (
                15.0 * self.state.bearing_wear +
                10.0 * (1.0 - self.state.gear_oil_quality)
            )

    # ── Physics: Power Curve ─────────────────────────────────────────────

    def power_from_wind(self, wind_speed: float) -> float:
    # CRITICAL turbine (bearing_wear > 0.75) → emergency stop
        if self.state.bearing_wear > 0.75:
            return 0.0
    # ... rest of existing code
        """
        Betz limit-based power curve with degradation derating.
        P = 0.5 * rho * A * Cp * v^3 (simplified as lookup curve)
        """
        if wind_speed < self.CUT_IN_SPEED or wind_speed > self.CUT_OUT_SPEED:
            return 0.0

        if wind_speed >= self.RATED_SPEED:
            power = self.RATED_POWER_KW
        else:
            # Cubic relationship between cut-in and rated
            ratio  = (wind_speed - self.CUT_IN_SPEED) / (self.RATED_SPEED - self.CUT_IN_SPEED)
            power  = self.RATED_POWER_KW * (ratio ** 3)

        # Derate power based on rotor imbalance and bearing wear
        derating = 1.0 - (0.15 * self.state.rotor_imbalance) \
                       - (0.10 * self.state.bearing_wear)
        return max(0.0, power * derating)

    def rotor_rpm(self, wind_speed: float) -> float:
        """Rotor RPM proportional to wind speed (below rated)."""
        if wind_speed < self.CUT_IN_SPEED:
            return 0.0
        rpm = self.ROTOR_RPM_RATED * min(wind_speed, self.RATED_SPEED) / self.RATED_SPEED
        # Add vibration from imbalance
        rpm_noise = self.rng.normal(0, 0.3 * (1 + self.state.rotor_imbalance))
        return max(0.0, rpm + rpm_noise)

    def generator_rpm(self, rotor_rpm: float) -> float:
        """Generator RPM = Rotor RPM × Gearbox ratio."""
        rpm_noise = self.rng.normal(0, 2.0 * (1 + self.state.bearing_wear))
        return max(0.0, rotor_rpm * self.GEARBOX_RATIO + rpm_noise)

    # ── Physics: Thermal ODE ─────────────────────────────────────────────

    def _thermal_ode(self, t, T, power_kw, ambient_temp):
        """
        dT/dt = (Q_gen - Q_loss) / thermal_mass
        Q_gen  = heat generated by losses (proportional to power)
        Q_loss = convective cooling (proportional to temp difference)
        """
        thermal_mass   = 5000.0    # J/°C — effective thermal mass
        loss_fraction  = 0.03      # 3% of power becomes heat
        cooling_coeff  = 150.0     # W/°C — convective cooling

        Q_generated = power_kw * 1000 * loss_fraction
        Q_lost      = cooling_coeff * (T - ambient_temp)

        # Degradation increases heat generation
        Q_degradation = 500.0 * self.state.bearing_wear \
                      + 300.0 * (1.0 - self.state.gear_oil_quality)

        dT_dt = (Q_generated + Q_degradation - Q_lost) / thermal_mass
        return dT_dt

    def gearbox_temperature(self, power_kw: float,
                             ambient_temp: float = 25.0,
                             dt_seconds: float = 10.0) -> float:
        """Simulate gearbox temperature using thermal ODE."""
        T0  = ambient_temp + 20.0 + self.state.temperature_bias
        sol = solve_ivp(
            self._thermal_ode,
            [0, dt_seconds],
            [T0],
            args=(power_kw, ambient_temp),
            method="RK45",
            dense_output=False
        )
        temp = float(sol.y[0, -1])
        noise = self.rng.normal(0, 0.5)
        return round(temp + noise, 2)

    # ── Physics: Vibration ───────────────────────────────────────────────

    def vibration_rms(self, rotor_rpm: float) -> float:
        """
        RMS vibration (mm/s).
        Increases with bearing wear and rotor imbalance.
        Baseline: 1.5 mm/s healthy. Critical: >7 mm/s.
        """
        baseline     = 1.5
        bearing_contrib  = 8.0  * self.state.bearing_wear ** 2
        imbalance_contrib = 4.0 * self.state.rotor_imbalance
        rpm_contrib  = 0.05 * (rotor_rpm / self.ROTOR_RPM_RATED)

        vibration = baseline + bearing_contrib + imbalance_contrib + rpm_contrib
        noise     = self.rng.normal(0, 0.2)
        return round(max(0.0, vibration + noise), 3)

    # ── Physics: Oil Pressure ─────────────────────────────────────────────

    def gear_oil_pressure(self) -> float:
        """
        Oil pressure in bar.
        Healthy: 3.5–4.5 bar. Degraded oil → pressure drop.
        """
        baseline = 4.0
        degradation_drop = 1.5 * (1.0 - self.state.gear_oil_quality)
        noise    = self.rng.normal(0, 0.05)
        return round(max(0.5, baseline - degradation_drop + noise), 3)

    # ── Degradation Update ───────────────────────────────────────────────

    def update_degradation(self, dt_hours: float = 1/6):
        """
        Update degradation state based on elapsed time.
        Called every simulation step.
        dt_hours: time elapsed in hours (default = 10 minutes)
        """
        dt = dt_hours * self.degradation_rate

        # Bearing wears linearly with time (accelerated near end of life)
        wear_rate = 1.0 / self.BEARING_LIFE_HOURS
        if self.state.bearing_wear > 0.7:
            wear_rate *= 3.0   # Accelerated wear in final stage
        self.state.bearing_wear = min(1.0,
            self.state.bearing_wear + wear_rate * dt)

        # Oil quality degrades over time
        oil_rate = 1.0 / self.OIL_CHANGE_HOURS
        self.state.gear_oil_quality = max(0.0,
            self.state.gear_oil_quality - oil_rate * dt)

        # Small random rotor imbalance accumulation
        if self.rng.random() < 0.001:   # 0.1% chance per step of imbalance event
            self.state.rotor_imbalance = min(1.0,
                self.state.rotor_imbalance + self.rng.uniform(0.01, 0.05))

        # Temperature bias from degradation
        self.state.temperature_bias = (
            15.0 * self.state.bearing_wear +
            10.0 * (1.0 - self.state.gear_oil_quality)
        )

        self.state.age_hours += dt_hours

    def inject_fault(self, fault_type: str = "bearing_wear"):
        """Instantly inject a fault for testing."""
        if fault_type == "bearing_wear":
            self.state.bearing_wear = min(1.0, self.state.bearing_wear + 0.4)
        elif fault_type == "oil_contamination":
            self.state.gear_oil_quality = max(0.0, self.state.gear_oil_quality - 0.5)
        elif fault_type == "rotor_imbalance":
            self.state.rotor_imbalance = min(1.0, self.state.rotor_imbalance + 0.3)
        self.state.fault_injected = True
        print(f"⚡ Fault injected [{fault_type}] on {self.state.turbine_id}")

    # ── Main: Generate Full Sensor Reading ──────────────────────────────

    def get_sensor_reading(self, wind_speed: float,
                            ambient_temp: float = 25.0,
                            dt_seconds: float = 10.0) -> Dict:
        """
        Generate one complete sensor reading snapshot.
        Returns a dict of all sensor values.
        """
        power_kw     = self.power_from_wind(wind_speed)
        rotor_rpm    = self.rotor_rpm(wind_speed)
        gen_rpm      = self.generator_rpm(rotor_rpm)
        gear_temp    = self.gearbox_temperature(power_kw, ambient_temp, dt_seconds)
        vibration    = self.vibration_rms(rotor_rpm)
        oil_pressure = self.gear_oil_pressure()

        # Derived health score (0=failed, 1=perfect)
        health_score = round(
            1.0
            - 0.5  * self.state.bearing_wear
            - 0.25 * (1.0 - self.state.gear_oil_quality)
            - 0.25 * self.state.rotor_imbalance,
            3
        )

        return {
            "turbine_id"      : self.state.turbine_id,
            "wind_speed_ms"   : round(wind_speed, 2),
            "power_kw"        : round(power_kw, 2),
            "rotor_rpm"       : round(rotor_rpm, 3),
            "generator_rpm"   : round(gen_rpm, 2),
            "gearbox_temp_c"  : gear_temp,
            "vibration_mms"   : vibration,
            "oil_pressure_bar": oil_pressure,
            "ambient_temp_c"  : round(ambient_temp + self.rng.normal(0, 0.3), 2),
            "bearing_wear"    : round(self.state.bearing_wear, 4),
            "oil_quality"     : round(self.state.gear_oil_quality, 4),
            "rotor_imbalance" : round(self.state.rotor_imbalance, 4),
            "health_score"    : health_score,
            "age_hours"       : round(self.state.age_hours, 2),
            "fault_injected"  : self.state.fault_injected,
        }

    def get_state_dict(self) -> Dict:
        """Return current degradation state as dict (for logging)."""
        return {
            "turbine_id"      : self.state.turbine_id,
            "age_hours"       : self.state.age_hours,
            "bearing_wear"    : self.state.bearing_wear,
            "gear_oil_quality": self.state.gear_oil_quality,
            "rotor_imbalance" : self.state.rotor_imbalance,
            "temperature_bias": self.state.temperature_bias,
            "fault_injected"  : self.state.fault_injected,
        }


# ── Quick test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    twin = DigitalTwin("WT-001", age_hours=1000, degradation_rate=2.0)

    print("=== Digital Twin Test ===")
    print("\n[Healthy state]")
    reading = twin.get_sensor_reading(wind_speed=10.0, ambient_temp=28.0)
    for k, v in reading.items():
        print(f"  {k:20s}: {v}")

    print("\n[Injecting bearing fault...]")
    twin.inject_fault("bearing_wear")
    reading = twin.get_sensor_reading(wind_speed=10.0, ambient_temp=28.0)
    print(f"  Vibration   : {reading['vibration_mms']} mm/s")
    print(f"  Health score: {reading['health_score']}")
    print(f"  Bearing wear: {reading['bearing_wear']}")