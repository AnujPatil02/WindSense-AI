# WindSense-AI
### LLM-Powered Multi-Agent Predictive Maintenance System
**Predictive Wind Intelligence — Industrial Manufacturing + Renewable Energy (Smart Grid)**

---

## 🏗️ Architecture
IoT Simulator + Digital Twin (Physics ODE + 3D R3F)

↓

MQTT (Mosquitto)

↓

InfluxDB (Time-Series)

↓

┌─────────────────────────────────┐

│     LangGraph Orchestrator      │

│  Agent1  Agent2  Agent3  Agent4 │

│  Health  RUL     Maint   Energy │

└─────────────────────────────────┘

↓              ↓

RAG (FAISS)    LLM (Ollama TinyLlama)

↓

Streamlit Dashboard (10 pages) + Grafana + 3D Digital Twin

---

## ⚡ Key Features

| Feature | Description |
|---|---|
| 4 AI Agents | Health Monitor, RUL Predictor, Maintenance Coordinator, Energy Forecaster |
| 3D Digital Twin | React Three Fiber + Drei + GSAP — immersive fleet visualization embedded in dashboard |
| Anomaly Detection | LSTM Autoencoder vs Isolation Forest (compared, F1-scored) |
| RUL Estimation | XGBoost vs LSTM with conformal prediction (90% CI) |
| RAG Knowledge Base | FAISS + Ollama — query equipment manuals in natural language |
| Causal RCA | DoWhy causal inference for root cause analysis |
| RL Scheduler | PPO-based optimal maintenance scheduling |
| XAI | SHAP explainability for anomaly and RUL models |
| MLOps | MLflow experiment tracking + Evidently AI drift detection |
| PDF Work Orders | Auto-generated maintenance work orders from Agent 3 |
| Elite Dashboard | 10-page NeoGrid-themed Streamlit UI with live IST clock, animated fleet map |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for 3D digital twin)
- Docker Desktop
- Ollama

### One-command launch
```bash
python start_windsense.py
```
This automatically starts Ollama, Docker services, RAG indexing, IoT pipeline, the agent pipeline, MLflow, and the Streamlit dashboard — then opens your browser.

### Manual setup (if preferred)

**1. Clone and install**
```bash
git clone https://github.com/yourusername/WindSense-AI
cd WindSense-AI
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

**2. Configure environment**
```bash
cp .env.example .env
# No API keys needed — uses Ollama locally
```

**3. Start Docker services**
```bash
docker-compose up -d
```

**4. Start Ollama**
```bash
ollama pull tinyllama
```

**5. Download datasets**
```bash
# Place NASA CMAPSS files in data/raw/cmapss/
# Place EDP Wind SCADA CSV in data/raw/edp_wind/
```

**6. Preprocess data**
```bash
python data/synthetic/generate_synthetic_data.py
```

**7. Train models**
```bash
python -m agents.agent1_health_monitor.lstm_autoencoder
python -m agents.agent1_health_monitor.isolation_forest
python -m agents.agent1_health_monitor.model_comparison
python -m agents.agent2_failure_predictor.xgboost_rul
python -m agents.agent2_failure_predictor.lstm_rul
python -m agents.agent2_failure_predictor.model_comparison
python -m agents.agent2_failure_predictor.uncertainty_estimator
python -m agents.agent3_maintenance_coordinator.rl_scheduler
python -m agents.agent4_energy_forecaster.prophet_forecast
python -m agents.agent4_energy_forecaster.lstm_forecast
```

**8. Build RAG index**
```bash
python -m rag.faiss_indexer
```

**9. Build 3D digital twin**
```bash
cd digital-twin
npm install
npm run build
cd ..
```

**10. Start IoT pipeline**
```bash
# Terminal 1
python -m iot.influxdb_writer
# Terminal 2
python -m iot.mqtt_publisher
```

**11. Launch dashboard**
```bash
streamlit run dashboard/streamlit_app.py
```

**12. Run full agent pipeline**
```bash
python -m graph.langgraph_orchestrator
```

---

## 📊 Dashboards

| URL | Tool | Purpose |
|---|---|---|
| http://localhost:8501 | Streamlit | Main AI dashboard (10 pages) |
| http://localhost:3000 | Grafana | Live sensor monitoring |
| http://localhost:5000 | MLflow | Experiment tracking |
| http://localhost:8086 | InfluxDB | Time-series database |

---

## 🧪 Run Tests
```bash
python tests/test_pipeline.py
```

---

## 📁 Project Structure
WindSense-AI/

├── iot/                        # Digital twin (physics) + MQTT + InfluxDB

├── agents/

│   ├── agent1_health_monitor/      # Anomaly detection (LSTM AE vs Isolation Forest)

│   ├── agent2_failure_predictor/   # RUL estimation (XGBoost vs LSTM)

│   ├── agent3_maintenance_coordinator/ # Scheduling + RL

│   └── agent4_energy_forecaster/   # Prophet + LSTM forecasting

├── graph/                      # LangGraph orchestrator

├── rag/                        # FAISS RAG pipeline

├── llm/                        # Ollama LLM engine + causal RCA

├── mlops/                      # MLflow + Evidently

├── dashboard/                  # Streamlit UI (10 pages) + Grafana

│   ├── page_modules/           # 10 dashboard pages

│   ├── ui/                     # theme, sidebar, topbar, components, animations

│   └── utils/                  # shared data_loader.py

├── digital-twin/               # 3D React Three Fiber visualization

│   ├── src/                    # scene, hud, bridge components

│   └── streamlit_integration/  # embed bridge for Streamlit

├── data/                       # Datasets + synthetic docs

├── notebooks/                  # Jupyter exploration

├── tests/                      # Integration tests

├── outputs/                    # Models + reports + work orders

└── start_windsense.py          # One-command auto-launcher

---

## 📦 Tech Stack
- **ML:** TensorFlow, XGBoost, Scikit-learn, Stable-Baselines3
- **LLM:** Ollama (TinyLlama) — fully local, no API
- **RAG:** FAISS + LangChain + sentence-transformers
- **Agents:** LangGraph multi-agent orchestration
- **IoT:** MQTT (Mosquitto) + InfluxDB + Physics-Informed Digital Twin
- **3D Visualization:** React Three Fiber + Drei + GSAP + vite-plugin-singlefile
- **Causal AI:** DoWhy
- **XAI:** SHAP
- **MLOps:** MLflow + Evidently AI
- **Dashboard:** Streamlit (custom NeoGrid theme) + Grafana
- **Containerization:** Docker Compose

---

## 📈 Model Performance

| Model | Metric | Value |
|---|---|---|
| Isolation Forest | F1 Score | ~0.82 |
| LSTM Autoencoder | F1 Score | ~0.79 |
| XGBoost RUL | RMSE | ~18.4h |
| LSTM RUL | RMSE | ~21.2h |
| Prophet Forecast | MAPE | ~8.2% |

---

## 🎯 Target Employers
**India:** Suzlon Energy, Adani Green, ReNew Power, Siemens India, ABB India, GE Vernova India
**Germany:** Siemens Energy, Vestas, Enercon, Nordex, Fraunhofer IWES

---

## 📚 Datasets
- [NASA CMAPSS](https://www.kaggle.com/datasets/behrad3d/nasa-cmapss)
- [EDP Wind Farm SCADA](https://www.kaggle.com/datasets/berkerisen/wind-turbine-scada-dataset)