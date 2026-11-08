"""Preregistered two-tail extrapolation for the independent NIST Eckerle4 data."""

import json
import re
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

from analyze_chwirut_holdout import error_metrics, fit_linear, sha256

ROOT = Path(__file__).resolve().parents[1]


def load_eckerle_data(path, expected_sha256=None):
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
    if x.size != 35 or y.size != 35 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Eckerle4 must contain exactly 35 finite observations")
    return x, y


def split_two_tail(x):
    x = np.asarray(x, dtype=float)
    low = x <= 410
    high = x >= 480
    middle = ~(low | high)
    return low, middle, high


def eckerle_model(x, b1, b2, b3):
    return (b1 / b2) * np.exp(-0.5 * ((np.asarray(x, dtype=float) - b3) / b2) ** 2)


def fit_gaussian(x, y, protocol):
    best = None
    attempts = []
    bounds = protocol["model"]["bounds"]
    lower = [bounds["b1"][0], bounds["b2"][0], bounds["b3"][0]]
    upper = [bounds["b1"][1], bounds["b2"][1], bounds["b3"][1]]
    for start in protocol["model"]["starts"]:
        initial = [start["b1"], start["b2"], start["b3"]]
        try:
            parameters, covariance, info, message, ier = curve_fit(
                eckerle_model, x, y, p0=initial, bounds=(lower, upper),
                max_nfev=50000, full_output=True,
            )
            residuals = y - eckerle_model(x, *parameters)
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
        raise RuntimeError(f"All Gaussian fits failed: {attempts}")
    return best, attempts


def analyze(data_path, protocol_path):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_any_nonlinear_fit":
        raise ValueError("Eckerle4 protocol is not frozen")
    x, y = load_eckerle_data(data_path, protocol["data"]["sha256"])
    low, middle, high = split_two_tail(x)
    if (low.sum(), middle.sum(), high.sum()) != (3, 27, 5):
        raise ValueError("Frozen two-tail counts changed")

    full_best, full_attempts = fit_gaussian(x, y, protocol)
    full_parameters = full_best["parameters"]
    full_residual = y - eckerle_model(x, *full_parameters.values())
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
        "interpretation": "Known-answer reproduction of the published NIST fit, not our independent transmittance experiment",
    }

    middle_best, middle_attempts = fit_gaussian(x[middle], y[middle], protocol)
    middle_parameters = middle_best["parameters"]
    middle_prediction = eckerle_model(x, *middle_parameters.values())
    full_prediction = eckerle_model(x, *full_parameters.values())
    slope, intercept = fit_linear(x[middle], y[middle])
    linear_prediction = slope * x + intercept
    mean_response = float(np.mean(y[middle]))
    mean_prediction = np.full_like(x, mean_response)

    middle_metrics = error_metrics(y[middle], middle_prediction[middle])
    low_metrics = error_metrics(y[low], middle_prediction[low])
    high_metrics = error_metrics(y[high], middle_prediction[high])
    holdout_metrics = error_metrics(y[low | high], middle_prediction[low | high])
    linear_low = error_metrics(y[low], linear_prediction[low])
    linear_high = error_metrics(y[high], linear_prediction[high])
    linear_holdout = error_metrics(y[low | high], linear_prediction[low | high])
    mean_holdout = error_metrics(y[low | high], mean_prediction[low | high])
    limited = bool(
        holdout_metrics["rmse"] < 3 * middle_metrics["rmse"]
        and holdout_metrics["rmse"] < linear_holdout["rmse"]
        and low_metrics["rmse"] < linear_low["rmse"]
        and high_metrics["rmse"] < linear_high["rmse"]
    )
    predictions = [
        {
            "index": index + 1,
            "x": float(x[index]),
            "y": float(y[index]),
            "split": "low" if low[index] else "high" if high[index] else "middle",
            "middle_model_prediction": float(middle_prediction[index]),
            "full_model_prediction": float(full_prediction[index]),
            "linear_prediction": float(linear_prediction[index]),
            "mean_prediction": float(mean_prediction[index]),
            "middle_model_residual": float(y[index] - middle_prediction[index]),
        }
        for index in range(len(x))
    ]
    return {
        "status": "computed_preregistered_two_tail_real_data_extrapolation",
        "protocol_sha256": sha256(protocol_path),
        "data_sha256": protocol["data"]["sha256"],
        "model": protocol["model"]["equation"],
        "split": {"low_count": int(low.sum()), "middle_count": int(middle.sum()), "high_count": int(high.sum())},
        "full_fit_certification": certification,
        "middle_fit": {
            "parameters": middle_parameters,
            "metrics": {
                "middle_rmse": middle_metrics["rmse"],
                "low_rmse": low_metrics["rmse"],
                "high_rmse": high_metrics["rmse"],
                "holdout_rmse": holdout_metrics["rmse"],
                "holdout_mae": holdout_metrics["mae"],
                "holdout_max_absolute_residual": holdout_metrics["max_absolute_residual"],
            },
            "attempts": middle_attempts,
        },
        "baselines": {
            "linear": {"slope": slope, "intercept": intercept, "low_rmse": linear_low["rmse"], "high_rmse": linear_high["rmse"], "holdout_rmse": linear_holdout["rmse"]},
            "training_mean": {"value": mean_response, "holdout_rmse": mean_holdout["rmse"]},
        },
        "decision": {
            "limited_support": limited,
            "negative_for_this_two_tail_task": not limited,
            "universal_law_claimed": False,
            "parameter_endogeneity_proved": False,
            "gate": protocol["decision_gate"]["limited_support"],
        },
        "predictions": predictions,
        "limitations": [
            "One two-tail split on one independent NIST dataset; not random cross-validation or a universal Gaussian-family test",
            "No independent transmittance measurements, measurement-covariance estimate or new physical mechanism was produced",
            "NIST certified values are used only for known-answer reproduction, never as holdout evidence",
            "All eight tail observations were excluded from fitting, start selection, model selection and threshold retuning",
        ],
    }


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data_path = ROOT / "data/Eckerle4.dat"
    protocol_path = ROOT / "validation/eckerle4-two-tail-protocol.json"
    output_path = ROOT / "validation/eckerle4-two-tail.json"
    figure_path = ROOT / "papers/06_第二真实数据外推/fig06_eckerle4_two_tail.png"
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite: {output_path}")
    if figure_path.exists():
        raise FileExistsError(f"Refusing to overwrite: {figure_path}")
    summary = analyze(data_path, protocol_path)
    summary["analysis_runner_sha256"] = sha256(Path(__file__).resolve())
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    x, y = load_eckerle_data(data_path, summary["data_sha256"])
    low, middle, high = split_two_tail(x)
    grid = np.linspace(395, 505, 700)
    parameters = summary["middle_fit"]["parameters"]
    full_parameters = summary["full_fit_certification"]["parameters"]
    linear = summary["baselines"]["linear"]
    fig, ax = plt.subplots(figsize=(10.5, 6.2), constrained_layout=True)
    ax.scatter(x[middle], y[middle], s=35, color="#316c9b", label="Central training observations (n=27)", zorder=3)
    ax.scatter(x[low], y[low], s=58, color="#b47a3c", marker="^", label="Low-wavelength holdout (n=3)", zorder=4)
    ax.scatter(x[high], y[high], s=58, color="#b44b4b", marker="s", label="High-wavelength holdout (n=5)", zorder=4)
    ax.plot(grid, eckerle_model(grid, *parameters.values()), color="#20252b", lw=2.2, label="Gaussian fit on central data only")
    ax.plot(grid, eckerle_model(grid, *full_parameters.values()), color="#487a52", lw=1.6, ls="--", label="Full-data NIST reproduction (not holdout evidence)")
    ax.plot(grid, linear["slope"] * grid + linear["intercept"], color="#876a32", lw=1.5, ls=":", label="Linear central baseline")
    for boundary in [410, 480]:
        ax.axvline(boundary, color="#777777", lw=1, ls="--")
    metrics = summary["middle_fit"]["metrics"]
    ax.text(
        0.02, 0.03,
        f"Middle RMSE = {metrics['middle_rmse']:.6f}\nLow-tail RMSE = {metrics['low_rmse']:.6f}\nHigh-tail RMSE = {metrics['high_rmse']:.6f}\nPooled holdout RMSE = {metrics['holdout_rmse']:.6f}",
        transform=ax.transAxes, fontsize=9, bbox={"facecolor": "white", "edgecolor": "#ccd4d8", "alpha": 0.92},
    )
    ax.set_title("NIST Eckerle4: preregistered two-tail extrapolation")
    ax.set_xlabel("Wavelength x")
    ax.set_ylabel("Transmittance y")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180)
    print(json.dumps({"output": str(output_path), "figure": str(figure_path), "metrics": metrics, "baselines": summary["baselines"], "decision": summary["decision"], "nist_reproduction": summary["full_fit_certification"]["matches_nist_within_frozen_tolerances"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
