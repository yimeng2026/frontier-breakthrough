"""Audit fixed-grid ENSO native Fourier ellipsoid radius sensitivity."""

import argparse
import json
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import sha256
from analyze_enso_native_ellipsoid_continuous import (
    critical_period_radius,
    median,
    outward,
    period_certificate,
    prediction_envelope,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/enso-native-ellipsoid-radius-sensitivity-protocol.json"
AMENDMENT = ROOT / "validation/enso-native-ellipsoid-radius-sensitivity-protocol-amendment-01.json"
OUT = ROOT / "validation/enso-native-ellipsoid-radius-sensitivity.json"
FIGURE = ROOT / "papers/55_ENSO原生椭球半径敏感性/fig55_enso_native_ellipsoid_radius_sensitivity.png"


def evaluate_case(source_fold, parameters, covariance, radius, critical):
    unique_x = sorted({float(point["x"]) for point in source_fold["held_out_points"]})
    below = radius < critical["radius"]
    certificate = period_certificate(parameters, covariance, radius)
    available = certificate["positive_certified"]
    if available != below:
        raise ValueError(f"Analytic and outward-rounded period decisions disagree: fold {source_fold['fold']} radius {radius}")
    envelopes = []
    envelope_by_x = {}
    if available:
        for x in unique_x:
            envelope = prediction_envelope(parameters, covariance, radius, x)
            record = {"envelope_id": f"enso:{source_fold['fold']}:{x}", "x": x, **envelope}
            envelopes.append(record)
            envelope_by_x[x] = record
    points = []
    mismatch = 0
    covered = 0
    for index, old in enumerate(source_fold["held_out_points"], start=1):
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
    return {
        "case_id": f"enso:{source_fold['fold']}:r{radius}",
        "radius": radius,
        "analytic_relation": "below_critical" if below else "at_or_above_critical",
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
    }


def aggregate_cases(cases):
    envelopes = [envelope for case in cases for envelope in case["envelopes"]]
    points = [point for case in cases for point in case["points"]]
    widths = [envelope["envelope_width"] for envelope in envelopes]
    residual_bounds = [point["residual_upper_bound"] for point in points if point["residual_upper_bound"] is not None]
    return {
        "certified_case_count": sum(case["prediction_envelope_available"] for case in cases),
        "available_point_count": sum(case["coverage"]["available_point_count"] for case in cases),
        "covered_point_count": sum(case["coverage"]["covered_point_count"] for case in cases),
        "violation_point_count": sum(case["coverage"]["violation_point_count"] for case in cases),
        "unavailable_point_count": sum(case["coverage"]["unavailable_point_count"] for case in cases),
        "center_prediction_envelope_mismatch_count": sum(case["coverage"]["center_prediction_envelope_mismatch_count"] for case in cases),
        "max_envelope_width": max(widths) if widths else None,
        "median_envelope_width": median(widths),
        "max_residual_upper_bound": max(residual_bounds) if residual_bounds else None,
        "median_residual_upper_bound": median(residual_bounds),
    }


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_enso_native_ellipsoid_radius_sensitivity":
        raise ValueError("ENSO ellipsoid radius-sensitivity protocol is not frozen")
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    if amendment["original_protocol"]["sha256"] != sha256(protocol_path):
        raise ValueError("Count amendment original protocol hash mismatch")
    for key, info in protocol["inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {key}")
    source = json.loads((ROOT / protocol["inputs"]["native_identifiability"]["file"]).read_text(encoding="utf-8"))
    baseline_source = json.loads((ROOT / protocol["inputs"]["baseline_bounds"]["file"]).read_text(encoding="utf-8"))
    radii = protocol["grid_rule"]["radii"]
    if radii != [1, 2, 4, 8, 16, 32]:
        raise ValueError("The frozen radius grid changed")
    folds = []
    for source_fold in source["folds"]:
        parameters = source_fold["native_parameters"]
        covariance = source_fold["training_jacobian"]["parameter_covariance_matrix"]
        critical = critical_period_radius(parameters, covariance)
        half = period_certificate(parameters, covariance, critical["radius"] / 2)
        exact = period_certificate(parameters, covariance, critical["radius"])
        negative_control = {
            "half_radius_accepted": half["positive_certified"],
            "exact_radius_rejected": not exact["positive_certified"],
        }
        if not all(negative_control.values()):
            raise ValueError(f"Critical-period negative control failed: {source_fold['fold']}")
        cases = [evaluate_case(source_fold, parameters, covariance, radius, critical) for radius in radii]
        certified_grid = [case["radius"] for case in cases if case["prediction_envelope_available"]]
        folds.append({
            "fold": source_fold["fold"],
            "native_test_rmse": source_fold["test_metrics"]["rmse"],
            "critical_period": critical,
            "negative_control": negative_control,
            "cases": cases,
            "max_certified_grid_radius": max(certified_grid) if certified_grid else None,
            "grid_maximum_scope": "Largest certified radius in the frozen grid only; not the exact or universal safe maximum",
        })

    baseline_radius = protocol["baseline_rule"]["radius"]
    baseline_cases = []
    fold_projection_mismatch_ids = []
    projection_keys = [
        "period_certificate", "prediction_envelope_available", "unavailable_reason", "envelopes", "points",
        "coverage", "max_envelope_width", "median_envelope_width", "max_residual_upper_bound", "median_residual_upper_bound",
    ]
    for fold, baseline_fold in zip(folds, baseline_source["folds"]):
        case = next(case for case in fold["cases"] if case["radius"] == baseline_radius)
        baseline_cases.append(case)
        projection = {
            "fold": fold["fold"],
            "native_test_rmse": fold["native_test_rmse"],
            "critical_period": fold["critical_period"],
            "negative_control": fold["negative_control"],
            **{key: case[key] for key in projection_keys},
        }
        if projection != baseline_fold:
            fold_projection_mismatch_ids.append(fold["fold"])
    baseline = {
        "radius": baseline_radius,
        "certified_fold_count": sum(case["prediction_envelope_available"] for case in baseline_cases),
        **{key: value for key, value in aggregate_cases(baseline_cases).items() if key != "certified_case_count"},
        "exact_fold_projection_match_count": len(folds) - len(fold_projection_mismatch_ids),
        "fold_projection_mismatch_ids": fold_projection_mismatch_ids,
    }
    expected_baseline = baseline_source["totals"]
    baseline_matches = (
        not fold_projection_mismatch_ids
        and baseline["certified_fold_count"] == expected_baseline["certified_fold_count"]
        and all(baseline[key] == expected_baseline[key] for key in [
            "available_point_count", "covered_point_count", "violation_point_count", "unavailable_point_count",
            "center_prediction_envelope_mismatch_count", "max_envelope_width", "median_envelope_width",
            "max_residual_upper_bound", "median_residual_upper_bound",
        ])
    )
    baseline["matches_frozen_baseline"] = baseline_matches
    if not baseline_matches:
        raise ValueError("Radius-4 case no longer exactly matches the frozen stage-47 baseline")

    cases = [case for fold in folds for case in fold["cases"]]
    radius_summaries = []
    for radius in radii:
        selected = [case for case in cases if case["radius"] == radius]
        radius_summaries.append({
            "radius": radius,
            **aggregate_cases(selected),
            "unavailable_case_ids": [case["case_id"] for case in selected if not case["prediction_envelope_available"]],
        })
    unavailable_ids = [case["case_id"] for case in cases if not case["prediction_envelope_available"]]
    minimum_fold = min(folds, key=lambda fold: fold["critical_period"]["radius"])
    aggregate = aggregate_cases(cases)
    totals = {
        "fold_count": len(folds),
        "radius_count": len(radii),
        "case_count": len(cases),
        "held_out_point_count_per_radius": sum(len(fold["held_out_points"]) for fold in source["folds"]),
        "unique_month_count_per_radius": sum(len({float(point["x"]) for point in fold["held_out_points"]}) for fold in source["folds"]),
        "fold_held_out_point_counts": [len(fold["held_out_points"]) for fold in source["folds"]],
        "fold_unique_month_counts": [len({float(point["x"]) for point in fold["held_out_points"]}) for fold in source["folds"]],
        "maximum_point_evaluations": len(radii) * sum(len(fold["held_out_points"]) for fold in source["folds"]),
        "maximum_envelope_evaluations": len(radii) * sum(len({float(point["x"]) for point in fold["held_out_points"]}) for fold in source["folds"]),
        "actual_envelope_evaluation_count": sum(len(case["envelopes"]) for case in cases),
        "certified_case_count": aggregate["certified_case_count"],
        "available_point_count": aggregate["available_point_count"],
        "covered_point_count": aggregate["covered_point_count"],
        "violation_point_count": aggregate["violation_point_count"],
        "unavailable_point_count": aggregate["unavailable_point_count"],
        "unavailable_case_count": len(unavailable_ids),
        "unavailable_case_ids": unavailable_ids,
        "center_prediction_envelope_mismatch_count": aggregate["center_prediction_envelope_mismatch_count"],
        "max_envelope_width": aggregate["max_envelope_width"],
        "median_envelope_width": aggregate["median_envelope_width"],
        "max_residual_upper_bound": aggregate["max_residual_upper_bound"],
        "median_residual_upper_bound": aggregate["median_residual_upper_bound"],
        "minimum_critical_period_radius": minimum_fold["critical_period"]["radius"],
        "minimum_critical_period_radius_fold": minimum_fold["fold"],
        "minimum_critical_period_parameter": minimum_fold["critical_period"]["limiting_parameter"],
    }
    expected = dict(protocol["expected_structure"])
    expected.update(amendment["correction"]["corrected_structure"])
    for key in [
        "fold_count", "radius_count", "case_count", "held_out_point_count_per_radius", "unique_month_count_per_radius",
        "fold_held_out_point_counts", "fold_unique_month_counts", "maximum_point_evaluations", "maximum_envelope_evaluations",
    ]:
        if totals[key] != expected[key]:
            raise ValueError(f"Frozen structure mismatch: {key}")
    if totals["center_prediction_envelope_mismatch_count"]:
        raise ValueError("Center-envelope mismatch detected")
    return {
        "status": "computed_enso_native_ellipsoid_radius_sensitivity",
        "protocol_sha256": sha256(protocol_path),
        "metadata_amendment_sha256": sha256(AMENDMENT),
        "native_identifiability_sha256": sha256(ROOT / protocol["inputs"]["native_identifiability"]["file"]),
        "baseline_bounds_sha256": sha256(ROOT / protocol["inputs"]["baseline_bounds"]["file"]),
        "baseline_runner_sha256": sha256(ROOT / protocol["inputs"]["baseline_runner"]["file"]),
        "analysis_scope": {
            **protocol["analysis_scope"],
            "refit": False,
            "radii_frozen_before_results": radii,
            "original_fourier_model": True,
            "independent_coefficient_relaxation": True,
            "high_precision_decimal_digits": 80,
            "outward_rounding": True,
            "outward_relative_margin": 1.0e-24,
            "exact_rational_certificate": False,
            "probability_region": False,
            "new_period_mechanism": False,
            "count_correction": {
                "original_maximum_evaluations": 5040,
                "corrected_maximum_evaluations": 1008,
                "original_protocol_preserved": True,
            },
        },
        "known_answer": source["known_answer"],
        "parameter_stability": source["parameter_stability"],
        "baseline": baseline,
        "folds": folds,
        "radius_summaries": radius_summaries,
        "totals": totals,
        "decision": protocol["decision"],
        "limitations": [
            "This is a retrospective fixed-grid sensitivity audit, not prospective independent validation or radius optimization",
            "Critical radii are geometric properties of the selected ellipsoids, not probabilities, physical periods or universal maxima",
            "The largest certified grid radius is separate from the analytic critical radius and is not an exact safe maximum",
            "Exact critical radii are rejected because period positivity is strict; unavailable cases receive no finite envelope",
            "Independent coefficient relaxations are conservative and are not joint nonlinear optima; finite bounds need not be informative",
            "Center-prediction containment and actual-residual coverage are arithmetic consistency checks, not probability coverage or external validation",
            "High-precision outward-rounded numerical certificates are not exact rational-algebra proofs",
            "The optimizer mismatch and certified forward pass remain known-answer diagnostics, not holdout evidence",
            "The count correction is explicit and the original protocol and all stage-47 historical files remain unchanged",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    actual_critical = [fold.get("critical_period", {}).get("radius") for fold in summary.get("folds", [])]
    expected_critical = [fold["critical_period"]["radius"] for fold in expected["folds"]]
    if actual_critical != expected_critical:
        errors.append("Critical period radius mismatch")
    for key, value in summary.get("decision", {}).items():
        if key in expected["decision"] and value != expected["decision"][key]:
            errors.append(f"Overclaim or decision-scope mismatch: {key}")
    if not summary.get("baseline", {}).get("matches_frozen_baseline", False):
        errors.append("Frozen radius-4 baseline mismatch")
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
    positions = np.arange(len(radii))
    colors = ["#316c9b", "#4f7b5b", "#876a32", "#6a4c93", "#b44b4b"]
    fig, axes = plt.subplots(2, 2, figsize=(16.0, 11.5), constrained_layout=True)

    for name, color, marker in [("b4", "#316c9b", "o"), ("b7", "#876a32", "s")]:
        axes[0, 0].plot(numbers, [fold["critical_period"][f"{name}_radius"] for fold in folds], marker=marker, color=color, label=f"{name} critical radius")
    for index, radius in enumerate(radii):
        axes[0, 0].axhline(radius, color="#666666", linestyle="--", linewidth=0.8, alpha=0.6, label="frozen grid radii" if index == 0 else None)
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks(numbers)
    axes[0, 0].set_xlabel("Frozen fold")
    axes[0, 0].set_ylabel("Positive-period critical radius (log)")
    axes[0, 0].set_title("A. Analytic thresholds and the fixed grid")
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 0].grid(which="both", alpha=0.18)

    for fold, color in zip(folds, colors):
        axes[0, 1].plot(positions, [case["prediction_envelope_available"] for case in fold["cases"]], "o-", color=color, label=f"fold {fold['fold']}")
    axes[0, 1].set_xticks(positions, radii)
    axes[0, 1].set_ylim(-0.15, 1.15)
    axes[0, 1].set_yticks([0, 1], ["unavailable", "certified"])
    axes[0, 1].set_xlabel("Frozen radius")
    axes[0, 1].set_title("B. All 30 case outcomes; none are hidden")
    axes[0, 1].grid(alpha=0.2)
    axes[0, 1].legend(frameon=False, fontsize=8, ncol=2)

    for fold, color in zip(folds, colors):
        axes[1, 0].plot(positions, [case["max_envelope_width"] if case["max_envelope_width"] is not None else np.nan for case in fold["cases"]], "o-", color=color, label=f"fold {fold['fold']}")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_xticks(positions, radii)
    axes[1, 0].set_xlabel("Frozen radius")
    axes[1, 0].set_ylabel("Maximum envelope width (log)")
    axes[1, 0].set_title("C. Width sensitivity; unavailable cases have no bound")
    axes[1, 0].grid(which="both", alpha=0.2)
    axes[1, 0].legend(frameon=False, fontsize=8, ncol=2)

    for fold, color in zip(folds, colors):
        axes[1, 1].plot(positions, [case["median_envelope_width"] if case["median_envelope_width"] is not None else np.nan for case in fold["cases"]], "o-", color=color, label=f"fold {fold['fold']}")
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_xticks(positions, radii)
    axes[1, 1].set_xlabel("Frozen radius")
    axes[1, 1].set_ylabel("Median envelope width (log)")
    axes[1, 1].set_title("D. Width information is not a radius objective")
    axes[1, 1].grid(which="both", alpha=0.2)
    axes[1, 1].legend(frameon=False, fontsize=8, ncol=2)

    totals = summary["totals"]
    fig.suptitle(f"ENSO native Fourier radius sensitivity: {totals['case_count']} cases; {totals['actual_envelope_evaluation_count']} available envelopes; {totals['unavailable_point_count']} unavailable points", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Five folds × six frozen radii; 1008 point evaluations. Radius 4 exactly reproduces stage 47; no probability, physical-period or radius-optimization claim.",
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
            errors.append("Missing ENSO ellipsoid radius-sensitivity output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored ENSO ellipsoid radius-sensitivity output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid ENSO ellipsoid radius-sensitivity figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "cases": summary["totals"]["case_count"],
        "point_evaluations": summary["totals"]["maximum_point_evaluations"],
        "actual_envelopes": summary["totals"]["actual_envelope_evaluation_count"],
        "unavailable_cases": summary["totals"]["unavailable_case_ids"],
        "baseline_matches": summary["baseline"]["matches_frozen_baseline"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
