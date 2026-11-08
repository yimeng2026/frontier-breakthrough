"""Read-only post-hoc diagnosis of frozen Gauss1 denominator bounds."""

import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

import numpy as np

from exact_roots import as_fraction, evaluate
from ellipsoid_bounds import covariance_support_upper_bound

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "validation/gauss1-ellipsoid-coverage.json"
PROTOCOL = ROOT / "validation/gauss1-ellipsoid-coverage-protocol.json"
RAW_DATA = ROOT / "data/Gauss1.dat"
ORIGINAL_RUNNER = ROOT / "scripts/analyze_gauss1_ellipsoid_coverage.py"
OUT = ROOT / "validation/gauss1-bound-mechanism.json"
FIGURE = ROOT / "papers/21_Gauss1界失效机制/fig21_gauss1_bound_mechanism.png"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_source():
    summary = json.loads(SOURCE.read_text(encoding="utf-8"))
    if summary["protocol_sha256"] != sha256(PROTOCOL):
        raise ValueError("Frozen Gauss1 protocol hash mismatch")
    if summary["data_sha256"] != sha256(RAW_DATA):
        raise ValueError("Frozen Gauss1 raw-data hash mismatch")
    if summary["analysis_runner_sha256"] != sha256(ORIGINAL_RUNNER):
        raise ValueError("Frozen Gauss1 analysis-runner hash mismatch")
    return summary


def inspect_point(fold, point):
    parameters = fold["model_parameters"]
    x = as_fraction(point["x"])
    numerator = evaluate([parameters[name] for name in ["b1", "b2", "b3", "b4"]], x)
    denominator = evaluate([1, parameters["b5"], parameters["b6"], parameters["b7"]], x)
    if denominator == 0:
        raise ValueError("Snapshot denominator is zero")
    support, variance = covariance_support_upper_bound(fold["denominator_covariance"], [x, x**2, x**3])
    radius = as_fraction(1)
    perturbation = radius * support
    denominator_lower = abs(denominator) - perturbation
    available = denominator_lower > 0
    actual_residual = abs(as_fraction(point["observed_y"]) - numerator / denominator)
    shift = None
    residual = None
    if available:
        shift = abs(numerator) * perturbation / (abs(denominator) * denominator_lower)
        residual = actual_residual + shift
    return {
        "x": point["x"],
        "available": available,
        "denominator_lower": float(denominator_lower),
        "support": float(support),
        "support_variance": float(variance),
        "actual_residual": float(actual_residual),
        "shift": float(shift) if shift is not None else None,
        "residual_bound": float(residual) if residual is not None else None,
    }


def extreme(points, key, mode):
    candidates = [point for point in points if point[key] is not None]
    if not candidates:
        return None
    chooser = min if mode == "min" else max
    point = chooser(candidates, key=lambda item: item[key])
    result = {"x": point["x"], "value": point[key]}
    if key == "residual_bound":
        result.update({
            "actual_absolute_residual": point["actual_residual"],
            "prediction_shift": point["shift"],
            "shift_share": point["shift"] / point[key],
        })
    return result


def analyze():
    source = load_source()
    folds = []
    totals = {
        "point_count": 0,
        "ellipsoid_available_point_count": 0,
        "ellipsoid_unavailable_point_count": 0,
        "classification_mismatch_count": 0,
        "stored_bound_agreement_count": 0,
        "stored_bound_mismatch_count": 0,
    }
    for fold in source["folds"]:
        diagnostics = [inspect_point(fold, point) for point in fold["point_results"]]
        agreements = 0
        classification_mismatches = 0
        bound_mismatches = 0
        for point, diagnostic in zip(fold["point_results"], diagnostics):
            if point["ellipsoid_available"] != diagnostic["available"]:
                classification_mismatches += 1
            if not point["ellipsoid_available"]:
                continue
            comparisons = [
                (diagnostic["denominator_lower"], point["ellipsoid_denominator_lower_bound_float"]),
                (diagnostic["shift"], point["ellipsoid_prediction_shift_upper_bound_float"]),
                (diagnostic["residual_bound"], point["ellipsoid_absolute_residual_upper_bound_float"]),
            ]
            if all(math.isclose(actual, stored, rel_tol=1.0e-9, abs_tol=1.0e-8) for actual, stored in comparisons):
                agreements += 1
            else:
                bound_mismatches += 1
        available_count = sum(point["ellipsoid_available"] for point in fold["point_results"])
        unavailable_reasons = Counter(point["ellipsoid_unavailable_reason"] for point in fold["point_results"] if not point["ellipsoid_available"])
        case = {
            "fold": fold["fold"],
            "continuous_ellipsoid_safe": fold["continuous_ellipsoid_safe"],
            "snapshot_root_count": fold["continuous_certificate"]["snapshot_root_count"],
            "support_polynomial_root_count": fold["continuous_certificate"]["support_polynomial_root_count"],
            "model_rmse": fold["test_metrics"]["rmse"],
            "baseline_rmse": fold["baseline_test_metrics"]["rmse"],
            "point_count": len(fold["point_results"]),
            "ellipsoid_available_point_count": available_count,
            "ellipsoid_unavailable_point_count": len(fold["point_results"]) - available_count,
            "unavailable_reason_counts": dict(unavailable_reasons),
            "unavailable_x": [point["x"] for point in fold["point_results"] if not point["ellipsoid_available"]],
            "minimum_denominator_lower": extreme(diagnostics, "denominator_lower", "min"),
            "maximum_covariance_support": extreme(diagnostics, "support", "max"),
            "maximum_prediction_shift_upper_bound": extreme(diagnostics, "shift", "max"),
            "maximum_residual_upper_bound": extreme(diagnostics, "residual_bound", "max"),
            "median_residual_upper_bound": statistics.median(point["residual_bound"] for point in diagnostics if point["residual_bound"] is not None) if available_count else None,
            "classification_mismatch_count": classification_mismatches,
            "stored_bound_agreement_count": agreements,
            "stored_bound_mismatch_count": bound_mismatches,
        }
        folds.append(case)
        totals["point_count"] += case["point_count"]
        totals["ellipsoid_available_point_count"] += available_count
        totals["ellipsoid_unavailable_point_count"] += case["ellipsoid_unavailable_point_count"]
        totals["classification_mismatch_count"] += classification_mismatches
        totals["stored_bound_agreement_count"] += agreements
        totals["stored_bound_mismatch_count"] += bound_mismatches
    return {
        "status": "computed_gauss1_post_hoc_bound_mechanism",
        "source_sha256": sha256(SOURCE),
        "protocol_sha256": sha256(PROTOCOL),
        "diagnostic_runner_sha256": sha256(Path(__file__).resolve()),
        "analysis_scope": {"post_hoc": True, "refit": False, "retuned": False, "radius": 1, "observations": 250},
        "folds": folds,
        "totals": totals,
        "decision": {
            "continuous_noncertification_called_unsafe": False,
            "probability_calibration_claimed": False,
            "native_physical_model_claimed": False,
            "independent_physical_experiment_claimed": False,
        },
        "limitations": [
            "This is a post-hoc diagnostic of frozen outputs, not a new prospective test",
            "Continuous non-certification is not proof of unsafety",
            "Denominator diagnostics do not explain or justify the candidate physical mechanism",
            "Stored bounds use observed residuals and are not probability intervals",
        ],
    }


def validate_summary(summary):
    errors = []
    totals = summary["totals"]
    expected = {
        "point_count": 250,
        "ellipsoid_available_point_count": 190,
        "ellipsoid_unavailable_point_count": 60,
        "classification_mismatch_count": 0,
        "stored_bound_agreement_count": 190,
        "stored_bound_mismatch_count": 0,
    }
    for key, value in expected.items():
        if totals.get(key) != value:
            errors.append(f"Unexpected {key}: {totals.get(key)} != {value}")
    if len(summary["folds"]) != 5:
        errors.append("Expected five folds")
    for key in ["continuous_noncertification_called_unsafe", "probability_calibration_claimed", "native_physical_model_claimed", "independent_physical_experiment_claimed"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def render_figure(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    folds = summary["folds"]
    indices = [case["fold"] for case in folds]
    minimum_lower = [case["minimum_denominator_lower"]["value"] for case in folds]
    maximum_support = [case["maximum_covariance_support"]["value"] for case in folds]
    medians = [case["median_residual_upper_bound"] if case["median_residual_upper_bound"] is not None else np.nan for case in folds]
    maxima = [case["maximum_residual_upper_bound"]["value"] if case["maximum_residual_upper_bound"] else np.nan for case in folds]
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), constrained_layout=True)
    axes[0].plot(indices, minimum_lower, "o-", color="#b44b4b", label="Minimum denominator lower bound")
    axes[0].plot(indices, maximum_support, "s--", color="#316c9b", label="Maximum covariance support")
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set_yscale("symlog", linthresh=1.0)
    axes[0].set_xticks(indices)
    axes[0].set_xlabel("Contiguous fold")
    axes[0].set_ylabel("Denominator-scale quantity")
    axes[0].set_title("Availability boundary; negative lower bounds are retained")
    axes[0].grid(alpha=0.2)
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].plot(indices, medians, "o-", color="#316c9b", label="Median residual upper bound")
    axes[1].plot(indices, maxima, "s--", color="#876a32", label="Maximum residual upper bound")
    axes[1].set_yscale("log")
    axes[1].set_xticks(indices)
    axes[1].set_xlabel("Contiguous fold")
    axes[1].set_ylabel("Available deterministic residual upper bound")
    axes[1].set_title("Bound availability is not bound usefulness")
    axes[1].grid(which="both", alpha=0.2)
    axes[1].legend(frameon=False, fontsize=8)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite Gauss1 mechanism outputs")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_figure(summary)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "totals": summary["totals"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
