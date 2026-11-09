"""Read-only local-identifiability diagnostics for frozen native ENSO Fourier fits."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import error_metrics, sha256
from analyze_enso_native_holdout import native_model
from external_coverage import load_observations

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/enso-native-identifiability-protocol.json"
OUT = ROOT / "validation/enso-native-identifiability.json"
FIGURE = ROOT / "papers/48_ENSO原生参数可识别性/fig48_enso_native_identifiability.png"
PARAMETER_NAMES = ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9"]


def native_jacobian(x, parameters):
    x = np.asarray(x, dtype=float)
    values = {name: float(parameters[name]) for name in PARAMETER_NAMES}
    b4 = values["b4"]
    b7 = values["b7"]
    if b4 == 0 or b7 == 0:
        return np.full((len(x), len(PARAMETER_NAMES)), np.nan, dtype=float)
    annual = 2 * np.pi * x / 12
    long_1 = 2 * np.pi * x / b4
    long_2 = 2 * np.pi * x / b7
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        return np.column_stack([
            np.ones_like(x),
            np.cos(annual),
            np.sin(annual),
            (long_1 / b4) * (values["b5"] * np.sin(long_1) - values["b6"] * np.cos(long_1)),
            np.cos(long_1),
            np.sin(long_1),
            (long_2 / b7) * (values["b8"] * np.sin(long_2) - values["b9"] * np.cos(long_2)),
            np.cos(long_2),
            np.sin(long_2),
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


def period_diagnostics(parameters, correlation):
    indices = {name: index for index, name in enumerate(PARAMETER_NAMES)}
    absolute = np.abs(correlation)

    def block_max(first, second):
        return float(max(absolute[indices[left], indices[right]] for left in first for right in second))

    b4 = float(parameters["b4"])
    b7 = float(parameters["b7"])
    return {
        "b4_b7_ratio": b4 / b7 if b4 != 0 and b7 != 0 else None,
        "b4_b7_absolute_correlation": float(absolute[indices["b4"], indices["b7"]]),
        "max_b4_own_amplitude_absolute_correlation": block_max(["b4"], ["b5", "b6"]),
        "max_b7_own_amplitude_absolute_correlation": block_max(["b7"], ["b8", "b9"]),
        "max_cross_harmonic_block_absolute_correlation": block_max(["b4", "b5", "b6"], ["b7", "b8", "b9"]),
        "max_annual_long_block_absolute_correlation": block_max(["b2", "b3"], ["b4", "b5", "b6", "b7", "b8", "b9"]),
        "new_physical_period_proved": False,
        "interpretation": "Local harmonic parameter correlations only; not posterior dependence, causal coupling or new physical periods",
    }


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_enso_native_identifiability":
        raise ValueError("Native ENSO identifiability protocol is not frozen")
    for key in ["native_holdout", "native_holdout_protocol", "diagnostic_amendment"]:
        info = protocol["inputs"][key]
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {info['file']}")
    native_protocol = json.loads((ROOT / protocol["inputs"]["native_holdout_protocol"]["file"]).read_text(encoding="utf-8"))
    amendment = json.loads((ROOT / protocol["inputs"]["diagnostic_amendment"]["file"]).read_text(encoding="utf-8"))
    if amendment["original_protocol"]["sha256"] != protocol["inputs"]["native_holdout_protocol"]["sha256"]:
        raise ValueError("ENSO diagnostic amendment does not match the frozen original protocol")
    source = json.loads((ROOT / protocol["inputs"]["native_holdout"]["file"]).read_text(encoding="utf-8"))
    if source["known_answer"]["within_certified_tolerances"] or not source["known_answer"]["certified_forward_rss_check_passed"] or source["known_answer"]["original_tolerances_relaxed"] or source["known_answer"]["optimizer_mismatch_hidden"]:
        raise ValueError("ENSO known-answer evidence layering changed")
    data_info = protocol["inputs"]["data"]
    x, y = load_observations(ROOT / data_info["file"], data_info["observations"], data_info["sha256"])
    if len(np.unique(x)) != len(x):
        raise ValueError("Native ENSO local diagnostics require unique month values")

    folds = []
    for frozen in source["folds"]:
        number = frozen["fold"]
        lower, upper = protocol["fold_rule"]["ranges"][str(number)]
        test_indices = np.flatnonzero((x >= lower) & (x <= upper))
        train_mask = np.ones(len(x), dtype=bool)
        train_mask[test_indices] = False
        expected_train = protocol["fold_rule"]["train_points_per_fold"][number - 1]
        expected_test = protocol["fold_rule"]["test_points_per_fold"][number - 1]
        if int(train_mask.sum()) != expected_train or len(test_indices) != expected_test or not frozen["optimizer_success"]:
            raise ValueError(f"Unexpected frozen fold state: {number}")
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
        jacobian = native_jacobian(x[train_mask], parameters)
        test_jacobian = native_jacobian(x[test_indices], parameters)
        residual_df = protocol["fold_rule"]["residual_degrees_of_freedom_per_fold"][number - 1]
        training_jacobian, prediction_sd = local_diagnostics(jacobian, test_jacobian, parameters, training_rss, residual_df)
        if not training_jacobian["local_covariance_valid"]:
            raise ValueError(f"Local ENSO covariance diagnostic failed: {number}: {training_jacobian.get('failure_reason')}")
        harmonic = period_diagnostics(parameters, np.array(training_jacobian["parameter_correlation_matrix"], dtype=float))
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
            "period_diagnostics": harmonic,
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
        "full_numerical_rank_fold_count": sum(fold["training_jacobian"]["numerical_rank"] == 9 for fold in folds),
        "local_diagnostic_failure_count": sum(not fold["training_jacobian"]["local_covariance_valid"] for fold in folds),
        "max_scaled_condition_number": max(valid_conditions) if valid_conditions else None,
        "max_absolute_off_diagonal_parameter_correlation": max(valid_correlations) if valid_correlations else None,
        "max_local_prediction_standard_deviation": max(valid_prediction_sd) if valid_prediction_sd else None,
        "native_test_rmse_minimum": min(fold["test_metrics"]["rmse"] for fold in folds),
        "native_test_rmse_maximum": max(fold["test_metrics"]["rmse"] for fold in folds),
        "max_b4_b7_absolute_correlation": max(fold["period_diagnostics"]["b4_b7_absolute_correlation"] for fold in folds),
        "max_cross_harmonic_block_absolute_correlation": max(fold["period_diagnostics"]["max_cross_harmonic_block_absolute_correlation"] for fold in folds),
        "max_annual_long_block_absolute_correlation": max(fold["period_diagnostics"]["max_annual_long_block_absolute_correlation"] for fold in folds),
        "max_b4_own_amplitude_absolute_correlation": max(fold["period_diagnostics"]["max_b4_own_amplitude_absolute_correlation"] for fold in folds),
        "max_b7_own_amplitude_absolute_correlation": max(fold["period_diagnostics"]["max_b7_own_amplitude_absolute_correlation"] for fold in folds),
    }
    return {
        "status": "computed_enso_native_identifiability",
        "protocol_sha256": sha256(protocol_path),
        "native_holdout_sha256": sha256(ROOT / protocol["inputs"]["native_holdout"]["file"]),
        "native_holdout_protocol_sha256": sha256(ROOT / protocol["inputs"]["native_holdout_protocol"]["file"]),
        "diagnostic_amendment_sha256": sha256(ROOT / protocol["inputs"]["diagnostic_amendment"]["file"]),
        "data_sha256": data_info["sha256"],
        "analysis_scope": {
            "post_hoc": True,
            "refit": False,
            "new_model_or_parameters": False,
            "new_holdout_selection": False,
            "analytic_jacobian": True,
            "nonlinear_period_derivatives": True,
            "local_linearization": True,
            "fold_specific_residual_degrees_of_freedom": True,
            "calibrated_interval": False,
            "global_identifiability": False,
            "new_period_mechanism": False,
            "independent_validation": False,
            "certified_full_fit_used_as_holdout": False,
        },
        "known_answer": {
            "optimizer_within_certified_tolerances": source["known_answer"]["within_certified_tolerances"],
            "certified_forward_rss_check_passed": source["known_answer"]["certified_forward_rss_check_passed"],
            "original_tolerances_relaxed": source["known_answer"]["original_tolerances_relaxed"],
            "optimizer_mismatch_hidden": source["known_answer"]["optimizer_mismatch_hidden"],
            "used_as_holdout": False,
            "certified_reference_periods": {name: native_protocol["known_answer_rule"]["certified_parameters"][name] for name in ["b4", "b7"]},
        },
        "folds": folds,
        "parameter_stability": stability,
        "totals": totals,
        "decision": protocol["decision"],
        "limitations": [
            "Local Jacobians, numerical ranks, covariances and delta-method sensitivities do not prove global structural identifiability or calibrated uncertainty",
            "Column-normalized condition numbers reduce unit-scale dominance but do not remove nonlinear period-amplitude compensation",
            "Harmonic correlations are local parameter diagnostics, not posterior dependence, causal coupling or new physical cycles",
            "Lower held-out RMSE does not imply unique, invariant or physically endogenous periods or amplitudes",
            "Parameter variation across folds is descriptive and is not a posterior distribution or independent physical estimate",
            "The full-data optimizer mismatch and certified forward pass remain separate from all five-fold diagnostics and are not holdout evidence",
            "No rational denominator, ellipsoid, box or continuous-safety claim is transferred to the native Fourier model",
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
        if fold["train_count"] != expected_train or fold["test_count"] != expected_test or jacobian["shape"] != [expected_train, 9] or len(fold["held_out_points"]) != expected_test:
            errors.append(f"Fold design mismatch: {number}")
        if not math.isclose(jacobian.get("training_residual_variance_estimate", -1), fold["training_rss"] / (expected_train - 9), rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Residual degrees of freedom mismatch: {number}")
        if jacobian["local_covariance_valid"]:
            if jacobian["scaled_condition_number"] is None or not math.isfinite(jacobian["scaled_condition_number"]) or jacobian["scaled_condition_number"] < 1:
                errors.append(f"Invalid condition number: {number}")
            if fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"] < 0:
                errors.append(f"Negative prediction sensitivity: {number}")
        diagnostics = fold["period_diagnostics"]
        for key in ["b4_b7_absolute_correlation", "max_b4_own_amplitude_absolute_correlation", "max_b7_own_amplitude_absolute_correlation", "max_cross_harmonic_block_absolute_correlation", "max_annual_long_block_absolute_correlation"]:
            if not 0 <= diagnostics[key] <= 1:
                errors.append(f"Invalid harmonic correlation: {number}: {key}")
        if diagnostics["new_physical_period_proved"]:
            errors.append(f"New physical period overclaim: {number}")
    if summary["totals"]["full_numerical_rank_fold_count"] != sum(fold["training_jacobian"]["numerical_rank"] == 9 for fold in summary["folds"]):
        errors.append("Full-rank fold count mismatch")
    if summary["totals"]["local_diagnostic_failure_count"] != sum(not fold["training_jacobian"]["local_covariance_valid"] for fold in summary["folds"]):
        errors.append("Local diagnostic failure count mismatch")
    known = summary["known_answer"]
    if known["optimizer_within_certified_tolerances"] or not known["certified_forward_rss_check_passed"] or known["original_tolerances_relaxed"] or known["optimizer_mismatch_hidden"] or known["used_as_holdout"]:
        errors.append("Known-answer evidence layering changed")
    for key in ["refit", "global_structural_identifiability_proved", "physical_parameter_endogeneity_proved", "new_physical_periods_proved", "calibrated_prediction_intervals_produced", "rational_bounds_transferred_to_native", "prediction_stability_equals_parameter_uniqueness", "rank_deficiency_hidden", "period_singularities_hidden", "native_deterministic_bounds_claimed", "optimizer_known_answer_mismatch_hidden", "original_tolerances_relaxed"]:
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
    axes[0, 0].set_title("A. Local conditioning; nine parameters")
    axes[0, 0].grid(axis="y", which="both", alpha=0.2)

    correlations = [fold["training_jacobian"]["max_absolute_off_diagonal_parameter_correlation"] for fold in folds]
    axes[0, 1].bar(numbers, correlations, color="#876a32")
    axes[0, 1].set_ylim(0, 1.05)
    axes[0, 1].set_xticks(numbers)
    axes[0, 1].set_xlabel("Frozen fold")
    axes[0, 1].set_ylabel("Max |off-diagonal correlation|")
    axes[0, 1].set_title("B. Maximum local parameter compensation")
    axes[0, 1].grid(axis="y", alpha=0.2)

    for name, color in [("b4", "#316c9b"), ("b7", "#876a32")]:
        axes[0, 2].plot(numbers, [fold["native_parameters"][name] for fold in folds], "o-", color=color, label=name)
        reference = summary["known_answer"]["certified_reference_periods"][name]
        axes[0, 2].axhline(reference, color=color, linestyle=":", linewidth=1, label=f"{name} certified reference")
    axes[0, 2].set_xticks(numbers)
    axes[0, 2].set_xlabel("Frozen fold")
    axes[0, 2].set_ylabel("Period (months)")
    axes[0, 2].set_title("C. Fold periods; references are not holdout fits")
    axes[0, 2].grid(alpha=0.2)
    axes[0, 2].legend(frameon=False, fontsize=8)

    labels = ["b4–b7", "cross harmonic", "annual–long"]
    keys = ["b4_b7_absolute_correlation", "max_cross_harmonic_block_absolute_correlation", "max_annual_long_block_absolute_correlation"]
    x_positions = np.arange(len(numbers))
    width = 0.25
    for index, (label, key) in enumerate(zip(labels, keys)):
        axes[1, 0].bar(x_positions + (index - 1) * width, [fold["period_diagnostics"][key] for fold in folds], width=width, label=label)
    axes[1, 0].set_xticks(x_positions, numbers)
    axes[1, 0].set_ylim(0, 1.05)
    axes[1, 0].set_xlabel("Frozen fold")
    axes[1, 0].set_ylabel("Absolute local correlation")
    axes[1, 0].set_title("D. Harmonic correlation blocks")
    axes[1, 0].legend(frameon=False, fontsize=8)
    axes[1, 0].grid(axis="y", alpha=0.2)

    max_sd = [fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"] for fold in folds]
    rmse = [fold["test_metrics"]["rmse"] for fold in folds]
    axes[1, 1].plot(numbers, max_sd, "o-", color="#316c9b", label="Max local prediction SD")
    axes[1, 1].plot(numbers, rmse, "s--", color="#b44b4b", label="Observed test RMSE")
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_xticks(numbers)
    axes[1, 1].set_xlabel("Frozen fold")
    axes[1, 1].set_ylabel("Response units (log scale)")
    axes[1, 1].set_title("E. Local sensitivity is not a calibrated error bar")
    axes[1, 1].grid(which="both", alpha=0.2)
    axes[1, 1].legend(frameon=False, fontsize=8)

    for name, color in [("b4", "#316c9b"), ("b7", "#876a32")]:
        relative = []
        for fold in folds:
            record = next(item for item in fold["training_jacobian"]["parameters"] if item["name"] == name)
            relative.append(record["absolute_relative_standard_error"])
        axes[1, 2].plot(numbers, relative, "o-", color=color, label=name)
    axes[1, 2].set_yscale("log")
    axes[1, 2].set_xticks(numbers)
    axes[1, 2].set_xlabel("Frozen fold")
    axes[1, 2].set_ylabel("Local relative standard error")
    axes[1, 2].set_title("F. Period uncertainty is local, not posterior")
    axes[1, 2].grid(which="both", alpha=0.2)
    axes[1, 2].legend(frameon=False, fontsize=8)

    fig.suptitle("ENSO native Fourier fits: local period-amplitude diagnostics without refitting", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Analytic nonlinear-period Jacobians; no global-identifiability, new-cycle, probability-interval or independent-experiment claim.",
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
            errors.append("Missing native ENSO identifiability output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored native ENSO identifiability output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid native ENSO identifiability figure")
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
