"""Certify native Roszman1 arctangent envelopes over explicit parameter ellipsoids."""

import argparse
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np

from analyze_chwirut_holdout import sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-native-ellipsoid-continuous-protocol.json"
OUT = ROOT / "validation/roszman1-native-ellipsoid-continuous-bounds.json"
FIGURE = ROOT / "papers/53_Roszman1原生椭球奇异界/fig53_roszman1_native_ellipsoid_continuous_bounds.png"
mp.mp.dps = 80
MARGIN = mp.mpf("1e-24")
PARAMETER_NAMES = ["b1", "b2", "b3", "b4"]


def covariance_spd(covariance):
    size = len(covariance)
    matrix = mp.matrix([[mp.mpf(str(value)) for value in row] for row in covariance])
    for i in range(size):
        for j in range(i):
            left = matrix[i, j]
            right = matrix[j, i]
            if abs(left - right) > mp.mpf("1e-12") * (1 + max(abs(left), abs(right))):
                raise ValueError("Covariance matrix must be symmetric positive definite")
    try:
        mp.cholesky(matrix)
    except Exception as error:
        raise ValueError("Covariance matrix must be symmetric positive definite") from error
    return matrix


def support_value(covariance, vector, radius):
    matrix = covariance_spd(covariance)
    direction = mp.matrix([mp.mpf(str(value)) for value in vector])
    quadratic = (direction.T * matrix * direction)[0]
    if quadratic <= 0:
        raise ValueError("Support direction must have positive quadratic form")
    return mp.mpf(str(radius)) * mp.sqrt(quadratic)


def outward(value, lower=True):
    adjustment = MARGIN * (1 + abs(value))
    adjusted = value - adjustment if lower else value + adjustment
    converted = float(adjusted)
    return float(np.nextafter(converted, -np.inf if lower else np.inf))


def denominator_point_bounds(parameters, covariance, radius, x):
    support = support_value(covariance, [0, 0, 0, 1], radius)
    center = mp.mpf(str(x)) - mp.mpf(str(parameters["b4"]))
    zero_tolerance = float(mp.mpf("1e-12") * (1 + abs(center) + abs(support)))
    return {
        "minimum": outward(center - support, lower=True),
        "maximum": outward(center + support, lower=False),
        "zero_tolerance": zero_tolerance,
    }


def sign_bounds(parameters, covariance, radius, x_lower, x_upper):
    if x_lower > x_upper:
        raise ValueError("Interval must be ordered")
    left = denominator_point_bounds(parameters, covariance, radius, x_lower)
    right = denominator_point_bounds(parameters, covariance, radius, x_upper)
    negative = left["maximum"] < -left["zero_tolerance"] and right["maximum"] < -right["zero_tolerance"]
    positive = left["minimum"] > left["zero_tolerance"] and right["minimum"] > right["zero_tolerance"]
    nonzero = negative or positive
    return {
        "interval": [float(x_lower), float(x_upper)],
        "endpoint_results": [
            {"x": float(x_lower), **left},
            {"x": float(x_upper), **right},
        ],
        "minimum": min(left["minimum"], right["minimum"]),
        "maximum": max(left["maximum"], right["maximum"]),
        "sign": "negative" if negative else "positive" if positive else "crossing_or_zero",
        "nonzero_certified": nonzero,
        "unavailable_reason": None if nonzero else "x-b4 has no certified nonzero sign over the ellipsoid and interval",
    }


def critical_sign_radius(parameters, covariance, x_lower, x_upper):
    records = []
    for label, x in [("left", x_lower), ("right", x_upper)]:
        center = mp.mpf(str(x)) - mp.mpf(str(parameters["b4"]))
        records.append({"endpoint": label, "x": float(x), "center": float(center)})
    if records[0]["center"] * records[1]["center"] <= 0:
        raise ValueError("Endpoint centers must have the same sign for a nonzero-sign critical radius")
    for record in records:
        support = support_value(covariance, [0, 0, 0, 1], 1)
        radius = abs(mp.mpf(str(record["center"]))) / support
        record["unit_support"] = float(support)
        record["radius"] = outward(radius, lower=False)
    left, right = records
    left_mp = mp.mpf(str(left["radius"]))
    right_mp = mp.mpf(str(right["radius"]))
    limiting = "left" if left_mp < right_mp else "right" if right_mp < left_mp else "tie"
    return {
        "radius": min(left["radius"], right["radius"]),
        "left_radius": left["radius"],
        "right_radius": right["radius"],
        "limiting_endpoint": limiting,
        "endpoint_results": records,
        "strict_rule": "nonzero x-b4 sign requires radius < critical radius; exact critical radius is rejected",
    }


def prediction_envelope(parameters, covariance, radius, x):
    sign = sign_bounds(parameters, covariance, radius, x, x)
    if not sign["nonzero_certified"]:
        raise ValueError("Cannot form a finite prediction envelope when x-b4 has no certified nonzero sign")
    x = mp.mpf(str(x))
    b1 = mp.mpf(str(parameters["b1"]))
    b2 = mp.mpf(str(parameters["b2"]))
    b3 = mp.mpf(str(parameters["b3"]))
    b1_support = support_value(covariance, [1, 0, 0, 0], radius)
    b2_support = support_value(covariance, [0, 1, 0, 0], radius)
    b3_support = support_value(covariance, [0, 0, 1, 0], radius)
    b1_min = outward(b1 - b1_support, lower=True)
    b1_max = outward(b1 + b1_support, lower=False)
    b2_min = outward(b2 - b2_support, lower=True)
    b2_max = outward(b2 + b2_support, lower=False)
    b3_min = outward(b3 - b3_support, lower=True)
    b3_max = outward(b3 + b3_support, lower=False)
    linear_candidates = [
        b1_min - b2_min * x,
        b1_min - b2_max * x,
        b1_max - b2_min * x,
        b1_max - b2_max * x,
    ]
    linear_minimum = outward(min(linear_candidates), lower=True)
    linear_maximum = outward(max(linear_candidates), lower=False)
    denominator_minimum = sign["minimum"]
    denominator_maximum = sign["maximum"]
    argument_candidates = [
        b3_min / denominator_minimum,
        b3_min / denominator_maximum,
        b3_max / denominator_minimum,
        b3_max / denominator_maximum,
    ]
    argument_minimum = outward(min(argument_candidates), lower=True)
    argument_maximum = outward(max(argument_candidates), lower=False)
    arctan_minimum = outward(mp.atan(argument_minimum), lower=True)
    arctan_maximum = outward(mp.atan(argument_maximum), lower=False)
    prediction_minimum = outward(linear_minimum - arctan_maximum / mp.pi, lower=True)
    prediction_maximum = outward(linear_maximum - arctan_minimum / mp.pi, lower=False)
    return {
        "prediction_minimum": prediction_minimum,
        "prediction_maximum": prediction_maximum,
        "envelope_width": outward(prediction_maximum - prediction_minimum, lower=False),
        "linear_minimum": linear_minimum,
        "linear_maximum": linear_maximum,
        "argument_minimum": argument_minimum,
        "argument_maximum": argument_maximum,
        "arctan_minimum": arctan_minimum,
        "arctan_maximum": arctan_maximum,
        "denominator_minimum": denominator_minimum,
        "denominator_maximum": denominator_maximum,
        "b3_minimum": b3_min,
        "b3_maximum": b3_max,
    }


def median(values):
    return float(np.median(values)) if values else None


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_roszman1_native_ellipsoid_continuous_bounds":
        raise ValueError("Native Roszman1 ellipsoid continuous protocol is not frozen")
    info = protocol["inputs"]["native_identifiability"]
    source_path = ROOT / info["file"]
    if sha256(source_path) != info["sha256"]:
        raise ValueError("Frozen native identifiability input hash changed")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if len(source["folds"]) != protocol["expected_structure"]["fold_count"] or source["totals"]["held_out_point_count"] != protocol["expected_structure"]["held_out_point_count"]:
        raise ValueError("Frozen Roszman1 fold or point structure changed")
    radius = protocol["region_rule"]["radius"]
    folds = []
    for case in source["folds"]:
        parameters = case["native_parameters"]
        covariance = case["training_jacobian"]["parameter_covariance_matrix"]
        held_out = case["held_out_points"]
        unique_x = sorted({float(point["x"]) for point in held_out})
        interval = [min(unique_x), max(unique_x)]
        critical = critical_sign_radius(parameters, covariance, *interval)
        half = sign_bounds(parameters, covariance, critical["radius"] / 2, *interval)
        exact = sign_bounds(parameters, covariance, critical["radius"], *interval)
        negative_control = {
            "half_radius_accepted": half["nonzero_certified"],
            "exact_radius_rejected": not exact["nonzero_certified"],
        }
        if not all(negative_control.values()):
            raise ValueError(f"Critical-sign negative control failed: {case['fold']}")
        sign = sign_bounds(parameters, covariance, radius, *interval)
        available = sign["nonzero_certified"]
        if available != (radius < critical["radius"]):
            raise ValueError(f"Analytic and outward-rounded sign decisions disagree: {case['fold']}")
        envelopes = []
        envelope_by_x = {}
        if available:
            for x in unique_x:
                envelope = prediction_envelope(parameters, covariance, radius, x)
                envelope_id = f"roszman1:{case['fold']}:{x}"
                record = {"envelope_id": envelope_id, "x": x, **envelope}
                envelopes.append(record)
                envelope_by_x[x] = record
        points = []
        mismatch = 0
        covered = 0
        for index, old in enumerate(held_out, start=1):
            x = float(old["x"])
            observed = float(old["observed_y"])
            native_prediction = float(old["native_prediction"])
            actual_absolute = abs(float(old["residual"]))
            if available:
                envelope = envelope_by_x[x]
                lower = envelope["prediction_minimum"]
                upper = envelope["prediction_maximum"]
                residual_bound = outward(max(abs(observed - lower), abs(observed - upper)), lower=False)
                inside = lower <= native_prediction <= upper
                point_covered = actual_absolute <= residual_bound
                if not inside or not point_covered:
                    mismatch += 1
                covered += point_covered
                values = {
                    "prediction_minimum": lower,
                    "prediction_maximum": upper,
                    "residual_upper_bound": residual_bound,
                    "covered": point_covered,
                    "envelope_width": envelope["envelope_width"],
                    "center_prediction_inside": inside,
                }
            else:
                values = {
                    "prediction_minimum": None,
                    "prediction_maximum": None,
                    "residual_upper_bound": None,
                    "covered": None,
                    "envelope_width": None,
                    "center_prediction_inside": None,
                }
            points.append({
                "point_index": index,
                "x": x,
                "observed_y": observed,
                "native_prediction": native_prediction,
                "actual_absolute_residual": actual_absolute,
                **values,
            })
        widths = [envelope["envelope_width"] for envelope in envelopes]
        residual_bounds = [point["residual_upper_bound"] for point in points if point["residual_upper_bound"] is not None]
        folds.append({
            "fold": case["fold"],
            "native_test_rmse": case["test_metrics"]["rmse"],
            "critical_sign": critical,
            "negative_control": negative_control,
            "sign_certificate": sign,
            "prediction_envelope_available": available,
            "unavailable_reason": sign["unavailable_reason"],
            "envelopes": envelopes,
            "points": points,
            "coverage": {
                "available_point_count": len(points) if available else 0,
                "covered_point_count": covered if available else 0,
                "violation_point_count": len(points) - covered if available else 0,
                "unavailable_point_count": 0 if available else len(points),
                "center_prediction_envelope_mismatch_count": mismatch,
            },
            "max_envelope_width": max(widths) if widths else None,
            "median_envelope_width": median(widths),
            "max_residual_upper_bound": max(residual_bounds) if residual_bounds else None,
            "median_residual_upper_bound": median(residual_bounds),
        })
    all_points = [point for fold in folds for point in fold["points"]]
    all_envelopes = [envelope for fold in folds for envelope in fold["envelopes"]]
    available = sum(fold["coverage"]["available_point_count"] for fold in folds)
    covered = sum(fold["coverage"]["covered_point_count"] for fold in folds)
    violations = sum(fold["coverage"]["violation_point_count"] for fold in folds)
    unavailable = sum(fold["coverage"]["unavailable_point_count"] for fold in folds)
    mismatch = sum(fold["coverage"]["center_prediction_envelope_mismatch_count"] for fold in folds)
    widths = [envelope["envelope_width"] for envelope in all_envelopes]
    residual_bounds = [point["residual_upper_bound"] for point in all_points if point["residual_upper_bound"] is not None]
    unique_x = {point["x"] for point in all_points}
    totals = {
        "fold_count": len(folds),
        "held_out_point_count": len(all_points),
        "unique_x_count": len(unique_x),
        "unique_envelope_count": len(all_envelopes),
        "certified_fold_count": sum(fold["prediction_envelope_available"] for fold in folds),
        "certified_fold_ids": [fold["fold"] for fold in folds if fold["prediction_envelope_available"]],
        "unavailable_fold_ids": [fold["fold"] for fold in folds if not fold["prediction_envelope_available"]],
        "available_point_count": available,
        "covered_point_count": covered,
        "violation_point_count": violations,
        "unavailable_point_count": unavailable,
        "center_prediction_envelope_mismatch_count": mismatch,
        "minimum_critical_sign_radius": min(fold["critical_sign"]["radius"] for fold in folds),
        "minimum_critical_sign_radius_fold": min(folds, key=lambda fold: fold["critical_sign"]["radius"])["fold"],
        "max_envelope_width": max(widths) if widths else None,
        "median_envelope_width": median(widths),
        "max_residual_upper_bound": max(residual_bounds) if residual_bounds else None,
        "median_residual_upper_bound": median(residual_bounds),
    }
    expected = protocol["expected_structure"]
    if totals["held_out_point_count"] != expected["held_out_point_count"] or totals["unique_x_count"] != expected["unique_held_out_x_count"] or available + unavailable != expected["held_out_point_count"] or covered + violations != available or mismatch:
        raise ValueError("Frozen structure or center-envelope consistency check failed")
    return {
        "status": "computed_roszman1_native_ellipsoid_continuous_bounds",
        "protocol_sha256": sha256(protocol_path),
        "native_identifiability_sha256": sha256(source_path),
        "analysis_scope": {
            "refit": False,
            "changed_center_or_covariance": False,
            "radius": radius,
            "radius_is_probability": False,
            "taylor_prediction_approximation": False,
            "original_arctangent_model": True,
            "continuous_interval_certificate": True,
            "high_precision_decimal_digits": 80,
            "outward_rounding": True,
            "outward_relative_margin": 1.0e-24,
            "exact_rational_certificate": False,
            "probability_region": False,
            "actual_coverage_is_external_validation": False,
        },
        "folds": folds,
        "parameter_stability": source["parameter_stability"],
        "totals": totals,
        "decision": protocol["decision"],
        "limitations": [
            "The ellipsoid is a chosen arithmetic region based on frozen local covariance, not a confidence or posterior region",
            "Certificates apply only to the defined ellipsoid and closed interval, not all parameters, all x or physical reality",
            "Independent linear-term, argument and arctangent relaxations are conservative and may be wide",
            "Center-prediction containment and actual-residual coverage are arithmetic consistency checks, not probability coverage or external validation",
            "High-precision outward-rounded numerical certificates are not exact rational-algebra proofs",
            "Sign crossings and unavailable folds have no finite prediction or residual bound and are never silently dropped",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    for key, value in summary.get("decision", {}).items():
        if value is not False:
            errors.append(f"Overclaim detected: {key}")
    for fold in summary.get("folds", []):
        available = fold["prediction_envelope_available"]
        for point in fold["points"]:
            if available:
                if point["residual_upper_bound"] < point["actual_absolute_residual"] or point["prediction_minimum"] > point["prediction_maximum"] or not point["center_prediction_inside"]:
                    errors.append(f"Bound consistency failure: fold {fold['fold']} point {point['point_index']}")
            elif any(point[key] is not None for key in ["prediction_minimum", "prediction_maximum", "residual_upper_bound", "covered", "envelope_width"]):
                errors.append(f"Uncertified fold received a bound: {fold['fold']}")
    expected = analyze()
    if summary != expected:
        errors.append("Summary content differs from deterministic frozen-input recomputation")
    return errors


def render_figure(summary, output_path=FIGURE):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path = Path(output_path)
    fig, axes = plt.subplots(2, 2, figsize=(16.0, 11.5), constrained_layout=True)
    folds = summary["folds"]
    numbers = [fold["fold"] for fold in folds]
    colors = ["#316c9b", "#4f7b5b", "#876a32", "#6a4c93", "#b44b4b"]
    critical = [fold["critical_sign"]["radius"] for fold in folds]
    axes[0, 0].bar(numbers, critical, color="#316c9b", width=0.58)
    axes[0, 0].axhline(4, color="#b44b4b", linestyle="--", linewidth=1.1, label="frozen radius 4")
    for fold, value in zip(folds, critical):
        axes[0, 0].text(fold["fold"], value, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
    axes[0, 0].set_xticks(numbers)
    axes[0, 0].set_xlabel("Frozen fold")
    axes[0, 0].set_ylabel("Critical radius for nonzero x-b4 sign")
    axes[0, 0].set_title("A. Strict sign requires radius < critical value")
    axes[0, 0].legend(frameon=False)
    axes[0, 0].grid(axis="y", alpha=0.2)

    for fold, color in zip(folds, colors):
        left = fold["sign_certificate"]["endpoint_results"][0]["maximum"]
        right = fold["sign_certificate"]["endpoint_results"][1]["maximum"]
        axes[0, 1].scatter([fold["fold"], fold["fold"]], [left, right], color=color, s=55, label=f"fold {fold['fold']}")
    axes[0, 1].axhline(0, color="#b44b4b", linestyle="--", linewidth=1)
    axes[0, 1].set_xticks(numbers)
    axes[0, 1].set_xlabel("Frozen fold")
    axes[0, 1].set_ylabel("Endpoint d_max = x-b4")
    axes[0, 1].set_title("B. Negative-sign certificates at radius 4")
    axes[0, 1].grid(axis="y", alpha=0.2)
    axes[0, 1].legend(frameon=False, fontsize=8)

    for fold, color in zip(folds, colors):
        for envelope in fold["envelopes"]:
            axes[1, 0].scatter(envelope["argument_minimum"], envelope["argument_maximum"], color=color, s=18, alpha=0.65)
    axes[1, 0].axhline(0, color="#555555", linewidth=0.8)
    axes[1, 0].set_xlabel("Minimum arctangent argument")
    axes[1, 0].set_ylabel("Maximum arctangent argument")
    axes[1, 0].set_title("C. Conservative argument ranges drive the envelope")
    axes[1, 0].grid(alpha=0.2)

    for fold, color in zip(folds, colors):
        actual = [point["actual_absolute_residual"] for point in fold["points"] if point["covered"] is not None]
        bounds = [point["residual_upper_bound"] for point in fold["points"] if point["covered"] is not None]
        if actual:
            axes[1, 1].scatter(actual, bounds, color=color, s=18, alpha=0.65, label=f"fold {fold['fold']}")
    positive = [point["actual_absolute_residual"] for fold in folds for point in fold["points"] if point["covered"] is not None and point["actual_absolute_residual"] > 0]
    if positive:
        lower = min(positive) * 0.7
        upper = max(point["residual_upper_bound"] for fold in folds for point in fold["points"] if point["residual_upper_bound"] is not None) * 1.3
        axes[1, 1].plot([lower, upper], [lower, upper], linestyle="--", color="#555555", linewidth=1, label="bound = actual residual")
        axes[1, 1].set_xlim(lower, upper)
        axes[1, 1].set_ylim(lower, upper)
    axes[1, 1].set_xscale("log")
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_xlabel("Actual absolute residual (log)")
    axes[1, 1].set_ylabel("Residual upper bound (log)")
    axes[1, 1].set_title("D. Center consistency is not external validation")
    axes[1, 1].grid(which="both", alpha=0.2)
    axes[1, 1].legend(frameon=False, fontsize=7)

    totals = summary["totals"]
    fig.suptitle(f"Roszman1 native arctangent ellipsoid bounds: {totals['certified_fold_count']}/5 folds certified; smallest critical radius {totals['minimum_critical_sign_radius']:.6f}", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Radius 4 is arithmetic, not probability. Original arctangent model; continuous x-b4 sign certificate; no Taylor substitution or independent experiment.",
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
            errors.append("Missing native Roszman1 ellipsoid output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored native Roszman1 ellipsoid output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid native Roszman1 ellipsoid figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "certified_folds": summary["totals"]["certified_fold_ids"],
        "unavailable_folds": summary["totals"]["unavailable_fold_ids"],
        "minimum_critical_sign_radius": summary["totals"]["minimum_critical_sign_radius"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
