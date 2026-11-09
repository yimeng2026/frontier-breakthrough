"""Construct conservative full-ellipsoid Lipschitz bounds and intersections."""

import argparse
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np

from analyze_chwirut_holdout import sha256
from analyze_enso_native_ellipsoid_continuous import PARAMETER_NAMES
from analyze_enso_native_holdout import native_model
from analyze_roszman1_native_ellipsoid_continuous import outward, support_value

mp.mp.dps = 80
ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/enso-full-ellipsoid-lipschitz-protocol.json"
OUT = ROOT / "validation/enso-full-ellipsoid-lipschitz-intersection.json"
FIGURE = ROOT / "papers/58_ENSO全椭球Lipschitz交集/fig58_enso_full_ellipsoid_lipschitz_intersection.png"
COEFFICIENTS = ["b1", "b2", "b3", "b5", "b6", "b8", "b9"]
COEFFICIENT_INDICES = [0, 1, 2, 4, 5, 7, 8]


def trigonometric_vector(parameters, x):
    x = mp.mpf(str(x))
    annual = 2 * mp.pi * x / 12
    long_1 = 2 * mp.pi * x / mp.mpf(str(parameters["b4"]))
    long_2 = 2 * mp.pi * x / mp.mpf(str(parameters["b7"]))
    return [mp.mpf("1"), mp.cos(annual), mp.sin(annual), mp.cos(long_1), mp.sin(long_1), mp.cos(long_2), mp.sin(long_2)]


def fourier_value(parameters, x):
    vector = trigonometric_vector(parameters, x)
    return sum((mp.mpf(str(parameters[name])) * value for name, value in zip(COEFFICIENTS, vector)), mp.mpf("0"))


def lipschitz_envelope(parameters, covariance, radius, x, period_certificate):
    vector = trigonometric_vector(parameters, x)
    coefficient_matrix = [[covariance[row][column] for column in COEFFICIENT_INDICES] for row in COEFFICIENT_INDICES]
    linear_support = support_value(coefficient_matrix, vector, radius)
    period_values = {}
    for period in ["b4", "b7"]:
        index = PARAMETER_NAMES.index(period)
        direction = [0] * len(PARAMETER_NAMES)
        direction[index] = 1
        delta_max = support_value(covariance, direction, radius)
        period_min = mp.mpf(str(period_certificate[f"{period}_minimum"]))
        center = mp.mpf(str(parameters[period]))
        if period_min <= 0:
            raise ValueError(f"Positive period minimum required for Lipschitz bound: {period}")
        phase_cap = min(mp.mpf("2"), 2 * mp.pi * abs(mp.mpf(str(x))) * delta_max / (center * period_min))
        period_values[period] = {"delta_max": delta_max, "minimum": period_min, "phase_cap": phase_cap}
    amplitude_b4 = abs(mp.mpf(str(parameters["b5"]))) + abs(mp.mpf(str(parameters["b6"]))) + mp.mpf(str(radius)) * (mp.sqrt(mp.mpf(str(covariance[4][4]))) + mp.sqrt(mp.mpf(str(covariance[5][5]))))
    amplitude_b7 = abs(mp.mpf(str(parameters["b8"]))) + abs(mp.mpf(str(parameters["b9"]))) + mp.mpf(str(radius)) * (mp.sqrt(mp.mpf(str(covariance[7][7]))) + mp.sqrt(mp.mpf(str(covariance[8][8]))))
    remainder = amplitude_b4 * period_values["b4"]["phase_cap"] + amplitude_b7 * period_values["b7"]["phase_cap"]
    full_support = linear_support + remainder
    center_prediction = fourier_value(parameters, x)
    native_prediction = float(native_model(float(x), *[float(parameters[name]) for name in PARAMETER_NAMES]))
    if not math.isclose(float(center_prediction), native_prediction, rel_tol=1.0e-12, abs_tol=1.0e-12):
        raise ValueError("Center prediction differs from the original native Fourier model")
    lower = outward(center_prediction - full_support, lower=True)
    upper = outward(center_prediction + full_support, lower=False)
    return {
        "x": float(x),
        "center_prediction": float(center_prediction),
        "linear_support": float(linear_support),
        "remainder_support": float(remainder),
        "full_support": float(full_support),
        "d4": float(period_values["b4"]["phase_cap"]),
        "d7": float(period_values["b7"]["phase_cap"]),
        "amplitude_cap_b4": float(amplitude_b4),
        "amplitude_cap_b7": float(amplitude_b7),
        "period_min_b4": float(period_values["b4"]["minimum"]),
        "period_min_b7": float(period_values["b7"]["minimum"]),
        "prediction_minimum": lower,
        "prediction_maximum": upper,
        "envelope_width": outward(upper - lower, lower=False),
    }


def intersect_bounds(alternative_minimum, alternative_maximum, independent_minimum, independent_maximum):
    lower = max(alternative_minimum, independent_minimum)
    upper = min(alternative_maximum, independent_maximum)
    return {
        "prediction_minimum": lower,
        "prediction_maximum": upper,
        "envelope_width": outward(upper - lower, lower=False),
    }


def median(values):
    return float(np.median(values)) if values else None


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_enso_full_ellipsoid_lipschitz_intersection":
        raise ValueError("Full-ellipsoid Lipschitz protocol is not frozen")
    for key, info in protocol["inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {key}")
    source = json.loads((ROOT / protocol["inputs"]["native_identifiability"]["file"]).read_text(encoding="utf-8"))
    independent = json.loads((ROOT / protocol["inputs"]["independent_bounds"]["file"]).read_text(encoding="utf-8"))
    independent_receipt = json.loads((ROOT / protocol["inputs"]["independent_receipt"]["file"]).read_text(encoding="utf-8"))
    slices = json.loads((ROOT / protocol["inputs"]["slice_witnesses"]["file"]).read_text(encoding="utf-8"))
    slice_receipt = json.loads((ROOT / protocol["inputs"]["slice_receipt"]["file"]).read_text(encoding="utf-8"))
    independent_hash = sha256(ROOT / protocol["inputs"]["independent_bounds"]["file"])
    slice_hash = sha256(ROOT / protocol["inputs"]["slice_witnesses"]["file"])
    independent_receipt_verified = independent_receipt["status"] == "passed" and independent_receipt["summarySha256"] == independent_hash
    slice_receipt_verified = slice_receipt["status"] == "passed" and slice_receipt["summarySha256"] == slice_hash
    if not independent_receipt_verified or not slice_receipt_verified:
        raise ValueError("Frozen baseline or slice receipt mismatch")
    radius = protocol["decomposition_rule"]["baseline_radius"]
    folds = []
    for source_fold, independent_fold, slice_fold in zip(source["folds"], independent["folds"], slices["folds"]):
        if len({source_fold["fold"], independent_fold["fold"], slice_fold["fold"]}) != 1:
            raise ValueError("Frozen fold order changed")
        parameters = source_fold["native_parameters"]
        covariance = source_fold["training_jacobian"]["parameter_covariance_matrix"]
        independent_envelopes = {float(envelope["x"]): envelope for envelope in independent_fold["envelopes"]}
        independent_points = {float(point["x"]): point for point in independent_fold["points"]}
        slice_envelopes = {float(envelope["x"]): envelope for envelope in slice_fold["slice_envelopes"]}
        envelopes = []
        alternative_violations = 0
        intersection_violations = 0
        independent_violations = 0
        feasibility_failures = 0
        center_mismatches = 0
        nonempty_count = 0
        for x in sorted(independent_envelopes):
            alternative = lipschitz_envelope(parameters, covariance, radius, x, independent_fold["period_certificate"])
            baseline = independent_envelopes[x]
            intersection = intersect_bounds(
                alternative["prediction_minimum"], alternative["prediction_maximum"],
                baseline["prediction_minimum"], baseline["prediction_maximum"],
            )
            nonempty = intersection["prediction_minimum"] <= intersection["prediction_maximum"]
            nonempty_count += nonempty
            center = independent_points[x]["native_prediction"]
            if not alternative["prediction_minimum"] <= center <= alternative["prediction_maximum"] or not intersection["prediction_minimum"] <= center <= intersection["prediction_maximum"]:
                center_mismatches += 1
            if alternative["envelope_width"] < baseline["envelope_width"]:
                comparison = "tighter"
            elif alternative["envelope_width"] > baseline["envelope_width"]:
                comparison = "wider"
            else:
                comparison = "equal"
            ratio = intersection["envelope_width"] / baseline["envelope_width"]
            reduction = baseline["envelope_width"] - intersection["envelope_width"]
            tightened = intersection["envelope_width"] < baseline["envelope_width"]
            bound_changed = intersection["prediction_minimum"] > baseline["prediction_minimum"] or intersection["prediction_maximum"] < baseline["prediction_maximum"]
            evaluations = []
            for candidate in slice_envelopes[x]["candidate_evaluations"]:
                prediction = candidate["prediction"]
                feasible = candidate["feasible"] and math.isclose(candidate["ellipsoid_quadratic"], 16.0, rel_tol=1.0e-10, abs_tol=1.0e-10)
                inside_independent = baseline["prediction_minimum"] <= prediction <= baseline["prediction_maximum"]
                inside_alternative = alternative["prediction_minimum"] <= prediction <= alternative["prediction_maximum"]
                inside_intersection = intersection["prediction_minimum"] <= prediction <= intersection["prediction_maximum"]
                feasibility_failures += not feasible
                independent_violations += not inside_independent
                alternative_violations += not inside_alternative
                intersection_violations += not inside_intersection
                evaluations.append({
                    "direction": candidate["direction"],
                    "prediction": prediction,
                    "ellipsoid_quadratic": candidate["ellipsoid_quadratic"],
                    "feasible": feasible,
                    "inside_independent": inside_independent,
                    "inside_alternative": inside_alternative,
                    "inside_intersection": inside_intersection,
                })
            envelopes.append({
                "x": float(x),
                "center_prediction": center,
                "alternative_minimum": alternative["prediction_minimum"],
                "alternative_maximum": alternative["prediction_maximum"],
                "alternative_width": alternative["envelope_width"],
                "alternative_to_independent_width_ratio": alternative["envelope_width"] / baseline["envelope_width"],
                "alternative_comparison": comparison,
                "linear_support": alternative["linear_support"],
                "remainder_support": alternative["remainder_support"],
                "d4": alternative["d4"],
                "d7": alternative["d7"],
                "amplitude_cap_b4": alternative["amplitude_cap_b4"],
                "amplitude_cap_b7": alternative["amplitude_cap_b7"],
                "period_min_b4": alternative["period_min_b4"],
                "period_min_b7": alternative["period_min_b7"],
                "independent_minimum": baseline["prediction_minimum"],
                "independent_maximum": baseline["prediction_maximum"],
                "independent_width": baseline["envelope_width"],
                "intersection_minimum": intersection["prediction_minimum"],
                "intersection_maximum": intersection["prediction_maximum"],
                "intersection_width": intersection["envelope_width"],
                "intersection_to_independent_width_ratio": ratio,
                "intersection_width_reduction": reduction,
                "intersection_tightened": tightened,
                "intersection_bound_changed": bound_changed,
                "intersection_nonempty": nonempty,
                "candidate_evaluations": evaluations,
            })
        if alternative_violations or intersection_violations or independent_violations or feasibility_failures or center_mismatches or nonempty_count != len(envelopes):
            raise ValueError(f"Full-ellipsoid consistency failure: fold {source_fold['fold']}; alternative={alternative_violations}, intersection={intersection_violations}, independent={independent_violations}, feasible={feasibility_failures}, centers={center_mismatches}, nonempty={nonempty_count}")
        alternative_ratios = [envelope["alternative_to_independent_width_ratio"] for envelope in envelopes]
        intersection_ratios = [envelope["intersection_to_independent_width_ratio"] for envelope in envelopes]
        reductions = [envelope["intersection_width_reduction"] for envelope in envelopes]
        largest = max(envelopes, key=lambda envelope: envelope["intersection_width_reduction"])
        folds.append({
            "fold": source_fold["fold"],
            "native_test_rmse": source_fold["test_metrics"]["rmse"],
            "envelopes": envelopes,
            "candidate_evaluation_count": sum(len(envelope["candidate_evaluations"]) for envelope in envelopes),
            "alternative_tighter_count": sum(envelope["alternative_comparison"] == "tighter" for envelope in envelopes),
            "alternative_wider_count": sum(envelope["alternative_comparison"] == "wider" for envelope in envelopes),
            "alternative_equal_count": sum(envelope["alternative_comparison"] == "equal" for envelope in envelopes),
            "intersection_tightened_count": sum(envelope["intersection_tightened"] for envelope in envelopes),
            "intersection_unchanged_count": sum(not envelope["intersection_tightened"] for envelope in envelopes),
            "intersection_bound_changed_count": sum(envelope["intersection_bound_changed"] for envelope in envelopes),
            "nonempty_intersection_count": nonempty_count,
            "alternative_candidate_violation_count": alternative_violations,
            "intersection_candidate_violation_count": intersection_violations,
            "independent_candidate_violation_count": independent_violations,
            "candidate_feasibility_failure_count": feasibility_failures,
            "center_prediction_mismatch_count": center_mismatches,
            "min_alternative_to_independent_width_ratio": min(alternative_ratios),
            "median_alternative_to_independent_width_ratio": median(alternative_ratios),
            "max_alternative_to_independent_width_ratio": max(alternative_ratios),
            "min_intersection_to_independent_width_ratio": min(intersection_ratios),
            "median_intersection_to_independent_width_ratio": median(intersection_ratios),
            "max_intersection_to_independent_width_ratio": max(intersection_ratios),
            "max_intersection_width_reduction": max(reductions),
            "median_intersection_width_reduction": median(reductions),
            "max_alternative_remainder_support": max(envelope["remainder_support"] for envelope in envelopes),
            "largest_intersection_tightening": {
                "x": largest["x"],
                "intersection_to_independent_width_ratio": largest["intersection_to_independent_width_ratio"],
                "intersection_width_reduction": largest["intersection_width_reduction"],
                "independent_minimum": largest["independent_minimum"],
                "independent_maximum": largest["independent_maximum"],
                "alternative_minimum": largest["alternative_minimum"],
                "alternative_maximum": largest["alternative_maximum"],
                "intersection_minimum": largest["intersection_minimum"],
                "intersection_maximum": largest["intersection_maximum"],
            },
        })

    envelopes = [envelope for fold in folds for envelope in fold["envelopes"]]
    alternative_ratios = [envelope["alternative_to_independent_width_ratio"] for envelope in envelopes]
    intersection_ratios = [envelope["intersection_to_independent_width_ratio"] for envelope in envelopes]
    reductions = [envelope["intersection_width_reduction"] for envelope in envelopes]
    largest = max((fold["largest_intersection_tightening"] for fold in folds), key=lambda record: record["intersection_width_reduction"])
    totals = {
        "fold_count": len(folds),
        "held_out_point_count": len(envelopes),
        "alternative_bound_count": len(envelopes),
        "intersection_bound_count": len(envelopes),
        "candidate_evaluation_count": sum(fold["candidate_evaluation_count"] for fold in folds),
        "alternative_tighter_count": sum(fold["alternative_tighter_count"] for fold in folds),
        "alternative_wider_count": sum(fold["alternative_wider_count"] for fold in folds),
        "alternative_equal_count": sum(fold["alternative_equal_count"] for fold in folds),
        "intersection_tightened_count": sum(fold["intersection_tightened_count"] for fold in folds),
        "intersection_unchanged_count": sum(fold["intersection_unchanged_count"] for fold in folds),
        "intersection_bound_changed_count": sum(fold["intersection_bound_changed_count"] for fold in folds),
        "nonempty_intersection_count": sum(fold["nonempty_intersection_count"] for fold in folds),
        "alternative_candidate_violation_count": sum(fold["alternative_candidate_violation_count"] for fold in folds),
        "intersection_candidate_violation_count": sum(fold["intersection_candidate_violation_count"] for fold in folds),
        "independent_candidate_violation_count": sum(fold["independent_candidate_violation_count"] for fold in folds),
        "candidate_feasibility_failure_count": sum(fold["candidate_feasibility_failure_count"] for fold in folds),
        "center_prediction_mismatch_count": sum(fold["center_prediction_mismatch_count"] for fold in folds),
        "min_alternative_to_independent_width_ratio": min(alternative_ratios),
        "median_alternative_to_independent_width_ratio": median(alternative_ratios),
        "max_alternative_to_independent_width_ratio": max(alternative_ratios),
        "min_intersection_to_independent_width_ratio": min(intersection_ratios),
        "median_intersection_to_independent_width_ratio": median(intersection_ratios),
        "max_intersection_to_independent_width_ratio": max(intersection_ratios),
        "max_intersection_width_reduction": max(reductions),
        "median_intersection_width_reduction": median(reductions),
        "max_alternative_remainder_support": max(envelope["remainder_support"] for envelope in envelopes),
        "largest_intersection_tightening": largest,
        "refit_count": 0,
    }
    expected = protocol["expected_structure"]
    for key in [
        "fold_count", "held_out_point_count", "alternative_bound_count", "intersection_bound_count",
        "candidate_evaluation_count", "nonempty_intersection_count", "alternative_candidate_violation_count",
        "intersection_candidate_violation_count", "center_prediction_mismatch_count", "refit_count",
    ]:
        if totals[key] != expected[key]:
            raise ValueError(f"Frozen structural expectation failed: {key}")
    return {
        "status": "computed_enso_full_ellipsoid_lipschitz_intersection",
        "protocol_sha256": sha256(protocol_path),
        "native_identifiability_sha256": sha256(ROOT / protocol["inputs"]["native_identifiability"]["file"]),
        "independent_bounds_sha256": independent_hash,
        "slice_witnesses_sha256": slice_hash,
        "independent_receipt_verified": independent_receipt_verified,
        "slice_receipt_verified": slice_receipt_verified,
        "analysis_scope": {
            **protocol["analysis_scope"],
            "baseline_radius": radius,
            "high_precision_decimal_digits": 80,
            "outward_rounding": True,
            "outward_relative_margin": 1.0e-24,
            "exact_rational_certificate": False,
            "alternative_replaces_baseline": False,
            "probability_region": False,
            "new_period_mechanism": False,
        },
        "known_answer": source["known_answer"],
        "folds": folds,
        "totals": totals,
        "full_ellipsoid_joint_nonlinear_optimum": None,
        "decision": protocol["decision"],
        "limitations": [
            "The alternative uses exact linear decomposition, marginal support, triangle inequality and Lipschitz phase caps; it is not the joint full nonlinear optimum",
            "The marginal coefficient block is used only for the full linear-support term and is not substituted for the fixed-period Schur slice matrix",
            "Alternative bounds may be wider than the independent baseline and every such case is retained",
            "Intersections are never intended to be wider than both valid inputs, but they may be unchanged and are not global optima",
            "Candidate checks are implementation-consistency tests, not the analytic proof or a global optimizer",
            "The Lipschitz phase remainder is not a Taylor model substitution or a probability interval",
            "High-precision outward-rounded numerical intervals are not exact rational-algebra certificates",
            "Positive periods do not prove unique or physical periods; center and candidate containment are not external scientific validation",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    actual_ratios = [envelope.get("intersection_to_independent_width_ratio") for fold in summary.get("folds", []) for envelope in fold.get("envelopes", [])]
    expected_ratios = [envelope["intersection_to_independent_width_ratio"] for fold in expected["folds"] for envelope in fold["envelopes"]]
    if actual_ratios != expected_ratios:
        errors.append("Intersection-to-independent width ratio mismatch")
    for key in ["alternative_candidate_violation_count", "intersection_candidate_violation_count"]:
        if summary.get("totals", {}).get(key) != expected["totals"][key]:
            errors.append(f"Candidate violation count mismatch: {key}")
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
    colors = ["#316c9b", "#4f7b5b", "#876a32", "#6a4c93", "#b44b4b"]
    fig, axes = plt.subplots(2, 2, figsize=(16.0, 11.5), constrained_layout=True)
    for fold, color in zip(folds, colors):
        ratios = [envelope["alternative_to_independent_width_ratio"] for envelope in fold["envelopes"]]
        axes[0, 0].scatter([fold["fold"]] * len(ratios), ratios, s=15, alpha=0.65, color=color, label=f"fold {fold['fold']}")
    axes[0, 0].axhline(1, color="#b44b4b", linestyle="--", linewidth=1, label="alternative = independent")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks(numbers)
    axes[0, 0].set_xlabel("Frozen fold")
    axes[0, 0].set_ylabel("Alternative width / independent width (log)")
    axes[0, 0].set_title("A. The alternative is not assumed tighter")
    axes[0, 0].grid(which="both", alpha=0.2)
    axes[0, 0].legend(frameon=False, fontsize=8)

    for fold, color in zip(folds, colors):
        ratios = [envelope["intersection_to_independent_width_ratio"] for envelope in fold["envelopes"]]
        axes[0, 1].scatter([fold["fold"]] * len(ratios), ratios, s=15, alpha=0.65, color=color, label=f"fold {fold['fold']}")
    axes[0, 1].axhline(1, color="#555555", linestyle="--", linewidth=1)
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_xticks(numbers)
    axes[0, 1].set_xlabel("Frozen fold")
    axes[0, 1].set_ylabel("Intersection width / independent width (log)")
    axes[0, 1].set_title("B. Intersection never widens the baseline")
    axes[0, 1].grid(which="both", alpha=0.2)
    axes[0, 1].legend(frameon=False, fontsize=8)

    for fold, color in zip(folds, colors):
        reductions = [envelope["intersection_width_reduction"] for envelope in fold["envelopes"]]
        axes[1, 0].scatter([fold["fold"]] * len(reductions), reductions, s=15, alpha=0.65, color=color, label=f"fold {fold['fold']}")
    axes[1, 0].axhline(0, color="#555555", linestyle="--", linewidth=1)
    axes[1, 0].set_xticks(numbers)
    axes[1, 0].set_xlabel("Frozen fold")
    axes[1, 0].set_ylabel("Independent width minus intersection width")
    axes[1, 0].set_title("C. Every tightening and unchanged month is retained")
    axes[1, 0].grid(alpha=0.2)
    axes[1, 0].legend(frameon=False, fontsize=8)

    positions = np.arange(len(folds))
    tighter = [fold["alternative_tighter_count"] for fold in folds]
    wider = [fold["alternative_wider_count"] for fold in folds]
    equal = [fold["alternative_equal_count"] for fold in folds]
    axes[1, 1].bar(positions, tighter, color="#316c9b", label="alternative tighter")
    axes[1, 1].bar(positions, wider, bottom=tighter, color="#b44b4b", label="alternative wider")
    axes[1, 1].bar(positions, equal, bottom=[a + b for a, b in zip(tighter, wider)], color="#888888", label="alternative equal")
    axes[1, 1].set_xticks(positions, numbers)
    axes[1, 1].set_xlabel("Frozen fold")
    axes[1, 1].set_ylabel("Month count")
    axes[1, 1].set_title("D. Full alternative comparison inventory")
    axes[1, 1].legend(frameon=False, fontsize=8)
    axes[1, 1].grid(axis="y", alpha=0.2)

    totals = summary["totals"]
    fig.suptitle(f"ENSO full-ellipsoid Lipschitz bounds: {totals['intersection_tightened_count']} tightened, {totals['intersection_unchanged_count']} unchanged; 672/672 candidates inside", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Marginal linear support + Lipschitz period remainder, intersected with stage 47. Candidate checks are consistency tests, not global optimality proof.",
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
            errors.append("Missing full-ellipsoid Lipschitz output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored full-ellipsoid Lipschitz output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid full-ellipsoid Lipschitz figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "alternative_tighter": summary["totals"]["alternative_tighter_count"],
        "alternative_wider": summary["totals"]["alternative_wider_count"],
        "intersection_tightened": summary["totals"]["intersection_tightened_count"],
        "intersection_unchanged": summary["totals"]["intersection_unchanged_count"],
        "intersection_candidate_violations": summary["totals"]["intersection_candidate_violation_count"],
        "median_intersection_ratio": summary["totals"]["median_intersection_to_independent_width_ratio"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
