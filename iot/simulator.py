"""
WindSense-AI — SCADA Sensor Stream Simulator
Combines Digital Twin physics model with real CMAPSS/Wind dataset patterns.
Simulates multiple turbines in parallel.
"""

import numpy as np
import pandas as pd
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Callable, Optional
from loguru import logger

from iot.digital_twin import DigitalTwin


# ── Configuration ─────────────────────────────────────────────────────────────

PROCESSED_DIR   = Path("data/processed")
NUM_TURBINES    = 5          # Number of turbines to simulate
PUBLISH_INTERVAL = 5.0       # Seconds between readings per turbine
DT_HOURS        = PUBLISH_INTERVAL / 3600.0   # Time step in hours


class WindSpeedModel:
    """
    Generates realistic wind speed time-series using AR(2) model.
    Based on statistical properties of EDP Wind Farm SCADA data.
    """

    def __init__(self, mean_speed: float = 8.0, std_speed: float = 3.0,
                 seed: int = 42):
        self.mean  = mean_speed
        self.std   = std_speed
        self.rng   = np.random.default_rng(seed)
        self.v1    = mean_speed    # Previous wind speed
        self.v2    = mean_speed    # Wind speed before that
        # AR(2) coefficients (fitted to match real wind statistics)
        self.phi1  = 0.95
        self.phi2  = -0.05

    def next(self) -> float:
        """Generate next wind speed using AR(2) model."""
        noise  = self.rng.normal(0, self.std * 0.05)
        v_new  = (self.mean * (1 - self.phi1 - self.phi2)
                  + self.phi1 * self.v1
                  + self.phi2 * self.v2
                  + noise)
        v_new  = float(np.clip(v_new, 0.0, 30.0))
        self.v2 = self.v1
        self.v1 = v_new
        return round(v_new, 2)


class CMAPSSReplayStream:
    """
    Replays real NASA CMAPSS sensor patterns to augment digital twin output.
    Maps CMAPSS sensors to turbine sensor names.
    """

    CMAPSS_TO_TURBINE = {
        "sensor_2" : "lpt_outlet_temp",
        "sensor_3" : "hpt_coolant_bleed",
        "sensor_4" : "lpt_outlet_pressure",
        "sensor_7" : "bypass_ratio",
        "sensor_8" : "htbleed",
        "sensor_11": "hpT_efficiency",
        "sensor_12": "lpT_efficiency",
        "sensor_15": "w31",
        "sensor_17": "w32",
        "sensor_20": "bpr",
        "sensor_21": "nf",
    }

    def __init__(self, unit_id: int = 1):
        self.unit_id = unit_id
        self.df      = None
        self.idx     = 0
        self._load()

    def _load(self):
        csv_path = PROCESSED_DIR / "train_cmapss_processed.csv"
        if csv_path.exists():
            full_df   = pd.read_csv(csv_path)
            self.df   = full_df[full_df["unit_id"] == self.unit_id].reset_index(drop=True)
            logger.info(f"CMAPSS replay: unit {self.unit_id} — {len(self.df)} cycles")
        else:
            logger.warning("CMAPSS processed CSV not found — using zeros for auxiliary sensors")

    def next_row(self) -> Dict:
        """Return next row of CMAPSS data, cycling when exhausted."""
        if self.df is None or len(self.df) == 0:
            return {}

        row = self.df.iloc[self.idx % len(self.df)]
        self.idx += 1

        result = {}
        for cmapss_col, turbine_col in self.CMAPSS_TO_TURBINE.items():
            if cmapss_col in row.index:
                result[turbine_col] = round(float(row[cmapss_col]), 4)

        result["cmapss_rul"]    = float(row.get("RUL", 125))
        result["cmapss_anomaly"] = int(row.get("anomaly", 0))
        return result


class TurbineSimulator:
    """
    Simulates a single turbine — combines Digital Twin + CMAPSS replay.
    Runs in its own thread.
    """

    def __init__(self, turbine_id: str,
                 age_hours: float = 0.0,
                 degradation_rate: float = 1.0,
                 cmapss_unit: int = 1,
                 on_reading: Optional[Callable] = None):
        """
        Args:
            turbine_id       : e.g. 'WT-001'
            age_hours        : Starting degradation age
            degradation_rate : >1 degrades faster (useful for demo)
            cmapss_unit      : Which CMAPSS engine unit to replay
            on_reading       : Callback function called with each reading dict
        """
        self.turbine_id   = turbine_id
        self.twin         = DigitalTwin(turbine_id, age_hours, degradation_rate)
        self.wind_model   = WindSpeedModel(
            mean_speed=np.random.uniform(6.0, 10.0),
            seed=hash(turbine_id) % 2**31
        )
        self.cmapss       = CMAPSSReplayStream(unit_id=cmapss_unit)
        self.on_reading   = on_reading
        self._stop_event  = threading.Event()
        self._thread      = None
        self.reading_count = 0

    def _generate_reading(self) -> Dict:
        """Generate one complete sensor reading."""
        # Step degradation forward
        self.twin.update_degradation(dt_hours=DT_HOURS)

        # Get wind speed
        wind_speed   = self.wind_model.next()
        ambient_temp = np.random.uniform(20.0, 35.0)   # °C — Mumbai climate

        # Get physics-based readings from digital twin
        physics_reading = self.twin.get_sensor_reading(
            wind_speed=wind_speed,
            ambient_temp=ambient_temp,
            dt_seconds=PUBLISH_INTERVAL
        )

        # Get CMAPSS auxiliary sensor readings
        cmapss_reading = self.cmapss.next_row()

        # Merge all readings
        reading = {
            **physics_reading,
            **cmapss_reading,
            "timestamp"     : datetime.now(timezone.utc).isoformat(),
            "reading_number": self.reading_count,
        }

        self.reading_count += 1
        return reading

    def _run(self):
        """Thread loop — generate and publish readings."""
        logger.info(f"▶ Simulator started: {self.turbine_id}")
        while not self._stop_event.is_set():
            try:
                reading = self._generate_reading()

                # Log key stats every 10 readings
                if self.reading_count % 10 == 0:
                    logger.info(
                        f"{self.turbine_id} | "
                        f"Wind: {reading['wind_speed_ms']:5.1f} m/s | "
                        f"Power: {reading['power_kw']:7.1f} kW | "
                        f"Vibration: {reading['vibration_mms']:5.2f} mm/s | "
                        f"Health: {reading['health_score']:.3f}"
                    )

                # Call callback (e.g., MQTT publisher)
                if self.on_reading:
                    self.on_reading(reading)

            except Exception as e:
                logger.error(f"Error in {self.turbine_id}: {e}")

            self._stop_event.wait(timeout=PUBLISH_INTERVAL)

        logger.info(f"⏹ Simulator stopped: {self.turbine_id}")

    def start(self):
        """Start simulator in background thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop simulator."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)

    def inject_fault(self, fault_type: str = "bearing_wear"):
        """Inject fault into this turbine's digital twin."""
        self.twin.inject_fault(fault_type)


class FleetSimulator:
    """
    Manages simulation of multiple turbines simultaneously.
    Main entry point for the IoT layer.
    """

    def __init__(self, num_turbines: int = NUM_TURBINES,
                 on_reading: Optional[Callable] = None):
        self.simulators: List[TurbineSimulator] = []
        self.on_reading = on_reading

        # Create turbines with varying ages for realistic diversity
        ages = np.linspace(0, 5000, num_turbines)
        rates = np.linspace(1.0, 3.0, num_turbines)   # Later turbines degrade faster

        for i in range(num_turbines):
            turbine_id = f"WT-{str(i+1).zfill(3)}"
            sim = TurbineSimulator(
                turbine_id=turbine_id,
                age_hours=float(ages[i]),
                degradation_rate=float(rates[i]),
                cmapss_unit=(i % 100) + 1,     # Cycle through CMAPSS units
                on_reading=on_reading,
            )
            self.simulators.append(sim)
            logger.info(
                f"Initialized {turbine_id} | "
                f"Age: {ages[i]:.0f}h | "
                f"Degradation rate: {rates[i]:.1f}x"
            )

    def start_all(self):
        """Start all turbine simulators."""
        logger.info(f"🚀 Starting fleet of {len(self.simulators)} turbines...")
        for sim in self.simulators:
            sim.start()
            time.sleep(0.2)   # Stagger starts slightly

    def stop_all(self):
        """Stop all turbine simulators."""
        logger.info("⏹ Stopping all turbines...")
        for sim in self.simulators:
            sim.stop()

    def inject_fault(self, turbine_id: str, fault_type: str):
        """Inject fault into a specific turbine by ID."""
        for sim in self.simulators:
            if sim.turbine_id == turbine_id:
                sim.inject_fault(fault_type)
                return
        logger.warning(f"Turbine {turbine_id} not found")

    def get_status(self) -> List[Dict]:
        """Return current degradation state of all turbines."""
        return [sim.twin.get_state_dict() for sim in self.simulators]


# ── Standalone test (no MQTT) ───────────────────────────────────────────────
if __name__ == "__main__":
    import json

    readings_log = []

    def print_reading(reading: Dict):
        readings_log.append(reading)
        print(
            f"[{reading['turbine_id']}] "
            f"Wind: {reading['wind_speed_ms']:5.1f} m/s | "
            f"Power: {reading['power_kw']:7.1f} kW | "
            f"Vibration: {reading['vibration_mms']:.3f} mm/s | "
            f"Health: {reading['health_score']:.3f} | "
            f"Gearbox: {reading['gearbox_temp_c']:.1f}°C"
        )

    fleet = FleetSimulator(num_turbines=3, on_reading=print_reading)
    fleet.start_all()

    print("\n=== Fleet running for 30 seconds ===")
    print("Press Ctrl+C to stop\n")

    try:
        # Inject a fault on WT-002 after 10 seconds
        time.sleep(10)
        print("\n⚡ Injecting bearing fault on WT-002...\n")
        fleet.inject_fault("WT-002", "bearing_wear")
        time.sleep(20)
    except KeyboardInterrupt:
        pass
    finally:
        fleet.stop_all()
        print(f"\nTotal readings captured: {len(readings_log)}")