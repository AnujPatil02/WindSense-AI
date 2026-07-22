"""WindSense-AI — Auto Launcher"""

import subprocess
import time
import sys
import os
import webbrowser
from pathlib import Path

BASE   = Path(__file__).parent
PYTHON = sys.executable


def run_bg(cmd, name):
    Path("outputs").mkdir(exist_ok=True)
    log = open(BASE / f"outputs/{name}.log", "w")
    p   = subprocess.Popen(cmd, stdout=log, stderr=log, cwd=str(BASE))
    print(f"  ✅ {name} started (PID {p.pid})")
    return p


def run_fg(cmd, name, ignore_error=False):
    print(f"  ⏳ {name}...")
    r = subprocess.run(cmd, cwd=str(BASE),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok = r.returncode == 0
    print(f"  {'✅' if ok else ('⚠️' if ignore_error else '❌')} {name}")
    return ok


def wait_for(url, name, timeout=30):
    import urllib.request
    print(f"  ⏳ Waiting for {name}", end="", flush=True)
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=2)
            print(" ✅")
            return True
        except Exception:
            print(".", end="", flush=True)
            time.sleep(1)
    print(" ⚠️ timeout")
    return False


def ensure_ollama():
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        print("  ✅ Ollama already running")
        return
    except Exception:
        pass
    print("  ⏳ Starting Ollama...")
    try:
        kw = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if sys.platform == "win32":
            kw["creationflags"] = subprocess.CREATE_NO_WINDOW
        subprocess.Popen(["ollama", "serve"], **kw)
        time.sleep(4)
        print("  ✅ Ollama started")
    except Exception as e:
        print(f"  ⚠️ Ollama: {e}")


def main():
    processes = []

    print("\n" + "═"*52)
    print("  WindSense-AI  |  Predictive Wind Intelligence")
    print("Auto-Starting...")
    print("═"*52 + "\n")

    # 1. Ollama
    print("▸ [1/7] Ollama LLM...")
    ensure_ollama()

    # 2. Docker services
    print("\n▸ [2/7] Docker services (InfluxDB, Grafana, MQTT)...")
    subprocess.run(["docker-compose", "up", "-d"], cwd=str(BASE),
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_for("http://localhost:8086/ping", "InfluxDB", 30)

    # 3. RAG Index
    print("\n▸ [3/7] RAG Knowledge Base...")
    faiss_index = BASE / "outputs/models/faiss_index.bin"
    if faiss_index.exists():
        print("  ✅ FAISS index exists — skipping rebuild")
    else:
        print("  ⏳ Building FAISS index (first run only)...")
        run_fg([PYTHON, "-m", "rag.faiss_indexer"], "FAISS Indexer")

    # 4. IoT Pipeline
    print("\n▸ [4/7] IoT Sensor Pipeline...")
    p1 = run_bg([PYTHON, "-m", "iot.influxdb_writer"], "influxdb_writer")
    processes.append(p1)
    time.sleep(2)
    p2 = run_bg([PYTHON, "-m", "iot.mqtt_publisher"], "mqtt_publisher")
    processes.append(p2)
    time.sleep(2)

    # 5. Agent Pipeline
    print("\n▸ [5/7] LangGraph Agent Pipeline...")
    run_fg([PYTHON, "-m", "graph.langgraph_orchestrator"],
           "LangGraph Pipeline", ignore_error=True)

    # 6. MLflow
    print("\n▸ [6/7] MLflow...")
    # Replace the MLflow section with:
    mlruns_abs = (BASE / "mlruns").absolute()
    mlruns_uri = mlruns_abs.as_uri()  # converts to file:///D:/Anuj/WindSense-AI/mlruns

    run_fg([PYTHON, "-m", "mlops.mlflow_tracker"], "MLflow Logger", ignore_error=True)

    p3 = run_bg(
    [PYTHON, "-m", "mlflow", "ui",
     "--backend-store-uri", mlruns_uri,
     "--host", "127.0.0.1",
     "--port", "5001"],
    "mlflow_ui",
    )

    # 7. Streamlit Dashboard
    print("\n▸ [7/7] Launching WindSense Dashboard...")
    p4 = run_bg(
        [PYTHON, "-m", "streamlit", "run",
         "dashboard/streamlit_app.py",
         "--server.port", "8501",
         "--server.headless", "true",
         "--server.runOnSave", "false",
         "--browser.gatherUsageStats", "false"],
        "streamlit"
    )
    processes.append(p4)
    wait_for("http://localhost:8501", "Streamlit", 30)

    # Open browser
    webbrowser.open("http://localhost:8501")
    time.sleep(0.5)

    print("\n" + "═"*52)
    print("  ✅ WindSense-AI — All Systems Active")
    print("═"*52)
    print(f"  🖥️  Dashboard  → http://localhost:8501")
    print(f"  📊  MLflow     → http://localhost:5001")
    print(f"  📡  Grafana    → http://localhost:3000")
    print(f"  🗄️  InfluxDB   → http://localhost:8086")
    print(f"  🤖  Ollama     → http://localhost:11434")
    print(f"\n  Logs → outputs/*.log")
    print(f"  📌  Ctrl+C to stop all services\n")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n  ⏹ Shutting down WindSense-AI...")
        for p in processes:
            try: p.terminate()
            except Exception: pass
        subprocess.run(["docker-compose", "down"], cwd=str(BASE),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("  ✅ All services stopped.\n")


if __name__ == "__main__":
    main()