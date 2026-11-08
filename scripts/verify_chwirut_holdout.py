"""Independently recompute every prediction and metric in the Chwirut holdout output."""

import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_summary(path):
    path = Path(path)
    summary = json.loads(path.read_text(encoding="utf-8"))
    protocol = json.loads((ROOT / "validation/chwirut-holdout-protocol.json").read_text(encoding="utf-8"))
    if summary["protocol_sha256"] != sha256(ROOT / "validation/chwirut-holdout-protocol.json"):
        raise ValueError("Protocol hash mismatch")
    if summary["analysis_runner_sha256"] != sha256(ROOT / "scripts/analyze_chwirut_holdout.py"):
        raise ValueError("Analysis runner hash mismatch")
    rows = summary["predictions"]
    if len(rows) != 54:
        raise ValueError("Expected 54 predictions")
    x = np.array([row["x"] for row in rows], dtype=float)
    y = np.array([row["y"] for row in rows], dtype=float)
    train = np.array([row["split"] == "train" for row in rows])
    holdout = ~train
    train_parameters = summary["train_fit"]["parameters"]
    full_parameters = summary["full_fit_certification"]["parameters"]
    linear = summary["baselines"]["linear"]
    mean = summary["baselines"]["training_mean"]["value"]

    def model(params):
        return np.exp(-params["b1"] * x) / (params["b2"] + params["b3"] * x)

    expected = {
        "train_model_prediction": model(train_parameters),
        "full_model_prediction": model(full_parameters),
        "linear_prediction": linear["slope"] * x + linear["intercept"],
        "mean_prediction": np.full_like(x, mean),
    }
    prediction_errors = []
    for key, values in expected.items():
        stored = np.array([row[key] for row in rows])
        prediction_errors.append(float(np.max(np.abs(stored - values))))
    max_prediction_error = max(prediction_errors)
    if max_prediction_error > 1.0e-9:
        raise ValueError(f"Prediction mismatch: {max_prediction_error}")

    def rmse(mask, prediction):
        residual = y[mask] - prediction[mask]
        return float(np.sqrt(np.mean(residual ** 2)))

    metric_comparisons = {
        "train_rmse": (rmse(train, expected["train_model_prediction"]), summary["train_fit"]["metrics"]["train_rmse"]),
        "holdout_rmse": (rmse(holdout, expected["train_model_prediction"]), summary["train_fit"]["metrics"]["holdout_rmse"]),
        "linear_holdout_rmse": (rmse(holdout, expected["linear_prediction"]), summary["baselines"]["linear"]["holdout_rmse"]),
        "mean_holdout_rmse": (rmse(holdout, expected["mean_prediction"]), summary["baselines"]["training_mean"]["holdout_rmse"]),
    }
    metric_errors = {name: abs(actual - stored) for name, (actual, stored) in metric_comparisons.items()}
    max_metric_error = max(metric_errors.values())
    if max_metric_error > 1.0e-9:
        raise ValueError(f"Metric mismatch: {metric_errors}")
    train_rmse = metric_comparisons["train_rmse"][0]
    holdout_rmse = metric_comparisons["holdout_rmse"][0]
    linear_rmse = metric_comparisons["linear_holdout_rmse"][0]
    limited = holdout_rmse < 3 * train_rmse and holdout_rmse < linear_rmse
    if limited != summary["decision"]["limited_support"]:
        raise ValueError("Decision gate mismatch")
    if summary["decision"]["universal_law_claimed"] or summary["decision"]["parameter_endogeneity_proved"]:
        raise ValueError("Forbidden claim detected")
    return {
        "verification": "passed",
        "prediction_count": len(rows),
        "maximum_prediction_absolute_error": max_prediction_error,
        "maximum_metric_absolute_error": 0 if max_metric_error < 1.0e-9 else max_metric_error,
        "metric_error_tolerance": 1.0e-9,
        "decision_gate_recomputed": limited,
        "protocol_sha256": summary["protocol_sha256"],
        "summary_sha256": sha256(path),
        "verification_runner_sha256": sha256(Path(__file__).resolve()),
        "boundaries": summary["limitations"],
    }


def main():
    source = ROOT / "validation/chwirut-holdout.json"
    output = ROOT / "validation/chwirut-holdout-verification.json"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")
    result = verify_summary(source)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
