"""Certify native ENSO Fourier envelopes over explicit parameter ellipsoids."""

import argparse
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np

from analyze_chwirut_holdout import sha256
from analyze_enso_native_holdout import native_model
from analyze_roszman1_native_ellipsoid_continuous import outward, support_value

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/enso-native-ellipsoid-continuous-protocol.json"
OUT = ROOT / "validation/enso-native-ellipsoid-continuous-bounds.json"
FIGURE = ROOT / "papers/54_ENSO原生椭球连续界/fig54_enso_native_ellipsoid_continuous_bounds.png"
PARAMETER_NAMES = ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9"]
PERIOD_NAMES = ["b4", "b7"]


def parameter_index(name):
    return PARAMETER_NAMES.index(name)


def critical_period_radius(parameters, covariance):
    records = []
    for name in PERIOD_NAMES:
        center = mp.mpf(str(parameters[name]))
        if center <= 0:
            raise ValueError("Period centers must be positive for a positive-period critical radius")
        vector = [0] * len(PARAMETER_NAMES)
        vector[parameter_index(name)] = 1
        support = support_value(covariance, vector, 1)
        radius = center / support
        records.append({"parameter": name, "center": float(center), "unit_support": float(support), "radius": outward(radius, lower=False)})
    b4_record, b7_record = records
    b4_value = mp.mpf(str(b4_record["radius"]))
    b7_value = mp.mpf(str(b7_record["radius"]))
    limiting = "b4" if b4_value < b7_value else "b7" if b7_value < b4_value else "tie"
    return {
        "radius": min(b4_record["radius"], b7_record["radius"]),
        "b4_radius": b4_record["radius"],
        "b7_radius": b7_record["radius"],
        "limiting_parameter": limiting,
        "endpoint_results": records,
        "strict_rule": "positive periods require radius < critical radius; exact critical radius is rejected",
    }


def period_certificate(parameters, covariance, radius):
    result = {}
    for name in PERIOD_NAMES:
        center = mp.mpf(str(parameters[name]))
        vector = [0] * len(PARAMETER_NAMES)
        vector[parameter_index(name)] = 1
        support = support_value(covariance, vector, radius)
        minimum = outward(center - support, lower=True)
        maximum = outward(center + support, lower=False)
        zero_tolerance = float(mp.mpf("1e-12") * (1 + abs(center) + abs(support)))
        result[f"{name}_minimum"] = minimum
        result[f"{name}_maximum"] = maximum
        result[f"{name}_zero_tolerance"] = zero_tolerance
    positive = result["b4_minimum"] > result["b4_zero_tolerance"] and result["b7_minimum"] > result["b7_zero_tolerance"]
    return {
        **result,
        "positive_certified": positive,
        "unavailable_reason": None if positive else "at least one period is not certified strictly positive",
    }


def _coefficient_bounds(parameters, name, covariance, radius):
    center = mp.mpf(str(parameters[name]))
    vector = [0] * len(PARAMETER_NAMES)
    vector[parameter_index(name)] = 1
    support = support_value(covariance, vector, radius)
    return {
        "minimum": outward(center - support, lower=True),
        "maximum": outward(center + support, lower=False),
    }


def prediction_envelope(parameters, covariance, radius, x):
    certificate = period_certificate(parameters, covariance, radius)
    if not certificate["positive_certified"]:
        raise ValueError("Cannot form a finite prediction envelope without positive periods")
    annual = 2 * mp.pi * x / 12
    long_1 = 2 * mp.pi * x / mp.mpf(str(parameters["b4"]))
    long_2 = 2 * mp.pi * x / mp.mpf(str(parameters["b7"]))
    definitions = [
        ("b2", mp.cos(annual), "cos(A0)"),
        ("b3", mp.sin(annual), "sin(A0)"),
        ("b5", mp.cos(long_1), "cos(A)"),
        ("b6", mp.sin(long_1), "sin(A)"),
        ("b8", mp.cos(long_2), "cos(B)"),
        ("b9", mp.sin(long_2), "sin(B)"),
    ]
    terms = []
    lower_sum = mp.mpf("0")
    upper_sum = mp.mpf("0")
    for name, trig_value, trig_label in definitions:
        bounds = _coefficient_bounds(parameters, name, covariance, radius)
        coefficient_min = bounds["minimum"]
        coefficient_max = bounds["maximum"]
        if trig_value >= 0:
            lower = outward(coefficient_min * trig_value, lower=True)
            upper = outward(coefficient_max * trig_value, lower=False)
        else:
            lower = outward(coefficient_max * trig_value, lower=True)
            upper = outward(coefficient_min * trig_value, lower=False)
        terms.append({
            "parameter": name,
            "trigonometric_term": trig_label,
            "trig_value": float(trig_value),
            "coefficient_minimum": coefficient_min,
            "coefficient_maximum": coefficient_max,
            "minimum": lower,
            "maximum": upper,
        })
        lower_sum += lower
        upper_sum += upper
    intercept = _coefficient_bounds(parameters, "b1", covariance, radius)
    prediction_minimum = outward(intercept["minimum"] + lower_sum, lower=True)
    prediction_maximum = outward(intercept["maximum"] + upper_sum, lower=False)
    return {
        "prediction_minimum": prediction_minimum,
        "prediction_maximum": prediction_maximum,
        "envelope_width": outward(prediction_maximum - prediction_minimum, lower=False),
        "intercept_minimum": intercept["minimum"],
        "intercept_maximum": intercept["maximum"],
        "terms": terms,
    }


def median(values):
    return float(np.median(values)) if values else None


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_enso_native_ellipsoid_continuous_bounds":
        raise ValueError("Native ENSO ellipsoid continuous protocol is not frozen")
    info = protocol["inputs"]["native_identifiability"]
    source_path = ROOT / info["file"]
    if sha256(source_path) != info["sha256"]:
        raise ValueError("Frozen native identifiability input hash changed")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if len(source["folds"]) != protocol["expected_structure"]["fold_count"] or source["totals"]["held_out_point_count"] != protocol["expected_structure"]["held_out_point_count"]:
        raise ValueError("Frozen ENSO fold or point structure changed")
    radius = protocol["region_rule"]["radius"]
    folds = []
    for case in source["folds"]:
        parameters = case["native_parameters"]
        covariance = case["training_jacobian"]["parameter_covariance_matrix"]
        held_out = case["held_out_points"]
        unique_x = sorted({float(point["x"]) for point in held_out})
        critical = critical_period_radius(parameters, covariance)
        half = period_certificate(parameters, covariance, critical["radius"] / 2)
        exact = period_certificate(parameters, covariance, critical["radius"])
        negative_control = {
            "half_radius_accepted": half["positive_certified"],
            "exact_radius_rejected": not exact["positive_certified"],
        }
        if not all(negative_control.values()):
            raise ValueError(f"Critical-period negative control failed: {case['fold']}")
        certificate = period_certificate(parameters, covariance, radius)
        available = certificate["positive_certified"]
        if available != (radius < critical["radius"]):
            raise ValueError(f"Analytic and outward-rounded period decisions disagree: {case['fold']}")
        envelopes = []
        envelope_by_x = {}
        if available:
            for x in unique_x:
                envelope = prediction_envelope(parameters, covariance, radius, x)
                envelope_id = f"enso:{case['fold']}:{x}"
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
            "critical_period": critical,
            "negative_control": negative_control,
            "period_certificate": certificate,
            "prediction_envelope_available": available,
            "unavailable_reason": certificate["unavailable_reason"],
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
    minimum_fold = min(folds, key=lambda fold: fold["critical_period"]["radius"])
    totals = {
        "fold_count": len(folds),
        "held_out_point_count": len(all_points),
        "unique_month_count": len(unique_x),
        "unique_envelope_count": len(all_envelopes),
        "certified_fold_count": sum(fold["prediction_envelope_available"] for fold in folds),
        "certified_fold_ids": [fold["fold"] for fold in folds if fold["prediction_envelope_available"]],
        "unavailable_fold_ids": [fold["fold"] for fold in folds if not fold["prediction_envelope_available"]],
        "available_point_count": available,
        "covered_point_count": covered,
        "violation_point_count": violations,
        "unavailable_point_count": unavailable,
        "center_prediction_envelope_mismatch_count": mismatch,
        "minimum_critical_period_radius": minimum_fold["critical_period"]["radius"],
        "minimum_critical_period_radius_fold": minimum_fold["fold"],
        "minimum_critical_period_parameter": minimum_fold["critical_period"]["limiting_parameter"],
        "max_envelope_width": max(widths) if widths else None,
        "median_envelope_width": median(widths),
        "max_residual_upper_bound": max(residual_bounds) if residual_bounds else None,
        "median_residual_upper_bound": median(residual_bounds),
    }
    expected = protocol["expected_structure"]
    if totals["held_out_point_count"] != expected["held_out_point_count"] or totals["unique_month_count"] != expected["unique_month_count"] or available + unavailable != expected["held_out_point_count"] or covered + violations != available or mismatch:
        raise ValueError("Frozen structure or center-envelope consistency check failed")
    return {
        "status": "computed_enso_native_ellipsoid_continuous_bounds",
        "protocol_sha256": sha256(protocol_path),
        "native_identifiability_sha256": sha256(source_path),
        "analysis_scope": {
            "refit": False,
            "changed_center_or_covariance": False,
            "radius": radius,
            "radius_is_probability": False,
            "taylor_or_fixed_period_approximation": False,
            "original_fourier_model": True,
            "continuous_month_certificate": True,
            "high_precision_decimal_digits": 80,
            "outward_rounding": True,
            "outward_relative_margin": 1.0e-24,
            "exact_rational_certificate": False,
            "probability_region": False,
            "actual_coverage_is_external_validation": False,
            "new_period_mechanism": False,
        },
        "known_answer": source["known_answer"],
        "folds": folds,
        "parameter_stability": source["parameter_stability"],
        "totals": totals,
        "decision": protocol["decision"],
        "limitations": [
            "The ellipsoid is a chosen arithmetic region based on frozen local covariance, not a confidence or posterior region",
            "Positive periods only make the Fourier model defined; they do not identify unique or physical periods",
            "Independent coefficient relaxations are conservative and may produce wide envelopes",
            "Center-prediction containment and actual-residual coverage are arithmetic consistency checks, not probability coverage or external validation",
            "High-precision outward-rounded numerical certificates are not exact rational-algebra proofs",
            "Non-positive periods and unavailable folds have no finite prediction or residual bound and are never silently dropped",
            "The full-data optimizer mismatch and certified forward pass remain separate from all five-fold diagnostics and are not holdout evidence",
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
    positions = np.arange(len(folds))
    width = 0.35
    axes[0, 0].bar(positions - width / 2, [fold["critical_period"]["b4_radius"] for fold in folds], width=width, label="b4 critical radius", color="#316c9b")
    axes[0, 0].bar(positions + width / 2, [fold["critical_period"]["b7_radius"] for fold in folds], width=width, label="b7 critical radius", color="#876a32")
    axes[0, 0].axhline(4, color="#b44b4b", linestyle="--", linewidth=1.1, label="frozen radius 4")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks(positions, numbers)
    axes[0, 0].set_xlabel("Frozen fold")
    axes[0, 0].set_ylabel("Positive-period critical radius (log)")
    axes[0, 0].set_title("A. Strict positivity requires radius < critical value")
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 0].grid(axis="y", which="both", alpha=0.2)

    for name, color, marker in [("b4", "#316c9b", "o"), ("b7", "#876a32", "s")]:
        axes[0, 1].plot(numbers, [fold["period_certificate"][f"{name}_minimum"] for fold in folds], marker=marker, linestyle="-", color=color, label=f"{name} minimum")
    axes[0, 1].axhline(0, color="#b44b4b", linestyle="--", linewidth=1)
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_xticks(numbers)
    axes[0, 1].set_xlabel("Frozen fold")
    axes[0, 1].set_ylabel("Period minimum (months, log)")
    axes[0, 1].set_title("B. Positive-period certificates at radius 4")
    axes[0, 1].grid(which="both", alpha=0.2)
    axes[0, 1].legend(frameon=False, fontsize=8)

    for fold, color in zip(folds, colors):
        widths = [envelope["envelope_width"] for envelope in fold["envelopes"]]
        if widths:
            axes[1, 0].scatter([fold["fold"]] * len(widths), widths, s=15, alpha=0.65, color=color)
        else:
            axes[1, 0].scatter(fold["fold"], 1, marker="x", s=60, color="#b44b4b")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_xticks(numbers)
    axes[1, 0].set_xlabel("Frozen fold")
    axes[1, 0].set_ylabel("Envelope width (log)")
    axes[1, 0].set_title("C. Validity and information width are different")
    axes[1, 0].grid(which="both", alpha=0.2)

    for fold, color in zip(folds, colors):
        actual = [point["actual_absolute_residual"] for point in fold["points"] if point["covered"] is not None]
        bounds = [point["residual_upper_bound"] for point in fold["points"] if point["covered"] is not None]
        if actual:
            axes[1, 1].scatter(actual, bounds, color=color, s=15, alpha=0.65, label=f"fold {fold['fold']}")
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
    fig.suptitle(f"ENSO native Fourier ellipsoid bounds: {totals['certified_fold_count']}/5 folds certified; smallest critical radius {totals['minimum_critical_period_radius']:.3f}", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Radius 4 is arithmetic, not probability. Original Fourier model; positive-period certificate and trigonometric bounds; no fixed-period or Taylor substitution.",
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
            errors.append("Missing native ENSO ellipsoid output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored native ENSO ellipsoid output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid native ENSO ellipsoid figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "certified_folds": summary["totals"]["certified_fold_ids"],
        "unavailable_folds": summary["totals"]["unavailable_fold_ids"],
        "minimum_critical_period_radius": summary["totals"]["minimum_critical_period_radius"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
