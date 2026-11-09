"""Read-only local-identifiability diagnostics for frozen native Chwirut1 fits."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import error_metrics, sha256
from analyze_chwirut1_native_holdout import native_model
from external_coverage import load_observations

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/chwirut1-native-identifiability-protocol.json"
OUT = ROOT / "validation/chwirut1-native-identifiability.json"
FIGURE = ROOT / "papers/47_Chwirut1原生参数可识别性/fig47_chwirut1_native_identifiability.png"
PARAMETER_NAMES = ["b1", "b2", "b3"]


def native_jacobian(x, parameters):
    x = np.asarray(x, dtype=float)
    b1 = float(parameters["b1"])
    b2 = float(parameters["b2"])
    b3 = float(parameters["b3"])
    denominator = b2 + b3 * x
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        prediction = native_model(x, b1, b2, b3)
        return np.column_stack([
            -x * prediction,
            -prediction / denominator,
            -x * prediction / denominator,
        ])


def local_diagnostics(jacobian, test_jacobian, parameters, training_rss, residual_degrees_of_freedom):
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
    sigma2 = float(training_rss / residual_degrees_of_freedom)
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


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_chwirut1_native_identifiability":
        raise ValueError("Native Chwirut1 identifiability protocol is not frozen")
    for key in ["native_holdout", "native_holdout_protocol", "metadata_amendment"]:
        info = protocol["inputs"][key]
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {info['file']}")
    amendment = json.loads((ROOT / protocol["inputs"]["metadata_amendment"]["file"]).read_text(encoding="utf-8"))
    if amendment["original_protocol"]["sha256"] != protocol["inputs"]["native_holdout_protocol"]["sha256"]:
        raise ValueError("Metadata amendment does not match the frozen native protocol")
    if amendment["correction"]["corrected_observation_counts"] != protocol["fold_rule"]["test_points_per_fold"]:
        raise ValueError("Fold counts do not match the frozen metadata amendment")
    source = json.loads((ROOT / protocol["inputs"]["native_holdout"]["file"]).read_text(encoding="utf-8"))
    data_info = protocol["inputs"]["data"]
    x, y = load_observations(ROOT / data_info["file"], data_info["observations"], data_info["sha256"])
    if len(np.unique(x)) != data_info["unique_predictor_values"]:
        raise ValueError("Frozen unique-distance count changed")

    folds = []
    for frozen in source["folds"]:
        number = frozen["fold"]
        test_x = protocol["fold_rule"]["unique_x"][str(number)]
        test_indices = np.flatnonzero(np.isin(x, test_x))
        train_mask = np.ones(len(x), dtype=bool)
        train_mask[test_indices] = False
        expected_train = protocol["fold_rule"]["train_points_per_fold"][number - 1]
        expected_test = protocol["fold_rule"]["test_points_per_fold"][number - 1]
        expected_unique = protocol["fold_rule"]["train_unique_distances_per_fold"][number - 1]
        train_unique = len(np.unique(x[train_mask]))
        if int(train_mask.sum()) != expected_train or len(test_indices) != expected_test or train_unique != expected_unique or not frozen["optimizer_success"]:
            raise ValueError(f"Unexpected frozen fold state: {number}")
        if np.any(np.isin(x[train_mask], test_x)):
            raise ValueError(f"A frozen distance crosses fitting and test sets: {number}")
        parameters = frozen["native_parameters"]
        values = [parameters[name] for name in PARAMETER_NAMES]
        train_prediction = native_model(x[train_mask], *values)
        test_prediction = native_model(x[test_indices], *values)
        if not np.all(np.isfinite(train_prediction)) or not np.all(np.isfinite(test_prediction)):
            raise ValueError(f"Non-finite native prediction in frozen fold: {number}")
        training_rss = float(np.sum((y[train_mask] - train_prediction) ** 2))
        if not math.isclose(training_rss, frozen["training_rss"], rel_tol=1.0e-9, abs_tol=1.0e-12):
            raise ValueError(f"Frozen training RSS does not reproduce: {number}")
        test_metrics = error_metrics(y[test_indices], test_prediction)
        if test_metrics != frozen["native_test_metrics"]:
            raise ValueError(f"Frozen test metrics do not reproduce: {number}")

        b2 = float(parameters["b2"])
        b3 = float(parameters["b3"])
        train_denominator = b2 + b3 * x[train_mask]
        test_denominator = b2 + b3 * x[test_indices]
        all_denominator = np.concatenate([train_denominator, test_denominator])
        pole_x = -b2 / b3 if b3 != 0 else None
        observed_range = protocol["dataset_scope"]["observed_x_closed_range"]
        denominator_diagnostics = {
            "minimum_absolute_denominator_train": float(np.min(np.abs(train_denominator))),
            "minimum_absolute_denominator_held_out": float(np.min(np.abs(test_denominator))),
            "minimum_absolute_denominator_all": float(np.min(np.abs(all_denominator))),
            "zero_denominator_count": int(np.sum(all_denominator == 0)),
            "pole_x": pole_x,
            "pole_inside_observed_closed_range": bool(pole_x is not None and observed_range[0] <= pole_x <= observed_range[1]),
            "singular_evaluation_hidden": False,
            "interpretation": "Native exponential denominator geometry at the frozen fit; not a transferred rational certificate",
        }
        jacobian = native_jacobian(x[train_mask], parameters)
        test_jacobian = native_jacobian(x[test_indices], parameters)
        residual_df = protocol["fold_rule"]["residual_degrees_of_freedom_per_fold"][number - 1]
        training_jacobian, prediction_sd = local_diagnostics(jacobian, test_jacobian, parameters, training_rss, residual_df)
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
            "train_unique_distance_count": train_unique,
            "test_count": len(test_indices),
            "native_parameters": parameters,
            "training_rss": training_rss,
            "training_metrics": error_metrics(y[train_mask], train_prediction),
            "test_metrics": test_metrics,
            "denominator_diagnostics": denominator_diagnostics,
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
        "held_out_point_count": sum(fold["test_count"] for fold in folds),
        "full_numerical_rank_fold_count": sum(fold["training_jacobian"]["numerical_rank"] == 3 for fold in folds),
        "local_diagnostic_failure_count": sum(not fold["training_jacobian"]["local_covariance_valid"] for fold in folds),
        "max_scaled_condition_number": max(valid_conditions) if valid_conditions else None,
        "max_absolute_off_diagonal_parameter_correlation": max(valid_correlations) if valid_correlations else None,
        "max_local_prediction_standard_deviation": max(valid_prediction_sd) if valid_prediction_sd else None,
        "native_test_rmse_minimum": min(fold["test_metrics"]["rmse"] for fold in folds),
        "native_test_rmse_maximum": max(fold["test_metrics"]["rmse"] for fold in folds),
        "minimum_absolute_denominator": min(fold["denominator_diagnostics"]["minimum_absolute_denominator_all"] for fold in folds),
        "pole_inside_observed_range_fold_count": sum(fold["denominator_diagnostics"]["pole_inside_observed_closed_range"] for fold in folds),
    }
    return {
        "status": "computed_chwirut1_native_identifiability",
        "protocol_sha256": sha256(protocol_path),
        "native_holdout_sha256": sha256(ROOT / protocol["inputs"]["native_holdout"]["file"]),
        "native_holdout_protocol_sha256": sha256(ROOT / protocol["inputs"]["native_holdout_protocol"]["file"]),
        "metadata_amendment_sha256": sha256(ROOT / protocol["inputs"]["metadata_amendment"]["file"]),
        "data_sha256": data_info["sha256"],
        "analysis_scope": {
            "post_hoc": True,
            "refit": False,
            "new_model_or_parameters": False,
            "new_holdout_selection": False,
            "analytic_jacobian": True,
            "local_linearization": True,
            "fold_specific_residual_degrees_of_freedom": True,
            "repeated_observations_retained": True,
            "calibrated_interval": False,
            "global_identifiability": False,
            "independent_validation": False,
            "independent_model_family_test": False,
            "related_prior_dataset": protocol["dataset_scope"]["related_prior_dataset"],
        },
        "folds": folds,
        "parameter_stability": stability,
        "totals": totals,
        "decision": protocol["decision"],
        "limitations": [
            "Local Jacobians, numerical ranks, covariances and delta-method sensitivities do not prove global structural identifiability or calibrated uncertainty",
            "Column-normalized condition numbers reduce unit-scale dominance but do not remove nonlinear parameter compensation",
            "Lower held-out RMSE does not imply unique, invariant or physically endogenous parameters",
            "Parameter variation across folds is descriptive and is not a posterior distribution or independent physical estimate",
            "Native denominator and pole diagnostics are not rational certificates or native deterministic bounds",
            "Chwirut1 shares its study and native model family with Chwirut2 and is not an independent model-family or laboratory replication",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads((ROOT / protocol["inputs"]["native_holdout"]["file"]).read_text(encoding="utf-8"))
    if len(summary.get("folds", [])) != 5:
        errors.append("Expected five native folds")
    if summary["analysis_scope"].get("refit") is not False:
        errors.append("Refitting is not permitted")
    for fold, frozen in zip(summary["folds"], source["folds"]):
        number = fold["fold"]
        if fold["native_parameters"] != frozen["native_parameters"] or fold["test_metrics"] != frozen["native_test_metrics"]:
            errors.append(f"Frozen fit changed: {number}")
        expected_train = protocol["fold_rule"]["train_points_per_fold"][number - 1]
        expected_test = protocol["fold_rule"]["test_points_per_fold"][number - 1]
        jacobian = fold["training_jacobian"]
        if fold["train_count"] != expected_train or fold["test_count"] != expected_test or jacobian["shape"] != [expected_train, 3] or len(fold["held_out_points"]) != expected_test:
            errors.append(f"Fold design mismatch: {number}")
        if not math.isclose(jacobian.get("training_residual_variance_estimate", -1), fold["training_rss"] / (expected_train - 3), rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Residual degrees of freedom mismatch: {number}")
        if jacobian["local_covariance_valid"]:
            if jacobian["scaled_condition_number"] is None or not math.isfinite(jacobian["scaled_condition_number"]) or jacobian["scaled_condition_number"] < 1:
                errors.append(f"Invalid condition number: {number}")
            if fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"] < 0:
                errors.append(f"Negative prediction sensitivity: {number}")
        denominator = fold["denominator_diagnostics"]
        if denominator["singular_evaluation_hidden"] or denominator["zero_denominator_count"] != 0:
            errors.append(f"Denominator singularity hidden: {number}")
    if summary["totals"]["full_numerical_rank_fold_count"] != sum(fold["training_jacobian"]["numerical_rank"] == 3 for fold in summary["folds"]):
        errors.append("Full-rank fold count mismatch")
    if summary["totals"]["local_diagnostic_failure_count"] != sum(not fold["training_jacobian"]["local_covariance_valid"] for fold in summary["folds"]):
        errors.append("Local diagnostic failure count mismatch")
    if summary["totals"]["pole_inside_observed_range_fold_count"] != sum(fold["denominator_diagnostics"]["pole_inside_observed_closed_range"] for fold in summary["folds"]):
        errors.append("Pole-location fold count mismatch")
    for key in ["refit", "global_structural_identifiability_proved", "physical_parameter_endogeneity_proved", "calibrated_prediction_intervals_produced", "rational_bounds_transferred_to_native", "prediction_stability_equals_parameter_uniqueness", "rank_deficiency_hidden", "denominator_singularities_hidden", "independent_model_family_claimed", "native_deterministic_bounds_claimed"]:
        if summary["decision"].get(key) is not False:
            errors.append(f"Overclaim detected: {key}")
    return errors


def render_figure(summary, output_path=FIGURE):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path = Path(output_path)
    folds = summary["folds"]
    numbers = [fold["fold"] for fold in folds]
    fig, axes = plt.subplots(2, 3, figsize=(18.0, 10.5), constrained_layout=True)
    conditions = [fold["training_jacobian"]["scaled_condition_number"] for fold in folds]
    axes[0, 0].bar(numbers, conditions, color="#316c9b")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks(numbers)
    axes[0, 0].set_xlabel("Frozen fold")
    axes[0, 0].set_ylabel("Scaled Jacobian condition number")
    axes[0, 0].set_title("A. Local conditioning; not global identifiability")
    axes[0, 0].grid(axis="y", which="both", alpha=0.2)

    correlations = [fold["training_jacobian"]["max_absolute_off_diagonal_parameter_correlation"] for fold in folds]
    axes[0, 1].bar(numbers, correlations, color="#876a32")
    axes[0, 1].set_ylim(0, 1.05)
    axes[0, 1].set_xticks(numbers)
    axes[0, 1].set_xlabel("Frozen fold")
    axes[0, 1].set_ylabel("Max |off-diagonal correlation|")
    axes[0, 1].set_title("B. Local parameter compensation")
    axes[0, 1].grid(axis="y", alpha=0.2)

    train_denominator = [fold["denominator_diagnostics"]["minimum_absolute_denominator_train"] for fold in folds]
    test_denominator = [fold["denominator_diagnostics"]["minimum_absolute_denominator_held_out"] for fold in folds]
    axes[0, 2].plot(numbers, train_denominator, "o-", label="training minimum", color="#316c9b")
    axes[0, 2].plot(numbers, test_denominator, "s--", label="held-out minimum", color="#876a32")
    axes[0, 2].set_yscale("log")
    axes[0, 2].set_xticks(numbers)
    axes[0, 2].set_xlabel("Frozen fold")
    axes[0, 2].set_ylabel("Minimum |b2 + b3 x|")
    axes[0, 2].set_title("C. Native denominator geometry")
    axes[0, 2].grid(which="both", alpha=0.2)
    axes[0, 2].legend(frameon=False, fontsize=8)

    max_sd = [fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"] for fold in folds]
    rmse = [fold["test_metrics"]["rmse"] for fold in folds]
    axes[1, 0].plot(numbers, max_sd, "o-", color="#316c9b", label="Max local prediction SD")
    axes[1, 0].plot(numbers, rmse, "s--", color="#b44b4b", label="Observed test RMSE")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_xticks(numbers)
    axes[1, 0].set_xlabel("Frozen fold")
    axes[1, 0].set_ylabel("Response units (log scale)")
    axes[1, 0].set_title("D. Local sensitivity is not a calibrated error bar")
    axes[1, 0].grid(which="both", alpha=0.2)
    axes[1, 0].legend(frameon=False, fontsize=8)

    for name, color in zip(PARAMETER_NAMES, ["#316c9b", "#876a32", "#6a4c93"]):
        median = summary["parameter_stability"][name]["median"]
        normalized = [fold["native_parameters"][name] / median for fold in folds]
        axes[1, 1].plot(numbers, normalized, "o-", label=name, color=color)
    axes[1, 1].axhline(1.0, color="#777777", linestyle=":", linewidth=1)
    axes[1, 1].set_xticks(numbers)
    axes[1, 1].set_xlabel("Frozen fold")
    axes[1, 1].set_ylabel("Parameter / five-fold median")
    axes[1, 1].set_title("E. Parameter values are not frozen by prediction")
    axes[1, 1].grid(alpha=0.2)
    axes[1, 1].legend(frameon=False, fontsize=8)

    poles = [fold["denominator_diagnostics"]["pole_x"] for fold in folds]
    axes[1, 2].axhspan(0.5, 6.0, color="#4f7b5b", alpha=0.15, label="observed x range [0.5, 6]")
    axes[1, 2].plot(numbers, poles, "o-", color="#6a4c93", label="pole x = -b2/b3")
    axes[1, 2].axhline(0, color="#777777", linewidth=0.8)
    axes[1, 2].set_xticks(numbers)
    axes[1, 2].set_xlabel("Frozen fold")
    axes[1, 2].set_ylabel("Native denominator pole location")
    axes[1, 2].set_title("F. Pole location versus observed distances")
    axes[1, 2].grid(alpha=0.2)
    axes[1, 2].legend(frameon=False, fontsize=8, loc="best")

    fig.suptitle("Chwirut1 native exponential fits: five-fold local diagnostics without refitting", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Analytic Jacobians and fold-specific residual degrees of freedom; no global-identifiability, probability-interval or independent-replication claim.",
        ha="center", fontsize=9, color="#555555",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    summary = analyze()
    errors = validate_summary(summary)
    if args.check:
        if not OUT.exists():
            errors.append("Missing native Chwirut1 identifiability output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored native Chwirut1 identifiability output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid native Chwirut1 identifiability figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "folds": summary["totals"]["fold_count"],
        "held_out_points": summary["totals"]["held_out_point_count"],
        "full_rank_folds": summary["totals"]["full_numerical_rank_fold_count"],
        "max_condition": summary["totals"]["max_scaled_condition_number"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
