"""
WindSense-AI Project Structure Setup
Run this once to create all folders.
"""

import os

# All directories to create
directories = [
    "config",
    "data/raw/cmapss",
    "data/raw/edp_wind",
    "data/processed",
    "data/synthetic/equipment_manuals",
    "data/rag_docs",
    "iot",
    "agents/agent1_health_monitor",
    "agents/agent2_failure_predictor",
    "agents/agent3_maintenance_coordinator",
    "agents/agent4_energy_forecaster",
    "graph",
    "rag",
    "llm",
    "mlops",
    "federated",
    "gnn",
    "dashboard/pages",
    "dashboard/grafana",
    "notebooks",
    "tests",
    "outputs/models",
    "outputs/reports",
    "outputs/work_orders",
    "outputs/decision_logs",
    ".github/workflows",
]

# Create all directories
for directory in directories:
    os.makedirs(directory, exist_ok=True)
    # Add __init__.py to Python package directories
    if not directory.startswith(("data", "config", "notebooks", 
                                  "outputs", ".github", "dashboard/grafana")):
        init_file = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f"# WindSense-AI — {directory}\n")

print("✅ All directories created successfully!")
print("\nProject structure:")
for root, dirs, files in os.walk("."):
    # Skip hidden dirs and __pycache__
    dirs[:] = [d for d in dirs if not d.startswith(('.', '__'))]
    level = root.replace(".", "").count(os.sep)
    indent = "  " * level
    print(f"{indent}{os.path.basename(root)}/")