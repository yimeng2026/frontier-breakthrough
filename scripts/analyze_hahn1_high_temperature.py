"""Preregistered high-temperature extrapolation for NIST Hahn1 rational models."""

import json
import re
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

from analyze_chwirut_holdout import error_metrics, fit_linear, sha256

ROOT = Path(__file__).resolve().parents[1]
PARAMETER_NAMES = ("b1", "b2", "b3", "b4", "b5", "b6", "b7")


def load_hahn_data(path, expected_sha256=None):
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
    if x.size != 236 or y.size != 236 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Hahn1 must contain exactly 236 finite observations")
    return x, y


def split_high_temperature(x):
    holdout = np.asarray(x, dtype=float) >= 700
    return ~holdout, holdout


def hahn_model(x, b1, b2, b3, b4, b5, b6, b7):
    x = np.asarray(x, dtype=float)
    return (b1 + b2 * x + b3 * x ** 2 + b4 * x ** 3) / (1 + b5 * x + b6 * x ** 2 + b7 * x ** 3)


def fit_cubic_baseline(x, y):
    return np.polyfit(np.asarray(x, dtype=float), np.asarray(y, dtype=float), 3)


def fit_rational(x, y, starts):
    best = None
    attempts = []
    for start in starts:
        initial = [start[name] for name in PARAMETER_NAMES]
        try:
            parameters, covariance, info, message, ier = curve_fit(
                hahn_model, x, y, p0=initial, maxfev=200000, full_output=True, method="lm",
            )
            residuals = y - hahn_model(x, *parameters)
            rss = float(residuals @ residuals)
            record = {
                "start": initial,
                "parameters": dict(zip(PARAMETER_NAMES, map(float, parameters))),
                "rss": rss,
                "success": bool(ier > 0 and np.isfinite(parameters).all() and np.isfinite(rss)),
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
        raise RuntimeError(f"All rational fits failed: {attempts}")
    return best, attempts


def denominator_audit(parameters):
    b5, b6, b7 = parameters["b5"], parameters["b6"], parameters["b7"]
    grid = np.linspace(0, 900, 9001)
    denominator = 1 + b5 * grid + b6 * grid ** 2 + b7 * grid ** 3
    roots = np.roots([b7, b6, b5, 1.0])
    real_within = sorted(float(root.real) for root in roots if abs(root.imag) < 1.0e-8 and 0 <= root.real <= 900)
    return {
        "minimum_on_0_to_900": float(np.min(denominator)),
        "maximum_on_0_to_900": float(np.max(denominator)),
        "real_roots_within_0_to_900": real_within,
        "has_real_singularity_within_experimental_range": any(root <= 850.98 for root in real_within),
        "denominator_sign_consistent": bool(np.all(denominator > 0) or np.all(denominator < 0)),
        "interpretation": "Denominator signs and real roots are reported independently of fit quality; no positivity assumption is invented",
    }


def analyze(data_path, protocol_path):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_any_rational_fit":
        raise ValueError("Hahn1 protocol is not frozen")
    x, y = load_hahn_data(data_path, protocol["data"]["sha256"])
    train, holdout = split_high_temperature(x)
    if (train.sum(), holdout.sum()) != (219, 17):
        raise ValueError("Frozen high-temperature counts changed")

    full_best, full_attempts = fit_rational(x, y, protocol["model"]["starts"])
    full_parameters = full_best["parameters"]
    full_residual = y - hahn_model(x, *full_parameters.values())
    full_rsd = float(np.sqrt(full_residual @ full_residual / (len(x) - 7)))
    certified = protocol["full_fit_certification_rule"]
    relative_parameter_errors = {
        name: abs(full_parameters[name] / certified["certified_parameters"][name] - 1)
        for name in PARAMETER_NAMES
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
        "interpretation": "Known-answer reproduction of the published NIST fit, not our independent thermal-expansion experiment",
    }

    train_best, train_attempts = fit_rational(x[train], y[train], protocol["model"]["starts"])
    train_parameters = train_best["parameters"]
    train_prediction = hahn_model(x, *train_parameters.values())
    full_prediction = hahn_model(x, *full_parameters.values())
    slope, intercept = fit_linear(x[train], y[train])
    linear_prediction = slope * x + intercept
    cubic_coefficients = fit_cubic_baseline(x[train], y[train])
    cubic_prediction = np.polyval(cubic_coefficients, x)
    mean_response = float(np.mean(y[train]))
    mean_prediction = np.full_like(x, mean_response)

    train_metrics = error_metrics(y[train], train_prediction[train])
    holdout_metrics = error_metrics(y[holdout], train_prediction[holdout])
    linear_holdout = error_metrics(y[holdout], linear_prediction[holdout])
    cubic_holdout = error_metrics(y[holdout], cubic_prediction[holdout])
    mean_holdout = error_metrics(y[holdout], mean_prediction[holdout])
    ratio = holdout_metrics["rmse"] / train_metrics["rmse"]
    limited = bool(holdout_metrics["rmse"] < 3 * train_metrics["rmse"] and holdout_metrics["rmse"] < cubic_holdout["rmse"])
    predictions = [
        {
            "index": index + 1,
            "x": float(x[index]),
            "y": float(y[index]),
            "split": "holdout" if holdout[index] else "train",
            "train_model_prediction": float(train_prediction[index]),
            "full_model_prediction": float(full_prediction[index]),
            "linear_prediction": float(linear_prediction[index]),
            "cubic_prediction": float(cubic_prediction[index]),
            "mean_prediction": float(mean_prediction[index]),
            "train_model_residual": float(y[index] - train_prediction[index]),
        }
        for index in range(len(x))
    ]
    return {
        "status": "computed_preregistered_rational_high_temperature_extrapolation",
        "protocol_sha256": sha256(protocol_path),
        "data_sha256": protocol["data"]["sha256"],
        "model": protocol["model"]["equation"],
        "split": {"train_count": int(train.sum()), "holdout_count": int(holdout.sum()), "threshold_x": 700},
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
            "linear": {"slope": slope, "intercept": intercept, "holdout_rmse": linear_holdout["rmse"]},
            "cubic_polynomial": {"coefficients_descending": cubic_coefficients.tolist(), "holdout_rmse": cubic_holdout["rmse"]},
            "training_mean": {"value": mean_response, "holdout_rmse": mean_holdout["rmse"]},
        },
        "denominator_audit": {
            "train_model": denominator_audit(train_parameters),
            "full_model": denominator_audit(full_parameters),
        },
        "decision": {
            "limited_support": limited,
            "negative_for_this_high_temperature_task": not limited,
            "universal_law_claimed": False,
            "parameter_endogeneity_proved": False,
            "gate": protocol["decision_gate"]["limited_support"],
        },
        "predictions": predictions,
        "limitations": [
            "One high-temperature split on one NIST dataset; not random cross-validation or a universal rational-family test",
            "No independent thermal-expansion measurements, measurement-covariance estimate or new physical mechanism was produced",
            "NIST certified values are used only for known-answer reproduction, never as holdout evidence",
            "The 17 highest-temperature observations were not used for fitting, start selection, model selection or threshold retuning",
            "Seven coefficients are not automatically physically endogenous; denominator roots and multiple minima must be reviewed separately",
        ],
    }


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data_path = ROOT / "data/Hahn1.dat"
    protocol_path = ROOT / "validation/hahn1-high-temperature-protocol.json"
    output_path = ROOT / "validation/hahn1-high-temperature.json"
    figure_path = ROOT / "papers/07_有理模型外推/fig07_hahn1_high_temperature.png"
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite: {output_path}")
    if figure_path.exists():
        raise FileExistsError(f"Refusing to overwrite: {figure_path}")
    summary = analyze(data_path, protocol_path)
    summary["analysis_runner_sha256"] = sha256(Path(__file__).resolve())
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    x, y = load_hahn_data(data_path, summary["data_sha256"])
    train, holdout = split_high_temperature(x)
    grid = np.linspace(0, 875, 900)
    parameters = summary["train_fit"]["parameters"]
    full_parameters = summary["full_fit_certification"]["parameters"]
    cubic = summary["baselines"]["cubic_polynomial"]["coefficients_descending"]
    fig, ax = plt.subplots(figsize=(10.5, 6.2), constrained_layout=True)
    ax.scatter(x[train], y[train], s=25, color="#316c9b", label="Training observations (n=219)", zorder=3)
    ax.scatter(x[holdout], y[holdout], s=52, color="#b44b4b", marker="s", label="High-temperature holdout (n=17)", zorder=4)
    ax.plot(grid, hahn_model(grid, *parameters.values()), color="#20252b", lw=2.2, label="Rational fit on training only")
    ax.plot(grid, hahn_model(grid, *full_parameters.values()), color="#487a52", lw=1.6, ls="--", label="Full-data NIST reproduction (not holdout evidence)")
    ax.plot(grid, np.polyval(cubic, grid), color="#876a32", lw=1.5, ls=":", label="Cubic polynomial training baseline")
    ax.axvline(700, color="#777777", lw=1, ls="--")
    metrics = summary["train_fit"]["metrics"]
    ax.text(
        0.02, 0.03,
        f"Train RMSE = {metrics['train_rmse']:.6f}\nHoldout RMSE = {metrics['holdout_rmse']:.6f}\nCubic holdout RMSE = {summary['baselines']['cubic_polynomial']['holdout_rmse']:.6f}",
        transform=ax.transAxes, fontsize=9, bbox={"facecolor": "white", "edgecolor": "#ccd4d8", "alpha": 0.92},
    )
    ax.set_title("NIST Hahn1: preregistered high-temperature rational extrapolation")
    ax.set_xlabel("Temperature x (K)")
    ax.set_ylabel("Coefficient of thermal expansion y")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180)
    print(json.dumps({"output": str(output_path), "figure": str(figure_path), "metrics": metrics, "baselines": summary["baselines"], "decision": summary["decision"], "denominator_audit": summary["denominator_audit"], "nist_reproduction": summary["full_fit_certification"]["matches_nist_within_frozen_tolerances"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
