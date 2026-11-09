"""Audit analytic critical radii and fixed-grid native Chwirut1 ellipsoid bounds."""

import argparse
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np

from analyze_chwirut_holdout import sha256
from analyze_chwirut1_native_ellipsoid_continuous import (
    denominator_bounds,
    outward,
    prediction_envelope,
    support_value,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/chwirut1-native-ellipsoid-radius-sensitivity-protocol.json"
AMENDMENT = ROOT / "validation/chwirut1-native-ellipsoid-radius-sensitivity-protocol-amendment-02.json"
OUT = ROOT / "validation/chwirut1-native-ellipsoid-radius-sensitivity.json"
FIGURE = ROOT / "papers/52_Chwirut1原生椭球半径敏感性/fig52_chwirut1_native_ellipsoid_radius_sensitivity.png"


def critical_radius(parameters, covariance, x_lower, x_upper):
    records = []
    for label, x in [("left", x_lower), ("right", x_upper)]:
        center = mp.mpf(str(parameters["b2"])) + mp.mpf(str(parameters["b3"])) * mp.mpf(str(x))
        if center <= 0:
            raise ValueError("No positive denominator-safe radius exists at a non-positive center endpoint")
        support = support_value(covariance, [0, 1, x], 1)
        radius = center / support
        records.append({"endpoint": label, "x": float(x), "center": float(center), "unit_support": float(support), "radius": float(radius)})
    left, right = records
    left_mp = mp.mpf(str(left["radius"]))
    right_mp = mp.mpf(str(right["radius"]))
    limiting = "left" if left_mp < right_mp else "right" if right_mp < left_mp else "tie"
    left["radius"] = outward(left_mp, lower=False)
    right["radius"] = outward(right_mp, lower=False)
    return {
        "radius": min(left["radius"], right["radius"]),
        "left_radius": left["radius"],
        "right_radius": right["radius"],
        "limiting_endpoint": limiting,
        "endpoint_results": records,
        "strict_rule": "positive denominator requires radius < critical radius; exact critical radius is rejected",
    }


def median(values):
    return float(np.median(values)) if values else None


def evaluate_case(case, parameters, covariance, radius, critical):
    unique_x = sorted({float(point["x"]) for point in case["held_out_points"]})
    interval = [min(unique_x), max(unique_x)]
    denominator = denominator_bounds(parameters, covariance, radius, *interval)
    below = radius < critical
    available = denominator["positive_certified"]
    if available != below:
        raise ValueError(f"Analytic and outward-rounded radius decisions disagree: fold {case['fold']} radius {radius}")
    envelopes = []
    envelope_by_x = {}
    if available:
        for x in unique_x:
            envelope = prediction_envelope(parameters, covariance, radius, x)
            envelope_id = f"chwirut1:{case['fold']}:r{radius}:x{x}"
            record = {"envelope_id": envelope_id, "x": x, **envelope}
            envelopes.append(record)
            envelope_by_x[x] = record
    points = []
    mismatch = 0
    covered = 0
    for index, old in enumerate(case["held_out_points"], start=1):
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
    coverage = {
        "available_point_count": len(points) if available else 0,
        "covered_point_count": covered if available else 0,
        "violation_point_count": len(points) - covered if available else 0,
        "unavailable_point_count": 0 if available else len(points),
        "center_prediction_envelope_mismatch_count": mismatch,
    }
    return {
        "case_id": f"chwirut1:{case['fold']}:r{radius}",
        "radius": radius,
        "analytic_relation": "below_critical" if below else "at_or_above_critical",
        "continuous_denominator": denominator,
        "prediction_envelope_available": available,
        "unavailable_reason": denominator["unavailable_reason"],
        "envelopes": envelopes,
        "points": points,
        "coverage": coverage,
        "max_envelope_width": max(widths) if widths else None,
        "median_envelope_width": median(widths),
        "max_residual_upper_bound": max(residual_bounds) if residual_bounds else None,
        "median_residual_upper_bound": median(residual_bounds),
    }


def case_totals(case):
    return {
        "available_point_count": case["coverage"]["available_point_count"],
        "covered_point_count": case["coverage"]["covered_point_count"],
        "violation_point_count": case["coverage"]["violation_point_count"],
        "unavailable_point_count": case["coverage"]["unavailable_point_count"],
        "center_prediction_envelope_mismatch_count": case["coverage"]["center_prediction_envelope_mismatch_count"],
        "max_envelope_width": case["max_envelope_width"],
        "median_envelope_width": case["median_envelope_width"],
        "max_residual_upper_bound": case["max_residual_upper_bound"],
        "median_residual_upper_bound": case["median_residual_upper_bound"],
    }


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_chwirut1_native_ellipsoid_radius_sensitivity":
        raise ValueError("Native Chwirut1 ellipsoid radius-sensitivity protocol is not frozen")
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    if amendment["original_protocol"]["sha256"] != sha256(protocol_path):
        raise ValueError("Metadata amendment original protocol hash mismatch")
    if "superseded_amendment" in amendment and sha256(ROOT / amendment["superseded_amendment"]["file"]) != amendment["superseded_amendment"]["sha256"]:
        raise ValueError("Superseded amendment hash mismatch")
    for key in ["native_identifiability", "baseline_bounds"]:
        info = protocol["inputs"][key]
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {key}")
    source = json.loads((ROOT / protocol["inputs"]["native_identifiability"]["file"]).read_text(encoding="utf-8"))
    baseline_source = json.loads((ROOT / protocol["inputs"]["baseline_bounds"]["file"]).read_text(encoding="utf-8"))
    radii = protocol["grid_rule"]["radii"]
    baseline = {"radius": protocol["baseline_rule"]["radius"]}
    folds = []
    for case in source["folds"]:
        parameters = case["native_parameters"]
        covariance = case["training_jacobian"]["parameter_covariance_matrix"]
        unique_x = sorted({float(point["x"]) for point in case["held_out_points"]})
        interval = [min(unique_x), max(unique_x)]
        critical = critical_radius(parameters, covariance, *interval)
        half = denominator_bounds(parameters, covariance, critical["radius"] / 2, *interval)
        exact = denominator_bounds(parameters, covariance, critical["radius"], *interval)
        negative_control = {
            "half_radius_accepted": half["positive_certified"],
            "exact_radius_rejected": not exact["positive_certified"],
        }
        if not all(negative_control.values()):
            raise ValueError(f"Critical-radius negative control failed: {case['fold']}")
        cases = [evaluate_case(case, parameters, covariance, radius, critical["radius"]) for radius in radii]
        if any(case_item["coverage"]["center_prediction_envelope_mismatch_count"] for case_item in cases):
            raise ValueError(f"Center-envelope consistency failed: {case['fold']}")
        certified_grid = [case_item["radius"] for case_item in cases if case_item["prediction_envelope_available"]]
        folds.append({
            "fold": case["fold"],
            "critical": critical,
            "negative_control": negative_control,
            "cases": cases,
            "max_certified_grid_radius": max(certified_grid) if certified_grid else None,
            "grid_maximum_scope": "Largest certified radius in the frozen grid only; not the exact or universal safe maximum",
        })
    if baseline is None:
        raise ValueError("Baseline radius is absent from the frozen grid")
    baseline_cases = [case_item for fold in folds for case_item in fold["cases"] if case_item["radius"] == baseline["radius"]]
    baseline_envelopes = [envelope for case_item in baseline_cases for envelope in case_item["envelopes"]]
    baseline_points = [point for case_item in baseline_cases for point in case_item["points"]]
    baseline_widths = [envelope["envelope_width"] for envelope in baseline_envelopes]
    baseline_residual_bounds = [point["residual_upper_bound"] for point in baseline_points if point["residual_upper_bound"] is not None]
    baseline = {
        "radius": baseline["radius"],
        "certified_fold_count": sum(case_item["prediction_envelope_available"] for case_item in baseline_cases),
        "available_point_count": sum(case_item["coverage"]["available_point_count"] for case_item in baseline_cases),
        "covered_point_count": sum(case_item["coverage"]["covered_point_count"] for case_item in baseline_cases),
        "violation_point_count": sum(case_item["coverage"]["violation_point_count"] for case_item in baseline_cases),
        "unavailable_point_count": sum(case_item["coverage"]["unavailable_point_count"] for case_item in baseline_cases),
        "center_prediction_envelope_mismatch_count": sum(case_item["coverage"]["center_prediction_envelope_mismatch_count"] for case_item in baseline_cases),
        "max_envelope_width": max(baseline_widths) if baseline_widths else None,
        "median_envelope_width": median(baseline_widths),
        "max_residual_upper_bound": max(baseline_residual_bounds) if baseline_residual_bounds else None,
        "median_residual_upper_bound": median(baseline_residual_bounds),
    }
    baseline_expected = baseline_source["totals"]
    baseline_matches = (
        baseline["certified_fold_count"] == baseline_expected["certified_fold_count"]
        and baseline["available_point_count"] == baseline_expected["available_point_count"]
        and baseline["covered_point_count"] == baseline_expected["covered_point_count"]
        and baseline["violation_point_count"] == baseline_expected["violation_point_count"]
        and baseline["unavailable_point_count"] == baseline_expected["unavailable_point_count"]
        and baseline["center_prediction_envelope_mismatch_count"] == baseline_expected["center_prediction_envelope_mismatch_count"]
        and math.isclose(baseline["max_envelope_width"], baseline_expected["max_envelope_width"], rel_tol=0, abs_tol=0)
        and math.isclose(baseline["median_envelope_width"], baseline_expected["median_envelope_width"], rel_tol=0, abs_tol=0)
        and math.isclose(baseline["max_residual_upper_bound"], baseline_expected["max_residual_upper_bound"], rel_tol=0, abs_tol=0)
        and math.isclose(baseline["median_residual_upper_bound"], baseline_expected["median_residual_upper_bound"], rel_tol=0, abs_tol=0)
    )
    baseline["matches_frozen_baseline"] = baseline_matches
    if not baseline_matches:
        raise ValueError("Radius-4 case no longer matches the frozen baseline")

    cases = [case_item for fold in folds for case_item in fold["cases"]]
    unavailable = [case_item["case_id"] for case_item in cases if not case_item["prediction_envelope_available"]]
    totals = {
        "fold_count": len(folds),
        "radius_count": len(radii),
        "case_count": len(cases),
        "held_out_point_count_per_case": 214,
        "unique_distance_count": len({point["x"] for fold in folds for case_item in fold["cases"][:1] for point in case_item["points"]}),
        "maximum_point_evaluations": len(radii) * sum(len(case["held_out_points"]) for case in source["folds"]),
        "maximum_envelope_evaluations": len(radii) * sum(len({float(point["x"]) for point in case["held_out_points"]}) for case in source["folds"]),
        "actual_envelope_evaluation_count": sum(len(case_item["envelopes"]) for case_item in cases),
        "unavailable_case_count": len(unavailable),
        "unavailable_case_ids": unavailable,
        "center_prediction_envelope_mismatch_count": sum(case_item["coverage"]["center_prediction_envelope_mismatch_count"] for case_item in cases),
        "minimum_critical_radius": min(fold["critical"]["radius"] for fold in folds),
        "minimum_critical_radius_fold": min(folds, key=lambda fold: fold["critical"]["radius"])["fold"],
    }
    expected = dict(protocol["expected_structure"])
    expected["maximum_point_evaluations"] = amendment["correction"]["corrected_value"]
    for key, expected_key in [
        ("fold_count", "fold_count"),
        ("radius_count", "radius_count"),
        ("case_count", "case_count"),
        ("held_out_point_count_per_case", "held_out_point_count_per_case"),
        ("unique_distance_count", "unique_distance_count"),
        ("maximum_point_evaluations", "maximum_point_evaluations"),
        ("maximum_envelope_evaluations", "maximum_envelope_evaluations"),
    ]:
        if totals[key] != expected[expected_key]:
            raise ValueError(f"Frozen structure mismatch: {key}")
    if totals["center_prediction_envelope_mismatch_count"]:
        raise ValueError("Center-envelope mismatch detected")
    return {
        "status": "computed_chwirut1_native_ellipsoid_radius_sensitivity",
        "protocol_sha256": sha256(protocol_path),
        "metadata_amendment_sha256": sha256(AMENDMENT),
        "native_identifiability_sha256": sha256(ROOT / protocol["inputs"]["native_identifiability"]["file"]),
        "baseline_bounds_sha256": sha256(ROOT / protocol["inputs"]["baseline_bounds"]["file"]),
        "analysis_scope": {
            "refit": False,
            "changed_center_or_covariance": False,
            "radii_frozen_before_results": radii,
            "radius_optimization": False,
            "critical_radius_is_geometric_only": True,
            "critical_radius_is_probability": False,
            "grid_maximum_is_exact_safe_maximum": False,
            "original_nonlinear_model": True,
            "high_precision_decimal_digits": 80,
            "outward_relative_margin": 1.0e-24,
            "exact_rational_certificate": False,
            "related_prior_dataset": source["analysis_scope"]["related_prior_dataset"],
        },
        "baseline": baseline,
        "folds": folds,
        "totals": totals,
        "decision": protocol["decision"],
        "limitations": [
            "Critical radii are geometric properties of the selected ellipsoids and continuous intervals, not probabilities, optima or universal maxima",
            "The largest certified grid radius is reported separately from the analytic critical radius and is never called the exact safe maximum",
            "Exact critical radii are rejected because denominator positivity is strict; unavailable cases receive no finite envelope",
            "Center-prediction containment and actual-residual coverage are arithmetic consistency checks, not probability coverage or external validation",
            "Envelope widths can grow rapidly with radius and must be reported alongside any positive certificate",
            "Chwirut1 shares its study and native model family with Chwirut2 and is not independent replication",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    actual_critical = [fold.get("critical", {}).get("radius") for fold in summary.get("folds", [])]
    expected_critical = [fold["critical"]["radius"] for fold in expected["folds"]]
    if actual_critical != expected_critical:
        errors.append("Critical radius mismatch")
    for key, value in summary.get("decision", {}).items():
        if key in expected["decision"] and value != expected["decision"][key]:
            errors.append(f"Overclaim or decision-scope mismatch: {key}")
    if summary != expected:
        errors.append("Summary content differs from deterministic frozen-input recomputation")
    return errors


def render_figure(summary, output_path=FIGURE):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path = Path(output_path)
    folds = summary["folds"]
    numbers = [fold["fold"] for fold in folds]
    radii = [case["radius"] for case in folds[0]["cases"]]
    colors = ["#b44b4b", "#316c9b", "#4f7b5b", "#876a32", "#6a4c93"]
    fig, axes = plt.subplots(2, 2, figsize=(16.0, 11.5), constrained_layout=True)
    critical_values = [fold["critical"]["radius"] for fold in folds]
    axes[0, 0].bar(numbers, critical_values, color="#316c9b", width=0.58)
    for fold, value in zip(folds, critical_values):
        axes[0, 0].text(fold["fold"], value, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
    for radius, color in zip(radii, ["#4f7b5b", "#876a32", "#6a4c93", "#b44b4b", "#555555"]):
        axes[0, 0].axhline(radius, color=color, linestyle="--", linewidth=1, label=f"r={radius}")
    axes[0, 0].set_xticks(numbers)
    axes[0, 0].set_xlabel("Frozen fold")
    axes[0, 0].set_ylabel("Analytic critical radius")
    axes[0, 0].set_title("A. Strict positivity requires radius < critical value")
    axes[0, 0].legend(frameon=False, fontsize=8, ncol=2)
    axes[0, 0].grid(axis="y", alpha=0.2)

    for fold, color in zip(folds, colors):
        axes[0, 1].plot(radii, [case["prediction_envelope_available"] for case in fold["cases"]], "o-", color=color, label=f"fold {fold['fold']}")
    axes[0, 1].set_xticks(radii)
    axes[0, 1].set_ylim(-0.15, 1.15)
    axes[0, 1].set_yticks([0, 1], ["unavailable", "certified"])
    axes[0, 1].set_xlabel("Frozen radius")
    axes[0, 1].set_title("B. Certificate status at every grid radius")
    axes[0, 1].grid(alpha=0.2)
    axes[0, 1].legend(frameon=False, fontsize=8)

    for fold, color in zip(folds, colors):
        axes[1, 0].plot(radii, [case["max_envelope_width"] if case["max_envelope_width"] is not None else np.nan for case in fold["cases"]], "o-", color=color, label=f"fold {fold['fold']}")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_xticks(radii)
    axes[1, 0].set_xlabel("Frozen radius")
    axes[1, 0].set_ylabel("Maximum envelope width (log)")
    axes[1, 0].set_title("C. Width sensitivity; unavailable cases have no finite bound")
    axes[1, 0].grid(which="both", alpha=0.2)
    axes[1, 0].legend(frameon=False, fontsize=8)

    for fold, color in zip(folds, colors):
        axes[1, 1].plot(radii, [case["median_envelope_width"] if case["median_envelope_width"] is not None else np.nan for case in fold["cases"]], "o-", color=color, label=f"fold {fold['fold']}")
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_xticks(radii)
    axes[1, 1].set_xlabel("Frozen radius")
    axes[1, 1].set_ylabel("Median envelope width (log)")
    axes[1, 1].set_title("D. No radius is selected as optimal")
    axes[1, 1].grid(which="both", alpha=0.2)
    axes[1, 1].legend(frameon=False, fontsize=8)

    minimum = summary["totals"]["minimum_critical_radius"]
    limiting_fold = summary["totals"]["minimum_critical_radius_fold"]
    fig.suptitle(f"Chwirut1 ellipsoid radius sensitivity: smallest critical radius {minimum:.6f} at fold {limiting_fold}", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Five folds × five frozen radii. Exact critical radii are rejected; grid maxima are not universal safe maxima; no probability or radius optimization.",
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
            errors.append("Missing native ellipsoid radius-sensitivity output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored native ellipsoid radius-sensitivity output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid native ellipsoid radius-sensitivity figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "cases": summary["totals"]["case_count"],
        "unavailable_cases": summary["totals"]["unavailable_case_ids"],
        "minimum_critical_radius": summary["totals"]["minimum_critical_radius"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
