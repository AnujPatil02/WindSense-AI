"""
WindSense-AI — InfluxDB Writer
Subscribes to MQTT and writes all sensor readings to InfluxDB.
"""

import json
import os
import time
import signal
from datetime import datetime, timezone
from typing import Dict
from loguru import logger
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

load_dotenv()

# ── InfluxDB Config ────────────────────────────────────────────────────────────
INFLUX_URL    = os.getenv("INFLUXDB_URL",    "http://localhost:8086")
INFLUX_TOKEN  = os.getenv("INFLUXDB_TOKEN",  "")
INFLUX_ORG    = os.getenv("INFLUXDB_ORG",    "windsense")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET", "sensor_data")

# ── MQTT Config ────────────────────────────────────────────────────────────────
BROKER_HOST   = os.getenv("MQTT_BROKER", "localhost")
BROKER_PORT   = int(os.getenv("MQTT_PORT", 1883))
SUBSCRIBE_TOPIC = "windsense/turbine/+/sensors"   # + = wildcard for turbine_id


class InfluxDBWriter:
    """
    Subscribes to MQTT sensor topic and writes readings to InfluxDB.
    Uses batch writing for efficiency.
    """

    # Fields that are numeric measurements (written as fields in InfluxDB)
    NUMERIC_FIELDS = [
        "wind_speed_ms", "power_kw", "rotor_rpm", "generator_rpm",
        "gearbox_temp_c", "vibration_mms", "oil_pressure_bar",
        "ambient_temp_c", "bearing_wear", "oil_quality",
        "rotor_imbalance", "health_score", "age_hours",
        "cmapss_rul", "reading_number",
        "lpt_outlet_temp", "hpt_coolant_bleed", "lpt_outlet_pressure",
        "bypass_ratio", "htbleed", "hpT_efficiency", "lpT_efficiency",
    ]

    # Tags (indexed metadata in InfluxDB — use for filtering)
    TAG_FIELDS = ["turbine_id"]

    def __init__(self):
        self.write_count  = 0
        self.error_count  = 0
        self._running     = False

        # InfluxDB client
        self.influx_client = InfluxDBClient(
            url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG
        )
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        logger.info(f"InfluxDB client initialized: {INFLUX_URL}")

        # MQTT client
        self.mqtt_client = mqtt.Client(
            client_id="windsense_influx_writer",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.mqtt_client.on_connect    = self._on_connect
        self.mqtt_client.on_message    = self._on_message
        self.mqtt_client.on_disconnect = self._on_disconnect

    # ── MQTT Callbacks ─────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.success(f"✅ MQTT connected — subscribing to {SUBSCRIBE_TOPIC}")
            client.subscribe(SUBSCRIBE_TOPIC, qos=1)
        else:
            logger.error(f"❌ MQTT connect failed: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.warning(f"⚠ MQTT disconnected: {reason_code}")
        # Auto-reconnect
        if self._running:
            time.sleep(5)
            try:
                client.reconnect()
            except Exception as e:
                logger.error(f"Reconnect failed: {e}")

    def _on_message(self, client, userdata, msg):
        """Called for every incoming MQTT message."""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            self._write_to_influx(payload)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Message processing error: {e}")

    # ── InfluxDB Write ─────────────────────────────────────────────────────

    def _write_to_influx(self, reading: Dict):
        """Convert a reading dict to InfluxDB Point and write."""
        try:
            # Parse timestamp
            ts_str = reading.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
            except Exception:
                ts = datetime.now(timezone.utc)

            # ── Sensor readings point ─────────────────────────────────────
            point = Point("turbine_sensors") \
                .tag("turbine_id", reading.get("turbine_id", "unknown"))

            # Write all numeric fields
            for field in self.NUMERIC_FIELDS:
                if field in reading and reading[field] is not None:
                    try:
                        point = point.field(field, float(reading[field]))
                    except (ValueError, TypeError):
                        pass

            point = point.time(ts, WritePrecision.NS)
            self.write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

            # ── Health score point (separate measurement for alerting) ────
            health_point = Point("turbine_health") \
                .tag("turbine_id", reading.get("turbine_id", "unknown")) \
                .field("health_score",  float(reading.get("health_score", 1.0))) \
                .field("bearing_wear",  float(reading.get("bearing_wear", 0.0))) \
                .field("oil_quality",   float(reading.get("oil_quality", 1.0))) \
                .field("anomaly_flag",  int(reading.get("cmapss_anomaly", 0))) \
                .time(ts, WritePrecision.NS)

            self.write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=health_point)

            self.write_count += 1

            if self.write_count % 50 == 0:
                logger.info(
                    f"✍ Written {self.write_count} readings to InfluxDB | "
                    f"Last: {reading.get('turbine_id')} | "
                    f"Health: {reading.get('health_score', 'N/A')}"
                )

        except Exception as e:
            self.error_count += 1
            logger.error(f"InfluxDB write error: {e}")

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def verify_influx_connection(self) -> bool:
        """Ping InfluxDB to verify connectivity."""
        try:
            health = self.influx_client.health()
            if health.status == "pass":
                logger.success(f"✅ InfluxDB healthy: {INFLUX_URL}")
                return True
            else:
                logger.error(f"❌ InfluxDB unhealthy: {health.status}")
                return False
        except Exception as e:
            logger.error(f"❌ InfluxDB connection failed: {e}")
            return False

    def start(self):
        """Start MQTT subscription and begin writing to InfluxDB."""
        if not self.verify_influx_connection():
            raise RuntimeError("InfluxDB not reachable — check Docker container")

        max_retries = 5
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to MQTT (attempt {attempt+1})...")
                self.mqtt_client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
                break
            except Exception as e:
                logger.warning(f"MQTT connect failed: {e}")
                time.sleep(3)
        else:
            raise RuntimeError("Cannot connect to MQTT broker")

        self._running = True
        logger.success("🚀 InfluxDB Writer started")
        logger.info(f"   Subscribing to : {SUBSCRIBE_TOPIC}")
        logger.info(f"   Writing to     : {INFLUX_URL} / {INFLUX_BUCKET}")

        # Blocking loop
        self.mqtt_client.loop_forever()

    def stop(self):
        """Stop writer cleanly."""
        self._running = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        self.write_api.close()
        self.influx_client.close()
        logger.info(
            f"⏹ Writer stopped | "
            f"Written: {self.write_count} | "
            f"Errors: {self.error_count}"
        )


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    writer = InfluxDBWriter()

    def handle_shutdown(sig, frame):
        logger.info("Shutdown signal received...")
        writer.stop()

    signal.signal(signal.SIGINT,  handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    writer.start()