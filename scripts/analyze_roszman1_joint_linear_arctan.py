"""Construct Roszman1 joint-linear arctangent envelopes and intersections."""

import argparse
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np

from analyze_chwirut_holdout import sha256
from analyze_roszman1_native_ellipsoid_continuous import outward, support_value
from analyze_roszman1_native_holdout import native_model

mp.mp.dps = 80
ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-joint-linear-arctan-protocol.json"
OUT = ROOT / "validation/roszman1-joint-linear-arctan-intersection.json"
FIGURE = ROOT / "papers/61_Roszman1联合线性反正切交集/fig61_roszman1_joint_linear_arctan_intersection.png"
PARAMETER_NAMES = ["b1", "b2", "b3", "b4"]
DIRECTIONS = [("b1_minus", "b1", -1), ("b1_plus", "b1", 1), ("b2_minus", "b2", -1), ("b2_plus", "b2", 1), ("b3_minus", "b3", -1), ("b3_plus", "b3", 1), ("b4_minus", "b4", -1), ("b4_plus", "b4", 1)]


def joint_linear_support(parameters, covariance, radius, x):
    x = mp.mpf(str(x))
    center = mp.mpf(str(parameters["b1"])) - mp.mpf(str(parameters["b2"])) * x
    support = support_value(covariance, [1, -x, 0, 0], radius)
    return {
        "center": float(center),
        "support": float(support),
        "minimum": outward(center - support, lower=True),
        "maximum": outward(center + support, lower=False),
    }


def joint_arctan_envelope(parameters, covariance, radius, x, independent_envelope):
    linear = joint_linear_support(parameters, covariance, radius, x)
    argument_minimum = independent_envelope["argument_minimum"]
    argument_maximum = independent_envelope["argument_maximum"]
    arctan_minimum = independent_envelope["arctan_minimum"]
    arctan_maximum = independent_envelope["arctan_maximum"]
    lower = outward(mp.mpf(str(linear["minimum"])) - mp.mpf(str(arctan_maximum)) / mp.pi, lower=True)
    upper = outward(mp.mpf(str(linear["maximum"])) - mp.mpf(str(arctan_minimum)) / mp.pi, lower=False)
    x_mp = mp.mpf(str(x))
    denominator = x_mp - mp.mpf(str(parameters["b4"]))
    if denominator == 0:
        raise ValueError("Cannot evaluate the native arctangent at a singular denominator")
    center_prediction = mp.mpf(str(parameters["b1"])) - mp.mpf(str(parameters["b2"])) * x_mp - mp.atan(mp.mpf(str(parameters["b3"])) / denominator) / mp.pi
    native_prediction = float(native_model(float(x), *[float(parameters[name]) for name in PARAMETER_NAMES]))
    if not math.isclose(float(center_prediction), native_prediction, rel_tol=1.0e-12, abs_tol=1.0e-12):
        raise ValueError("Center prediction differs from the original Roszman1 model")
    return {
        "x": float(x),
        "center_prediction": float(center_prediction),
        "linear_minimum": linear["minimum"],
        "linear_maximum": linear["maximum"],
        "linear_support": linear["support"],
        "argument_minimum": argument_minimum,
        "argument_maximum": argument_maximum,
        "arctan_minimum": arctan_minimum,
        "arctan_maximum": arctan_maximum,
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


def ellipsoid_quadratic(center, parameters, covariance):
    matrix = mp.matrix([[mp.mpf(str(value)) for value in row] for row in covariance])
    delta = mp.matrix([mp.mpf(str(parameters[name])) - mp.mpf(str(center[name])) for name in PARAMETER_NAMES])
    solved = mp.lu_solve(matrix, delta)
    return float((delta.T * solved)[0])


def support_candidates(parameters, covariance, radius):
    matrix = mp.matrix([[mp.mpf(str(value)) for value in row] for row in covariance])
    candidates = []
    for direction, parameter, sign in DIRECTIONS:
        index = PARAMETER_NAMES.index(parameter)
        displacement_vector = [mp.mpf(str(radius)) * matrix[row, index] / mp.sqrt(matrix[index, index]) for row in range(len(PARAMETER_NAMES))]
        exact = {name: mp.mpf(str(parameters[name])) + sign * displacement_vector[row] for row, name in enumerate(PARAMETER_NAMES)}
        exact_parameters = {name: mp.nstr(exact[name], 80) for name in PARAMETER_NAMES}
        quadratic = ellipsoid_quadratic(parameters, exact_parameters, covariance)
        feasible = math.isclose(quadratic, radius ** 2, rel_tol=1.0e-10, abs_tol=1.0e-10)
        candidates.append({
            "direction": direction,
            "parameter": parameter,
            "sign": sign,
            "displacement_vector": [float(value) for value in displacement_vector],
            "parameters": {name: float(exact[name]) for name in PARAMETER_NAMES},
            "exact_parameters": exact_parameters,
            "ellipsoid_quadratic": quadratic,
            "feasible": feasible,
        })
    return candidates


def median(values):
    return float(np.median(values)) if values else None


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_roszman1_joint_linear_arctan_intersection":
        raise ValueError("Roszman1 joint-linear arctan protocol is not frozen")
    for key, info in protocol["inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {key}")
    source = json.loads((ROOT / protocol["inputs"]["native_identifiability"]["file"]).read_text(encoding="utf-8"))
    independent = json.loads((ROOT / protocol["inputs"]["independent_bounds"]["file"]).read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / protocol["inputs"]["independent_receipt"]["file"]).read_text(encoding="utf-8"))
    independent_hash = sha256(ROOT / protocol["inputs"]["independent_bounds"]["file"])
    independent_receipt_verified = receipt["status"] == "passed" and receipt["summarySha256"] == independent_hash
    if not independent_receipt_verified:
        raise ValueError("Stage-46 independent receipt mismatch")
    radius = protocol["joint_support_rule"]["baseline_radius"]
    folds = []
    for source_fold, independent_fold in zip(source["folds"], independent["folds"]):
        if source_fold["fold"] != independent_fold["fold"]:
            raise ValueError("Frozen fold order changed")
        parameters = source_fold["native_parameters"]
        covariance = source_fold["training_jacobian"]["parameter_covariance_matrix"]
        available = independent_fold["prediction_envelope_available"]
        if not available:
            points = [{
                "point_index": old["point_index"],
                "x": old["x"],
                "observed_y": old["observed_y"],
                "native_prediction": old["native_prediction"],
                "actual_absolute_residual": old["actual_absolute_residual"],
                "intersection_minimum": None,
                "intersection_maximum": None,
                "residual_upper_bound": None,
                "covered": None,
                "center_prediction_inside": None,
            } for old in independent_fold["points"]]
            folds.append({
                "fold": source_fold["fold"],
                "native_test_rmse": source_fold["test_metrics"]["rmse"],
                "prediction_envelope_available": False,
                "unavailable_reason": independent_fold["unavailable_reason"],
                "candidate_directions": [],
                "envelopes": [],
                "points": points,
                "candidate_evaluation_count": 0,
                "alternative_tighter_count": 0,
                "alternative_wider_count": 0,
                "alternative_equal_count": 0,
                "intersection_tightened_count": 0,
                "intersection_unchanged_count": 0,
                "intersection_bound_changed_count": 0,
                "nonempty_intersection_count": 0,
                "alternative_candidate_violation_count": 0,
                "intersection_candidate_violation_count": 0,
                "independent_candidate_violation_count": 0,
                "candidate_feasibility_failure_count": 0,
                "center_prediction_mismatch_count": 0,
                "covered_point_count": 0,
                "violation_point_count": 0,
                "unavailable_point_count": len(points),
                "min_alternative_to_independent_width_ratio": None,
                "median_alternative_to_independent_width_ratio": None,
                "max_alternative_to_independent_width_ratio": None,
                "min_intersection_to_independent_width_ratio": None,
                "median_intersection_to_independent_width_ratio": None,
                "max_intersection_to_independent_width_ratio": None,
                "max_intersection_width_reduction": None,
                "median_intersection_width_reduction": None,
                "largest_intersection_tightening": None,
            })
            continue
        candidates = support_candidates(parameters, covariance, radius)
        independent_envelopes = {float(envelope["x"]): envelope for envelope in independent_fold["envelopes"]}
        envelopes = []
        alternative_violations = 0
        intersection_violations = 0
        independent_violations = 0
        feasibility_failures = 0
        center_mismatches = 0
        nonempty_count = 0
        for x in sorted(independent_envelopes):
            baseline = independent_envelopes[x]
            alternative = joint_arctan_envelope(parameters, covariance, radius, x, baseline)
            intersection = intersect_bounds(
                alternative["prediction_minimum"], alternative["prediction_maximum"],
                baseline["prediction_minimum"], baseline["prediction_maximum"],
            )
            nonempty = intersection["prediction_minimum"] <= intersection["prediction_maximum"]
            nonempty_count += nonempty
            if not alternative["prediction_minimum"] <= alternative["center_prediction"] <= alternative["prediction_maximum"] or not intersection["prediction_minimum"] <= alternative["center_prediction"] <= intersection["prediction_maximum"]:
                center_mismatches += 1
            ratio = intersection["envelope_width"] / baseline["envelope_width"]
            reduction = baseline["envelope_width"] - intersection["envelope_width"]
            tightened = intersection["envelope_width"] < baseline["envelope_width"]
            bound_changed = intersection["prediction_minimum"] > baseline["prediction_minimum"] or intersection["prediction_maximum"] < baseline["prediction_maximum"]
            evaluations = []
            for candidate in candidates:
                exact = candidate["exact_parameters"]
                denominator = x - mp.mpf(str(exact["b4"]))
                denominator_sign_preserved = denominator < 0 if independent_fold["sign_certificate"]["sign"] == "negative" else denominator > 0
                prediction = None
                if denominator_sign_preserved:
                    prediction_mp = mp.mpf(str(exact["b1"])) - mp.mpf(str(exact["b2"])) * x - mp.atan(mp.mpf(str(exact["b3"])) / denominator) / mp.pi
                    prediction = float(prediction_mp)
                    native_prediction = float(native_model(float(x), *[candidate["parameters"][name] for name in PARAMETER_NAMES]))
                    if not math.isclose(prediction, native_prediction, rel_tol=1.0e-12, abs_tol=1.0e-12):
                        raise ValueError("Candidate prediction differs from the original Roszman1 model")
                feasible = candidate["feasible"] and math.isclose(candidate["ellipsoid_quadratic"], 16.0, rel_tol=1.0e-10, abs_tol=1.0e-10) and denominator_sign_preserved and prediction is not None and math.isfinite(prediction)
                inside_independent = prediction is not None and baseline["prediction_minimum"] <= prediction <= baseline["prediction_maximum"]
                inside_alternative = prediction is not None and alternative["prediction_minimum"] <= prediction <= alternative["prediction_maximum"]
                inside_intersection = prediction is not None and intersection["prediction_minimum"] <= prediction <= intersection["prediction_maximum"]
                feasibility_failures += not feasible
                independent_violations += not inside_independent
                alternative_violations += not inside_alternative
                intersection_violations += not inside_intersection
                evaluations.append({
                    "direction": candidate["direction"],
                    "prediction": prediction,
                    "ellipsoid_quadratic": candidate["ellipsoid_quadratic"],
                    "feasible": feasible,
                    "denominator_sign_preserved": denominator_sign_preserved,
                    "inside_independent": inside_independent,
                    "inside_joint_alternative": inside_alternative,
                    "inside_intersection": inside_intersection,
                })
            if alternative["envelope_width"] < baseline["envelope_width"]:
                alternative_comparison = "tighter"
            elif alternative["envelope_width"] > baseline["envelope_width"]:
                alternative_comparison = "wider"
            else:
                alternative_comparison = "equal"
            envelopes.append({
                **{key: value for key, value in alternative.items() if key not in ["prediction_minimum", "prediction_maximum", "envelope_width"]},
                "joint_alternative_minimum": alternative["prediction_minimum"],
                "joint_alternative_maximum": alternative["prediction_maximum"],
                "joint_alternative_width": alternative["envelope_width"],
                "alternative_comparison": alternative_comparison,
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
        points = []
        for old in independent_fold["points"]:
            envelope = next(item for item in envelopes if item["x"] == old["x"])
            lower = envelope["intersection_minimum"]
            upper = envelope["intersection_maximum"]
            observed = old["observed_y"]
            native_prediction = old["native_prediction"]
            actual_absolute = old["actual_absolute_residual"]
            residual_bound = outward(max(abs(observed - lower), abs(observed - upper)), lower=False)
            inside = lower <= native_prediction <= upper
            covered = actual_absolute <= residual_bound
            if not inside or not covered:
                center_mismatches += 1
            points.append({
                "point_index": old["point_index"],
                "x": old["x"],
                "observed_y": observed,
                "native_prediction": native_prediction,
                "actual_absolute_residual": actual_absolute,
                "intersection_minimum": lower,
                "intersection_maximum": upper,
                "residual_upper_bound": residual_bound,
                "covered": covered,
                "center_prediction_inside": inside,
            })
        if alternative_violations or intersection_violations or independent_violations or feasibility_failures or center_mismatches or nonempty_count != len(envelopes):
            raise ValueError(f"Roszman1 joint-linear consistency failure: fold {source_fold['fold']}; alternative={alternative_violations}, intersection={intersection_violations}, independent={independent_violations}, feasible={feasibility_failures}, centers={center_mismatches}, nonempty={nonempty_count}")
        alternative_ratios = [envelope["joint_alternative_width"] / envelope["independent_width"] for envelope in envelopes]
        intersection_ratios = [envelope["intersection_to_independent_width_ratio"] for envelope in envelopes]
        reductions = [envelope["intersection_width_reduction"] for envelope in envelopes]
        largest = max(envelopes, key=lambda envelope: envelope["intersection_width_reduction"])
        folds.append({
            "fold": source_fold["fold"],
            "native_test_rmse": source_fold["test_metrics"]["rmse"],
            "prediction_envelope_available": True,
            "unavailable_reason": None,
            "candidate_directions": candidates,
            "envelopes": envelopes,
            "points": points,
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
            "covered_point_count": sum(point["covered"] for point in points),
            "violation_point_count": sum(not point["covered"] for point in points),
            "unavailable_point_count": 0,
            "min_alternative_to_independent_width_ratio": min(alternative_ratios),
            "median_alternative_to_independent_width_ratio": median(alternative_ratios),
            "max_alternative_to_independent_width_ratio": max(alternative_ratios),
            "min_intersection_to_independent_width_ratio": min(intersection_ratios),
            "median_intersection_to_independent_width_ratio": median(intersection_ratios),
            "max_intersection_to_independent_width_ratio": max(intersection_ratios),
            "max_intersection_width_reduction": max(reductions),
            "median_intersection_width_reduction": median(reductions),
            "largest_intersection_tightening": {
                "x": largest["x"],
                "intersection_to_independent_width_ratio": largest["intersection_to_independent_width_ratio"],
                "intersection_width_reduction": largest["intersection_width_reduction"],
                "independent_minimum": largest["independent_minimum"],
                "independent_maximum": largest["independent_maximum"],
                "joint_alternative_minimum": largest["joint_alternative_minimum"],
                "joint_alternative_maximum": largest["joint_alternative_maximum"],
                "intersection_minimum": largest["intersection_minimum"],
                "intersection_maximum": largest["intersection_maximum"],
            },
        })

    envelopes = [envelope for fold in folds for envelope in fold["envelopes"]]
    alternative_ratios = [envelope["joint_alternative_width"] / envelope["independent_width"] for envelope in envelopes]
    intersection_ratios = [envelope["intersection_to_independent_width_ratio"] for envelope in envelopes]
    reductions = [envelope["intersection_width_reduction"] for envelope in envelopes]
    largest = max((fold["largest_intersection_tightening"] for fold in folds if fold["largest_intersection_tightening"] is not None), key=lambda record: record["intersection_width_reduction"], default=None)
    totals = {
        "fold_count": len(folds),
        "held_out_point_count": sum(len(fold["points"]) for fold in folds),
        "available_point_count": sum(fold["covered_point_count"] for fold in folds),
        "unavailable_point_count": sum(fold["unavailable_point_count"] for fold in folds),
        "unavailable_fold_ids": [fold["fold"] for fold in folds if not fold["prediction_envelope_available"]],
        "joint_alternative_bound_count": len(envelopes),
        "intersection_bound_count": len(envelopes),
        "candidate_direction_count": sum(len(fold["candidate_directions"]) for fold in folds),
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
        "covered_point_count": sum(fold["covered_point_count"] for fold in folds),
        "violation_point_count": sum(fold["violation_point_count"] for fold in folds),
        "min_alternative_to_independent_width_ratio": min(alternative_ratios),
        "median_alternative_to_independent_width_ratio": median(alternative_ratios),
        "max_alternative_to_independent_width_ratio": max(alternative_ratios),
        "min_intersection_to_independent_width_ratio": min(intersection_ratios),
        "median_intersection_to_independent_width_ratio": median(intersection_ratios),
        "max_intersection_to_independent_width_ratio": max(intersection_ratios),
        "max_intersection_width_reduction": max(reductions),
        "median_intersection_width_reduction": median(reductions),
        "largest_intersection_tightening": largest,
        "refit_count": 0,
    }
    expected = protocol["expected_structure"]
    for key in [
        "fold_count", "held_out_point_count", "available_point_count", "unavailable_point_count", "unavailable_fold_ids",
        "joint_alternative_bound_count", "intersection_bound_count", "candidate_direction_count", "candidate_evaluation_count",
        "nonempty_intersection_count", "alternative_candidate_violation_count", "intersection_candidate_violation_count",
        "independent_candidate_violation_count", "center_prediction_mismatch_count", "candidate_feasibility_failure_count", "refit_count",
    ]:
        if totals[key] != expected[key]:
            raise ValueError(f"Frozen structural expectation failed: {key}")
    return {
        "status": "computed_roszman1_joint_linear_arctan_intersection",
        "protocol_sha256": sha256(protocol_path),
        "native_identifiability_sha256": sha256(ROOT / protocol["inputs"]["native_identifiability"]["file"]),
        "independent_bounds_sha256": independent_hash,
        "independent_receipt_verified": independent_receipt_verified,
        "analysis_scope": {
            **protocol["analysis_scope"],
            "baseline_radius": radius,
            "high_precision_decimal_digits": 80,
            "outward_rounding": True,
            "outward_relative_margin": 1.0e-24,
            "exact_rational_certificate": False,
            "historical_baseline_replaced": False,
            "probability_region": False,
        },
        "known_answer": source.get("known_answer"),
        "folds": folds,
        "totals": totals,
        "full_nonlinear_global_optimum": None,
        "decision": protocol["decision"],
        "limitations": [
            "Only the linear b1-b2*x part is jointly supported; the argument relaxation and their sum are not a joint full nonlinear optimum",
            "The independent stage-46 argument interval is reused and is not claimed to encode all parameter correlations",
            "The alternative may be wider than the independent envelope and every such case is retained",
            "Intersections may remain unchanged and are not global optima; historical baselines are not replaced",
            "Fold 5 crosses x-b4 and receives no finite alternative, intersection or residual bound",
            "Candidate checks are implementation-consistency tests, not the analytic support proof or a global optimizer",
            "High-precision outward-rounded numerical intervals are not exact rational-algebra certificates or probability regions",
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
        ratios = [envelope["joint_alternative_width"] / envelope["independent_width"] for envelope in fold["envelopes"]]
        if ratios:
            axes[0, 0].scatter([fold["fold"]] * len(ratios), ratios, s=20, alpha=0.75, color=color, label=f"fold {fold['fold']}")
    axes[0, 0].axhline(1, color="#b44b4b", linestyle="--", linewidth=1)
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks(numbers)
    axes[0, 0].set_xlabel("Frozen fold")
    axes[0, 0].set_ylabel("Joint alternative / independent width (log)")
    axes[0, 0].set_title("A. Joint linear support need not be globally optimal")
    axes[0, 0].grid(which="both", alpha=0.2)
    axes[0, 0].legend(frameon=False, fontsize=8)

    for fold, color in zip(folds, colors):
        ratios = [envelope["intersection_to_independent_width_ratio"] for envelope in fold["envelopes"]]
        if ratios:
            axes[0, 1].scatter([fold["fold"]] * len(ratios), ratios, s=20, alpha=0.75, color=color, label=f"fold {fold['fold']}")
    axes[0, 1].axhline(1, color="#555555", linestyle="--", linewidth=1)
    axes[0, 1].text(5, 0.5, "fold 5\nunavailable", color="#b44b4b", ha="center", fontsize=9)
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_xticks(numbers)
    axes[0, 1].set_xlabel("Frozen fold")
    axes[0, 1].set_ylabel("Intersection / independent width (log)")
    axes[0, 1].set_title("B. Intersection never widens the baseline")
    axes[0, 1].grid(which="both", alpha=0.2)
    axes[0, 1].legend(frameon=False, fontsize=8)

    for fold, color in zip(folds, colors):
        reductions = [envelope["intersection_width_reduction"] for envelope in fold["envelopes"]]
        if reductions:
            axes[1, 0].scatter([fold["fold"]] * len(reductions), reductions, s=20, alpha=0.75, color=color, label=f"fold {fold['fold']}")
    axes[1, 0].axhline(0, color="#555555", linestyle="--", linewidth=1)
    axes[1, 0].set_xticks(numbers)
    axes[1, 0].set_xlabel("Frozen fold")
    axes[1, 0].set_ylabel("Independent width minus intersection width")
    axes[1, 0].set_title("C. Every tightening and unchanged available point")
    axes[1, 0].grid(alpha=0.2)
    axes[1, 0].legend(frameon=False, fontsize=8)

    available_folds = folds[:4]
    positions = np.arange(len(available_folds))
    tighter = [fold["alternative_tighter_count"] for fold in available_folds]
    wider = [fold["alternative_wider_count"] for fold in available_folds]
    equal = [fold["alternative_equal_count"] for fold in available_folds]
    axes[1, 1].bar(positions, tighter, color="#316c9b", label="alternative tighter")
    axes[1, 1].bar(positions, wider, bottom=tighter, color="#b44b4b", label="alternative wider")
    axes[1, 1].bar(positions, equal, bottom=[a + b for a, b in zip(tighter, wider)], color="#888888", label="alternative equal")
    axes[1, 1].set_xticks(positions, [fold["fold"] for fold in available_folds])
    axes[1, 1].set_xlabel("Frozen fold")
    axes[1, 1].set_ylabel("Available-point count")
    axes[1, 1].set_title("D. Alternative comparison inventory")
    axes[1, 1].legend(frameon=False, fontsize=8)
    axes[1, 1].grid(axis="y", alpha=0.2)

    totals = summary["totals"]
    fig.suptitle(f"Roszman1 joint-linear arctangent bounds: {totals['intersection_tightened_count']} tightened, {totals['intersection_unchanged_count']} unchanged; 160/160 candidates inside", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Exact support for b1-b2*x plus the frozen argument interval. Fold 5 remains unavailable; no global optimum or probability claim.",
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
            errors.append("Missing Roszman1 joint-linear output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored Roszman1 joint-linear output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid Roszman1 joint-linear figure")
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
