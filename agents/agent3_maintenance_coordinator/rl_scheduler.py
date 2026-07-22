"""
RL-based Maintenance Scheduler using PPO (Stable-Baselines3) — Agent 3
Learns optimal scheduling by maximizing reward = energy saved - maintenance cost.
"""

import numpy as np
import json
from pathlib import Path
from typing import Optional
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback
from loguru import logger

MODELS_DIR = Path("outputs/models")
REPORTS    = Path("outputs/reports")


class MaintenanceEnv(gym.Env):
    """
    Custom Gym environment for turbine maintenance scheduling.
    
    State : [rul_normalized, anomaly_score, bearing_wear,
              oil_quality, load_pct, hours_since_maintenance]
    Action: 0=Monitor, 1=Reduce load 50%, 2=Schedule soon, 3=Immediate shutdown
    Reward: Energy revenue - maintenance cost - failure penalty
    """
    metadata = {"render_modes": []}

    # Cost constants (USD)
    REVENUE_PER_HOUR    = 150.0   # 2MW turbine at avg tariff
    MAINTENANCE_COST    = 5000.0  # Planned maintenance
    FAILURE_PENALTY     = 50000.0 # Unplanned failure cost
    MAX_RUL             = 125.0

    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(6,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(4)
        self._reset_state()

    def _reset_state(self):
        self.rul              = np.random.uniform(20, 125)
        self.anomaly_score    = np.random.uniform(0, 0.5)
        self.bearing_wear     = np.random.uniform(0, 0.4)
        self.oil_quality      = np.random.uniform(0.6, 1.0)
        self.load_pct         = 1.0
        self.hours_since_maint= np.random.uniform(0, 500)
        self.step_count       = 0

    def _get_obs(self) -> np.ndarray:
        return np.array([
            self.rul / self.MAX_RUL,
            self.anomaly_score,
            self.bearing_wear,
            1.0 - self.oil_quality,
            self.load_pct,
            min(self.hours_since_maint / 1000.0, 1.0),
        ], dtype=np.float32)

    def step(self, action: int):
        reward      = 0.0
        terminated  = False
        info        = {}

        # ── Action effects ────────────────────────────────────────────────
        if action == 0:   # Monitor — continue running
            energy_reward = self.REVENUE_PER_HOUR * self.load_pct
            reward        += energy_reward

        elif action == 1:  # Reduce load to 50%
            self.load_pct  = 0.5
            reward         += self.REVENUE_PER_HOUR * 0.5

        elif action == 2:  # Schedule planned maintenance
            reward         -= self.MAINTENANCE_COST * 0.5   # Planned = cheaper
            self.rul        = self.MAX_RUL                   # Reset after maintenance
            self.bearing_wear = 0.0
            self.oil_quality  = 1.0
            self.load_pct     = 1.0
            self.hours_since_maint = 0
            reward         += 2000.0   # Bonus for proactive action

        elif action == 3:  # Immediate shutdown
            reward         -= self.MAINTENANCE_COST
            self.rul        = self.MAX_RUL
            self.bearing_wear = 0.0
            self.oil_quality  = 1.0
            self.load_pct     = 1.0
            self.hours_since_maint = 0

        # ── Natural degradation ───────────────────────────────────────────
        deg_rate       = 0.5 + self.bearing_wear * 2.0
        self.rul      -= deg_rate
        self.bearing_wear = min(1.0, self.bearing_wear + 0.002)
        self.oil_quality  = max(0.0, self.oil_quality - 0.001)
        self.anomaly_score = max(0.0, min(1.0,
            self.anomaly_score + np.random.normal(0.005, 0.01)))
        self.hours_since_maint += 1
        self.step_count        += 1

        # ── Failure condition ─────────────────────────────────────────────
        if self.rul <= 0 or self.bearing_wear >= 1.0:
            reward    -= self.FAILURE_PENALTY
            terminated = True
            info["event"] = "FAILURE"

        # ── Bad action penalty ────────────────────────────────────────────
        # Penalize ignoring critical state
        if action == 0 and self.anomaly_score > 0.8 and self.rul < 20:
            reward -= 10000.0

        truncated = self.step_count >= 500
        return self._get_obs(), reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._reset_state()
        return self._get_obs(), {}


def train(total_timesteps: int = 200_000):
    MODELS_DIR.mkdir(exist_ok=True)

    # Vectorized env for faster training
    env      = make_vec_env(MaintenanceEnv, n_envs=4)
    eval_env = make_vec_env(MaintenanceEnv, n_envs=1)

    model = PPO(
        "MlpPolicy", env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        verbose=1,
        tensorboard_log=str(REPORTS / "ppo_tensorboard"),
    )

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(MODELS_DIR),
        log_path=str(REPORTS),
        eval_freq=10_000,
        n_eval_episodes=10,
        verbose=0,
    )

    logger.info(f"Training PPO for {total_timesteps:,} timesteps...")
    model.learn(total_timesteps=total_timesteps, callback=eval_callback)
    model.save(str(MODELS_DIR / "rl_scheduler_ppo"))

    logger.success("RL Scheduler (PPO) training complete.")
    return model


def predict(state: np.ndarray) -> dict:
    """
    Given environment state, return RL action + label.
    state: [rul_norm, anomaly_score, bearing_wear, oil_quality_inv, load_pct, maint_norm]
    """
    model = PPO.load(str(MODELS_DIR / "rl_scheduler_ppo"))
    action, _ = model.predict(state.astype(np.float32), deterministic=True)

    labels = {
        0: "MONITOR",
        1: "REDUCE_LOAD_50PCT",
        2: "SCHEDULE_PLANNED_MAINTENANCE",
        3: "IMMEDIATE_SHUTDOWN",
    }
    return {"action_id": int(action), "action": labels[int(action)]}


def state_from_reading(reading: dict) -> np.ndarray:
    """Convert live turbine reading to RL state vector."""
    return np.array([
        min(reading.get("cmapss_rul", 125) / 125.0, 1.0),
        float(reading.get("anomaly_score", 0.0)),
        float(reading.get("bearing_wear", 0.0)),
        1.0 - float(reading.get("oil_quality", 1.0)),
        float(reading.get("recommended_load_pct", 100)) / 100.0,
        min(float(reading.get("age_hours", 0)) / 1000.0, 1.0),
    ], dtype=np.float32)


if __name__ == "__main__":
    train(total_timesteps=100_000)

    # Quick test
    env   = MaintenanceEnv()
    obs, _= env.reset()
    model = PPO.load(str(MODELS_DIR / "rl_scheduler_ppo"))

    print("\n=== RL Scheduler Test (10 steps) ===")
    for step in range(10):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        labels = ["MONITOR", "REDUCE_LOAD", "SCHEDULE", "SHUTDOWN"]
        print(f"Step {step+1:2d} | Action: {labels[action]:15s} | "
              f"RUL: {obs[0]*125:.1f}h | Reward: {reward:8.1f}")
        if terminated:
            print("  → Turbine failure!")
            obs, _ = env.reset()