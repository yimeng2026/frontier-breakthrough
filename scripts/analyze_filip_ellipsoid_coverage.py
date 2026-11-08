"""External candidate-model stress test for covariance ellipsoids on NIST Filip."""

import hashlib
import json
import re
import statistics
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import error_metrics, sha256
from analyze_ellipsoid_box_comparison import denominator_covariance
from analyze_grouped_stress import make_contiguous_folds
from analyze_hahn1_high_temperature import fit_cubic_baseline, fit_rational, hahn_model
from box_stability import certified_box_safe
from ellipsoid_bounds import pointwise_ellipsoid_bound
from ellipsoid_interval import certify_ellipsoid_interval
from rational_format import bounded_text
from prediction_box_bounds import pointwise_prediction_bound

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/filip-ellipsoid-coverage-protocol.json"
OUT = ROOT / "validation/filip-ellipsoid-coverage.json"
FIGURE = ROOT / "papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png"


def load_filip_data(path, expected_sha256=None):
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
    if x.size != 82 or y.size != 82 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Filip must contain exactly 82 finite observations")
    return x, y


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_any_filip_rational_fit":
        raise ValueError("Filip protocol is not frozen")
    if sha256(ROOT / protocol["dataset_scope"]["file"]) != protocol["dataset_scope"]["sha256"]:
        raise ValueError("Filip raw data hash changed")
    x, y = load_filip_data(ROOT / protocol["dataset_scope"]["file"], protocol["dataset_scope"]["sha256"])
    radius = protocol["ellipsoid_rule"]["radius"]
    folds = []
    for fold_index, (train, test) in enumerate(make_contiguous_folds(x, 5), 1):
        baseline_coefficients = fit_cubic_baseline(x[train], y[train])
        baseline_prediction = np.polyval(baseline_coefficients, x[test])
        baseline_metrics = error_metrics(y[test], baseline_prediction)
        try:
            best, attempts = fit_rational(x[train], y[train], protocol["candidate_rule"]["starts"])
            parameters = best["parameters"]
            covariance = denominator_covariance({"model_parameters": parameters, "attempts": attempts}, ("b5", "b6", "b7"))
            coefficients = [1, parameters["b5"], parameters["b6"], parameters["b7"]]
            numerator = [parameters[name] for name in ["b1", "b2", "b3", "b4"]]
            scales = [float(np.sqrt(covariance[index][index])) for index in range(3)]
            lower, upper = float(np.min(x[test])), float(np.max(x[test]))
            continuous = certify_ellipsoid_interval(coefficients, covariance, radius, lower, upper)
            box_safe = certified_box_safe(coefficients, scales, lower, upper, radius)
            results = []
            for index in np.flatnonzero(test):
                prediction = float(hahn_model(x[index], *parameters.values()))
                actual = float(abs(y[index] - prediction))
                result = {
                    "x": float(x[index]),
                    "observed_y": float(y[index]),
                    "snapshot_prediction": prediction,
                    "actual_absolute_residual": actual,
                }
                try:
                    bound = pointwise_ellipsoid_bound(numerator, x[index], coefficients, covariance, radius, y[index])
                    result.update({
                        "ellipsoid_available": True,
                        "ellipsoid_unavailable_reason": None,
                        "ellipsoid_denominator_lower_bound_float": float(bound["denominator_lower_bound"]),
                        "ellipsoid_prediction_shift_upper_bound_rational": bounded_text(bound["prediction_shift_upper_bound"]),
                        "ellipsoid_prediction_shift_upper_bound_float": float(bound["prediction_shift_upper_bound"]),
                        "ellipsoid_absolute_residual_upper_bound_rational": bounded_text(bound["absolute_residual_upper_bound"]),
                        "ellipsoid_absolute_residual_upper_bound_float": float(bound["absolute_residual_upper_bound"]),
                        "coverage_violation": int(actual > float(bound["absolute_residual_upper_bound"]) + 1.0e-9),
                    })
                except ValueError as error:
                    result.update({"ellipsoid_available": False, "ellipsoid_unavailable_reason": str(error), "coverage_violation": None})
                try:
                    bound = pointwise_prediction_bound(numerator, x[index], coefficients, scales, radius, y[index])
                    result.update({
                        "box_available": True,
                        "box_prediction_shift_upper_bound_rational": bounded_text(bound["prediction_shift_upper_bound"]),
                        "box_prediction_shift_upper_bound_float": float(bound["prediction_shift_upper_bound"]),
                        "box_absolute_residual_upper_bound_float": float(bound["absolute_residual_upper_bound"]),
                    })
                except ValueError as error:
                    result.update({"box_available": False, "box_unavailable_reason": str(error)})
                if result["ellipsoid_available"] and result["box_available"] and result["box_prediction_shift_upper_bound_float"] > 0:
                    result["shift_ratio_ellipsoid_over_box"] = result["ellipsoid_prediction_shift_upper_bound_float"] / result["box_prediction_shift_upper_bound_float"]
                    result["ellipsoid_tighter"] = result["shift_ratio_ellipsoid_over_box"] < 1
                else:
                    result["shift_ratio_ellipsoid_over_box"] = None
                    result["ellipsoid_tighter"] = None
                results.append(result)
            case = {
                "fold": fold_index,
                "optimizer_success": True,
                "model_parameters": parameters,
                "test_metrics": error_metrics(y[test], np.asarray([hahn_model(x[index], *parameters.values()) for index in np.flatnonzero(test)])),
                "baseline_test_metrics": baseline_metrics,
                "continuous_ellipsoid_safe": continuous["continuous_ellipsoid_safe"],
                "continuous_certificate": continuous,
                "independent_box_continuous_safe": box_safe,
                "denominator_covariance": covariance,
                "point_results": results,
                "attempts": attempts,
            }
        except Exception as error:
            case = {
                "fold": fold_index,
                "optimizer_success": False,
                "error": str(error),
                "test_metrics": {"rmse": None, "mae": None, "max_absolute_residual": None},
                "baseline_test_metrics": baseline_metrics,
                "continuous_ellipsoid_safe": False,
                "independent_box_continuous_safe": False,
                "point_results": [{
                    "x": float(x[index]),
                    "observed_y": float(y[index]),
                    "snapshot_prediction": None,
                    "actual_absolute_residual": None,
                    "ellipsoid_available": False,
                    "box_available": False,
                    "coverage_violation": None,
                    "shift_ratio_ellipsoid_over_box": None,
                    "ellipsoid_tighter": None,
                } for index in np.flatnonzero(test)],
            }
        folds.append(case)
    all_points = [point for case in folds for point in case["point_results"]]
    ratios = [point["shift_ratio_ellipsoid_over_box"] for point in all_points if point.get("shift_ratio_ellipsoid_over_box") is not None]
    residual_bounds = [point["ellipsoid_absolute_residual_upper_bound_float"] for point in all_points if point.get("ellipsoid_available")]
    shift_bounds = [point["ellipsoid_prediction_shift_upper_bound_float"] for point in all_points if point.get("ellipsoid_available")]
    totals = {
        "fold_count": len(folds),
        "optimizer_failure_count": sum(not case["optimizer_success"] for case in folds),
        "point_count": len(all_points),
        "ellipsoid_available_point_count": sum(point.get("ellipsoid_available", False) for point in all_points),
        "covered_point_count": sum(point.get("coverage_violation") == 0 for point in all_points),
        "coverage_violation_count": sum(point.get("coverage_violation") == 1 for point in all_points),
        "max_ellipsoid_absolute_residual_upper_bound_float": max(residual_bounds, default=None),
        "median_ellipsoid_absolute_residual_upper_bound_float": statistics.median(residual_bounds) if residual_bounds else None,
        "max_ellipsoid_prediction_shift_upper_bound_float": max(shift_bounds, default=None),
        "continuous_safe_fold_count": sum(case["continuous_ellipsoid_safe"] for case in folds),
        "independent_box_continuous_safe_fold_count": sum(case["independent_box_continuous_safe"] for case in folds),
        "tighter_point_count": sum(point.get("ellipsoid_tighter") is True for point in all_points),
        "looser_point_count": sum(point.get("ellipsoid_tighter") is False for point in all_points),
        "median_shift_ratio": statistics.median(ratios) if ratios else None,
        "max_shift_ratio": max(ratios, default=None),
        "min_shift_ratio": min(ratios, default=None),
    }
    return {
        "status": "computed_external_filip_ellipsoid_coverage",
        "protocol_sha256": sha256(PROTOCOL),
        "data_sha256": protocol["dataset_scope"]["sha256"],
        "analysis_scope": {
            "candidate_model_not_native": True,
            "native_model": protocol["dataset_scope"]["native_model"],
            "dataset_used_to_design_previous_regions": False,
            "fixed_radius": radius,
            "independent_physical_experiment": False,
        },
        "folds": folds,
        "totals": totals,
        "decision": {
            "probability_calibration_claimed": False,
            "native_physical_model_claimed": False,
            "universal_external_validity_claimed": False,
            "continuous_x_error_bound_claimed": False,
            "optimizer_failures_hidden": False,
        },
        "limitations": [
            "The cubic/cubic candidate is only an approximation stress test and not the native Filip eleven-parameter model",
            "Deterministic residual bounds are not probability intervals or calibration evidence",
            "Continuous denominator safety does not imply accurate or useful prediction",
            "Pointwise bounds do not provide a continuous-x prediction error bound",
            "Optimizer failures and unavailable bounds are retained, not converted into successes",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    folds = summary.get("folds", [])
    points = [point for case in folds for point in case["point_results"]]
    if len(folds) != 5 or len(points) != 82:
        errors.append("Expected five folds and 82 points")
    for case in folds:
        if case["optimizer_success"]:
            certificate = case["continuous_certificate"]
            if case["continuous_ellipsoid_safe"] != certificate["continuous_ellipsoid_safe"]:
                errors.append(f"Continuous certificate mismatch in fold {case['fold']}")
    for point in points:
        if point.get("ellipsoid_available"):
            if point["ellipsoid_absolute_residual_upper_bound_float"] + 1.0e-9 < point["actual_absolute_residual"]:
                errors.append("Actual residual exceeds an ellipsoid bound")
            if point["coverage_violation"] != 0:
                errors.append("Coverage flag mismatch")
    if summary["totals"]["coverage_violation_count"] != sum(point.get("coverage_violation") == 1 for point in points):
        errors.append("Coverage violation total mismatch")
    for key in ["probability_calibration_claimed", "native_physical_model_claimed", "universal_external_validity_claimed", "continuous_x_error_bound_claimed", "optimizer_failures_hidden"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing Filip coverage outputs")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    folds = summary["folds"]
    indices = [case["fold"] for case in folds]
    model_rmse = [case["test_metrics"]["rmse"] if case["optimizer_success"] else np.nan for case in folds]
    baseline_rmse = [case["baseline_test_metrics"]["rmse"] for case in folds]
    positions = np.arange(len(folds))
    ellipsoid_counts = [sum(point.get("ellipsoid_available", False) for point in case["point_results"]) for case in folds]
    box_counts = [sum(point.get("box_available", False) for point in case["point_results"]) for case in folds]
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), constrained_layout=True)
    axes[0].plot(indices, model_rmse, "o-", color="#316c9b", label="Cubic/cubic candidate")
    axes[0].plot(indices, baseline_rmse, "s--", color="#876a32", label="Cubic baseline")
    axes[0].set_yscale("log")
    axes[0].set_xticks(indices)
    axes[0].set_xlabel("Contiguous fold")
    axes[0].set_ylabel("Held-out RMSE (log scale)")
    axes[0].set_title("External candidate predictive performance")
    axes[0].grid(which="both", alpha=0.2)
    axes[0].legend(frameon=False, fontsize=8)
    width = 0.36
    axes[1].bar(positions - width / 2, ellipsoid_counts, width=width, color="#316c9b", label="Ellipsoid bounds available")
    axes[1].bar(positions + width / 2, box_counts, width=width, color="#b44b4b", label="Independent-box bounds available")
    axes[1].set_xticks(positions, indices)
    axes[1].set_xlabel("Contiguous fold")
    axes[1].set_ylabel("Pointwise bound count")
    axes[1].set_title("Bound availability is not probability coverage")
    axes[1].set_ylim(bottom=0)
    axes[1].grid(axis="y", alpha=0.2)
    axes[1].legend(frameon=False, fontsize=8)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "totals": summary["totals"], "folds": [{"fold": case["fold"], "model_rmse": case["test_metrics"]["rmse"], "baseline_rmse": case["baseline_test_metrics"]["rmse"], "continuous_safe": case["continuous_ellipsoid_safe"]} for case in folds]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
