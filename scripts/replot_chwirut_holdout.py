"""Presentation-only correction for the Chwirut holdout figure; data are read-only."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analyze_chwirut_holdout import chwirut_model, load_chwirut_data, split_holdout

ROOT = Path(__file__).resolve().parents[1]
summary_path = ROOT / "validation/chwirut-holdout.json"
summary = json.loads(summary_path.read_text(encoding="utf-8"))
x, y = load_chwirut_data(ROOT / "data/Chwirut2.dat", summary["data_sha256"])
train, holdout = split_holdout(x, 5.0)
grid = np.linspace(0.4, 6.2, 500)
parameters = summary["train_fit"]["parameters"]
full_parameters = summary["full_fit_certification"]["parameters"]
linear = summary["baselines"]["linear"]
metrics = summary["train_fit"]["metrics"]

fig, ax = plt.subplots(figsize=(10.5, 6.2), constrained_layout=True)
ax.scatter(x[train], y[train], s=36, color="#316c9b", label="Training observations (n=47)", zorder=3)
ax.scatter(x[holdout], y[holdout], s=58, color="#b44b4b", marker="s", label="Held-out high distance (n=7)", zorder=4)
ax.plot(grid, chwirut_model(grid, *parameters.values()), color="#20252b", lw=2.2, label="Three-parameter fit on training only")
ax.plot(grid, chwirut_model(grid, *full_parameters.values()), color="#487a52", lw=1.6, ls="--", label="Full-data NIST reproduction (not holdout evidence)")
ax.plot(grid, linear["slope"] * grid + linear["intercept"], color="#876a32", lw=1.5, ls=":", label="Linear training baseline")
ax.axvline(5.0, color="#777777", lw=1, ls="--")
ax.text(4.92, max(y) * 0.54, "Frozen split x = 5.0", rotation=90, va="center", ha="right", color="#555555")
ax.text(
    0.02, 0.03,
    f"Train RMSE = {metrics['train_rmse']:.4f}\nHoldout RMSE = {metrics['holdout_rmse']:.4f}\nLinear holdout RMSE = {linear['holdout_rmse']:.4f}",
    transform=ax.transAxes, fontsize=9, bbox={"facecolor": "white", "edgecolor": "#ccd4d8", "alpha": 0.92},
)
ax.set_title("NIST Chwirut2: preregistered high-distance extrapolation")
ax.set_xlabel("Metal distance x")
ax.set_ylabel("Ultrasonic response y")
ax.grid(alpha=0.2)
ax.legend(frameon=False, fontsize=8, loc="upper right")
figure = ROOT / "papers/04_真实数据留出/fig04_chwirut_holdout.png"
fig.savefig(figure, dpi=180)
print(figure)
