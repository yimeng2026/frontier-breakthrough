"""Whitened full-ellipsoid cover grids with explicit unresolved cells."""

import argparse
import itertools
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np

from analyze_chwirut_holdout import sha256
from analyze_roszman1_native_ellipsoid_continuous import covariance_spd, outward
from analyze_roszman1_native_holdout import native_model

mp.mp.dps = 80
ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-whitened-cover-grid-protocol.json"
OUT = ROOT / "validation/roszman1-whitened-cover-grid.json"
FIGURE = ROOT / "papers/65_Roszman1协方差白化覆盖/fig65_roszman1_whitened_cover_grid.png"
PARAMETER_NAMES = ["b1", "b2", "b3", "b4"]


def whitening(parameters, covariance, radius):
    matrix = covariance_spd(covariance)
    symmetric = mp.matrix([[(matrix[i, j] + matrix[j, i]) / 2 for j in range(4)] for i in range(4)])
    factor = mp.cholesky(symmetric)
    reconstructed = factor * factor.T
    error = max(abs(reconstructed[i, j] - symmetric[i, j]) for i in range(4) for j in range(4))
    scale = 1 + max(abs(symmetric[i, j]) for i in range(4) for j in range(4))
    if error > mp.mpf("1e-35") * scale:
        raise ValueError("Cholesky reconstruction exceeds the frozen numerical tolerance")
    return {
        "factor": factor,
        "radius": mp.mpf(str(radius)),
        "symmetric_covariance": [[float(symmetric[i, j]) for j in range(4)] for i in range(4)],
        "factor_rows": [[float(factor[i, j]) for j in range(4)] for i in range(4)],
        "reconstruction_max_error": float(error),
    }


def minimum_norm_squared(lower, upper):
    total = mp.mpf(0)
    for left, right in zip(lower, upper):
        left, right = mp.mpf(str(left)), mp.mpf(str(right))
        if left > right:
            raise ValueError("Whitened cell interval must be ordered")
        distance = mp.mpf(0) if left <= 0 <= right else min(abs(left), abs(right))
        total += distance ** 2
    return float(total)


def affine_interval(center, coefficients, lower, upper):
    low = mp.mpf(str(center))
    high = mp.mpf(str(center))
    for coefficient, left, right in zip(coefficients, lower, upper):
        left, right = mp.mpf(str(left)), mp.mpf(str(right))
        values = [coefficient * left, coefficient * right]
        low += min(values)
        high += max(values)
    return low, high


def whitened_cell_interval(parameters, factor, radius, x, lower, upper, outside_tolerance_relative=1.0e-12):
    minimum_norm = minimum_norm_squared(lower, upper)
    outside_tolerance = outside_tolerance_relative * (1 + float(radius) ** 2)
    if minimum_norm > float(radius) ** 2 + outside_tolerance:
        return {"lower": lower, "upper": upper, "status": "outside_ball", "minimum_norm_squared": minimum_norm, "prediction_minimum": None, "prediction_maximum": None}
    x_mp = mp.mpf(str(x))
    direction = [mp.mpf(1), -x_mp, mp.mpf(0), mp.mpf(0)]
    linear_coefficients = [sum(direction[i] * factor[i, j] for i in range(4)) for j in range(4)]
    linear_center = mp.mpf(str(parameters["b1"])) - mp.mpf(str(parameters["b2"])) * x_mp
    b3_coefficients = [factor[2, j] for j in range(4)]
    denominator_coefficients = [factor[3, j] for j in range(4)]
    linear_minimum, linear_maximum = affine_interval(linear_center, linear_coefficients, lower, upper)
    b3_minimum, b3_maximum = affine_interval(mp.mpf(str(parameters["b3"])), b3_coefficients, lower, upper)
    denominator_minimum, denominator_maximum = affine_interval(x_mp - mp.mpf(str(parameters["b4"])), denominator_coefficients, lower, upper)
    base = {"lower": lower, "upper": upper, "minimum_norm_squared": minimum_norm, "denominator_minimum": float(denominator_minimum), "denominator_maximum": float(denominator_maximum)}
    if denominator_minimum <= 0 <= denominator_maximum:
        return {**base, "status": "unresolved_denominator", "prediction_minimum": None, "prediction_maximum": None}
    ratio_values = [b3_value / denominator for b3_value in [b3_minimum, b3_maximum] for denominator in [denominator_minimum, denominator_maximum]]
    ratio_minimum, ratio_maximum = min(ratio_values), max(ratio_values)
    atan_minimum, atan_maximum = mp.atan(ratio_minimum), mp.atan(ratio_maximum)
    prediction_minimum = outward(linear_minimum - atan_maximum / mp.pi, lower=True)
    prediction_maximum = outward(linear_maximum - atan_minimum / mp.pi, lower=False)
    return {
        **base,
        "status": "evaluated",
        "linear_minimum": float(linear_minimum),
        "linear_maximum": float(linear_maximum),
        "b3_minimum": float(b3_minimum),
        "b3_maximum": float(b3_maximum),
        "ratio_minimum": float(ratio_minimum),
        "ratio_maximum": float(ratio_maximum),
        "prediction_minimum": prediction_minimum,
        "prediction_maximum": prediction_maximum,
    }


def whitened_grid(parameters, covariance, radius, x, divisions, outside_tolerance_relative=1.0e-12):
    if divisions not in [1, 2, 4]:
        raise ValueError("Whitened grid divisions are frozen to 1, 2 or 4")
    transformed = whitening(parameters, covariance, radius)
    factor = transformed["factor"]
    lower = [outward(-mp.mpf(str(radius)), lower=True)] * 4
    upper = [outward(mp.mpf(str(radius)), lower=False)] * 4
    cells = []
    for indices in itertools.product(range(divisions), repeat=4):
        cell_lower, cell_upper = [], []
        for axis, index in enumerate(indices):
            left, right = mp.mpf(str(lower[axis])), mp.mpf(str(upper[axis]))
            cell_lower.append(float(left + index * (right - left) / divisions))
            cell_upper.append(float(left + (index + 1) * (right - left) / divisions))
        record = whitened_cell_interval(parameters, factor, radius, x, cell_lower, cell_upper, outside_tolerance_relative)
        cells.append({"indices": list(indices), **record})
    evaluated = sum(cell["status"] == "evaluated" for cell in cells)
    outside = sum(cell["status"] == "outside_ball" for cell in cells)
    unresolved = sum(cell["status"] == "unresolved_denominator" for cell in cells)
    bounded = unresolved == 0
    if bounded and evaluated + outside != len(cells):
        raise ValueError("No evaluated cell remains in a supposedly bounded grid")
    return {
        "divisions": divisions,
        "cells": cells,
        "partition_cell_count": len(cells),
        "evaluated_cell_count": evaluated,
        "outside_cell_count": outside,
        "unresolved_cell_count": unresolved,
        "outside_boundary_tolerance": outside_tolerance_relative * (1 + float(radius) ** 2),
        "union_bounded": bounded,
        "union_minimum": min((cell["prediction_minimum"] for cell in cells if cell["status"] == "evaluated"), default=None) if bounded else None,
        "union_maximum": max((cell["prediction_maximum"] for cell in cells if cell["status"] == "evaluated"), default=None) if bounded else None,
        "symmetric_covariance": transformed["symmetric_covariance"],
        "cholesky_factor": transformed["factor_rows"],
        "cholesky_reconstruction_max_error": transformed["reconstruction_max_error"],
    }


def candidate_transform(parameters, factor, radius, exact_parameters):
    delta = mp.matrix([mp.mpf(str(exact_parameters[name])) - mp.mpf(str(parameters[name])) for name in PARAMETER_NAMES])
    u = mp.lu_solve(factor, delta)
    reconstructed = factor * u
    residual = max(abs(reconstructed[i] - delta[i]) for i in range(4))
    scaled_error = max(abs(reconstructed[i] - delta[i]) / (1 + abs(delta[i])) for i in range(4))
    norm = mp.sqrt((u.T * u)[0])
    tolerance = mp.mpf("1e-10") * (1 + mp.mpf(str(radius)))
    valid = scaled_error <= mp.mpf("1e-10") and norm <= mp.mpf(str(radius)) + tolerance
    return {
        "u": [float(value) for value in u],
        "whitened_norm": float(norm),
        "reconstructed_parameters": {name: float(mp.mpf(str(parameters[name])) + reconstructed[index]) for index, name in enumerate(PARAMETER_NAMES)},
        "reconstruction_max_residual": float(residual),
        "max_scaled_reconstruction_error": float(scaled_error),
        "transform_valid": valid,
    }


def evaluate_candidate(candidate, kind, parameters, factor, radius, x, grids):
    exact = candidate["exact_parameters"]
    transformed = candidate_transform(parameters, factor, radius, exact)
    values = [float(exact[name]) for name in PARAMETER_NAMES]
    denominator = float(mp.mpf(str(x)) - mp.mpf(str(exact["b4"])))
    prediction = float(native_model(float(x), *values))
    feasible = candidate["feasible"] and transformed["transform_valid"] and denominator < 0 and math.isfinite(prediction) and math.isclose(candidate["ellipsoid_quadratic"], 16.0, rel_tol=1.0e-10, abs_tol=1.0e-10)
    checks = []
    for grid in grids:
        inside_union = True if not grid["union_bounded"] else grid["union_minimum"] <= prediction <= grid["union_maximum"]
        checks.append({
            "divisions": grid["divisions"],
            "union_bounded": grid["union_bounded"],
            "finite_union_check": grid["union_bounded"],
            "inside_union": inside_union,
            "inside_intersection": grid["intersection_minimum"] <= prediction <= grid["intersection_maximum"],
        })
    return {
        "kind": kind,
        "direction": candidate["direction"],
        "prediction": prediction,
        "denominator": denominator,
        "ellipsoid_quadratic": candidate["ellipsoid_quadratic"],
        **transformed,
        "feasible": feasible,
        "grid_checks": checks,
    }


def native_center(parameters, x):
    x_mp = mp.mpf(str(x))
    value = mp.mpf(str(parameters["b1"])) - mp.mpf(str(parameters["b2"])) * x_mp - mp.atan(mp.mpf(str(parameters["b3"])) / (x_mp - mp.mpf(str(parameters["b4"])))) / mp.pi
    center = float(value)
    if not math.isclose(center, float(native_model(float(x), *[parameters[name] for name in PARAMETER_NAMES])), rel_tol=1.0e-12, abs_tol=1.0e-12):
        raise ValueError("Center prediction differs from the frozen native model")
    return center


def intersection_record(grid, baseline, fold, x):
    lower = baseline["intersection_minimum"] if not grid["union_bounded"] else max(grid["union_minimum"], baseline["intersection_minimum"])
    upper = baseline["intersection_maximum"] if not grid["union_bounded"] else min(grid["union_maximum"], baseline["intersection_maximum"])
    width = outward(upper - lower, lower=False)
    return {
        **grid,
        "baseline_minimum": baseline["intersection_minimum"],
        "baseline_maximum": baseline["intersection_maximum"],
        "intersection_minimum": lower,
        "intersection_maximum": upper,
        "intersection_width": width,
        "intersection_to_ratio_width_ratio": width / baseline["intersection_width"],
        "intersection_width_reduction": baseline["intersection_width"] - width,
        "intersection_tightened": width < baseline["intersection_width"],
        "intersection_nonempty": lower <= upper,
        "largest_intersection_tightening": {
            "fold": fold, "x": float(x), "divisions": grid["divisions"], "union_bounded": grid["union_bounded"],
            "intersection_to_ratio_width_ratio": width / baseline["intersection_width"],
            "intersection_width_reduction": baseline["intersection_width"] - width,
            "baseline_minimum": baseline["intersection_minimum"], "baseline_maximum": baseline["intersection_maximum"],
            "union_minimum": grid["union_minimum"], "union_maximum": grid["union_maximum"],
            "intersection_minimum": lower, "intersection_maximum": upper,
        },
    }


def median(values):
    return float(np.median(values)) if values else None


def primary_summary(fold):
    records = [envelope["grids"][2] for envelope in fold["envelopes"]]
    if not records:
        return None
    return {
        "divisions": 4,
        "unbounded_grid_count": sum(not record["union_bounded"] for record in records),
        "unresolved_cell_count": sum(record["unresolved_cell_count"] for record in records),
        "intersection_tightened_count": sum(record["intersection_tightened"] for record in records),
        "intersection_unchanged_count": sum(not record["intersection_tightened"] for record in records),
        "median_intersection_to_ratio_width_ratio": median([record["intersection_to_ratio_width_ratio"] for record in records]),
        "largest_intersection_tightening": max((record["largest_intersection_tightening"] for record in records), key=lambda item: item["intersection_width_reduction"]),
    }


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_roszman1_whitened_cover_grid":
        raise ValueError("Roszman1 whitened-cover protocol is not frozen")
    for key, info in protocol["inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {key}")
    amendment_path = protocol_path.with_name("roszman1-whitened-cover-grid-protocol-amendment-01.json")
    if not amendment_path.is_file():
        raise ValueError("Missing whitened-cover boundary amendment 01")
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    if amendment["status"] != "frozen_before_roszman1_whitened_cover_grid_results" or amendment["original_protocol"]["sha256"] != sha256(protocol_path) or amendment["correction"]["outside_distance_tolerance"] != "1e-12*(1+r^2)":
        raise ValueError("Whitened-cover boundary amendment is not aligned with the original protocol")
    outside_tolerance_relative = 1.0e-12
    source = json.loads((ROOT / protocol["inputs"]["native_identifiability"]["file"]).read_text(encoding="utf-8"))
    ratio = json.loads((ROOT / protocol["inputs"]["ratio_bounds"]["file"]).read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / protocol["inputs"]["ratio_receipt"]["file"]).read_text(encoding="utf-8"))
    ratio_hash = sha256(ROOT / protocol["inputs"]["ratio_bounds"]["file"])
    ratio_receipt_verified = receipt["status"] == "passed" and receipt["summarySha256"] == ratio_hash
    if not ratio_receipt_verified:
        raise ValueError("Stage-56 ratio receipt mismatch")
    radius = float(protocol["whitening_rule"]["radius"])
    folds = []
    for source_fold, ratio_fold in zip(source["folds"], ratio["folds"]):
        if source_fold["fold"] != ratio_fold["fold"]:
            raise ValueError("Frozen fold order changed")
        if not ratio_fold["prediction_envelope_available"]:
            points = [{
                "point_index": old["point_index"], "x": old["x"], "observed_y": old["observed_y"], "native_prediction": old["native_prediction"], "actual_absolute_residual": old["actual_absolute_residual"],
                "intersection_minimum": None, "intersection_maximum": None, "residual_upper_bound": None, "covered": None, "center_prediction_inside": None, "grid_checks": [],
            } for old in ratio_fold["points"]]
            folds.append({
                "fold": source_fold["fold"], "native_test_rmse": source_fold["test_metrics"]["rmse"], "prediction_envelope_available": False, "unavailable_reason": ratio_fold["unavailable_reason"],
                "candidate_directions": [], "envelopes": [], "points": points, "grid_cover_count": 0, "partition_cell_count": 0, "evaluated_cell_count": 0, "outside_cell_count": 0, "unresolved_cell_count": 0,
                "unbounded_grid_count": 0, "nonempty_intersection_count": 0, "candidate_evaluation_count": 0, "candidate_grid_containment_check_count": 0, "algebraic_extremizer_count": 0,
                "transform_witness_count": 0, "transform_violation_count": 0, "grid_candidate_violation_count": 0, "intersection_candidate_violation_count": 0, "candidate_feasibility_failure_count": 0,
                "center_prediction_mismatch_count": 0, "point_grid_consistency_check_count": 0, "covered_point_count": 0, "violation_point_count": 0, "unavailable_point_count": len(points), "primary": None,
            })
            continue
        parameters = source_fold["native_parameters"]
        covariance = source_fold["training_jacobian"]["parameter_covariance_matrix"]
        factor = whitening(parameters, covariance, radius)["factor"]
        candidates = ratio_fold["candidate_directions"]
        envelopes = []
        counters = {key: 0 for key in ["nonempty_intersection_count", "transform_violation_count", "grid_candidate_violation_count", "intersection_candidate_violation_count", "candidate_feasibility_failure_count", "center_prediction_mismatch_count"]}
        for baseline in ratio_fold["envelopes"]:
            x = float(baseline["x"])
            grids = [intersection_record(whitened_grid(parameters, covariance, radius, x, divisions, outside_tolerance_relative), baseline, source_fold["fold"], x) for divisions in [1, 2, 4]]
            center = native_center(parameters, x)
            for grid in grids:
                counters["nonempty_intersection_count"] += grid["intersection_nonempty"]
                center_in_union = True if not grid["union_bounded"] else grid["union_minimum"] <= center <= grid["union_maximum"]
                counters["center_prediction_mismatch_count"] += not (center_in_union and grid["intersection_minimum"] <= center <= grid["intersection_maximum"])
            evaluations = []
            for candidate in candidates:
                evaluations.append(evaluate_candidate(candidate, "full_covariance_support", parameters, factor, radius, x, grids))
            for candidate in baseline["algebraic_extremizers"]:
                evaluations.append(evaluate_candidate(candidate, "algebraic_extremizer", parameters, factor, radius, x, grids))
            for candidate in evaluations:
                counters["transform_violation_count"] += not candidate["transform_valid"]
                counters["candidate_feasibility_failure_count"] += not candidate["feasible"]
                for check in candidate["grid_checks"]:
                    counters["grid_candidate_violation_count"] += not check["inside_union"]
                    counters["intersection_candidate_violation_count"] += not check["inside_intersection"]
            envelopes.append({
                "x": x, "center_prediction": center,
                "ratio_minimum": baseline["intersection_minimum"], "ratio_maximum": baseline["intersection_maximum"], "ratio_width": baseline["intersection_width"],
                "grids": grids, "candidate_evaluations": evaluations,
            })
        if any(value for key, value in counters.items() if key != "nonempty_intersection_count") or counters["nonempty_intersection_count"] != len(envelopes) * 3:
            raise ValueError(f"Whitened-cover consistency failure: fold {source_fold['fold']}: {counters}")
        points = []
        for old in ratio_fold["points"]:
            envelope = next(item for item in envelopes if item["x"] == old["x"])
            checks = []
            for grid in envelope["grids"]:
                lower, upper = grid["intersection_minimum"], grid["intersection_maximum"]
                residual = outward(max(abs(old["observed_y"] - lower), abs(old["observed_y"] - upper)), lower=False)
                checks.append({"divisions": grid["divisions"], "residual_upper_bound": residual, "covered": old["actual_absolute_residual"] <= residual, "center_prediction_inside": lower <= old["native_prediction"] <= upper})
            primary = envelope["grids"][2]
            lower, upper = primary["intersection_minimum"], primary["intersection_maximum"]
            residual = outward(max(abs(old["observed_y"] - lower), abs(old["observed_y"] - upper)), lower=False)
            points.append({**old, "intersection_minimum": lower, "intersection_maximum": upper, "residual_upper_bound": residual, "covered": old["actual_absolute_residual"] <= residual, "center_prediction_inside": lower <= old["native_prediction"] <= upper, "grid_checks": checks})
        if any(not point["covered"] or not point["center_prediction_inside"] or any(not check["covered"] or not check["center_prediction_inside"] for check in point["grid_checks"]) for point in points):
            raise ValueError("Whitened point/grid arithmetic consistency failed")
        fold = {
            "fold": source_fold["fold"], "native_test_rmse": source_fold["test_metrics"]["rmse"], "prediction_envelope_available": True, "unavailable_reason": None,
            "candidate_directions": candidates, "envelopes": envelopes, "points": points,
            "grid_cover_count": sum(len(envelope["grids"]) for envelope in envelopes),
            "partition_cell_count": sum(grid["partition_cell_count"] for envelope in envelopes for grid in envelope["grids"]),
            "evaluated_cell_count": sum(grid["evaluated_cell_count"] for envelope in envelopes for grid in envelope["grids"]),
            "outside_cell_count": sum(grid["outside_cell_count"] for envelope in envelopes for grid in envelope["grids"]),
            "unresolved_cell_count": sum(grid["unresolved_cell_count"] for envelope in envelopes for grid in envelope["grids"]),
            "unbounded_grid_count": sum(not grid["union_bounded"] for envelope in envelopes for grid in envelope["grids"]),
            **counters,
            "candidate_evaluation_count": sum(len(envelope["candidate_evaluations"]) for envelope in envelopes),
            "candidate_grid_containment_check_count": sum(len(candidate["grid_checks"]) for envelope in envelopes for candidate in envelope["candidate_evaluations"]),
            "algebraic_extremizer_count": sum(len(envelope["candidate_evaluations"]) - len(candidates) for envelope in envelopes),
            "transform_witness_count": sum(len(envelope["candidate_evaluations"]) for envelope in envelopes),
            "point_grid_consistency_check_count": sum(len(point["grid_checks"]) for point in points),
            "covered_point_count": sum(point["covered"] for point in points),
            "violation_point_count": sum(not point["covered"] for point in points),
            "unavailable_point_count": 0,
        }
        fold["primary"] = primary_summary(fold)
        folds.append(fold)
    totals = {
        "fold_count": len(folds),
        "held_out_point_count": sum(len(fold["points"]) for fold in folds),
        "available_point_count": sum(fold["covered_point_count"] for fold in folds),
        "unavailable_point_count": sum(fold["unavailable_point_count"] for fold in folds),
        "unavailable_fold_ids": [fold["fold"] for fold in folds if not fold["prediction_envelope_available"]],
        "grid_cover_count": sum(fold["grid_cover_count"] for fold in folds),
        "partition_cell_count": sum(fold["partition_cell_count"] for fold in folds),
        "native_cell_evaluation_count": sum(fold["evaluated_cell_count"] for fold in folds),
        "outside_cell_count": sum(fold["outside_cell_count"] for fold in folds),
        "unresolved_cell_count": sum(fold["unresolved_cell_count"] for fold in folds),
        "unbounded_grid_count": sum(fold["unbounded_grid_count"] for fold in folds),
        "nonempty_intersection_count": sum(fold["nonempty_intersection_count"] for fold in folds),
        "candidate_direction_count": sum(len(fold["candidate_directions"]) for fold in folds),
        "algebraic_extremizer_count": sum(fold["algebraic_extremizer_count"] for fold in folds),
        "candidate_evaluation_count": sum(fold["candidate_evaluation_count"] for fold in folds),
        "candidate_grid_containment_check_count": sum(fold["candidate_grid_containment_check_count"] for fold in folds),
        "transform_witness_count": sum(fold["transform_witness_count"] for fold in folds),
        "transform_violation_count": sum(fold["transform_violation_count"] for fold in folds),
        "grid_candidate_violation_count": sum(fold["grid_candidate_violation_count"] for fold in folds),
        "intersection_candidate_violation_count": sum(fold["intersection_candidate_violation_count"] for fold in folds),
        "candidate_feasibility_failure_count": sum(fold["candidate_feasibility_failure_count"] for fold in folds),
        "center_prediction_mismatch_count": sum(fold["center_prediction_mismatch_count"] for fold in folds),
        "point_grid_consistency_check_count": sum(fold["point_grid_consistency_check_count"] for fold in folds),
        "covered_point_count": sum(fold["covered_point_count"] for fold in folds),
        "violation_point_count": sum(fold["violation_point_count"] for fold in folds),
        "refit_count": 0,
    }
    totals["bounded_grid_count"] = totals["grid_cover_count"] - totals["unbounded_grid_count"]
    grid_totals = []
    for divisions in [1, 2, 4]:
        records = [envelope["grids"][[1, 2, 4].index(divisions)] for fold in folds for envelope in fold["envelopes"]]
        largest = max((record["largest_intersection_tightening"] for record in records), key=lambda item: item["intersection_width_reduction"], default=None)
        grid_totals.append({
            "divisions": divisions,
            "grid_count": len(records),
            "partition_cell_count": sum(record["partition_cell_count"] for record in records),
            "evaluated_cell_count": sum(record["evaluated_cell_count"] for record in records),
            "outside_cell_count": sum(record["outside_cell_count"] for record in records),
            "unresolved_cell_count": sum(record["unresolved_cell_count"] for record in records),
            "unbounded_grid_count": sum(not record["union_bounded"] for record in records),
            "bounded_grid_count": sum(record["union_bounded"] for record in records),
            "intersection_tightened_count": sum(record["intersection_tightened"] for record in records),
            "intersection_unchanged_count": sum(not record["intersection_tightened"] for record in records),
            "min_intersection_to_ratio_width_ratio": min(record["intersection_to_ratio_width_ratio"] for record in records),
            "median_intersection_to_ratio_width_ratio": median([record["intersection_to_ratio_width_ratio"] for record in records]),
            "max_intersection_to_ratio_width_ratio": max(record["intersection_to_ratio_width_ratio"] for record in records),
            "max_intersection_width_reduction": max(record["intersection_width_reduction"] for record in records),
            "median_intersection_width_reduction": median([record["intersection_width_reduction"] for record in records]),
            "largest_intersection_tightening": largest,
        })
    primary = grid_totals[2]
    totals.update({
        "primary_intersection_tightened_count": primary["intersection_tightened_count"],
        "primary_intersection_unchanged_count": primary["intersection_unchanged_count"],
        "min_primary_intersection_to_ratio_width_ratio": primary["min_intersection_to_ratio_width_ratio"],
        "median_primary_intersection_to_ratio_width_ratio": primary["median_intersection_to_ratio_width_ratio"],
        "max_primary_intersection_to_ratio_width_ratio": primary["max_intersection_to_ratio_width_ratio"],
        "max_primary_intersection_width_reduction": primary["max_intersection_width_reduction"],
        "median_primary_intersection_width_reduction": primary["median_intersection_width_reduction"],
        "largest_primary_intersection_tightening": primary["largest_intersection_tightening"],
    })
    for key, value in protocol["expected_structure"].items():
        if totals[key] != value:
            raise ValueError(f"Frozen structural expectation failed: {key}: {totals[key]} != {value}")
    return {
        "status": "computed_roszman1_whitened_cover_grid",
        "protocol_sha256": sha256(protocol_path),
        "protocol_amendment_sha256": sha256(amendment_path),
        "native_identifiability_sha256": sha256(ROOT / protocol["inputs"]["native_identifiability"]["file"]),
        "ratio_bounds_sha256": ratio_hash,
        "ratio_receipt_verified": ratio_receipt_verified,
        "primary_grid": 4,
        "analysis_scope": {**protocol["analysis_scope"], "outside_boundary_amendment": "01", "outside_boundary_tolerance_relative": outside_tolerance_relative, "baseline_radius": radius, "high_precision_decimal_digits": 80, "outward_rounding": True, "outward_relative_margin": 1.0e-24, "exact_rational_certificate": False, "probability_region": False, "historical_baseline_replaced": False},
        "known_answer": source.get("known_answer"),
        "folds": folds,
        "grid_totals": grid_totals,
        "totals": totals,
        "exact_global_optimum": None,
        "decision": protocol["decision"],
        "limitations": [
            "Whitening maps the ellipsoid to a ball exactly, but the covering cube also contains points outside the ball and is not an exact nonlinear image",
            "Only cells proved wholly outside the ball can be discarded; every possible ball-intersecting zero-denominator cell remains unresolved and makes the grid union unbounded",
            "Unbounded-union candidate containment is not a finite-interval certificate; all bounded statuses and unchanged intersections are retained",
            "Fold 5 has no certified negative denominator and receives no cells, candidates or finite residual upper bounds",
            "The 200 transform witnesses and 600 grid checks are consistency checks, not a substitute for the complete cover or an independent experiment",
            "High-precision outward-rounded evaluated cells are not exact rational certificates, exact global optima or probability regions",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    actual = [envelope["grids"][2]["intersection_to_ratio_width_ratio"] for fold in summary.get("folds", []) for envelope in fold.get("envelopes", [])]
    required = [envelope["grids"][2]["intersection_to_ratio_width_ratio"] for fold in expected["folds"] for envelope in fold["envelopes"]]
    if actual != required:
        errors.append("Primary whitened intersection-to-stage56 width ratio mismatch")
    for key in ["grid_candidate_violation_count", "intersection_candidate_violation_count", "transform_violation_count"]:
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
    grid_totals = summary["grid_totals"]
    divisions = [item["divisions"] for item in grid_totals]
    fig, axes = plt.subplots(2, 2, figsize=(16.0, 11.5), constrained_layout=True)
    evaluated = [item["evaluated_cell_count"] for item in grid_totals]
    unresolved = [item["unresolved_cell_count"] for item in grid_totals]
    axes[0, 0].bar([str(value) for value in divisions], evaluated, color="#316c9b", label="evaluated")
    axes[0, 0].bar([str(value) for value in divisions], unresolved, bottom=evaluated, color="#b44b4b", label="unresolved")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xlabel("Divisions per dimension")
    axes[0, 0].set_ylabel("Cells (log)")
    axes[0, 0].set_title("A. Evaluated and unresolved cells retained")
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 0].grid(axis="y", which="both", alpha=0.2)

    axes[0, 1].plot(divisions, [item["median_intersection_to_ratio_width_ratio"] for item in grid_totals], marker="o", color="#316c9b", label="median")
    axes[0, 1].plot(divisions, [item["max_intersection_to_ratio_width_ratio"] for item in grid_totals], marker="s", color="#876a32", label="maximum")
    axes[0, 1].axhline(1, color="#555555", linestyle="--", linewidth=1)
    axes[0, 1].set_xticks(divisions)
    axes[0, 1].set_ylabel("Intersection / stage-56 width")
    axes[0, 1].set_title("B. No tightening is presumed")
    axes[0, 1].legend(frameon=False, fontsize=8)
    axes[0, 1].grid(alpha=0.2)

    for fold, color in zip(summary["folds"][:4], ["#316c9b", "#4f7b5b", "#876a32", "#6a4c93"]):
        norms = [candidate["whitened_norm"] for envelope in fold["envelopes"] for candidate in envelope["candidate_evaluations"]]
        axes[1, 0].scatter([fold["fold"]] * len(norms), norms, color=color, s=16, alpha=0.55)
    axes[1, 0].axhline(4, color="#b44b4b", linestyle="--", linewidth=1, label="radius 4")
    axes[1, 0].set_xticks(range(1, 6))
    axes[1, 0].set_ylabel("Candidate whitened norm")
    axes[1, 0].set_title("C. Every transform witness remains in the ball")
    axes[1, 0].legend(frameon=False, fontsize=8)
    axes[1, 0].grid(alpha=0.2)

    available = [len(fold["points"]) if fold["prediction_envelope_available"] else 0 for fold in summary["folds"]]
    unavailable = [fold["unavailable_point_count"] for fold in summary["folds"]]
    axes[1, 1].bar(range(1, 6), available, color="#316c9b", label="available")
    axes[1, 1].bar(range(1, 6), unavailable, bottom=available, color="#b44b4b", label="unavailable")
    axes[1, 1].set_xticks(range(1, 6))
    axes[1, 1].set_ylabel("Held-out observations")
    axes[1, 1].set_title("D. Fold 5 receives no cells or finite bounds")
    axes[1, 1].legend(frameon=False, fontsize=8)
    axes[1, 1].grid(axis="y", alpha=0.2)

    totals = summary["totals"]
    fig.suptitle(f"Roszman1 whitened cover: {totals['partition_cell_count']} cells, {totals['unresolved_cell_count']} unresolved, {totals['transform_witness_count']} transform witnesses", fontsize=15, y=1.045)
    fig.text(0.5, 1.012, "Exact affine whitening with conservative cover; no exact optimum, probability or hidden singular-cell claim.", ha="center", fontsize=9, color="#555555")
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
            errors.append("Missing Roszman1 whitened-cover output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored Roszman1 whitened-cover output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid Roszman1 whitened-cover figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "partition_cells": summary["totals"]["partition_cell_count"],
        "evaluated_cells": summary["totals"]["native_cell_evaluation_count"],
        "unresolved_cells": summary["totals"]["unresolved_cell_count"],
        "unbounded_grids": summary["totals"]["unbounded_grid_count"],
        "candidate_evaluations": summary["totals"]["candidate_evaluation_count"],
        "transform_witnesses": summary["totals"]["transform_witness_count"],
        "primary_tightened": summary["totals"]["primary_intersection_tightened_count"],
        "primary_unchanged": summary["totals"]["primary_intersection_unchanged_count"],
        "primary_median_ratio": summary["totals"]["median_primary_intersection_to_ratio_width_ratio"],
        "unavailable": summary["totals"]["unavailable_point_count"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
