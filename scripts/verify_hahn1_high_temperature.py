"""Independently recompute every Hahn1 prediction, metric and denominator audit."""

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
    protocol = json.loads((ROOT / "validation/hahn1-high-temperature-protocol.json").read_text(encoding="utf-8"))
    if summary["protocol_sha256"] != sha256(ROOT / "validation/hahn1-high-temperature-protocol.json"):
        raise ValueError("Protocol hash mismatch")
    if summary["analysis_runner_sha256"] != sha256(ROOT / "scripts/analyze_hahn1_high_temperature.py"):
        raise ValueError("Analysis runner hash mismatch")
    rows = summary["predictions"]
    if len(rows) != 236:
        raise ValueError("Expected 236 predictions")
    x = np.array([row["x"] for row in rows], dtype=float)
    y = np.array([row["y"] for row in rows], dtype=float)
    train = np.array([row["split"] == "train" for row in rows])
    holdout = ~train
    train_parameters = summary["train_fit"]["parameters"]
    full_parameters = summary["full_fit_certification"]["parameters"]
    linear = summary["baselines"]["linear"]
    cubic = summary["baselines"]["cubic_polynomial"]["coefficients_descending"]
    mean = summary["baselines"]["training_mean"]["value"]

    def model(params):
        return (
            params["b1"] + params["b2"] * x + params["b3"] * x ** 2 + params["b4"] * x ** 3
        ) / (1 + params["b5"] * x + params["b6"] * x ** 2 + params["b7"] * x ** 3)

    expected = {
        "train_model_prediction": model(train_parameters),
        "full_model_prediction": model(full_parameters),
        "linear_prediction": linear["slope"] * x + linear["intercept"],
        "cubic_prediction": np.polyval(cubic, x),
        "mean_prediction": np.full_like(x, mean),
    }
    prediction_errors = []
    for key, values in expected.items():
        stored = np.array([row[key] for row in rows])
        prediction_errors.append(float(np.max(np.abs(stored - values))))
    max_prediction_error = max(prediction_errors)
    if max_prediction_error > 1.0e-10:
        raise ValueError(f"Prediction mismatch: {max_prediction_error}")

    def rmse(mask, prediction):
        residual = y[mask] - prediction[mask]
        return float(np.sqrt(np.mean(residual ** 2)))

    comparisons = {
        "train_rmse": (rmse(train, expected["train_model_prediction"]), summary["train_fit"]["metrics"]["train_rmse"]),
        "holdout_rmse": (rmse(holdout, expected["train_model_prediction"]), summary["train_fit"]["metrics"]["holdout_rmse"]),
        "linear_holdout_rmse": (rmse(holdout, expected["linear_prediction"]), summary["baselines"]["linear"]["holdout_rmse"]),
        "cubic_holdout_rmse": (rmse(holdout, expected["cubic_prediction"]), summary["baselines"]["cubic_polynomial"]["holdout_rmse"]),
        "mean_holdout_rmse": (rmse(holdout, expected["mean_prediction"]), summary["baselines"]["training_mean"]["holdout_rmse"]),
    }
    metric_errors = {name: abs(actual - stored) for name, (actual, stored) in comparisons.items()}
    max_metric_error = max(metric_errors.values())
    if max_metric_error > 1.0e-10:
        raise ValueError(f"Metric mismatch: {metric_errors}")
    train_rmse = comparisons["train_rmse"][0]
    holdout_rmse = comparisons["holdout_rmse"][0]
    cubic_rmse = comparisons["cubic_holdout_rmse"][0]
    limited = holdout_rmse < 3 * train_rmse and holdout_rmse < cubic_rmse
    if limited != summary["decision"]["limited_support"]:
        raise ValueError("Decision gate mismatch")
    if summary["decision"]["universal_law_claimed"] or summary["decision"]["parameter_endogeneity_proved"]:
        raise ValueError("Forbidden claim detected")

    for label, parameters in [("train_model", train_parameters), ("full_model", full_parameters)]:
        grid = np.linspace(0, 900, 9001)
        denominator = 1 + parameters["b5"] * grid + parameters["b6"] * grid ** 2 + parameters["b7"] * grid ** 3
        stored = summary["denominator_audit"][label]
        if abs(stored["minimum_on_0_to_900"] - float(np.min(denominator))) > 1.0e-9:
            raise ValueError(f"Denominator minimum mismatch for {label}")
        if abs(stored["maximum_on_0_to_900"] - float(np.max(denominator))) > 1.0e-9:
            raise ValueError(f"Denominator maximum mismatch for {label}")
        roots = np.roots([parameters["b7"], parameters["b6"], parameters["b5"], 1.0])
        real_within = sorted(float(root.real) for root in roots if abs(root.imag) < 1.0e-8 and 0 <= root.real <= 900)
        if real_within != stored["real_roots_within_0_to_900"]:
            raise ValueError(f"Denominator roots mismatch for {label}")
        if (not real_within) == stored["has_real_singularity_within_experimental_range"]:
            raise ValueError(f"Denominator singularity flag mismatch for {label}")
    return {
        "verification": "passed",
        "prediction_count": len(rows),
        "maximum_prediction_absolute_error": max_prediction_error,
        "maximum_metric_absolute_error": 0 if max_metric_error < 1.0e-10 else max_metric_error,
        "metric_error_tolerance": 1.0e-10,
        "decision_gate_recomputed": limited,
        "denominator_audits_recomputed": True,
        "protocol_sha256": summary["protocol_sha256"],
        "summary_sha256": sha256(path),
        "verification_runner_sha256": sha256(Path(__file__).resolve()),
        "boundaries": summary["limitations"],
    }


def main():
    source = ROOT / "validation/hahn1-high-temperature.json"
    output = ROOT / "validation/hahn1-high-temperature-verification.json"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")
    result = verify_summary(source)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
