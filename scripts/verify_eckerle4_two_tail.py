"""Independently recompute every Eckerle4 two-tail prediction and metric."""

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
    protocol = json.loads((ROOT / "validation/eckerle4-two-tail-protocol.json").read_text(encoding="utf-8"))
    if summary["protocol_sha256"] != sha256(ROOT / "validation/eckerle4-two-tail-protocol.json"):
        raise ValueError("Protocol hash mismatch")
    if summary["analysis_runner_sha256"] != sha256(ROOT / "scripts/analyze_eckerle4_two_tail.py"):
        raise ValueError("Analysis runner hash mismatch")
    rows = summary["predictions"]
    if len(rows) != 35:
        raise ValueError("Expected 35 predictions")
    x = np.array([row["x"] for row in rows], dtype=float)
    y = np.array([row["y"] for row in rows], dtype=float)
    low = np.array([row["split"] == "low" for row in rows])
    high = np.array([row["split"] == "high" for row in rows])
    middle = ~(low | high)
    middle_parameters = summary["middle_fit"]["parameters"]
    full_parameters = summary["full_fit_certification"]["parameters"]
    linear = summary["baselines"]["linear"]
    mean = summary["baselines"]["training_mean"]["value"]

    def model(params):
        return (params["b1"] / params["b2"]) * np.exp(-0.5 * ((x - params["b3"]) / params["b2"]) ** 2)

    expected = {
        "middle_model_prediction": model(middle_parameters),
        "full_model_prediction": model(full_parameters),
        "linear_prediction": linear["slope"] * x + linear["intercept"],
        "mean_prediction": np.full_like(x, mean),
    }
    prediction_errors = []
    for key, values in expected.items():
        stored = np.array([row[key] for row in rows])
        prediction_errors.append(float(np.max(np.abs(stored - values))))
    max_prediction_error = max(prediction_errors)
    if max_prediction_error > 1.0e-12:
        raise ValueError(f"Prediction mismatch: {max_prediction_error}")

    def rmse(mask, prediction):
        residual = y[mask] - prediction[mask]
        return float(np.sqrt(np.mean(residual ** 2)))

    comparisons = {
        "middle_rmse": (rmse(middle, expected["middle_model_prediction"]), summary["middle_fit"]["metrics"]["middle_rmse"]),
        "low_rmse": (rmse(low, expected["middle_model_prediction"]), summary["middle_fit"]["metrics"]["low_rmse"]),
        "high_rmse": (rmse(high, expected["middle_model_prediction"]), summary["middle_fit"]["metrics"]["high_rmse"]),
        "holdout_rmse": (rmse(low | high, expected["middle_model_prediction"]), summary["middle_fit"]["metrics"]["holdout_rmse"]),
        "linear_low_rmse": (rmse(low, expected["linear_prediction"]), summary["baselines"]["linear"]["low_rmse"]),
        "linear_high_rmse": (rmse(high, expected["linear_prediction"]), summary["baselines"]["linear"]["high_rmse"]),
        "linear_holdout_rmse": (rmse(low | high, expected["linear_prediction"]), summary["baselines"]["linear"]["holdout_rmse"]),
        "mean_holdout_rmse": (rmse(low | high, expected["mean_prediction"]), summary["baselines"]["training_mean"]["holdout_rmse"]),
    }
    metric_errors = {name: abs(actual - stored) for name, (actual, stored) in comparisons.items()}
    max_metric_error = max(metric_errors.values())
    if max_metric_error > 1.0e-12:
        raise ValueError(f"Metric mismatch: {metric_errors}")
    middle_rmse = comparisons["middle_rmse"][0]
    holdout_rmse = comparisons["holdout_rmse"][0]
    linear_holdout = comparisons["linear_holdout_rmse"][0]
    limited = (
        holdout_rmse < 3 * middle_rmse
        and holdout_rmse < linear_holdout
        and comparisons["low_rmse"][0] < comparisons["linear_low_rmse"][0]
        and comparisons["high_rmse"][0] < comparisons["linear_high_rmse"][0]
    )
    if limited != summary["decision"]["limited_support"]:
        raise ValueError("Decision gate mismatch")
    if summary["decision"]["universal_law_claimed"] or summary["decision"]["parameter_endogeneity_proved"]:
        raise ValueError("Forbidden claim detected")
    return {
        "verification": "passed",
        "prediction_count": len(rows),
        "maximum_prediction_absolute_error": max_prediction_error,
        "maximum_metric_absolute_error": 0 if max_metric_error < 1.0e-12 else max_metric_error,
        "metric_error_tolerance": 1.0e-12,
        "decision_gate_recomputed": limited,
        "protocol_sha256": summary["protocol_sha256"],
        "summary_sha256": sha256(path),
        "verification_runner_sha256": sha256(Path(__file__).resolve()),
        "boundaries": summary["limitations"],
    }


def main():
    source = ROOT / "validation/eckerle4-two-tail.json"
    output = ROOT / "validation/eckerle4-two-tail-verification.json"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")
    result = verify_summary(source)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
