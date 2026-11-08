"""Dataset-prospective pole and local-identifiability gates for NIST Kirby2."""

import json
import re
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

from analyze_chwirut_holdout import error_metrics, sha256
from analyze_grouped_stress import make_contiguous_folds

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/kirby2-prospective-gate-protocol.json"
OUT = ROOT / "validation/kirby2-prospective-gate.json"
FIGURE = ROOT / "papers/11_Kirby2前瞻验收/fig11_kirby2_prospective_gate.png"
PARAMETER_NAMES = ("b1", "b2", "b3", "b4", "b5")


def kirby_model(x, b1, b2, b3, b4, b5):
    x = np.asarray(x, dtype=float)
    return (b1 + b2 * x + b3 * x ** 2) / (1 + b4 * x + b5 * x ** 2)


def denominator_values(x, parameters):
    x = np.asarray(x, dtype=float)
    return 1 + parameters["b4"] * x + parameters["b5"] * x ** 2


def kirby_jacobian(x, parameters):
    x = np.asarray(x, dtype=float)
    values = np.asarray([parameters[name] for name in PARAMETER_NAMES])
    numerator = values[0] + values[1] * x + values[2] * x ** 2
    denominator = 1 + values[3] * x + values[4] * x ** 2
    prediction = numerator / denominator
    jacobian = np.empty((x.size, 5))
    jacobian[:, 0] = 1 / denominator
    jacobian[:, 1] = x / denominator
    jacobian[:, 2] = x ** 2 / denominator
    jacobian[:, 3] = -prediction * x / denominator
    jacobian[:, 4] = -prediction * x ** 2 / denominator
    return jacobian


def denominator_root_records(parameters):
    roots = np.roots([parameters["b5"], parameters["b4"], 1.0])
    records = []
    for root in sorted(roots, key=lambda item: (float(item.real), float(item.imag))):
        is_real = bool(abs(root.imag) < 1.0e-8)
        record = {"root_real": float(root.real), "root_imag": float(root.imag), "is_real": is_real}
        if is_real:
            x = float(root.real)
            numerator = parameters["b1"] + parameters["b2"] * x + parameters["b3"] * x ** 2
            denominator = 1 + parameters["b4"] * x + parameters["b5"] * x ** 2
            derivative = parameters["b4"] + 2 * parameters["b5"] * x
            record.update({
                "root_x": x,
                "absolute_denominator_residual": float(abs(denominator)),
                "numerator_at_root": float(numerator),
                "denominator_derivative_at_root": float(derivative),
                "numerical_simple_pole_evidence": bool(numerator != 0 and derivative != 0),
            })
        records.append(record)
    return records


def load_kirby_data(path, expected_sha256=None):
    path = Path(path)
    if expected_sha256 is not None and sha256(path) != expected_sha256:
        raise ValueError(f"Raw data hash mismatch: {path}")
    x, y = [], []
    pattern = re.compile(r"^\s*[-+]?(?:\d+\.\d*|\.\d+)(?:E[+-]?\d+)?\s+[-+]?(?:\d+\.\d*|\.\d+)(?:E[+-]?\d+)?\s*$", re.I)
    for line in path.read_text(encoding="ascii").splitlines():
        if pattern.match(line):
            response, predictor = line.split()
            y.append(float(response))
            x.append(float(predictor))
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size != 151 or y.size != 151 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Kirby2 must contain exactly 151 finite observations")
    return x, y


def fit_kirby(x, y, starts):
    best = None
    attempts = []
    for start in starts:
        initial = [start[name] for name in PARAMETER_NAMES]
        try:
            parameters, covariance, info, message, ier = curve_fit(
                kirby_model, x, y, p0=initial, maxfev=200000, full_output=True, method="lm",
            )
            residual = y - kirby_model(x, *parameters)
            rss = float(residual @ residual)
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
        raise RuntimeError(f"All Kirby2 fits failed: {attempts}")
    return best, attempts


def assess_prediction_domain(parameters, test_x):
    test_x = np.asarray(test_x, dtype=float)
    lower, upper = float(np.min(test_x)), float(np.max(test_x))
    roots = denominator_root_records(parameters)
    inside = [root for root in roots if root["is_real"] and lower <= root["root_x"] <= upper]
    grid = np.linspace(lower, upper, 1001)
    grid_denominator = denominator_values(grid, parameters)
    test_denominator = denominator_values(test_x, parameters)
    prediction = kirby_model(test_x, *[parameters[name] for name in PARAMETER_NAMES])
    sign_changes = np.signbit(grid_denominator[:-1]) != np.signbit(grid_denominator[1:])
    finite = bool(np.isfinite(prediction).all() and np.isfinite(test_denominator).all() and np.isfinite(grid_denominator).all())
    nonzero = bool(np.all(test_denominator != 0) and np.all(grid_denominator != 0))
    return {
        "closed_interval": [lower, upper],
        "grid_point_count": int(grid.size),
        "real_roots_in_closed_interval": [root["root_x"] for root in inside],
        "real_root_records_in_closed_interval": inside,
        "grid_denominator_sign_change_count": int(np.sum(sign_changes)),
        "grid_min_absolute_denominator": float(np.min(np.abs(grid_denominator))),
        "test_min_absolute_denominator": float(np.min(np.abs(test_denominator))),
        "all_predictions_and_denominators_finite": finite,
        "all_denominators_nonzero": nonzero,
        "domain_admissible": bool(finite and nonzero and not inside and not np.any(sign_changes)),
        "interpretation": "Numerical admissibility on this closed held-out interval, not an exact algebraic proof outside it",
    }


def local_identifiability(x, y, parameters):
    prediction = kirby_model(x, *[parameters[name] for name in PARAMETER_NAMES])
    residual = y - prediction
    jacobian = kirby_jacobian(x, parameters)
    norms = np.linalg.norm(jacobian, axis=0)
    if np.any(norms <= 0) or not np.isfinite(jacobian).all():
        raise ValueError("Invalid training Jacobian")
    scaled = jacobian / norms
    singular_values = np.linalg.svd(scaled, compute_uv=False)
    tolerance = max(jacobian.shape) * np.finfo(float).eps * singular_values[0]
    rank = int(np.sum(singular_values > tolerance))
    unit_covariance = np.linalg.pinv(scaled.T @ scaled, rcond=1.0e-12, hermitian=True)
    sigma2 = float(residual @ residual) / (len(x) - 5)
    covariance = sigma2 * unit_covariance / np.outer(norms, norms)
    standard_errors = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    correlation = np.clip(covariance / np.outer(standard_errors, standard_errors), -1.0, 1.0)
    return {
        "numerical_rank": rank,
        "numerical_rank_tolerance": float(tolerance),
        "scaled_singular_values": singular_values.tolist(),
        "scaled_condition_number": float(singular_values[0] / singular_values[-1]),
        "local_standard_errors": dict(zip(PARAMETER_NAMES, map(float, standard_errors))),
        "max_absolute_off_diagonal_parameter_correlation": float(np.max(np.abs(correlation - np.eye(5)))),
        "minimal_numerical_identifiability": bool(rank == 5 and np.isfinite(standard_errors).all() and np.all(standard_errors > 0)),
        "training_metrics": error_metrics(y, prediction),
        "interpretation": "Minimal local numerical check; full rank does not establish global identifiability or physical endogeneity",
    }


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_any_kirby2_fit":
        raise ValueError("Kirby2 protocol is not frozen")
    x, y = load_kirby_data(ROOT / protocol["data"]["file"], protocol["data"]["sha256"])
    full_best, full_attempts = fit_kirby(x, y, protocol["model"]["starts"])
    full_parameters = full_best["parameters"]
    residual = y - kirby_model(x, *full_parameters.values())
    full_rsd = float(np.sqrt(residual @ residual / (len(x) - 5)))
    certified = protocol["full_fit_certification_rule"]
    parameter_errors = {name: abs(full_parameters[name] / certified["certified_parameters"][name] - 1) for name in PARAMETER_NAMES}
    rsd_error = abs(full_rsd / certified["certified_residual_standard_deviation"] - 1)
    certification = {
        "parameters": full_parameters,
        "residual_sum_of_squares": float(full_best["rss"]),
        "residual_standard_deviation": full_rsd,
        "relative_parameter_errors": parameter_errors,
        "relative_residual_standard_deviation_error": rsd_error,
        "matches_nist_within_frozen_tolerances": bool(max(parameter_errors.values()) <= certified["relative_tolerance_parameters"] and rsd_error <= certified["relative_tolerance_residual_standard_deviation"]),
        "attempts": full_attempts,
        "interpretation": "Known-answer implementation check only; not holdout evidence or a new microscope experiment",
    }
    folds = []
    for fold_index, (train, test) in enumerate(make_contiguous_folds(x, 5), 1):
        baseline_coefficients = np.polyfit(x[train], y[train], 2)
        baseline_prediction = np.polyval(baseline_coefficients, x[test])
        baseline_metrics = error_metrics(y[test], baseline_prediction)
        try:
            best, attempts = fit_kirby(x[train], y[train], protocol["model"]["starts"])
            parameters = best["parameters"]
            prediction = kirby_model(x[test], *parameters.values())
            record = {
                "fold": fold_index,
                "train_count": int(train.sum()),
                "test_count": int(test.sum()),
                "test_x_values": sorted(set(x[test].tolist())),
                "optimizer_success": True,
                "model_parameters": parameters,
                "test_metrics": error_metrics(y[test], prediction),
                "baseline_test_metrics": baseline_metrics,
                "baseline_coefficients_descending": baseline_coefficients.tolist(),
                "domain_audit": assess_prediction_domain(parameters, x[test]),
                "identifiability": local_identifiability(x[train], y[train], parameters),
                "attempts": attempts,
                "held_out_points": [{
                    "x": float(x[index]),
                    "y": float(y[index]),
                    "model_prediction": float(kirby_model(x[index], *parameters.values())),
                    "baseline_prediction": float(np.polyval(baseline_coefficients, x[index])),
                    "denominator": float(denominator_values(x[index], parameters)),
                } for index in np.flatnonzero(test)],
            }
        except Exception as error:
            record = {
                "fold": fold_index,
                "train_count": int(train.sum()),
                "test_count": int(test.sum()),
                "test_x_values": sorted(set(x[test].tolist())),
                "optimizer_success": False,
                "error": str(error),
                "test_metrics": {"rmse": None, "mae": None, "max_absolute_residual": None},
                "baseline_test_metrics": baseline_metrics,
                "baseline_coefficients_descending": baseline_coefficients.tolist(),
                "domain_audit": {"domain_admissible": False, "grid_point_count": 1001},
                "identifiability": {"minimal_numerical_identifiability": False},
            }
        gates = {
            "domain_admissible": bool(record["optimizer_success"] and record["domain_audit"]["domain_admissible"]),
            "minimal_numerical_identifiability": bool(record["optimizer_success"] and record["identifiability"]["minimal_numerical_identifiability"]),
            "not_worse_than_quadratic_baseline": bool(record["optimizer_success"] and record["test_metrics"]["rmse"] <= baseline_metrics["rmse"]),
        }
        record["decision"] = {**gates, "gated_limited_support": bool(all(gates.values()))}
        folds.append(record)
    return {
        "status": "computed_dataset_prospective_kirby2_gate",
        "protocol_sha256": sha256(PROTOCOL),
        "data_sha256": protocol["data"]["sha256"],
        "model": protocol["model"]["equation"],
        "analysis_scope": {"dataset_used_to_design_gate": False, "protocol_frozen_before_any_kirby2_fit": True, "independent_physical_experiment": False, "external_preregistration": False},
        "full_fit_certification": certification,
        "folds": folds,
        "decision": {
            "overall_all_folds_gated_support": all(fold["decision"]["gated_limited_support"] for fold in folds),
            "universal_law_claimed": False,
            "global_identifiability_proved": False,
            "physical_parameter_endogeneity_proved": False,
        },
        "limitations": [
            "One quadratic/quadratic NIST dataset is a dataset-prospective computational check, not an independent physical experiment",
            "Numerical roots and dense-grid checks cover each closed held-out interval only",
            "Full numerical rank and finite local standard errors do not prove global structural identifiability or physical endogeneity",
            "No model, start, fold or threshold was retuned after seeing Kirby2 outcomes",
            "NIST certified values are used only for known-answer implementation reproduction, never as held-out evidence",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    folds = summary.get("folds", [])
    if len(folds) != 5 or sum(fold["test_count"] for fold in folds) != 151:
        errors.append("Expected five folds covering 151 observations")
    for fold in folds:
        decision = fold["decision"]
        expected = decision["domain_admissible"] and decision["minimal_numerical_identifiability"] and decision["not_worse_than_quadratic_baseline"]
        if decision["gated_limited_support"] != expected:
            errors.append(f"Gate mismatch in fold {fold['fold']}")
        if fold["domain_audit"].get("grid_point_count") != 1001:
            errors.append(f"Dense-grid mismatch in fold {fold['fold']}")
    if summary["decision"]["overall_all_folds_gated_support"] != all(fold["decision"]["gated_limited_support"] for fold in folds):
        errors.append("Overall gate mismatch")
    if summary["decision"]["universal_law_claimed"]:
        errors.append("Universal claim detected")
    return errors


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing Kirby2 outputs")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    x, y = load_kirby_data(ROOT / protocol["data"]["file"], protocol["data"]["sha256"])
    folds = summary["folds"]
    indices = [fold["fold"] for fold in folds]
    model_rmse = [fold["test_metrics"]["rmse"] if fold["optimizer_success"] else np.nan for fold in folds]
    baseline_rmse = [fold["baseline_test_metrics"]["rmse"] for fold in folds]
    conditions = [fold["identifiability"].get("scaled_condition_number", np.nan) for fold in folds]
    root_counts = [len(fold["domain_audit"].get("real_roots_in_closed_interval", [])) for fold in folds]
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.6), constrained_layout=True)
    axes[0, 0].plot(indices, model_rmse, "o-", color="#316c9b", label="Rational model")
    axes[0, 0].plot(indices, baseline_rmse, "s--", color="#876a32", label="Quadratic baseline")
    for fold in folds:
        if not fold["decision"]["gated_limited_support"]:
            axes[0, 0].scatter(fold["fold"], fold["test_metrics"]["rmse"], marker="x", s=100, color="#b44b4b", zorder=5)
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks(indices)
    axes[0, 0].set_xlabel("Contiguous fold")
    axes[0, 0].set_ylabel("Held-out RMSE (log scale)")
    axes[0, 0].set_title("Every predictive success and failure is retained")
    axes[0, 0].grid(which="both", alpha=0.2)
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 1].bar(indices, root_counts, color=["#b44b4b" if count else "#487a52" for count in root_counts])
    axes[0, 1].set_xticks(indices)
    axes[0, 1].set_xlabel("Contiguous fold")
    axes[0, 1].set_ylabel("Numerical real roots in held-out interval")
    axes[0, 1].set_title("Prediction-domain pole gate")
    axes[0, 1].grid(axis="y", alpha=0.2)
    axes[1, 0].bar(indices, conditions, color="#316c9b")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_xticks(indices)
    axes[1, 0].set_xlabel("Contiguous fold")
    axes[1, 0].set_ylabel("Column-scaled Jacobian condition number")
    axes[1, 0].set_title("Conditioning is reported, not retrospectively thresholded")
    axes[1, 0].grid(axis="y", which="both", alpha=0.2)
    grid = np.linspace(float(np.min(x)), float(np.max(x)), 800)
    parameters = summary["full_fit_certification"]["parameters"]
    axes[1, 1].scatter(x, y, s=22, color="#316c9b", label="NIST observations")
    axes[1, 1].plot(grid, kirby_model(grid, *parameters.values()), color="#20252b", lw=2, label="Full-fit NIST reproduction")
    axes[1, 1].set_xlabel("Predictor x")
    axes[1, 1].set_ylabel("Response y")
    axes[1, 1].set_title("Known-answer fit is separate from holdout evidence")
    axes[1, 1].grid(alpha=0.2)
    axes[1, 1].legend(frameon=False, fontsize=8)
    fig.suptitle("Kirby2 dataset-prospective gate: quadratic rational model", fontsize=14)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps({
        "output": str(OUT),
        "figure": str(FIGURE),
        "nist_reproduction": summary["full_fit_certification"]["matches_nist_within_frozen_tolerances"],
        "overall_all_folds_gated_support": summary["decision"]["overall_all_folds_gated_support"],
        "folds": [{
            "fold": fold["fold"],
            "test_rmse": fold["test_metrics"]["rmse"],
            "baseline_rmse": fold["baseline_test_metrics"]["rmse"],
            "roots_in_test_interval": fold["domain_audit"].get("real_roots_in_closed_interval"),
            "numerical_rank": fold["identifiability"].get("numerical_rank"),
            "scaled_condition_number": fold["identifiability"].get("scaled_condition_number"),
            "decision": fold["decision"],
        } for fold in folds],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
