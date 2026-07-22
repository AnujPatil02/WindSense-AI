"""
WindSense-AI — Environment Verification
Checks all services and key imports.
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 55)
print("  WindSense-AI — Environment Verification")
print("=" * 55)

# ── 1. Python version check ──────────────────────────────
print(f"\n[1] Python version: {sys.version.split()[0]}", end="  ")
if sys.version_info >= (3, 10):
    print("✅")
else:
    print("❌  Need Python 3.10+")

# ── 2. Core library imports ──────────────────────────────
print("\n[2] Core libraries:")
core_libs = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("scikit-learn", "sklearn"),
    ("tensorflow", "tensorflow"),
    ("torch", "torch"),
    ("xgboost", "xgboost"),
    ("shap", "shap"),
    ("langchain", "langchain"),
    ("faiss-cpu", "faiss"),
    ("langgraph", "langgraph"),
    ("mlflow", "mlflow"),
    ("evidently", "evidently"),
    ("streamlit", "streamlit"),
    ("prophet", "prophet"),
    ("paho-mqtt", "paho.mqtt.client"),
    ("influxdb-client", "influxdb_client"),
    ("reportlab", "reportlab"),
    ("dowhy", "dowhy"),
    ("flwr", "flwr"),
    ("mapie", "mapie"),
    ("stable-baselines3", "stable_baselines3"),
]

all_ok = True
for display_name, import_name in core_libs:
    try:
        __import__(import_name)
        print(f"   ✅  {display_name}")
    except ImportError:
        print(f"   ❌  {display_name}  ← pip install {display_name}")
        all_ok = False

# ── 3. Docker services check ────────────────────────────
print("\n[3] Docker services (HTTP checks):")
import httpx

services = {
    "InfluxDB": "http://localhost:8086/ping",
    "Grafana":  "http://localhost:3000",
    "MLflow":   "http://localhost:5000",
}

for name, url in services.items():
    try:
        r = httpx.get(url, timeout=3)
        status = "✅" if r.status_code < 400 else "⚠️"
        print(f"   {status}  {name}  ({url})")
    except Exception:
        print(f"   ❌  {name} not reachable — run: docker-compose up -d")

# ── 4. MQTT broker check ────────────────────────────────
print("\n[4] MQTT broker:")
try:
    import paho.mqtt.client as mqtt
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    result = client.connect(
        os.getenv("MQTT_BROKER", "localhost"),
        int(os.getenv("MQTT_PORT", 1883)),
        keepalive=5
    )
    client.disconnect()
    print("   ✅  Mosquitto MQTT broker reachable")
except Exception as e:
    print(f"   ❌  MQTT not reachable: {e}")

# ── 5. Env variables check ──────────────────────────────
print("\n[5] Environment variables:")
required_env = [
    "INFLUXDB_TOKEN", "INFLUXDB_URL", "INFLUXDB_ORG",
    "INFLUXDB_BUCKET", "GEMINI_API_KEY", "MLFLOW_TRACKING_URI"
]
for var in required_env:
    val = os.getenv(var)
    if val and val != f"your_{var.lower()}_here":
        print(f"   ✅  {var}")
    else:
        print(f"   ⚠️   {var} — set in .env file")

# ── Summary ─────────────────────────────────────────────
print("\n" + "=" * 55)
if all_ok:
    print("  ✅  All libraries OK — ready for Step 2!")
else:
    print("  ⚠️   Fix missing libraries above, then re-run.")
print("=" * 55)