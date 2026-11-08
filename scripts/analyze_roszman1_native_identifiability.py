"""Read-only local-identifiability diagnostics for frozen native Roszman1 fits."""

import json
import math
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import error_metrics, sha256
from analyze_roszman1_native_holdout import native_model
from external_coverage import load_observations

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-native-identifiability-protocol.json"
SOURCE = ROOT / "validation/roszman1-native-holdout.json"
OUT = ROOT / "validation/roszman1-native-identifiability.json"
FIGURE = ROOT / "papers/40_Roszman1原生参数可识别性/fig40_roszman1_native_identifiability.png"
PARAMETER_NAMES = ["b1", "b2", "b3", "b4"]


def native_jacobian(x, parameters):
    x = np.asarray(x, dtype=float)
    b3 = float(parameters["b3"])
    b4 = float(parameters["b4"])
    shifted = x - b4
    denominator = shifted ** 2 + b3 ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.column_stack([
            np.ones_like(x),
            -x,
            -shifted / (np.pi * denominator),
            -b3 / (np.pi * denominator),
        ])


def local_diagnostics(jacobian, test_jacobian, parameters, training_rss):
    raw_singular = np.linalg.svd(jacobian, compute_uv=False)
    column_norms = np.linalg.norm(jacobian, axis=0)
    base = {
        "shape": list(jacobian.shape),
        "parameter_count": len(PARAMETER_NAMES),
        "raw_singular_values": raw_singular.tolist(),
        "column_norms": column_norms.tolist(),
        "local_covariance_valid": False,
        "interpretation": "Local linearization at the frozen fit; rank and conditioning do not establish global structural identifiability",
    }
    if not np.isfinite(jacobian).all() or np.any(column_norms <= 0):
        base["failure_reason"] = "Non-finite Jacobian or zero column norm"
        return base, None
    scaled = jacobian / column_norms
    singular = np.linalg.svd(scaled, compute_uv=False)
    tolerance = max(jacobian.shape) * np.finfo(float).eps * singular[0]
    rank = int(np.sum(singular > tolerance))
    condition = float(singular[0] / singular[-1]) if singular[-1] > 0 else None
    base.update({
        "scaled_singular_values": singular.tolist(),
        "scaled_condition_number": condition,
        "numerical_rank": rank,
        "numerical_rank_tolerance": float(tolerance),
    })
    unit_covariance = np.linalg.pinv(scaled.T @ scaled, rcond=1.0e-12, hermitian=True)
    sigma2 = float(training_rss / 16)
    covariance = sigma2 * unit_covariance / np.outer(column_norms, column_norms)
    variances = np.diag(covariance)
    if not np.isfinite(variances).all() or np.any(variances <= 0):
        base["failure_reason"] = "Non-positive or non-finite local parameter variance"
        return base, None
    standard_errors = np.sqrt(variances)
    correlation = np.clip(covariance / np.outer(standard_errors, standard_errors), -1.0, 1.0)
    off_diagonal = np.abs(correlation - np.eye(len(PARAMETER_NAMES)))
    test_scaled = test_jacobian / column_norms
    prediction_variances = sigma2 * np.einsum("ij,jk,ik->i", test_scaled, unit_covariance, test_scaled)
    variance_scale = max(1.0, float(np.max(np.abs(prediction_variances))))
    if not np.isfinite(prediction_variances).all() or np.any(prediction_variances < -1.0e-10 * variance_scale):
        base["failure_reason"] = "Invalid local prediction variance"
        return base, None
    prediction_sd = np.sqrt(np.maximum(prediction_variances, 0.0))
    parameter_records = []
    for index, name in enumerate(PARAMETER_NAMES):
        value = float(parameters[name])
        parameter_records.append({
            "name": name,
            "value": value,
            "local_standard_error": float(standard_errors[index]),
            "absolute_relative_standard_error": float(standard_errors[index] / abs(value)) if value != 0 else None,
        })
    base.update({
        "local_covariance_valid": True,
        "training_residual_variance_estimate": sigma2,
        "parameter_covariance_matrix": covariance.tolist(),
        "parameter_correlation_matrix": correlation.tolist(),
        "max_absolute_off_diagonal_parameter_correlation": float(np.max(off_diagonal)),
        "parameters": parameter_records,
    })
    return base, prediction_sd


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_roszman1_native_identifiability":
        raise ValueError("Native identifiability protocol is not frozen")
    for key in ["native_holdout", "native_holdout_protocol"]:
        info = protocol["inputs"][key]
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {info['file']}")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    data_info = protocol["inputs"]["data"]
    x, y = load_observations(ROOT / data_info["file"], data_info["observations"], data_info["sha256"])
    index_by_x = {float(value): index for index, value in enumerate(x)}
    folds = []
    for frozen in source["folds"]:
        number = frozen["fold"]
        test_x = protocol["fold_rule"]["assignments"][str(number)]
        test_indices = np.array([index_by_x[float(value)] for value in test_x], dtype=int)
        train_mask = np.ones(len(x), dtype=bool)
        train_mask[test_indices] = False
        if int(train_mask.sum()) != 20 or len(test_indices) != 5 or not frozen["optimizer_success"]:
            raise ValueError(f"Unexpected frozen fold state: {number}")
        parameters = frozen["native_parameters"]
        values = [parameters[name] for name in PARAMETER_NAMES]
        train_prediction = native_model(x[train_mask], *values)
        test_prediction = native_model(x[test_indices], *values)
        training_rss = float(np.sum((y[train_mask] - train_prediction) ** 2))
        if not math.isclose(training_rss, frozen["training_rss"], rel_tol=1.0e-9, abs_tol=1.0e-12):
            raise ValueError(f"Frozen training RSS does not reproduce: {number}")
        test_metrics = error_metrics(y[test_indices], test_prediction)
        if test_metrics != frozen["native_test_metrics"]:
            raise ValueError(f"Frozen test metrics do not reproduce: {number}")
        jacobian = native_jacobian(x[train_mask], parameters)
        test_jacobian = native_jacobian(x[test_indices], parameters)
        training_jacobian, prediction_sd = local_diagnostics(jacobian, test_jacobian, parameters, training_rss)
        points = []
        for local_index, source_index in enumerate(test_indices):
            points.append({
                "x": float(x[source_index]),
                "observed_y": float(y[source_index]),
                "native_prediction": float(test_prediction[local_index]),
                "residual": float(y[source_index] - test_prediction[local_index]),
                "local_linearized_prediction_standard_deviation": float(prediction_sd[local_index]) if prediction_sd is not None else None,
            })
        sensitivity = {
            "median_local_standard_deviation": float(np.median(prediction_sd)) if prediction_sd is not None else None,
            "max_local_standard_deviation": float(np.max(prediction_sd)) if prediction_sd is not None else None,
            "interpretation": "Delta-method local sensitivity propagated from the fitting design, not a calibrated prediction interval",
        }
        folds.append({
            "fold": number,
            "train_count": int(train_mask.sum()),
            "test_count": len(test_indices),
            "native_parameters": parameters,
            "training_rss": training_rss,
            "training_metrics": error_metrics(y[train_mask], train_prediction),
            "test_metrics": test_metrics,
            "training_jacobian": training_jacobian,
            "held_out_prediction_sensitivity": sensitivity,
            "held_out_points": points,
        })
    stability = {}
    for name in PARAMETER_NAMES:
        values = [fold["native_parameters"][name] for fold in folds]
        standard_errors = [
            next(item["local_standard_error"] for item in fold["training_jacobian"]["parameters"] if item["name"] == name)
            for fold in folds if fold["training_jacobian"]["local_covariance_valid"]
        ]
        stability[name] = {
            "values": values,
            "minimum": min(values),
            "maximum": max(values),
            "median": float(np.median(values)),
            "range": max(values) - min(values),
            "median_local_standard_error": float(np.median(standard_errors)) if len(standard_errors) == len(folds) else None,
        }
    valid_conditions = [fold["training_jacobian"]["scaled_condition_number"] for fold in folds if fold["training_jacobian"]["scaled_condition_number"] is not None]
    valid_correlations = [fold["training_jacobian"]["max_absolute_off_diagonal_parameter_correlation"] for fold in folds if fold["training_jacobian"]["local_covariance_valid"]]
    valid_prediction_sd = [fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"] for fold in folds if fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"] is not None]
    totals = {
        "fold_count": len(folds),
        "training_point_count_per_fold": 20,
        "held_out_point_count": sum(fold["test_count"] for fold in folds),
        "full_numerical_rank_fold_count": sum(fold["training_jacobian"]["numerical_rank"] == 4 for fold in folds),
        "local_diagnostic_failure_count": sum(not fold["training_jacobian"]["local_covariance_valid"] for fold in folds),
        "max_scaled_condition_number": max(valid_conditions) if valid_conditions else None,
        "max_absolute_off_diagonal_parameter_correlation": max(valid_correlations) if valid_correlations else None,
        "max_local_prediction_standard_deviation": max(valid_prediction_sd) if valid_prediction_sd else None,
        "native_test_rmse_minimum": min(fold["test_metrics"]["rmse"] for fold in folds),
        "native_test_rmse_maximum": max(fold["test_metrics"]["rmse"] for fold in folds),
    }
    return {
        "status": "computed_roszman1_native_identifiability",
        "protocol_sha256": sha256(PROTOCOL),
        "native_holdout_sha256": sha256(SOURCE),
        "data_sha256": data_info["sha256"],
        "analysis_scope": {
            "post_hoc": True,
            "refit": False,
            "new_model_or_parameters": False,
            "new_holdout_selection": False,
            "analytic_jacobian": True,
            "local_linearization": True,
            "calibrated_interval": False,
            "global_identifiability": False,
            "independent_validation": False,
        },
        "folds": folds,
        "parameter_stability": stability,
        "totals": totals,
        "decision": protocol["decision"],
        "limitations": [
            "Local Jacobians, numerical ranks, covariances and delta-method sensitivities do not prove global structural identifiability or calibrated uncertainty",
            "Column-normalized condition numbers reduce unit-scale dominance but do not remove nonlinear parameter compensation",
            "Stable held-out RMSE does not imply unique, invariant or physically endogenous parameters",
            "Parameter variation across folds is descriptive and is not a posterior distribution or independent physical estimate",
            "No rational denominator, ellipsoid, box or continuous-safety claim is transferred to the native arctangent model",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    if len(summary.get("folds", [])) != 5:
        errors.append("Expected five native folds")
    if summary["analysis_scope"].get("refit") is not False:
        errors.append("Refitting is not permitted")
    for fold, frozen in zip(summary["folds"], source["folds"]):
        if fold["native_parameters"] != frozen["native_parameters"] or fold["test_metrics"] != frozen["native_test_metrics"]:
            errors.append(f"Frozen fit changed: {fold['fold']}")
        jacobian = fold["training_jacobian"]
        if jacobian["shape"] != [20, 4] or len(fold["held_out_points"]) != 5:
            errors.append(f"Fold design mismatch: {fold['fold']}")
        if jacobian["local_covariance_valid"]:
            if jacobian["scaled_condition_number"] is None or not math.isfinite(jacobian["scaled_condition_number"]) or jacobian["scaled_condition_number"] < 1:
                errors.append(f"Invalid condition number: {fold['fold']}")
            if fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"] < 0:
                errors.append(f"Negative prediction sensitivity: {fold['fold']}")
    if summary["totals"]["full_numerical_rank_fold_count"] != sum(fold["training_jacobian"]["numerical_rank"] == 4 for fold in summary["folds"]):
        errors.append("Full-rank fold count mismatch")
    if summary["totals"]["local_diagnostic_failure_count"] != sum(not fold["training_jacobian"]["local_covariance_valid"] for fold in summary["folds"]):
        errors.append("Local diagnostic failure count mismatch")
    for key in ["refit", "global_structural_identifiability_proved", "physical_parameter_endogeneity_proved", "calibrated_prediction_intervals_produced", "rational_bounds_transferred_to_native", "prediction_stability_equals_parameter_uniqueness", "rank_deficiency_hidden"]:
        if summary["decision"].get(key) is not False:
            errors.append(f"Overclaim detected: {key}")
    return errors


def render_figure(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    folds = summary["folds"]
    numbers = [fold["fold"] for fold in folds]
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 10.0), constrained_layout=True)
    conditions = [fold["training_jacobian"]["scaled_condition_number"] for fold in folds]
    axes[0, 0].bar(numbers, conditions, color="#316c9b")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks(numbers)
    axes[0, 0].set_xlabel("Frozen fold")
    axes[0, 0].set_ylabel("Scaled Jacobian condition number")
    axes[0, 0].set_title("Local conditioning; rank is not global identifiability")
    axes[0, 0].grid(axis="y", which="both", alpha=0.2)
    max_sd = [fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"] for fold in folds]
    rmse = [fold["test_metrics"]["rmse"] for fold in folds]
    axes[0, 1].plot(numbers, max_sd, "o-", color="#316c9b", label="Max local prediction SD")
    axes[0, 1].plot(numbers, rmse, "s--", color="#b44b4b", label="Observed test RMSE")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_xticks(numbers)
    axes[0, 1].set_xlabel("Frozen fold")
    axes[0, 1].set_ylabel("Response units (log scale)")
    axes[0, 1].set_title("Delta-method sensitivity is not a calibrated error bar")
    axes[0, 1].grid(which="both", alpha=0.2)
    axes[0, 1].legend(frameon=False, fontsize=8)
    for name, color in zip(PARAMETER_NAMES, ["#316c9b", "#876a32", "#6a4c93", "#477a55"]):
        median = summary["parameter_stability"][name]["median"]
        normalized = [fold["native_parameters"][name] / median for fold in folds]
        axes[1, 0].plot(numbers, normalized, "o-", label=name, color=color)
    axes[1, 0].axhline(1.0, color="#777777", linestyle=":", linewidth=1)
    axes[1, 0].set_xticks(numbers)
    axes[1, 0].set_xlabel("Frozen fold")
    axes[1, 0].set_ylabel("Parameter / five-fold median")
    axes[1, 0].set_title("Prediction stability does not freeze parameter values")
    axes[1, 0].grid(alpha=0.2)
    axes[1, 0].legend(frameon=False, fontsize=8)
    correlations = [fold["training_jacobian"]["max_absolute_off_diagonal_parameter_correlation"] for fold in folds]
    axes[1, 1].bar(numbers, correlations, color="#876a32")
    axes[1, 1].set_ylim(0, 1.05)
    axes[1, 1].set_xticks(numbers)
    axes[1, 1].set_xlabel("Frozen fold")
    axes[1, 1].set_ylabel("Max |off-diagonal correlation|")
    axes[1, 1].set_title("Local parameter compensation remains visible")
    axes[1, 1].grid(axis="y", alpha=0.2)
    fig.suptitle("Roszman1 native fits: local diagnostics without refitting or probability claims", fontsize=13)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite native identifiability outputs")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    render_figure(summary)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "totals": summary["totals"], "parameter_stability": summary["parameter_stability"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
