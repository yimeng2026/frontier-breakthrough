"""Analytic Roszman1 ratio-denominator support and conservative intersections."""

import argparse
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np

from analyze_chwirut_holdout import sha256
from analyze_roszman1_joint_linear_arctan import ellipsoid_quadratic, joint_linear_support, support_candidates
from analyze_roszman1_native_ellipsoid_continuous import covariance_spd, outward, sign_bounds
from analyze_roszman1_native_holdout import native_model

mp.mp.dps = 80
ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-ratio-denominator-protocol.json"
OUT = ROOT / "validation/roszman1-ratio-denominator-intersection.json"
FIGURE = ROOT / "papers/63_Roszman1比值分母联合区间/fig63_roszman1_ratio_denominator_intersection.png"
PARAMETER_NAMES = ["b1", "b2", "b3", "b4"]


def ratio_denominator_interval(parameters, covariance, radius, x):
    """Return analytic support of b3/(x-b4) on a negative-denominator ellipsoid."""
    sign = sign_bounds(parameters, covariance, radius, x, x)
    if not sign["nonzero_certified"] or sign["sign"] != "negative":
        raise ValueError("Ratio support requires a certified negative denominator with nonzero sign")
    matrix = covariance_spd(covariance)
    c = mp.mpf(str(parameters["b3"]))
    d0 = mp.mpf(str(x)) - mp.mpf(str(parameters["b4"]))
    radius = mp.mpf(str(radius))
    # A quadratic form sees the symmetric part even when stored triangular entries differ slightly.
    c33, c34, c44 = matrix[2, 2], (matrix[2, 3] + matrix[3, 2]) / 2, matrix[3, 3]
    if d0 + radius * mp.sqrt(c44) >= 0:
        raise ValueError("Negative denominator sign gate failed")
    a = d0 ** 2 - radius ** 2 * c44
    b = c * d0 + radius ** 2 * c34
    d = c ** 2 - radius ** 2 * c33
    discriminant = b ** 2 - a * d
    if a <= 0 or discriminant < 0:
        raise ValueError("Ratio quadratic is outside the certified nondegenerate sign domain")
    root_discriminant = mp.sqrt(discriminant)
    # Use the reciprocal form for the root that would subtract nearly equal values.
    if b >= 0:
        roots = [d / (b + root_discriminant), (b + root_discriminant) / a]
    else:
        roots = [(b - root_discriminant) / a, d / (b - root_discriminant)]

    def values(t):
        alpha = c - t * d0
        q = c33 + 2 * t * c34 + t ** 2 * c44
        if q <= 0:
            raise ValueError("Ratio support direction must have positive quadratic form")
        root_q = mp.sqrt(q)
        return alpha, q, root_q, alpha + radius * root_q, alpha - radius * root_q

    lower = []
    upper = []
    branches = []
    for t in roots:
        alpha, q, root_q, h_plus, h_minus = values(t)
        tolerance = mp.mpf("1e-55") * (1 + abs(alpha) + radius * root_q)
        if abs(h_plus) <= tolerance and alpha <= tolerance:
            lower.append(t)
            branch = "lower"
        elif abs(h_minus) <= tolerance and alpha >= -tolerance:
            upper.append(t)
            branch = "upper"
        else:
            raise ValueError("Squared ratio root failed both unsquared branch identities")
        branches.append({
            "branch": branch,
            "root": float(t),
            "alpha": float(alpha),
            "q": float(q),
            "support_identity_residual": float(h_plus if branch == "lower" else h_minus),
        })
    if len(lower) != 1 or len(upper) != 1:
        raise ValueError("Ratio support requires exactly one lower and one upper branch")
    lower, upper = lower[0], upper[0]
    if lower > upper:
        raise ValueError("Ratio branches are not ordered")

    witnesses = []
    for label, t, sign_multiplier in [("ratio_minimum", lower, 1), ("ratio_maximum", upper, -1)]:
        alpha, q, root_q, h_plus, h_minus = values(t)
        direction = [matrix[row, 2] + t * matrix[row, 3] for row in range(4)]
        displacement = [sign_multiplier * radius * value / root_q for value in direction]
        exact = {name: mp.mpf(str(parameters[name])) + displacement[index] for index, name in enumerate(PARAMETER_NAMES)}
        denominator = mp.mpf(str(x)) - exact["b4"]
        ratio = exact["b3"] / denominator
        quadratic = ellipsoid_quadratic(parameters, exact, covariance)
        ratio_tolerance = mp.mpf("1e-45") * (1 + abs(t))
        feasible = denominator < 0 and math.isclose(quadratic, float(radius ** 2), rel_tol=1.0e-25, abs_tol=1.0e-25) and abs(ratio - t) <= ratio_tolerance
        native_prediction = float(native_model(float(x), *[float(exact[name]) for name in PARAMETER_NAMES]))
        witnesses.append({
            "kind": "algebraic_extremizer",
            "direction": label,
            "root": float(t),
            "displacement": [float(value) for value in displacement],
            "parameters": {name: float(exact[name]) for name in PARAMETER_NAMES},
            "exact_parameters": {name: mp.nstr(exact[name], 80) for name in PARAMETER_NAMES},
            "ellipsoid_quadratic": quadratic,
            "denominator": float(denominator),
            "ratio": float(ratio),
            "ratio_minus_root": mp.nstr(ratio - t, 30),
            "native_prediction": native_prediction,
            "support_identity_residual": float(h_plus if label == "ratio_minimum" else h_minus),
            "feasible": feasible,
        })
    if not all(witness["feasible"] for witness in witnesses):
        raise ValueError(f"Ratio algebraic extremizer is not a feasible branch witness: {witnesses}")
    return {
        "lower_root": float(lower),
        "upper_root": float(upper),
        "ratio_minimum": outward(lower, lower=True),
        "ratio_maximum": outward(upper, lower=False),
        "center_ratio": float(c / d0),
        "denominator_sign": "negative",
        "quadratic_coefficients": {"A": float(a), "B": float(b), "D": float(d), "discriminant": float(discriminant)},
        "branches": branches,
        "algebraic_extremizers": witnesses,
    }


def evaluate_candidate(candidate, kind, x, ratio, independent, joint_linear, alternative, intersection, radius):
    exact = candidate["exact_parameters"]
    denominator = mp.mpf(str(x)) - mp.mpf(str(exact["b4"]))
    denominator_sign_preserved = denominator < 0
    ratio_value = None
    prediction = None
    if denominator_sign_preserved:
        ratio_value = float(mp.mpf(str(exact["b3"])) / denominator)
        prediction_mp = mp.mpf(str(exact["b1"])) - mp.mpf(str(exact["b2"])) * mp.mpf(str(x)) - mp.atan(mp.mpf(str(exact["b3"])) / denominator) / mp.pi
        prediction = float(prediction_mp)
        original_prediction = float(native_model(float(x), *[float(exact[name]) for name in PARAMETER_NAMES]))
        if not math.isclose(prediction, original_prediction, rel_tol=1.0e-12, abs_tol=1.0e-12):
            raise ValueError("Candidate prediction differs from the frozen native model")
    feasible = candidate["feasible"] and denominator_sign_preserved and prediction is not None and math.isclose(candidate["ellipsoid_quadratic"], radius ** 2, rel_tol=1.0e-10, abs_tol=1.0e-10)
    inside_ratio = ratio_value is not None and ratio["ratio_minimum"] <= ratio_value <= ratio["ratio_maximum"]
    inside_independent = prediction is not None and independent["prediction_minimum"] <= prediction <= independent["prediction_maximum"]
    inside_joint = prediction is not None and joint_linear["intersection_minimum"] <= prediction <= joint_linear["intersection_maximum"]
    inside_alternative = prediction is not None and alternative["minimum"] <= prediction <= alternative["maximum"]
    inside_intersection = prediction is not None and intersection["minimum"] <= prediction <= intersection["maximum"]
    return {
        "kind": kind,
        "direction": candidate["direction"],
        "ratio": ratio_value,
        "prediction": prediction,
        "ellipsoid_quadratic": candidate["ellipsoid_quadratic"],
        "feasible": feasible,
        "denominator_sign_preserved": denominator_sign_preserved,
        "inside_ratio_interval": inside_ratio,
        "inside_independent": inside_independent,
        "inside_joint_linear": inside_joint,
        "inside_alternative": inside_alternative,
        "inside_intersection": inside_intersection,
    }


def median(values):
    return float(np.median(values)) if values else None


def ratio_stats(envelopes, value_key, baseline_key, argument_widths=False):
    if argument_widths:
        ratios = [(envelope["ratio_maximum"] - envelope["ratio_minimum"]) / (envelope["independent_argument_maximum"] - envelope["independent_argument_minimum"]) for envelope in envelopes]
    else:
        ratios = [envelope[value_key] / envelope[baseline_key] for envelope in envelopes]
    return {"minimum": min(ratios) if ratios else None, "median": median(ratios), "maximum": max(ratios) if ratios else None}


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_roszman1_ratio_denominator_joint_interval":
        raise ValueError("Roszman1 ratio-denominator protocol is not frozen")
    for key, info in protocol["inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {key}")
    source = json.loads((ROOT / protocol["inputs"]["native_identifiability"]["file"]).read_text(encoding="utf-8"))
    independent = json.loads((ROOT / protocol["inputs"]["independent_bounds"]["file"]).read_text(encoding="utf-8"))
    independent_receipt = json.loads((ROOT / protocol["inputs"]["independent_receipt"]["file"]).read_text(encoding="utf-8"))
    joint_linear = json.loads((ROOT / protocol["inputs"]["joint_linear_bounds"]["file"]).read_text(encoding="utf-8"))
    joint_receipt = json.loads((ROOT / protocol["inputs"]["joint_linear_receipt"]["file"]).read_text(encoding="utf-8"))
    independent_hash = sha256(ROOT / protocol["inputs"]["independent_bounds"]["file"])
    joint_hash = sha256(ROOT / protocol["inputs"]["joint_linear_bounds"]["file"])
    independent_receipt_verified = independent_receipt["status"] == "passed" and independent_receipt["summarySha256"] == independent_hash
    joint_linear_receipt_verified = joint_receipt["status"] == "passed" and joint_receipt["summarySha256"] == joint_hash
    if not independent_receipt_verified or not joint_linear_receipt_verified:
        raise ValueError("Frozen independent or joint-linear receipt mismatch")
    radius = protocol["ratio_rule"]["ellipsoid"].split("r=")[1].split(";")[0]
    radius = float(radius)
    folds = []
    for source_fold, independent_fold, joint_fold in zip(source["folds"], independent["folds"], joint_linear["folds"]):
        if source_fold["fold"] != independent_fold["fold"] or source_fold["fold"] != joint_fold["fold"]:
            raise ValueError("Frozen fold order changed")
        available = independent_fold["prediction_envelope_available"] and joint_fold["prediction_envelope_available"]
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
            } for old in joint_fold["points"]]
            folds.append({
                "fold": source_fold["fold"],
                "native_test_rmse": source_fold["test_metrics"]["rmse"],
                "prediction_envelope_available": False,
                "unavailable_reason": independent_fold["unavailable_reason"],
                "candidate_directions": [],
                "envelopes": [],
                "points": points,
                "candidate_evaluation_count": 0,
                "support_candidate_evaluation_count": 0,
                "algebraic_extremizer_count": 0,
                "ratio_candidate_violation_count": 0,
                "alternative_candidate_violation_count": 0,
                "intersection_candidate_violation_count": 0,
                "independent_candidate_violation_count": 0,
                "joint_linear_candidate_violation_count": 0,
                "extremizer_feasibility_failure_count": 0,
                "candidate_feasibility_failure_count": 0,
                "center_prediction_mismatch_count": 0,
                "covered_point_count": 0,
                "violation_point_count": 0,
                "unavailable_point_count": len(points),
                "nonempty_intersection_count": 0,
                "ratio_interval_tightened_count": 0,
                "ratio_interval_unchanged_count": 0,
                "alternative_tighter_count": 0,
                "alternative_wider_count": 0,
                "alternative_equal_count": 0,
                "intersection_tightened_count": 0,
                "intersection_unchanged_count": 0,
                "intersection_bound_changed_count": 0,
                "largest_intersection_tightening": None,
                "largest_ratio_tightening": None,
            })
            continue
        parameters = source_fold["native_parameters"]
        covariance = source_fold["training_jacobian"]["parameter_covariance_matrix"]
        candidates = support_candidates(parameters, covariance, radius)
        independent_envelopes = {float(item["x"]): item for item in independent_fold["envelopes"]}
        joint_envelopes = {float(item["x"]): item for item in joint_fold["envelopes"]}
        if independent_envelopes.keys() != joint_envelopes.keys():
            raise ValueError("Independent and joint-linear x inventories differ")
        envelopes = []
        counters = {key: 0 for key in ["ratio_candidate_violation_count", "alternative_candidate_violation_count", "intersection_candidate_violation_count", "independent_candidate_violation_count", "joint_linear_candidate_violation_count", "extremizer_feasibility_failure_count", "candidate_feasibility_failure_count", "center_prediction_mismatch_count", "nonempty_intersection_count"]}
        for x in sorted(independent_envelopes):
            old = independent_envelopes[x]
            previous = joint_envelopes[x]
            ratio = ratio_denominator_interval(parameters, covariance, radius, x)
            tolerance = 1.0e-12 * (1 + abs(old["argument_minimum"]) + abs(old["argument_maximum"]))
            if ratio["ratio_minimum"] < old["argument_minimum"] - tolerance or ratio["ratio_maximum"] > old["argument_maximum"] + tolerance:
                raise ValueError("Analytic ratio interval escaped the frozen independent argument interval")
            linear = joint_linear_support(parameters, covariance, radius, x)
            arctan_minimum = outward(mp.atan(mp.mpf(str(ratio["ratio_minimum"]))), lower=True)
            arctan_maximum = outward(mp.atan(mp.mpf(str(ratio["ratio_maximum"]))), lower=False)
            alternative = {
                "minimum": outward(mp.mpf(str(linear["minimum"])) - arctan_maximum / mp.pi, lower=True),
                "maximum": outward(mp.mpf(str(linear["maximum"])) - arctan_minimum / mp.pi, lower=False),
            }
            alternative["width"] = outward(alternative["maximum"] - alternative["minimum"], lower=False)
            intersection = {
                "minimum": max(alternative["minimum"], previous["intersection_minimum"]),
                "maximum": min(alternative["maximum"], previous["intersection_maximum"]),
            }
            intersection["width"] = outward(intersection["maximum"] - intersection["minimum"], lower=False)
            nonempty = intersection["minimum"] <= intersection["maximum"]
            counters["nonempty_intersection_count"] += nonempty
            center_prediction = mp.mpf(str(parameters["b1"])) - mp.mpf(str(parameters["b2"])) * mp.mpf(str(x)) - mp.atan(mp.mpf(str(parameters["b3"])) / (mp.mpf(str(x)) - mp.mpf(str(parameters["b4"])))) / mp.pi
            center_prediction = float(center_prediction)
            if not math.isclose(center_prediction, float(native_model(float(x), *[parameters[name] for name in PARAMETER_NAMES])), rel_tol=1.0e-12, abs_tol=1.0e-12):
                raise ValueError("Center prediction differs from the frozen native model")
            if not alternative["minimum"] <= center_prediction <= alternative["maximum"] or not intersection["minimum"] <= center_prediction <= intersection["maximum"]:
                counters["center_prediction_mismatch_count"] += 1
            evaluations = []
            for candidate in candidates:
                evaluations.append(evaluate_candidate(candidate, "full_covariance_support", x, ratio, old, previous, alternative, intersection, radius))
            for extremizer in ratio["algebraic_extremizers"]:
                evaluations.append(evaluate_candidate(extremizer, "algebraic_extremizer", x, ratio, old, previous, alternative, intersection, radius))
            for evaluation in evaluations:
                counters["ratio_candidate_violation_count"] += not evaluation["inside_ratio_interval"]
                counters["alternative_candidate_violation_count"] += not evaluation["inside_alternative"]
                counters["intersection_candidate_violation_count"] += not evaluation["inside_intersection"]
                counters["independent_candidate_violation_count"] += not evaluation["inside_independent"]
                counters["joint_linear_candidate_violation_count"] += not evaluation["inside_joint_linear"]
                counters["candidate_feasibility_failure_count"] += not evaluation["feasible"]
                counters["extremizer_feasibility_failure_count"] += evaluation["kind"] == "algebraic_extremizer" and not evaluation["feasible"]
            alternative_width_ratio = alternative["width"] / previous["joint_alternative_width"]
            comparison = "tighter" if alternative["width"] < previous["joint_alternative_width"] else "wider" if alternative["width"] > previous["joint_alternative_width"] else "equal"
            reduction = previous["intersection_width"] - intersection["width"]
            ratio_reduction = (old["argument_maximum"] - old["argument_minimum"]) - (ratio["ratio_maximum"] - ratio["ratio_minimum"])
            envelopes.append({
                "x": float(x),
                "center_prediction": center_prediction,
                "center_ratio": ratio["center_ratio"],
                "ratio_minimum": ratio["ratio_minimum"],
                "ratio_maximum": ratio["ratio_maximum"],
                "lower_root": ratio["lower_root"],
                "upper_root": ratio["upper_root"],
                "ratio_branches": ratio["branches"],
                "quadratic_coefficients": ratio["quadratic_coefficients"],
                "algebraic_extremizers": ratio["algebraic_extremizers"],
                "independent_argument_minimum": old["argument_minimum"],
                "independent_argument_maximum": old["argument_maximum"],
                "ratio_interval_width_reduction": ratio_reduction,
                "ratio_interval_tightened": ratio_reduction > 0,
                "linear_minimum": linear["minimum"],
                "linear_maximum": linear["maximum"],
                "linear_support": linear["support"],
                "arctan_minimum": arctan_minimum,
                "arctan_maximum": arctan_maximum,
                "alternative_minimum": alternative["minimum"],
                "alternative_maximum": alternative["maximum"],
                "alternative_width": alternative["width"],
                "joint_alternative_minimum": previous["joint_alternative_minimum"],
                "joint_alternative_maximum": previous["joint_alternative_maximum"],
                "joint_alternative_width": previous["joint_alternative_width"],
                "alternative_to_joint_alternative_width_ratio": alternative_width_ratio,
                "alternative_comparison": comparison,
                "joint_linear_minimum": previous["intersection_minimum"],
                "joint_linear_maximum": previous["intersection_maximum"],
                "joint_linear_width": previous["intersection_width"],
                "intersection_minimum": intersection["minimum"],
                "intersection_maximum": intersection["maximum"],
                "intersection_width": intersection["width"],
                "intersection_to_joint_linear_width_ratio": intersection["width"] / previous["intersection_width"],
                "intersection_width_reduction": reduction,
                "intersection_tightened": intersection["width"] < previous["intersection_width"],
                "intersection_bound_changed": intersection["minimum"] > previous["intersection_minimum"] or intersection["maximum"] < previous["intersection_maximum"],
                "intersection_nonempty": nonempty,
                "candidate_evaluations": evaluations,
            })
        if any(counters[key] for key in ["ratio_candidate_violation_count", "alternative_candidate_violation_count", "intersection_candidate_violation_count", "independent_candidate_violation_count", "joint_linear_candidate_violation_count", "extremizer_feasibility_failure_count", "candidate_feasibility_failure_count", "center_prediction_mismatch_count"]) or counters["nonempty_intersection_count"] != len(envelopes):
            raise ValueError(f"Roszman1 ratio-denominator consistency failure: fold {source_fold['fold']}: {counters}")
        points = []
        for old_point in joint_fold["points"]:
            envelope = next(item for item in envelopes if item["x"] == old_point["x"])
            lower, upper = envelope["intersection_minimum"], envelope["intersection_maximum"]
            residual_bound = outward(max(abs(old_point["observed_y"] - lower), abs(old_point["observed_y"] - upper)), lower=False)
            covered = old_point["actual_absolute_residual"] <= residual_bound
            inside = lower <= old_point["native_prediction"] <= upper
            points.append({**old_point, "intersection_minimum": lower, "intersection_maximum": upper, "residual_upper_bound": residual_bound, "covered": covered, "center_prediction_inside": inside})
        if not all(point["covered"] and point["center_prediction_inside"] for point in points):
            raise ValueError("Available-point arithmetic consistency failed")
        largest = max(envelopes, key=lambda item: item["intersection_width_reduction"])
        largest_ratio = max(envelopes, key=lambda item: item["ratio_interval_width_reduction"])
        folds.append({
            "fold": source_fold["fold"],
            "native_test_rmse": source_fold["test_metrics"]["rmse"],
            "prediction_envelope_available": True,
            "unavailable_reason": None,
            "candidate_directions": candidates,
            "envelopes": envelopes,
            "points": points,
            "candidate_evaluation_count": sum(len(item["candidate_evaluations"]) for item in envelopes),
            "support_candidate_evaluation_count": sum(sum(item["kind"] == "full_covariance_support" for item in envelope["candidate_evaluations"]) for envelope in envelopes),
            "algebraic_extremizer_count": sum(len(envelope["algebraic_extremizers"]) for envelope in envelopes),
            **counters,
            "covered_point_count": sum(point["covered"] for point in points),
            "violation_point_count": sum(not point["covered"] for point in points),
            "unavailable_point_count": 0,
            "ratio_interval_tightened_count": sum(envelope["ratio_interval_tightened"] for envelope in envelopes),
            "ratio_interval_unchanged_count": sum(not envelope["ratio_interval_tightened"] for envelope in envelopes),
            "alternative_tighter_count": sum(envelope["alternative_comparison"] == "tighter" for envelope in envelopes),
            "alternative_wider_count": sum(envelope["alternative_comparison"] == "wider" for envelope in envelopes),
            "alternative_equal_count": sum(envelope["alternative_comparison"] == "equal" for envelope in envelopes),
            "intersection_tightened_count": sum(envelope["intersection_tightened"] for envelope in envelopes),
            "intersection_unchanged_count": sum(not envelope["intersection_tightened"] for envelope in envelopes),
            "intersection_bound_changed_count": sum(envelope["intersection_bound_changed"] for envelope in envelopes),
            "ratio_interval_width_ratio": ratio_stats(envelopes, "ratio_maximum", "independent_argument_maximum", argument_widths=True),
            "alternative_width_ratio": ratio_stats(envelopes, "alternative_width", "joint_alternative_width"),
            "intersection_width_ratio": ratio_stats(envelopes, "intersection_width", "joint_linear_width"),
            "largest_intersection_tightening": {key: largest[key] for key in ["x", "intersection_to_joint_linear_width_ratio", "intersection_width_reduction", "joint_linear_minimum", "joint_linear_maximum", "alternative_minimum", "alternative_maximum", "intersection_minimum", "intersection_maximum"]},
            "largest_ratio_tightening": {key: largest_ratio[key] for key in ["x", "ratio_minimum", "ratio_maximum", "independent_argument_minimum", "independent_argument_maximum", "ratio_interval_width_reduction"]},
        })
    envelopes = [envelope for fold in folds for envelope in fold["envelopes"]]
    totals = {
        "fold_count": len(folds),
        "held_out_point_count": sum(len(fold["points"]) for fold in folds),
        "available_point_count": sum(fold["covered_point_count"] for fold in folds),
        "unavailable_point_count": sum(fold["unavailable_point_count"] for fold in folds),
        "unavailable_fold_ids": [fold["fold"] for fold in folds if not fold["prediction_envelope_available"]],
        "ratio_interval_count": len(envelopes),
        "ratio_alternative_bound_count": len(envelopes),
        "intersection_bound_count": len(envelopes),
        "candidate_direction_count": sum(len(fold["candidate_directions"]) for fold in folds),
        "algebraic_extremizer_count": sum(fold["algebraic_extremizer_count"] for fold in folds),
        "support_candidate_evaluation_count": sum(fold["support_candidate_evaluation_count"] for fold in folds),
        "candidate_evaluation_count": sum(fold["candidate_evaluation_count"] for fold in folds),
        "nonempty_intersection_count": sum(fold["nonempty_intersection_count"] for fold in folds),
        "ratio_candidate_violation_count": sum(fold["ratio_candidate_violation_count"] for fold in folds),
        "alternative_candidate_violation_count": sum(fold["alternative_candidate_violation_count"] for fold in folds),
        "intersection_candidate_violation_count": sum(fold["intersection_candidate_violation_count"] for fold in folds),
        "independent_candidate_violation_count": sum(fold["independent_candidate_violation_count"] for fold in folds),
        "joint_linear_candidate_violation_count": sum(fold["joint_linear_candidate_violation_count"] for fold in folds),
        "extremizer_feasibility_failure_count": sum(fold["extremizer_feasibility_failure_count"] for fold in folds),
        "candidate_feasibility_failure_count": sum(fold["candidate_feasibility_failure_count"] for fold in folds),
        "center_prediction_mismatch_count": sum(fold["center_prediction_mismatch_count"] for fold in folds),
        "covered_point_count": sum(fold["covered_point_count"] for fold in folds),
        "violation_point_count": sum(fold["violation_point_count"] for fold in folds),
        "ratio_interval_tightened_count": sum(fold["ratio_interval_tightened_count"] for fold in folds),
        "ratio_interval_unchanged_count": sum(fold["ratio_interval_unchanged_count"] for fold in folds),
        "alternative_tighter_count": sum(fold["alternative_tighter_count"] for fold in folds),
        "alternative_wider_count": sum(fold["alternative_wider_count"] for fold in folds),
        "alternative_equal_count": sum(fold["alternative_equal_count"] for fold in folds),
        "intersection_tightened_count": sum(fold["intersection_tightened_count"] for fold in folds),
        "intersection_unchanged_count": sum(fold["intersection_unchanged_count"] for fold in folds),
        "intersection_bound_changed_count": sum(fold["intersection_bound_changed_count"] for fold in folds),
        "min_alternative_to_joint_alternative_width_ratio": min(envelope["alternative_to_joint_alternative_width_ratio"] for envelope in envelopes),
        "median_alternative_to_joint_alternative_width_ratio": median([envelope["alternative_to_joint_alternative_width_ratio"] for envelope in envelopes]),
        "max_alternative_to_joint_alternative_width_ratio": max(envelope["alternative_to_joint_alternative_width_ratio"] for envelope in envelopes),
        "min_intersection_to_joint_linear_width_ratio": min(envelope["intersection_to_joint_linear_width_ratio"] for envelope in envelopes),
        "median_intersection_to_joint_linear_width_ratio": median([envelope["intersection_to_joint_linear_width_ratio"] for envelope in envelopes]),
        "max_intersection_to_joint_linear_width_ratio": max(envelope["intersection_to_joint_linear_width_ratio"] for envelope in envelopes),
        "max_intersection_width_reduction": max(envelope["intersection_width_reduction"] for envelope in envelopes),
        "median_intersection_width_reduction": median([envelope["intersection_width_reduction"] for envelope in envelopes]),
        "max_ratio_interval_width_reduction": max(envelope["ratio_interval_width_reduction"] for envelope in envelopes),
        "median_ratio_interval_width_reduction": median([envelope["ratio_interval_width_reduction"] for envelope in envelopes]),
        "largest_intersection_tightening": max((fold["largest_intersection_tightening"] for fold in folds if fold["largest_intersection_tightening"] is not None), key=lambda item: item["intersection_width_reduction"], default=None),
        "largest_ratio_tightening": max((fold["largest_ratio_tightening"] for fold in folds if fold["largest_ratio_tightening"] is not None), key=lambda item: item["ratio_interval_width_reduction"], default=None),
        "refit_count": 0,
    }
    for key, value in protocol["expected_structure"].items():
        if totals[key] != value:
            raise ValueError(f"Frozen structural expectation failed: {key}: {totals[key]} != {value}")
    return {
        "status": "computed_roszman1_ratio_denominator_intersection",
        "protocol_sha256": sha256(protocol_path),
        "native_identifiability_sha256": sha256(ROOT / protocol["inputs"]["native_identifiability"]["file"]),
        "independent_bounds_sha256": independent_hash,
        "joint_linear_bounds_sha256": joint_hash,
        "independent_receipt_verified": independent_receipt_verified,
        "joint_linear_receipt_verified": joint_linear_receipt_verified,
        "analysis_scope": {**protocol["analysis_scope"], "baseline_radius": radius, "high_precision_decimal_digits": 80, "outward_rounding": True, "outward_relative_margin": 1.0e-24, "exact_rational_certificate": False, "probability_region": False, "historical_baseline_replaced": False},
        "known_answer": source.get("known_answer"),
        "folds": folds,
        "totals": totals,
        "full_nonlinear_global_optimum": None,
        "decision": protocol["decision"],
        "limitations": [
            "The ratio b3/(x-b4) has analytic ellipsoid support at each fixed available x, but the linear and ratio supports may be attained at different parameters",
            "The sum of the linear support and ratio-arctangent support is conservative, not a joint full four-parameter nonlinear optimum",
            "The final intersection can remain unchanged and is not a global optimum; historical baselines are not replaced",
            "Fold 5 has no certified negative denominator and receives no ratio interval, finite prediction bound, extremizer, candidate evaluation or residual upper bound",
            "The 200 evaluations are implementation-consistency witnesses, not a global optimizer, probability coverage or independent experiment",
            "High-precision outward-rounded support is not an exact rational-algebra certificate or probability region",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    actual = [envelope.get("intersection_to_joint_linear_width_ratio") for fold in summary.get("folds", []) for envelope in fold.get("envelopes", [])]
    required = [envelope["intersection_to_joint_linear_width_ratio"] for fold in expected["folds"] for envelope in fold["envelopes"]]
    if actual != required:
        errors.append("Intersection-to-joint-linear width ratio mismatch")
    for key in ["ratio_candidate_violation_count", "alternative_candidate_violation_count", "intersection_candidate_violation_count"]:
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
    colors = ["#316c9b", "#4f7b5b", "#876a32", "#6a4c93", "#b44b4b"]
    fig, axes = plt.subplots(2, 2, figsize=(16.0, 11.5), constrained_layout=True)
    for fold, color in zip(folds, colors):
        for envelope in fold["envelopes"]:
            old_width = envelope["independent_argument_maximum"] - envelope["independent_argument_minimum"]
            new_width = envelope["ratio_maximum"] - envelope["ratio_minimum"]
            axes[0, 0].scatter(fold["fold"], new_width / old_width, color=color, s=24, alpha=0.75)
    axes[0, 0].axhline(1, color="#555555", linestyle="--", linewidth=1)
    axes[0, 0].set_xticks(range(1, 6))
    axes[0, 0].set_ylabel("Analytic ratio / independent argument width")
    axes[0, 0].set_title("A. Joint ratio-denominator support")
    axes[0, 0].grid(alpha=0.2)

    for fold, color in zip(folds, colors):
        axes[0, 1].scatter([fold["fold"]] * len(fold["envelopes"]), [envelope["alternative_to_joint_alternative_width_ratio"] for envelope in fold["envelopes"]], color=color, s=24, alpha=0.75)
    axes[0, 1].axhline(1, color="#555555", linestyle="--", linewidth=1)
    axes[0, 1].set_xticks(range(1, 6))
    axes[0, 1].set_ylabel("Alternative / previous alternative width")
    axes[0, 1].set_title("B. Component supports remain conservative")
    axes[0, 1].grid(alpha=0.2)

    for fold, color in zip(folds, colors):
        axes[1, 0].scatter([fold["fold"]] * len(fold["envelopes"]), [envelope["intersection_width_reduction"] for envelope in fold["envelopes"]], color=color, s=24, alpha=0.75)
    axes[1, 0].axhline(0, color="#555555", linewidth=1)
    axes[1, 0].set_xticks(range(1, 6))
    axes[1, 0].set_ylabel("Stage-54 width minus final intersection width")
    axes[1, 0].set_title("C. Local tightening and unchanged intersections")
    axes[1, 0].grid(alpha=0.2)

    available = [len(fold["points"]) if fold["prediction_envelope_available"] else 0 for fold in folds]
    unavailable = [fold["unavailable_point_count"] for fold in folds]
    axes[1, 1].bar(range(1, 6), available, color="#316c9b", label="20 points; 200 evaluations")
    axes[1, 1].bar(range(1, 6), unavailable, bottom=available, color="#b44b4b", label="fold 5 unavailable")
    axes[1, 1].set_xticks(range(1, 6))
    axes[1, 1].set_ylabel("Held-out observations")
    axes[1, 1].set_title("D. No bound is manufactured for fold 5")
    axes[1, 1].legend(frameon=False, fontsize=8)
    axes[1, 1].grid(axis="y", alpha=0.2)

    totals = summary["totals"]
    fig.suptitle(f"Roszman1 ratio-denominator support: {totals['ratio_interval_count']} intervals, {totals['algebraic_extremizer_count']} extremizers, {totals['candidate_evaluation_count']} evaluations", fontsize=15, y=1.045)
    fig.text(0.5, 1.012, "Analytic component support plus conservative intersection; not a full nonlinear optimum or probability region.", ha="center", fontsize=9, color="#555555")
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
            errors.append("Missing Roszman1 ratio-denominator output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored Roszman1 ratio-denominator output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid Roszman1 ratio-denominator figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "ratio_intervals": summary["totals"]["ratio_interval_count"],
        "algebraic_extremizers": summary["totals"]["algebraic_extremizer_count"],
        "candidate_evaluations": summary["totals"]["candidate_evaluation_count"],
        "intersection_tightened": summary["totals"]["intersection_tightened_count"],
        "intersection_unchanged": summary["totals"]["intersection_unchanged_count"],
        "median_intersection_ratio": summary["totals"]["median_intersection_to_joint_linear_width_ratio"],
        "unavailable": summary["totals"]["unavailable_point_count"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
