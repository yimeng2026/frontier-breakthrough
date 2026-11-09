"""Construct ENSO phase-interval bounds and triple intersections."""

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
PROTOCOL = ROOT / "validation/enso-phase-interval-triple-protocol.json"
OUT = ROOT / "validation/enso-phase-interval-triple-intersection.json"
FIGURE = ROOT / "papers/59_ENSO三角区间三重交集/fig59_enso_phase_interval_triple_intersection.png"
COEFFICIENTS = ["b1", "b2", "b3", "b5", "b6", "b8", "b9"]
COEFFICIENT_INDICES = [0, 1, 2, 4, 5, 7, 8]
TWO_PI = 2 * mp.pi


def _trig_interval_mp(lower, upper, kind):
    if kind not in {"sin", "cos"}:
        raise ValueError("Trigonometric interval kind must be sin or cos")
    lower = mp.mpf(str(lower))
    upper = mp.mpf(str(upper))
    if lower > upper:
        lower, upper = upper, lower
    if upper - lower >= TWO_PI:
        return mp.mpf("-1"), mp.mpf("1")
    points = [lower, upper]
    targets = [mp.mpf("0"), mp.pi] if kind == "cos" else [mp.pi / 2, -mp.pi / 2]
    for target in targets:
        first = int(mp.ceil((lower - target) / TWO_PI))
        last = int(mp.floor((upper - target) / TWO_PI))
        for index in range(first, last + 1):
            points.append(target + index * TWO_PI)
    function = mp.cos if kind == "cos" else mp.sin
    values = [function(point) for point in points]
    return min(values), max(values)


def trigonometric_interval(lower, upper, kind):
    minimum, maximum = _trig_interval_mp(lower, upper, kind)
    return {"minimum": float(minimum), "maximum": float(maximum)}


def _product_interval_mp(coefficient_minimum, coefficient_maximum, difference_minimum, difference_maximum):
    products = [
        coefficient_minimum * difference_minimum,
        coefficient_minimum * difference_maximum,
        coefficient_maximum * difference_minimum,
        coefficient_maximum * difference_maximum,
    ]
    return min(products), max(products)


def product_interval(coefficient_minimum, coefficient_maximum, difference_minimum, difference_maximum):
    values = [mp.mpf(str(value)) for value in [coefficient_minimum, coefficient_maximum, difference_minimum, difference_maximum]]
    minimum, maximum = _product_interval_mp(*values)
    return {"minimum": float(minimum), "maximum": float(maximum)}


def trigonometric_vector(parameters, x):
    x = mp.mpf(str(x))
    annual = TWO_PI * x / 12
    long_1 = TWO_PI * x / mp.mpf(str(parameters["b4"]))
    long_2 = TWO_PI * x / mp.mpf(str(parameters["b7"]))
    return [mp.mpf("1"), mp.cos(annual), mp.sin(annual), mp.cos(long_1), mp.sin(long_1), mp.cos(long_2), mp.sin(long_2)]


def fourier_value(parameters, x):
    vector = trigonometric_vector(parameters, x)
    return sum((mp.mpf(str(parameters[name])) * value for name, value in zip(COEFFICIENTS, vector)), mp.mpf("0"))


def phase_envelope(parameters, covariance, radius, x, period_certificate, independent_envelope):
    vector = trigonometric_vector(parameters, x)
    coefficient_matrix = [[covariance[row][column] for column in COEFFICIENT_INDICES] for row in COEFFICIENT_INDICES]
    linear_support = support_value(coefficient_matrix, vector, radius)
    terms = {term["parameter"]: term for term in independent_envelope["terms"]}
    remainder_minimum = mp.mpf("0")
    remainder_maximum = mp.mpf("0")
    period_details = {}
    for period, first, second in [("b4", "b5", "b6"), ("b7", "b8", "b9")]:
        period_minimum = mp.mpf(str(period_certificate[f"{period}_minimum"]))
        period_maximum = mp.mpf(str(period_certificate[f"{period}_maximum"]))
        if period_minimum <= 0 or period_maximum < period_minimum:
            raise ValueError(f"Invalid positive period interval: {period}")
        x_mp = mp.mpf(str(x))
        if x_mp > 0:
            phase_lower = TWO_PI * x_mp / period_maximum
            phase_upper = TWO_PI * x_mp / period_minimum
        elif x_mp < 0:
            phase_lower = TWO_PI * x_mp / period_minimum
            phase_upper = TWO_PI * x_mp / period_maximum
        else:
            phase_lower = phase_upper = mp.mpf("0")
        center_phase = TWO_PI * x_mp / mp.mpf(str(parameters[period]))
        cosine_minimum, cosine_maximum = _trig_interval_mp(phase_lower, phase_upper, "cos")
        sine_minimum, sine_maximum = _trig_interval_mp(phase_lower, phase_upper, "sin")
        center_cosine = mp.cos(center_phase)
        center_sine = mp.sin(center_phase)
        for coefficient, trig_kind, trig_min, trig_max, center_trig in [
            (first, "cos", cosine_minimum, cosine_maximum, center_cosine),
            (second, "sin", sine_minimum, sine_maximum, center_sine),
        ]:
            difference_minimum = trig_min - center_trig
            difference_maximum = trig_max - center_trig
            coefficient_minimum = mp.mpf(str(terms[coefficient]["coefficient_minimum"]))
            coefficient_maximum = mp.mpf(str(terms[coefficient]["coefficient_maximum"]))
            product_minimum, product_maximum = _product_interval_mp(coefficient_minimum, coefficient_maximum, difference_minimum, difference_maximum)
            remainder_minimum += product_minimum
            remainder_maximum += product_maximum
        period_details[period] = {
            "phase_minimum": float(phase_lower),
            "phase_maximum": float(phase_upper),
            "cosine_minimum": float(cosine_minimum),
            "cosine_maximum": float(cosine_maximum),
            "sine_minimum": float(sine_minimum),
            "sine_maximum": float(sine_maximum),
            "period_minimum": float(period_minimum),
            "period_maximum": float(period_maximum),
        }
    center_prediction = fourier_value(parameters, x)
    native_prediction = float(native_model(float(x), *[float(parameters[name]) for name in PARAMETER_NAMES]))
    if not math.isclose(float(center_prediction), native_prediction, rel_tol=1.0e-12, abs_tol=1.0e-12):
        raise ValueError("Center prediction differs from the original native Fourier model")
    lower = outward(center_prediction - linear_support + remainder_minimum, lower=True)
    upper = outward(center_prediction + linear_support + remainder_maximum, lower=False)
    return {
        "x": float(x),
        "center_prediction": float(center_prediction),
        "linear_support": float(linear_support),
        "remainder_minimum": float(remainder_minimum),
        "remainder_maximum": float(remainder_maximum),
        "period_details": period_details,
        "prediction_minimum": lower,
        "prediction_maximum": upper,
        "envelope_width": outward(upper - lower, lower=False),
    }


def intersect_three_bounds(phase_minimum, phase_maximum, independent_minimum, independent_maximum, lipschitz_minimum, lipschitz_maximum):
    lower = max(phase_minimum, independent_minimum, lipschitz_minimum)
    upper = min(phase_maximum, independent_maximum, lipschitz_maximum)
    return {
        "prediction_minimum": lower,
        "prediction_maximum": upper,
        "envelope_width": outward(upper - lower, lower=False),
    }


def median(values):
    return float(np.median(values)) if values else None


def comparison(value, baseline):
    return "tighter" if value < baseline else "wider" if value > baseline else "equal"


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_enso_phase_interval_triple_intersection":
        raise ValueError("Phase-interval triple-intersection protocol is not frozen")
    for key, info in protocol["inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {key}")
    source = json.loads((ROOT / protocol["inputs"]["native_identifiability"]["file"]).read_text(encoding="utf-8"))
    independent = json.loads((ROOT / protocol["inputs"]["independent_bounds"]["file"]).read_text(encoding="utf-8"))
    independent_receipt = json.loads((ROOT / protocol["inputs"]["independent_receipt"]["file"]).read_text(encoding="utf-8"))
    slices = json.loads((ROOT / protocol["inputs"]["slice_witnesses"]["file"]).read_text(encoding="utf-8"))
    slice_receipt = json.loads((ROOT / protocol["inputs"]["slice_receipt"]["file"]).read_text(encoding="utf-8"))
    lipschitz = json.loads((ROOT / protocol["inputs"]["lipschitz_bounds"]["file"]).read_text(encoding="utf-8"))
    lipschitz_receipt = json.loads((ROOT / protocol["inputs"]["lipschitz_receipt"]["file"]).read_text(encoding="utf-8"))
    independent_hash = sha256(ROOT / protocol["inputs"]["independent_bounds"]["file"])
    slice_hash = sha256(ROOT / protocol["inputs"]["slice_witnesses"]["file"])
    lipschitz_hash = sha256(ROOT / protocol["inputs"]["lipschitz_bounds"]["file"])
    independent_receipt_verified = independent_receipt["status"] == "passed" and independent_receipt["summarySha256"] == independent_hash
    slice_receipt_verified = slice_receipt["status"] == "passed" and slice_receipt["summarySha256"] == slice_hash
    lipschitz_receipt_verified = lipschitz_receipt["status"] == "passed" and lipschitz_receipt["summarySha256"] == lipschitz_hash
    if not independent_receipt_verified or not slice_receipt_verified or not lipschitz_receipt_verified:
        raise ValueError("Frozen independent, slice or Lipschitz receipt mismatch")
    if slices["totals"]["candidate_evaluation_count"] != 672 or lipschitz["totals"]["candidate_evaluation_count"] != 672:
        raise ValueError("Frozen candidate count changed")
    radius = protocol["phase_interval_rule"]["baseline_radius"]
    folds = []
    for source_fold, independent_fold, slice_fold, lipschitz_fold in zip(source["folds"], independent["folds"], slices["folds"], lipschitz["folds"]):
        if len({source_fold["fold"], independent_fold["fold"], slice_fold["fold"], lipschitz_fold["fold"]}) != 1:
            raise ValueError("Frozen fold order changed")
        parameters = source_fold["native_parameters"]
        covariance = source_fold["training_jacobian"]["parameter_covariance_matrix"]
        independent_envelopes = {float(envelope["x"]): envelope for envelope in independent_fold["envelopes"]}
        lipschitz_envelopes = {float(envelope["x"]): envelope for envelope in lipschitz_fold["envelopes"]}
        envelopes = []
        phase_violations = 0
        triple_violations = 0
        center_mismatches = 0
        feasibility_failures = 0
        nonempty_count = 0
        for x in sorted(independent_envelopes):
            baseline = independent_envelopes[x]
            lipschitz_baseline = lipschitz_envelopes[x]
            alternative = phase_envelope(parameters, covariance, radius, x, independent_fold["period_certificate"], baseline)
            triple = intersect_three_bounds(
                alternative["prediction_minimum"], alternative["prediction_maximum"],
                baseline["prediction_minimum"], baseline["prediction_maximum"],
                lipschitz_baseline["intersection_minimum"], lipschitz_baseline["intersection_maximum"],
            )
            nonempty = triple["prediction_minimum"] <= triple["prediction_maximum"]
            nonempty_count += nonempty
            center = lipschitz_baseline["center_prediction"]
            if not alternative["prediction_minimum"] <= center <= alternative["prediction_maximum"] or not triple["prediction_minimum"] <= center <= triple["prediction_maximum"]:
                center_mismatches += 1
            evaluations = []
            for candidate in lipschitz_baseline["candidate_evaluations"]:
                prediction = candidate["prediction"]
                feasible = candidate["feasible"] and math.isclose(candidate["ellipsoid_quadratic"], 16.0, rel_tol=1.0e-10, abs_tol=1.0e-10)
                inside_independent = baseline["prediction_minimum"] <= prediction <= baseline["prediction_maximum"]
                inside_lipschitz = lipschitz_baseline["intersection_minimum"] <= prediction <= lipschitz_baseline["intersection_maximum"]
                inside_phase = alternative["prediction_minimum"] <= prediction <= alternative["prediction_maximum"]
                inside_triple = triple["prediction_minimum"] <= prediction <= triple["prediction_maximum"]
                if not candidate["inside_independent"] or not candidate["inside_alternative"] or not candidate["inside_intersection"] or not inside_independent or not inside_lipschitz:
                    raise ValueError("Frozen independent or Lipschitz candidate containment changed")
                feasibility_failures += not feasible
                phase_violations += not inside_phase
                triple_violations += not inside_triple
                evaluations.append({
                    "direction": candidate["direction"],
                    "prediction": prediction,
                    "ellipsoid_quadratic": candidate["ellipsoid_quadratic"],
                    "feasible": feasible,
                    "inside_independent": inside_independent,
                    "inside_lipschitz_intersection": inside_lipschitz,
                    "inside_phase_alternative": inside_phase,
                    "inside_triple_intersection": inside_triple,
                })
            envelopes.append({
                "x": float(x),
                "center_prediction": center,
                "phase_minimum": alternative["prediction_minimum"],
                "phase_maximum": alternative["prediction_maximum"],
                "phase_width": alternative["envelope_width"],
                "phase_to_independent_width_ratio": alternative["envelope_width"] / baseline["envelope_width"],
                "phase_to_lipschitz_width_ratio": alternative["envelope_width"] / lipschitz_baseline["intersection_width"],
                "phase_comparison_to_independent": comparison(alternative["envelope_width"], baseline["envelope_width"]),
                "phase_comparison_to_lipschitz": comparison(alternative["envelope_width"], lipschitz_baseline["intersection_width"]),
                "linear_support": alternative["linear_support"],
                "remainder_minimum": alternative["remainder_minimum"],
                "remainder_maximum": alternative["remainder_maximum"],
                "period_details": alternative["period_details"],
                "independent_minimum": baseline["prediction_minimum"],
                "independent_maximum": baseline["prediction_maximum"],
                "independent_width": baseline["envelope_width"],
                "lipschitz_intersection_minimum": lipschitz_baseline["intersection_minimum"],
                "lipschitz_intersection_maximum": lipschitz_baseline["intersection_maximum"],
                "lipschitz_intersection_width": lipschitz_baseline["intersection_width"],
                "triple_minimum": triple["prediction_minimum"],
                "triple_maximum": triple["prediction_maximum"],
                "triple_width": triple["envelope_width"],
                "triple_to_lipschitz_width_ratio": triple["envelope_width"] / lipschitz_baseline["intersection_width"],
                "triple_width_reduction": lipschitz_baseline["intersection_width"] - triple["envelope_width"],
                "triple_tightened": triple["envelope_width"] < lipschitz_baseline["intersection_width"],
                "triple_bound_changed": triple["prediction_minimum"] > lipschitz_baseline["intersection_minimum"] or triple["prediction_maximum"] < lipschitz_baseline["intersection_maximum"],
                "triple_nonempty": nonempty,
                "candidate_evaluations": evaluations,
            })
        if phase_violations or triple_violations or center_mismatches or feasibility_failures or nonempty_count != len(envelopes):
            raise ValueError(f"Phase-interval consistency failure: fold {source_fold['fold']}; phase={phase_violations}, triple={triple_violations}, centers={center_mismatches}, feasible={feasibility_failures}, nonempty={nonempty_count}")
        phase_independent_ratios = [envelope["phase_to_independent_width_ratio"] for envelope in envelopes]
        phase_lipschitz_ratios = [envelope["phase_to_lipschitz_width_ratio"] for envelope in envelopes]
        triple_ratios = [envelope["triple_to_lipschitz_width_ratio"] for envelope in envelopes]
        reductions = [envelope["triple_width_reduction"] for envelope in envelopes]
        largest = max(envelopes, key=lambda envelope: envelope["triple_width_reduction"])
        folds.append({
            "fold": source_fold["fold"],
            "native_test_rmse": source_fold["test_metrics"]["rmse"],
            "envelopes": envelopes,
            "candidate_evaluation_count": sum(len(envelope["candidate_evaluations"]) for envelope in envelopes),
            "phase_tighter_than_independent_count": sum(envelope["phase_comparison_to_independent"] == "tighter" for envelope in envelopes),
            "phase_wider_than_independent_count": sum(envelope["phase_comparison_to_independent"] == "wider" for envelope in envelopes),
            "phase_equal_to_independent_count": sum(envelope["phase_comparison_to_independent"] == "equal" for envelope in envelopes),
            "phase_tighter_than_lipschitz_count": sum(envelope["phase_comparison_to_lipschitz"] == "tighter" for envelope in envelopes),
            "phase_wider_than_lipschitz_count": sum(envelope["phase_comparison_to_lipschitz"] == "wider" for envelope in envelopes),
            "phase_equal_to_lipschitz_count": sum(envelope["phase_comparison_to_lipschitz"] == "equal" for envelope in envelopes),
            "triple_tightened_count": sum(envelope["triple_tightened"] for envelope in envelopes),
            "triple_unchanged_count": sum(not envelope["triple_tightened"] for envelope in envelopes),
            "triple_bound_changed_count": sum(envelope["triple_bound_changed"] for envelope in envelopes),
            "nonempty_triple_intersection_count": nonempty_count,
            "phase_candidate_violation_count": phase_violations,
            "triple_candidate_violation_count": triple_violations,
            "candidate_feasibility_failure_count": feasibility_failures,
            "center_prediction_mismatch_count": center_mismatches,
            "min_phase_to_independent_width_ratio": min(phase_independent_ratios),
            "median_phase_to_independent_width_ratio": median(phase_independent_ratios),
            "max_phase_to_independent_width_ratio": max(phase_independent_ratios),
            "min_phase_to_lipschitz_width_ratio": min(phase_lipschitz_ratios),
            "median_phase_to_lipschitz_width_ratio": median(phase_lipschitz_ratios),
            "max_phase_to_lipschitz_width_ratio": max(phase_lipschitz_ratios),
            "min_triple_to_lipschitz_width_ratio": min(triple_ratios),
            "median_triple_to_lipschitz_width_ratio": median(triple_ratios),
            "max_triple_to_lipschitz_width_ratio": max(triple_ratios),
            "max_triple_width_reduction": max(reductions),
            "median_triple_width_reduction": median(reductions),
            "max_phase_remainder_width": max(envelope["remainder_maximum"] - envelope["remainder_minimum"] for envelope in envelopes),
            "largest_triple_tightening": {
                "x": largest["x"],
                "triple_to_lipschitz_width_ratio": largest["triple_to_lipschitz_width_ratio"],
                "triple_width_reduction": largest["triple_width_reduction"],
                "phase_minimum": largest["phase_minimum"],
                "phase_maximum": largest["phase_maximum"],
                "lipschitz_intersection_minimum": largest["lipschitz_intersection_minimum"],
                "lipschitz_intersection_maximum": largest["lipschitz_intersection_maximum"],
                "triple_minimum": largest["triple_minimum"],
                "triple_maximum": largest["triple_maximum"],
            },
        })

    envelopes = [envelope for fold in folds for envelope in fold["envelopes"]]
    phase_independent_ratios = [envelope["phase_to_independent_width_ratio"] for envelope in envelopes]
    phase_lipschitz_ratios = [envelope["phase_to_lipschitz_width_ratio"] for envelope in envelopes]
    triple_ratios = [envelope["triple_to_lipschitz_width_ratio"] for envelope in envelopes]
    reductions = [envelope["triple_width_reduction"] for envelope in envelopes]
    largest = max((fold["largest_triple_tightening"] for fold in folds), key=lambda record: record["triple_width_reduction"])
    totals = {
        "fold_count": len(folds),
        "held_out_point_count": len(envelopes),
        "phase_alternative_bound_count": len(envelopes),
        "triple_intersection_bound_count": len(envelopes),
        "candidate_evaluation_count": sum(fold["candidate_evaluation_count"] for fold in folds),
        "phase_tighter_than_independent_count": sum(fold["phase_tighter_than_independent_count"] for fold in folds),
        "phase_wider_than_independent_count": sum(fold["phase_wider_than_independent_count"] for fold in folds),
        "phase_equal_to_independent_count": sum(fold["phase_equal_to_independent_count"] for fold in folds),
        "phase_tighter_than_lipschitz_count": sum(fold["phase_tighter_than_lipschitz_count"] for fold in folds),
        "phase_wider_than_lipschitz_count": sum(fold["phase_wider_than_lipschitz_count"] for fold in folds),
        "phase_equal_to_lipschitz_count": sum(fold["phase_equal_to_lipschitz_count"] for fold in folds),
        "triple_tightened_count": sum(fold["triple_tightened_count"] for fold in folds),
        "triple_unchanged_count": sum(fold["triple_unchanged_count"] for fold in folds),
        "triple_bound_changed_count": sum(fold["triple_bound_changed_count"] for fold in folds),
        "nonempty_triple_intersection_count": sum(fold["nonempty_triple_intersection_count"] for fold in folds),
        "phase_candidate_violation_count": sum(fold["phase_candidate_violation_count"] for fold in folds),
        "triple_candidate_violation_count": sum(fold["triple_candidate_violation_count"] for fold in folds),
        "candidate_feasibility_failure_count": sum(fold["candidate_feasibility_failure_count"] for fold in folds),
        "center_prediction_mismatch_count": sum(fold["center_prediction_mismatch_count"] for fold in folds),
        "min_phase_to_independent_width_ratio": min(phase_independent_ratios),
        "median_phase_to_independent_width_ratio": median(phase_independent_ratios),
        "max_phase_to_independent_width_ratio": max(phase_independent_ratios),
        "min_phase_to_lipschitz_width_ratio": min(phase_lipschitz_ratios),
        "median_phase_to_lipschitz_width_ratio": median(phase_lipschitz_ratios),
        "max_phase_to_lipschitz_width_ratio": max(phase_lipschitz_ratios),
        "min_triple_to_lipschitz_width_ratio": min(triple_ratios),
        "median_triple_to_lipschitz_width_ratio": median(triple_ratios),
        "max_triple_to_lipschitz_width_ratio": max(triple_ratios),
        "max_triple_width_reduction": max(reductions),
        "median_triple_width_reduction": median(reductions),
        "max_phase_remainder_width": max(envelope["remainder_maximum"] - envelope["remainder_minimum"] for envelope in envelopes),
        "largest_triple_tightening": largest,
        "refit_count": 0,
    }
    expected = protocol["expected_structure"]
    for key in [
        "fold_count", "held_out_point_count", "phase_alternative_bound_count", "triple_intersection_bound_count",
        "candidate_evaluation_count", "nonempty_triple_intersection_count", "phase_candidate_violation_count",
        "triple_candidate_violation_count", "center_prediction_mismatch_count", "refit_count",
    ]:
        if totals[key] != expected[key]:
            raise ValueError(f"Frozen structural expectation failed: {key}")
    return {
        "status": "computed_enso_phase_interval_triple_intersection",
        "protocol_sha256": sha256(protocol_path),
        "native_identifiability_sha256": sha256(ROOT / protocol["inputs"]["native_identifiability"]["file"]),
        "independent_bounds_sha256": independent_hash,
        "slice_witnesses_sha256": slice_hash,
        "lipschitz_bounds_sha256": lipschitz_hash,
        "independent_receipt_verified": independent_receipt_verified,
        "slice_receipt_verified": slice_receipt_verified,
        "lipschitz_receipt_verified": lipschitz_receipt_verified,
        "analysis_scope": {
            **protocol["analysis_scope"],
            "baseline_radius": radius,
            "high_precision_decimal_digits": 80,
            "outward_rounding": True,
            "outward_relative_margin": 1.0e-24,
            "exact_rational_certificate": False,
            "historical_baselines_replaced": False,
            "probability_region": False,
            "new_period_mechanism": False,
        },
        "known_answer": source["known_answer"],
        "folds": folds,
        "totals": totals,
        "full_ellipsoid_joint_nonlinear_optimum": None,
        "decision": protocol["decision"],
        "limitations": [
            "Trigonometric ranges are computed exactly over frozen period intervals by endpoint and critical-point enumeration, not from point estimates",
            "Independent coefficient/product interval relaxations and the linear-support triangle inequality are conservative but not a joint global optimum",
            "The phase alternative may be wider than either earlier bound and every such month is retained",
            "The triple intersection cannot be wider than its valid inputs but may remain unchanged and is not a global optimum",
            "Candidate checks are implementation-consistency tests, not the interval proof or a global optimizer",
            "High-precision numerical interval arithmetic is not exact rational algebra or a probability region",
            "Positive periods do not prove unique or physical periods; center and candidate containment are not external scientific validation",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    actual_ratios = [envelope.get("triple_to_lipschitz_width_ratio") for fold in summary.get("folds", []) for envelope in fold.get("envelopes", [])]
    expected_ratios = [envelope["triple_to_lipschitz_width_ratio"] for fold in expected["folds"] for envelope in fold["envelopes"]]
    if actual_ratios != expected_ratios:
        errors.append("Triple-to-Lipschitz width ratio mismatch")
    for key in ["phase_candidate_violation_count", "triple_candidate_violation_count"]:
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
        ratios = [envelope["phase_to_lipschitz_width_ratio"] for envelope in fold["envelopes"]]
        axes[0, 0].scatter([fold["fold"]] * len(ratios), ratios, s=15, alpha=0.65, color=color, label=f"fold {fold['fold']}")
    axes[0, 0].axhline(1, color="#b44b4b", linestyle="--", linewidth=1, label="phase = Lipschitz intersection")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks(numbers)
    axes[0, 0].set_xlabel("Frozen fold")
    axes[0, 0].set_ylabel("Phase alternative / Lipschitz intersection (log)")
    axes[0, 0].set_title("A. Exact trigonometric ranges need not always tighten")
    axes[0, 0].grid(which="both", alpha=0.2)
    axes[0, 0].legend(frameon=False, fontsize=8)

    for fold, color in zip(folds, colors):
        ratios = [envelope["triple_to_lipschitz_width_ratio"] for envelope in fold["envelopes"]]
        axes[0, 1].scatter([fold["fold"]] * len(ratios), ratios, s=15, alpha=0.65, color=color, label=f"fold {fold['fold']}")
    axes[0, 1].axhline(1, color="#555555", linestyle="--", linewidth=1)
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_xticks(numbers)
    axes[0, 1].set_xlabel("Frozen fold")
    axes[0, 1].set_ylabel("Triple intersection / Lipschitz intersection (log)")
    axes[0, 1].set_title("B. Triple intersection never widens stage 51")
    axes[0, 1].grid(which="both", alpha=0.2)
    axes[0, 1].legend(frameon=False, fontsize=8)

    for fold, color in zip(folds, colors):
        reductions = [envelope["triple_width_reduction"] for envelope in fold["envelopes"]]
        axes[1, 0].scatter([fold["fold"]] * len(reductions), reductions, s=15, alpha=0.65, color=color, label=f"fold {fold['fold']}")
    axes[1, 0].axhline(0, color="#555555", linestyle="--", linewidth=1)
    axes[1, 0].set_xticks(numbers)
    axes[1, 0].set_xlabel("Frozen fold")
    axes[1, 0].set_ylabel("Lipschitz width minus triple width")
    axes[1, 0].set_title("C. All additional tightenings and unchanged months")
    axes[1, 0].grid(alpha=0.2)
    axes[1, 0].legend(frameon=False, fontsize=8)

    positions = np.arange(len(folds))
    tighter = [fold["phase_tighter_than_independent_count"] for fold in folds]
    wider = [fold["phase_wider_than_independent_count"] for fold in folds]
    equal = [fold["phase_equal_to_independent_count"] for fold in folds]
    axes[1, 1].bar(positions, tighter, color="#316c9b", label="phase tighter")
    axes[1, 1].bar(positions, wider, bottom=tighter, color="#b44b4b", label="phase wider")
    axes[1, 1].bar(positions, equal, bottom=[a + b for a, b in zip(tighter, wider)], color="#888888", label="phase equal")
    axes[1, 1].set_xticks(positions, numbers)
    axes[1, 1].set_xlabel("Frozen fold")
    axes[1, 1].set_ylabel("Month count")
    axes[1, 1].set_title("D. Phase alternative versus stage-47 baseline")
    axes[1, 1].legend(frameon=False, fontsize=8)
    axes[1, 1].grid(axis="y", alpha=0.2)

    totals = summary["totals"]
    fig.suptitle(f"ENSO phase-interval triple bounds: {totals['triple_tightened_count']} additionally tightened, {totals['triple_unchanged_count']} unchanged; 672/672 candidates inside", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Endpoint and critical-point trigonometric intervals with product bounds. No global optimality, probability or physical-period claim.",
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
            errors.append("Missing phase-interval triple-intersection output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored phase-interval triple-intersection output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid phase-interval triple-intersection figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "phase_tighter_than_lipschitz": summary["totals"]["phase_tighter_than_lipschitz_count"],
        "phase_wider_than_lipschitz": summary["totals"]["phase_wider_than_lipschitz_count"],
        "triple_tightened": summary["totals"]["triple_tightened_count"],
        "triple_unchanged": summary["totals"]["triple_unchanged_count"],
        "triple_candidate_violations": summary["totals"]["triple_candidate_violation_count"],
        "median_triple_ratio": summary["totals"]["median_triple_to_lipschitz_width_ratio"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
