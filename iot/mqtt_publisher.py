"""
WindSense-AI — MQTT Publisher
Publishes turbine sensor readings to Mosquitto broker.
Topic structure: windsense/turbine/{turbine_id}/sensors
"""

import json
import time
import os
from typing import Dict
from loguru import logger
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from iot.simulator import FleetSimulator

load_dotenv()

# ── MQTT Config ───────────────────────────────────────────────────────────────
BROKER_HOST    = os.getenv("MQTT_BROKER", "localhost")
BROKER_PORT    = int(os.getenv("MQTT_PORT", 1883))
TOPIC_PREFIX   = "windsense/turbine"
QOS            = 1       # At least once delivery
NUM_TURBINES   = 5


class WindSenseMQTTPublisher:
    """
    Connects to Mosquitto broker and publishes sensor readings.
    Each turbine publishes to its own topic.
    """

    def __init__(self, broker_host: str = BROKER_HOST,
                 broker_port: int = BROKER_PORT,
                 num_turbines: int = NUM_TURBINES):

        self.broker_host = broker_host
        self.broker_port = broker_port
        self.num_turbines = num_turbines
        self.publish_count = 0
        self.error_count   = 0

        # Setup MQTT client
        self.client = mqtt.Client(
            client_id="windsense_publisher",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.client.on_connect    = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish    = self._on_publish

        # Fleet simulator — callback will publish to MQTT
        self.fleet = FleetSimulator(
            num_turbines=num_turbines,
            on_reading=self.publish_reading
        )

    # ── MQTT Callbacks ────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.success(f"✅ Connected to MQTT broker: {self.broker_host}:{self.broker_port}")
            # Publish system status
            self.client.publish(
                f"{TOPIC_PREFIX}/system/status",
                json.dumps({"status": "online", "turbines": self.num_turbines}),
                qos=QOS, retain=True
            )
        else:
            logger.error(f"❌ MQTT connection failed: reason code {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.warning(f"⚠ MQTT disconnected: {reason_code}")

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        pass   # Silently track publish confirmations

    # ── Publish ───────────────────────────────────────────────────────────

    def publish_reading(self, reading: Dict):
        """
        Callback from FleetSimulator — publishes one reading to MQTT.
        Called from simulator thread.
        """
        if not self.client.is_connected():
            self.error_count += 1
            return

        turbine_id = reading["turbine_id"]
        topic      = f"{TOPIC_PREFIX}/{turbine_id}/sensors"
        payload    = json.dumps(reading, default=str)

        result = self.client.publish(topic, payload, qos=QOS)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            self.publish_count += 1
        else:
            self.error_count += 1
            logger.error(f"Publish failed for {turbine_id}: rc={result.rc}")

        # Also publish summary to aggregate topic every reading
        self._publish_summary(reading)

    def _publish_summary(self, reading: Dict):
        """Publish lightweight summary to aggregate topic."""
        summary = {
            "turbine_id"  : reading["turbine_id"],
            "timestamp"   : reading["timestamp"],
            "health_score": reading["health_score"],
            "power_kw"    : reading["power_kw"],
            "vibration"   : reading["vibration_mms"],
            "gearbox_temp": reading["gearbox_temp_c"],
            "bearing_wear": reading["bearing_wear"],
        }
        self.client.publish(
            f"{TOPIC_PREFIX}/{reading['turbine_id']}/summary",
            json.dumps(summary),
            qos=0   # Best effort for summaries
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def connect(self):
        """Connect to broker with retry logic."""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to MQTT broker (attempt {attempt+1}/{max_retries})...")
                self.client.connect(self.broker_host, self.broker_port, keepalive=60)
                self.client.loop_start()    # Start network loop in background thread
                time.sleep(1)              # Allow connection to establish
                if self.client.is_connected():
                    return True
            except Exception as e:
                logger.warning(f"Connection attempt {attempt+1} failed: {e}")
                time.sleep(3)

        logger.error("❌ Failed to connect to MQTT broker after all retries")
        return False

    def start(self):
        """Connect and start publishing."""
        if not self.connect():
            raise RuntimeError("Cannot start publisher — MQTT broker unreachable")
        self.fleet.start_all()
        logger.success(f"🚀 Publisher started — {self.num_turbines} turbines active")

    def stop(self):
        """Stop publishing and disconnect."""
        self.fleet.stop_all()
        self.client.publish(
            f"{TOPIC_PREFIX}/system/status",
            json.dumps({"status": "offline"}),
            qos=QOS, retain=True
        )
        self.client.loop_stop()
        self.client.disconnect()
        logger.info(
            f"⏹ Publisher stopped | "
            f"Published: {self.publish_count} | "
            f"Errors: {self.error_count}"
        )

    def inject_fault(self, turbine_id: str, fault_type: str):
        """Inject fault and publish fault event to MQTT."""
        self.fleet.inject_fault(turbine_id, fault_type)
        self.client.publish(
            f"{TOPIC_PREFIX}/{turbine_id}/fault_event",
            json.dumps({
                "turbine_id": turbine_id,
                "fault_type": fault_type,
                "severity"  : "HIGH"
            }),
            qos=QOS
        )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import signal

    publisher = WindSenseMQTTPublisher(num_turbines=NUM_TURBINES)

    def handle_shutdown(sig, frame):
        logger.info("Shutdown signal received...")
        publisher.stop()

    signal.signal(signal.SIGINT,  handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    publisher.start()

    logger.info("Publisher running. Press Ctrl+C to stop.")
    logger.info("Topics:")
    logger.info(f"  windsense/turbine/WT-XXX/sensors  — full readings")
    logger.info(f"  windsense/turbine/WT-XXX/summary  — lightweight summary")
    logger.info(f"  windsense/turbine/system/status   — system status")

    # Keep main thread alive
    try:
        while True:
            time.sleep(30)
            logger.info(
                f"📊 Status | Published: {publisher.publish_count} | "
                f"Errors: {publisher.error_count}"
            )
    except KeyboardInterrupt:
        pass