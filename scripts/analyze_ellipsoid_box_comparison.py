"""Compare deterministic box and covariance-ellipsoid prediction bounds point by point."""

import hashlib
import json
import statistics
from fractions import Fraction
from pathlib import Path

from ellipsoid_bounds import pointwise_ellipsoid_bound, require_positive_definite
from exact_roots import as_fraction, fraction_text

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/rational-ellipsoid-box-protocol.json"
OUT = ROOT / "validation/rational-ellipsoid-box-comparison.json"
FIGURE = ROOT / "papers/16_椭球与参数盒/fig16_ellipsoid_box_comparison.png"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_ellipsoid_box_comparison":
        raise ValueError("Ellipsoid-box protocol is not frozen")
    inputs, hashes = {}, {}
    for key, info in protocol["inputs"].items():
        path = ROOT / info["file"]
        digest = sha256(path)
        if digest != info["sha256"]:
            raise ValueError(f"Input hash changed: {path}")
        inputs[key] = json.loads(path.read_text(encoding="utf-8"))
        hashes[key] = digest
    return protocol, inputs, hashes


def denominator_covariance(source, denominator_names):
    best = min((attempt for attempt in source["attempts"] if attempt["success"]), key=lambda attempt: attempt["rss"])
    names = list(source["model_parameters"])
    indices = [names.index(name) for name in denominator_names]
    matrix = [[best["covariance"][row][column] for column in indices] for row in indices]
    require_positive_definite(matrix)
    return matrix


def analyze():
    protocol, inputs, hashes = load_inputs()
    cases = []
    for frozen in inputs["parameter_box"]["cases"]:
        dataset, fold = frozen["dataset"], frozen["fold"]
        source = next(item for item in inputs[dataset]["folds"] if item["fold"] == fold)
        box_case = next(item for item in inputs["prediction_box"]["cases"] if item["dataset"] == dataset and item["fold"] == fold)
        radius = frozen["certified_radius_lower_bound_float"]
        covariance_error = None
        try:
            covariance_source = next(item for item in inputs["hahn1_grouped"]["datasets"][2]["folds"] if item["fold"] == fold) if dataset == "hahn1" else source
            covariance = denominator_covariance(covariance_source, frozen["denominator_parameter_order"])
        except ValueError as error:
            covariance, covariance_error = None, str(error)
        comparisons = []
        for point in box_case["point_bounds"]:
            record = {
                "x": point["x"],
                "observed_y": point["observed_y"],
                "box_prediction_shift_upper_bound_rational": point["prediction_shift_upper_bound_rational"],
                "box_prediction_shift_upper_bound_float": point["prediction_shift_upper_bound_float"],
                "box_absolute_residual_upper_bound_float": point["absolute_residual_upper_bound_float"],
            }
            if not frozen["snapshot_safe"] or covariance_error is not None:
                record.update({
                    "ellipsoid_available": False,
                    "unavailable_reason": covariance_error or "Rooted snapshot has no root-free parameter region",
                    "shift_ratio_ellipsoid_over_box": None,
                })
                comparisons.append(record)
                continue
            try:
                bound = pointwise_ellipsoid_bound(
                    box_case["numerator_coefficients"], point["x"], box_case["denominator_coefficients"],
                    covariance, radius, point["observed_y"],
                )
                box_shift = as_fraction(point["prediction_shift_upper_bound_rational"])
                ellipsoid_shift = bound["prediction_shift_upper_bound"]
                ratio = ellipsoid_shift / box_shift if box_shift > 0 else None
                record.update({
                    "ellipsoid_available": True,
                    "unavailable_reason": None,
                    "covariance_support_variance_rational": fraction_text(bound["covariance_support_variance"]),
                    "covariance_support_upper_bound_rational": fraction_text(bound["covariance_support_upper_bound"]),
                    "denominator_lower_bound_rational": fraction_text(bound["denominator_lower_bound"]),
                    "denominator_lower_bound_float": float(bound["denominator_lower_bound"]),
                    "ellipsoid_prediction_shift_upper_bound_rational": fraction_text(ellipsoid_shift),
                    "ellipsoid_prediction_shift_upper_bound_float": float(ellipsoid_shift),
                    "ellipsoid_absolute_residual_upper_bound_rational": fraction_text(bound["absolute_residual_upper_bound"]),
                    "ellipsoid_absolute_residual_upper_bound_float": float(bound["absolute_residual_upper_bound"]),
                    "shift_ratio_ellipsoid_over_box_rational": fraction_text(ratio) if ratio is not None else None,
                    "shift_ratio_ellipsoid_over_box": float(ratio) if ratio is not None else None,
                })
            except ValueError as error:
                record.update({
                    "ellipsoid_available": False,
                    "unavailable_reason": str(error),
                    "shift_ratio_ellipsoid_over_box": None,
                })
            comparisons.append(record)
        ratios = [point["shift_ratio_ellipsoid_over_box"] for point in comparisons if point.get("shift_ratio_ellipsoid_over_box") is not None]
        ellipsoid_shifts = [point["ellipsoid_prediction_shift_upper_bound_float"] for point in comparisons if point["ellipsoid_available"]]
        cases.append({
            "dataset": dataset,
            "fold": fold,
            "certified_radius_lower_bound_float": radius,
            "snapshot_safe": frozen["snapshot_safe"],
            "comparison_available": bool(frozen["snapshot_safe"] and covariance_error is None),
            "unavailable_reason": covariance_error or (None if frozen["snapshot_safe"] else "Rooted snapshot has no root-free parameter region"),
            "denominator_covariance": covariance,
            "covariance_error": covariance_error,
            "point_comparisons": comparisons,
            "comparison_point_count": sum(point["ellipsoid_available"] for point in comparisons),
            "unavailable_point_count": sum(not point["ellipsoid_available"] for point in comparisons),
            "tighter_point_count": sum(point.get("shift_ratio_ellipsoid_over_box") is not None and point["shift_ratio_ellipsoid_over_box"] < 1 for point in comparisons),
            "looser_point_count": sum(point.get("shift_ratio_ellipsoid_over_box") is not None and point["shift_ratio_ellipsoid_over_box"] > 1 for point in comparisons),
            "equal_point_count": sum(point.get("shift_ratio_ellipsoid_over_box") == 1 for point in comparisons),
            "median_shift_ratio": statistics.median(ratios) if ratios else None,
            "max_shift_ratio": max(ratios, default=None),
            "max_box_prediction_shift_upper_bound_float": box_case["max_prediction_shift_upper_bound_float"],
            "max_ellipsoid_prediction_shift_upper_bound_float": max(ellipsoid_shifts, default=None),
        })
    all_points = [point for case in cases for point in case["point_comparisons"]]
    all_ratios = [point["shift_ratio_ellipsoid_over_box"] for point in all_points if point.get("shift_ratio_ellipsoid_over_box") is not None]
    totals = {
        "fold_count": len(cases),
        "unavailable_rooted_fold_count": sum(not case["snapshot_safe"] for case in cases),
        "point_count": len(all_points),
        "comparison_point_count": sum(point["ellipsoid_available"] for point in all_points),
        "unavailable_point_count": sum(not point["ellipsoid_available"] for point in all_points),
        "tighter_point_count": sum(point.get("shift_ratio_ellipsoid_over_box") is not None and point["shift_ratio_ellipsoid_over_box"] < 1 for point in all_points),
        "looser_point_count": sum(point.get("shift_ratio_ellipsoid_over_box") is not None and point["shift_ratio_ellipsoid_over_box"] > 1 for point in all_points),
        "equal_point_count": sum(point.get("shift_ratio_ellipsoid_over_box") == 1 for point in all_points),
        "median_shift_ratio": statistics.median(all_ratios) if all_ratios else None,
        "max_shift_ratio": max(all_ratios, default=None),
        "min_shift_ratio": min(all_ratios, default=None),
    }
    return {
        "status": "computed_exact_rational_ellipsoid_box_comparison",
        "protocol_sha256": sha256(PROTOCOL),
        "input_sha256": hashes,
        "cases": cases,
        "totals": totals,
        "decision": {
            "confidence_ellipsoid_claimed": False,
            "ellipsoid_always_tighter_claimed": False,
            "continuous_x_root_free_claimed": False,
            "linearized_prediction_approximation_used": False,
            "probability_or_physical_measurement_claimed": False,
        },
        "limitations": [
            "The covariance defines a deterministic ellipsoid only; no probability, confidence or physical measurement model is implied",
            "Bounds are pointwise and do not prove root freedom for an ellipsoid over a continuous x interval",
            "Numerator perturbation and model-structure error are outside the comparison",
            "An unavailable ellipsoid bound is not zero and no preferred tighter direction is assumed",
            "Rational square-root upper bounds may be conservative and all ratio classes are preserved",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    cases = summary.get("cases", [])
    all_points = [point for case in cases for point in case["point_comparisons"]]
    totals = summary.get("totals", {})
    if len(cases) != 15 or len(all_points) != 369:
        errors.append("Expected fifteen cases and 369 points")
    if totals.get("comparison_point_count", 0) + totals.get("unavailable_point_count", 0) != 369:
        errors.append("Comparison and unavailable counts do not cover all points")
    for point in all_points:
        if point["ellipsoid_available"] and point["denominator_lower_bound_float"] <= 0:
            errors.append("Available ellipsoid bound has non-positive denominator")
    for key in ["confidence_ellipsoid_claimed", "ellipsoid_always_tighter_claimed", "continuous_x_root_free_claimed", "linearized_prediction_approximation_used", "probability_or_physical_measurement_claimed"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing ellipsoid-box comparison")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cases = summary["cases"]
    available = [case for case in cases if case["comparison_point_count"] and case["max_ellipsoid_prediction_shift_upper_bound_float"] and case["max_box_prediction_shift_upper_bound_float"]]
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.6), constrained_layout=True)
    if available:
        box_values = [case["max_box_prediction_shift_upper_bound_float"] for case in available]
        ellipsoid_values = [case["max_ellipsoid_prediction_shift_upper_bound_float"] for case in available]
        axes[0].scatter(box_values, ellipsoid_values, c=["#316c9b" if case["max_ellipsoid_prediction_shift_upper_bound_float"] < case["max_box_prediction_shift_upper_bound_float"] else "#b44b4b" for case in available], s=48)
        minimum = min(box_values + ellipsoid_values)
        maximum = max(box_values + ellipsoid_values)
        axes[0].plot([minimum, maximum], [minimum, maximum], ls="--", color="#69777f", label="Equal bounds")
        axes[0].set_xscale("log")
        axes[0].set_yscale("log")
        for case in available:
            axes[0].annotate(f"{case['dataset'][0].upper()}{case['fold']}", (case["max_box_prediction_shift_upper_bound_float"], case["max_ellipsoid_prediction_shift_upper_bound_float"]), fontsize=7, xytext=(4, 4), textcoords="offset points")
        axes[0].set_xlabel("Max independent-box shift bound")
        axes[0].set_ylabel("Max covariance-ellipsoid shift bound")
        axes[0].set_title("Same certified radius and observation points")
        axes[0].grid(which="both", alpha=0.2)
        axes[0].legend(frameon=False, fontsize=8)
    labels = [f"{case['dataset'][0].upper()}{case['fold']}" for case in cases]
    tighter = [case["tighter_point_count"] for case in cases]
    looser = [case["looser_point_count"] for case in cases]
    axes[1].bar(range(len(cases)), tighter, color="#316c9b", label="Ellipsoid tighter")
    axes[1].bar(range(len(cases)), looser, bottom=tighter, color="#b44b4b", label="Ellipsoid looser")
    axes[1].set_xticks(range(len(cases)), labels, rotation=90)
    axes[1].set_ylabel("Compared observation count")
    axes[1].set_xlabel("Dataset fold")
    axes[1].set_title("Every tighter and looser comparison is retained")
    axes[1].grid(axis="y", alpha=0.2)
    axes[1].legend(frameon=False, fontsize=8)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "totals": summary["totals"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
