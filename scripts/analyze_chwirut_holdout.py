"""Preregistered high-distance holdout analysis for the NIST Chwirut2 data."""

import hashlib
import json
import re
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit


ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_chwirut_data(path, expected_sha256=None):
    path = Path(path)
    if expected_sha256 is not None and sha256(path) != expected_sha256:
        raise ValueError(f"Raw data hash mismatch: {path}")
    x, y = [], []
    pattern = re.compile(r"^\s*(?:\d+\.\d*|\.\d+)(?:E[+-]?\d+)?\s+(?:\d+\.\d*|\.\d+)(?:E[+-]?\d+)?\s*$", re.I)
    for line in path.read_text(encoding="ascii").splitlines():
        if not pattern.match(line):
            continue
        response, predictor = line.split()
        y.append(float(response))
        x.append(float(predictor))
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size != 54 or y.size != 54 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Chwirut2 must contain exactly 54 finite observations")
    return x, y


def split_holdout(x, threshold):
    x = np.asarray(x, dtype=float)
    holdout = x >= float(threshold)
    return ~holdout, holdout


def chwirut_model(x, b1, b2, b3):
    return np.exp(-b1 * np.asarray(x, dtype=float)) / (b2 + b3 * np.asarray(x, dtype=float))


def fit_linear(x, y):
    slope, intercept = np.polyfit(np.asarray(x, dtype=float), np.asarray(y, dtype=float), 1)
    return float(slope), float(intercept)


def fit_chwirut(x, y, starts):
    best = None
    attempts = []
    for index, start in enumerate(starts):
        initial = [start["b1"], start["b2"], start["b3"]]
        try:
            parameters, covariance, info, message, ier = curve_fit(
                chwirut_model, x, y, p0=initial, bounds=(0, np.inf), max_nfev=50000,
                full_output=True,
            )
            residuals = y - chwirut_model(x, *parameters)
            rss = float(residuals @ residuals)
            record = {
                "start": initial,
                "parameters": dict(zip(("b1", "b2", "b3"), map(float, parameters))),
                "rss": rss,
                "success": bool(ier > 0 and np.isfinite(parameters).all()),
                "ier": int(ier),
                "message": str(message),
                "nfev": int(info["nfev"]),
                "covariance": np.asarray(covariance).tolist(),
            }
        except Exception as error:
            record = {"start": initial, "success": False, "error": str(error)}
        attempts.append(record)
        if record["success"] and (best is None or record["rss"] < best["rss"]):
            best = record
    if best is None:
        raise RuntimeError(f"All Chwirut fits failed: {attempts}")
    return best, attempts


def error_metrics(y, prediction):
    residual = np.asarray(y) - np.asarray(prediction)
    return {
        "rmse": float(np.sqrt(np.mean(residual ** 2))),
        "mae": float(np.mean(np.abs(residual))),
        "max_absolute_residual": float(np.max(np.abs(residual))),
    }


def analyze(data_path, protocol_path):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_any_nonlinear_fit":
        raise ValueError("Chwirut protocol is not frozen")
    x, y = load_chwirut_data(data_path, protocol["data"]["sha256"])
    train, holdout = split_holdout(x, protocol["holdout_rule"]["definition"].split("x >= ")[1].split()[0])
    if (int(train.sum()), int(holdout.sum())) != (47, 7):
        raise ValueError("Frozen holdout counts changed")

    full_best, full_attempts = fit_chwirut(x, y, protocol["model"]["starts"])
    full_parameters = full_best["parameters"]
    full_residual = y - chwirut_model(x, *full_parameters.values())
    full_rsd = float(np.sqrt(full_residual @ full_residual / (len(x) - 3)))
    certified = protocol["full_fit_certification_rule"]
    relative_parameter_errors = {
        name: abs(full_parameters[name] / certified["certified_parameters"][name] - 1)
        for name in ("b1", "b2", "b3")
    }
    relative_rsd_error = abs(full_rsd / certified["certified_residual_standard_deviation"] - 1)
    certification = {
        "parameters": full_parameters,
        "residual_standard_deviation": full_rsd,
        "residual_sum_of_squares": full_best["rss"],
        "relative_parameter_errors": relative_parameter_errors,
        "relative_residual_standard_deviation_error": relative_rsd_error,
        "matches_nist_within_frozen_tolerances": bool(
            max(relative_parameter_errors.values()) <= certified["relative_tolerance_parameters"]
            and relative_rsd_error <= certified["relative_tolerance_residual_standard_deviation"]
        ),
        "attempts": full_attempts,
        "interpretation": "Known-answer reproduction of the published NIST fit, not our independent ultrasonic experiment",
    }

    train_best, train_attempts = fit_chwirut(x[train], y[train], protocol["model"]["starts"])
    train_parameters = train_best["parameters"]
    train_prediction = chwirut_model(x, *train_parameters.values())
    full_prediction = chwirut_model(x, *full_parameters.values())
    slope, intercept = fit_linear(x[train], y[train])
    linear_prediction = slope * x + intercept
    mean_response = float(np.mean(y[train]))
    mean_prediction = np.full_like(x, mean_response)
    train_metrics = error_metrics(y[train], train_prediction[train])
    holdout_metrics = error_metrics(y[holdout], train_prediction[holdout])
    linear_train = error_metrics(y[train], linear_prediction[train])
    linear_holdout = error_metrics(y[holdout], linear_prediction[holdout])
    mean_holdout = error_metrics(y[holdout], mean_prediction[holdout])
    ratio = holdout_metrics["rmse"] / train_metrics["rmse"]
    limited = bool(holdout_metrics["rmse"] < 3 * train_metrics["rmse"] and holdout_metrics["rmse"] < linear_holdout["rmse"])

    predictions = [
        {
            "index": index + 1,
            "x": float(x[index]),
            "y": float(y[index]),
            "split": "holdout" if holdout[index] else "train",
            "train_model_prediction": float(train_prediction[index]),
            "full_model_prediction": float(full_prediction[index]),
            "linear_prediction": float(linear_prediction[index]),
            "mean_prediction": float(mean_prediction[index]),
            "train_model_residual": float(y[index] - train_prediction[index]),
        }
        for index in range(len(x))
    ]
    return {
        "status": "computed_preregistered_real_data_holdout",
        "protocol_sha256": sha256(protocol_path),
        "data_sha256": protocol["data"]["sha256"],
        "model": protocol["model"]["equation"],
        "split": {"train_count": int(train.sum()), "holdout_count": int(holdout.sum()), "threshold_x": 5.0},
        "full_fit_certification": certification,
        "train_fit": {
            "parameters": train_parameters,
            "metrics": {
                "train_rmse": train_metrics["rmse"],
                "train_mae": train_metrics["mae"],
                "train_max_absolute_residual": train_metrics["max_absolute_residual"],
                "holdout_rmse": holdout_metrics["rmse"],
                "holdout_mae": holdout_metrics["mae"],
                "holdout_max_absolute_residual": holdout_metrics["max_absolute_residual"],
                "holdout_to_train_rmse_ratio": ratio,
            },
            "attempts": train_attempts,
        },
        "baselines": {
            "linear": {"slope": slope, "intercept": intercept, "train_rmse": linear_train["rmse"], "holdout_rmse": linear_holdout["rmse"]},
            "training_mean": {"value": mean_response, "holdout_rmse": mean_holdout["rmse"]},
        },
        "decision": {
            "limited_support": limited,
            "negative_for_this_extrapolation": not limited,
            "universal_law_claimed": False,
            "parameter_endogeneity_proved": False,
            "gate": protocol["decision_gate"]["limited_support"],
        },
        "predictions": predictions,
        "limitations": [
            "One contiguous high-distance split on one NIST dataset; not random cross-validation or a universal model-family test",
            "No independent ultrasonic measurements, measurement-covariance estimate or new physical mechanism was produced",
            "NIST certified values are used only for known-answer reproduction, never as holdout evidence",
            "The seven holdout observations were not used for fitting, start selection, model selection or threshold retuning",
        ],
    }


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data_path = ROOT / "data/Chwirut2.dat"
    protocol_path = ROOT / "validation/chwirut-holdout-protocol.json"
    output_path = ROOT / "validation/chwirut-holdout.json"
    figure_path = ROOT / "papers/04_真实数据留出/fig04_chwirut_holdout.png"
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite: {output_path}")
    if figure_path.exists():
        raise FileExistsError(f"Refusing to overwrite: {figure_path}")
    summary = analyze(data_path, protocol_path)
    summary["analysis_runner_sha256"] = sha256(Path(__file__).resolve())
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    x, y = load_chwirut_data(data_path, summary["data_sha256"])
    train, holdout = split_holdout(x, 5.0)
    grid = np.linspace(0.4, 6.2, 500)
    parameters = summary["train_fit"]["parameters"]
    full_parameters = summary["full_fit_certification"]["parameters"]
    linear = summary["baselines"]["linear"]
    fig, ax = plt.subplots(figsize=(10.5, 6.2), constrained_layout=True)
    ax.scatter(x[train], y[train], s=36, color="#316c9b", label="Training observations (n=47)", zorder=3)
    ax.scatter(x[holdout], y[holdout], s=58, color="#b44b4b", marker="s", label="Held-out high distance (n=7)", zorder=4)
    ax.plot(grid, chwirut_model(grid, *parameters.values()), color="#20252b", lw=2.2, label="Three-parameter fit on training only")
    ax.plot(grid, chwirut_model(grid, *full_parameters.values()), color="#487a52", lw=1.6, ls="--", label="Full-data NIST reproduction (not holdout evidence)")
    ax.plot(grid, linear["slope"] * grid + linear["intercept"], color="#876a32", lw=1.5, ls=":", label="Linear training baseline")
    ax.axvline(5.0, color="#777777", lw=1, ls="--")
    ax.text(5.04, max(y) * 0.92, "Frozen split x = 5.0", color="#555555")
    metrics = summary["train_fit"]["metrics"]
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
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180)
    print(json.dumps({
        "output": str(output_path),
        "figure": str(figure_path),
        "train_metrics": metrics,
        "baselines": summary["baselines"],
        "decision": summary["decision"],
        "nist_reproduction": summary["full_fit_certification"]["matches_nist_within_frozen_tolerances"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
