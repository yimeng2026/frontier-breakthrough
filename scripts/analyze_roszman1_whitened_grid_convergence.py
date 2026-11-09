"""Streamed 8-per-dimension whitened-cover convergence and vertex diagnostics."""

import argparse
import itertools
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np

from analyze_chwirut_holdout import sha256
from analyze_roszman1_native_ellipsoid_continuous import outward
from analyze_roszman1_native_holdout import native_model
from analyze_roszman1_whitened_cover_grid_erratum import candidate_transform, native_center, vertex_interval_audit, whitened_cell_interval, whitening

mp.mp.dps = 80
ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-whitened-grid-convergence-protocol.json"
OUT = ROOT / "validation/roszman1-whitened-grid-convergence.json"
FIGURE = ROOT / "papers/66_Roszman1白化网格收敛与共享见证/fig66_roszman1_whitened_grid_convergence.png"
PARAMETER_NAMES = ["b1", "b2", "b3", "b4"]


def vertex_witnesses(parameters, factor, radius, x, cell, endpoint):
    audit = vertex_interval_audit(parameters, factor, radius, x, cell, endpoint)
    if audit["vertex_interval_violation_count"]:
        raise ValueError(f"Corrected vertex interval gate failed: {audit}")
    return {
        "endpoint": endpoint,
        "cell": cell,
        "vertices": audit["vertices"],
        "vertex_evaluation_count": audit["vertex_evaluation_count"],
        "vertex_interval_violation_count": audit["vertex_interval_violation_count"],
        "feasible_vertex_count": audit["feasible_vertex_count"],
        "outer_vertex_count": audit["outer_vertex_count"],
        "max_interval_gap": audit["max_interval_gap"],
    }


def evaluate_grid8(parameters, covariance, radius, x):
    transformed = whitening(parameters, covariance, radius)
    factor = transformed["factor"]
    cover_lower = [outward(-mp.mpf(str(radius)), lower=True)] * 4
    cover_upper = [outward(mp.mpf(str(radius)), lower=False)] * 4
    divisions = 8
    counts = {"evaluated_cell_count": 0, "outside_cell_count": 0, "unresolved_cell_count": 0}
    union_minimum = None
    union_maximum = None
    minimum_cell = None
    maximum_cell = None
    for indices in itertools.product(range(divisions), repeat=4):
        lower, upper = [], []
        for axis, index in enumerate(indices):
            left, right = mp.mpf(str(cover_lower[axis])), mp.mpf(str(cover_upper[axis]))
            lower.append(float(left + index * (right - left) / divisions))
            upper.append(float(left + (index + 1) * (right - left) / divisions))
        cell = whitened_cell_interval(parameters, factor, radius, x, lower, upper, 1.0e-12)
        status = cell["status"]
        status_key = {"evaluated": "evaluated_cell_count", "outside_ball": "outside_cell_count", "unresolved_denominator": "unresolved_cell_count"}[status]
        counts[status_key] += 1
        if status != "evaluated":
            continue
        cell = {"indices": list(indices), **cell}
        if union_minimum is None or cell["prediction_minimum"] < union_minimum:
            union_minimum = cell["prediction_minimum"]
            minimum_cell = cell
        if union_maximum is None or cell["prediction_maximum"] > union_maximum:
            union_maximum = cell["prediction_maximum"]
            maximum_cell = cell
    bounded = counts["unresolved_cell_count"] == 0
    if bounded and counts["evaluated_cell_count"] == 0:
        raise ValueError("No evaluated cells remain in a bounded grid-8 cover")
    witnesses = []
    if bounded:
        witnesses.append(vertex_witnesses(parameters, factor, radius, x, minimum_cell, "union_minimum"))
        witnesses.append(vertex_witnesses(parameters, factor, radius, x, maximum_cell, "union_maximum"))
    return {
        "divisions": divisions,
        "partition_cell_count": divisions ** 4,
        **counts,
        "union_bounded": bounded,
        "union_minimum": union_minimum if bounded else None,
        "union_maximum": union_maximum if bounded else None,
        "outside_boundary_tolerance": 1.0e-12 * (1 + float(radius) ** 2),
        "symmetric_covariance": transformed["symmetric_covariance"],
        "cholesky_factor": transformed["factor_rows"],
        "cholesky_reconstruction_max_error": transformed["reconstruction_max_error"],
        "witness_cell_count": len(witnesses),
        "vertex_evaluation_count": sum(witness["vertex_evaluation_count"] for witness in witnesses),
        "vertex_witnesses": witnesses,
        "feasible_vertex_witness_count": sum(witness["feasible_vertex_count"] for witness in witnesses),
        "outer_vertex_witness_count": sum(witness["outer_vertex_count"] for witness in witnesses),
        "max_vertex_interval_gap": max((witness["max_interval_gap"] for witness in witnesses), default=0.0),
    }


def evaluate_candidate(candidate, kind, parameters, factor, radius, x, grid):
    exact = candidate["exact_parameters"]
    transformed = candidate_transform(parameters, factor, radius, exact)
    values = [float(exact[name]) for name in PARAMETER_NAMES]
    denominator = float(mp.mpf(str(x)) - mp.mpf(str(exact["b4"])))
    prediction = float(native_model(float(x), *values))
    feasible = candidate["feasible"] and transformed["transform_valid"] and denominator < 0 and math.isfinite(prediction) and math.isclose(candidate["ellipsoid_quadratic"], 16.0, rel_tol=1.0e-10, abs_tol=1.0e-10)
    inside_union = True if not grid["union_bounded"] else grid["union_minimum"] <= prediction <= grid["union_maximum"]
    check = {
        "union_bounded": grid["union_bounded"],
        "finite_union_check": grid["union_bounded"],
        "inside_union": inside_union,
        "inside_intersection": grid["intersection_minimum"] <= prediction <= grid["intersection_maximum"],
    }
    return {
        "kind": kind,
        "direction": candidate["direction"],
        "prediction": prediction,
        "denominator": denominator,
        "ellipsoid_quadratic": candidate["ellipsoid_quadratic"],
        **transformed,
        "feasible": feasible,
        "grid8_check": check,
    }


def median(values):
    return float(np.median(values)) if values else None


def fold_grid8_summary(fold):
    records = [envelope["grid8"] for envelope in fold["envelopes"]]
    if not records:
        return None
    return {
        "additional_tightened_count": sum(record["additional_tightened"] for record in records),
        "plateau_count": sum(record["plateau"] for record in records),
        "median_grid8_to_grid4_width_ratio": median([record["grid8_to_grid4_width_ratio"] for record in records]),
        "max_grid8_width_reduction_vs_grid4": max(record["grid8_width_reduction_vs_grid4"] for record in records),
        "witness_cell_count": sum(record["witness_cell_count"] for record in records),
        "feasible_vertex_witness_count": sum(record["feasible_vertex_witness_count"] for record in records),
        "outer_vertex_witness_count": sum(record["outer_vertex_witness_count"] for record in records),
        "largest_incremental_tightening": max((record["largest_incremental_tightening"] for record in records), key=lambda item: item["grid8_width_reduction_vs_grid4"]),
    }


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_roszman1_whitened_grid_convergence":
        raise ValueError("Whitened-grid convergence protocol is not frozen")
    for key, info in protocol["inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {key}")
    amendment_path = protocol_path.with_name("roszman1-whitened-grid-convergence-protocol-amendment-01.json")
    if not amendment_path.is_file():
        raise ValueError("Missing convergence erratum-alignment amendment 01")
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    if amendment["status"] != "frozen_before_roszman1_whitened_grid_convergence_results" or amendment["original_protocol"]["sha256"] != sha256(protocol_path):
        raise ValueError("Convergence amendment does not match the original protocol")
    for key, info in amendment["corrected_inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Corrected input hash changed: {key}")
    source = json.loads((ROOT / protocol["inputs"]["native_identifiability"]["file"]).read_text(encoding="utf-8"))
    corrected = amendment["corrected_inputs"]
    whitened = json.loads((ROOT / corrected["whitened_bounds"]["file"]).read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / corrected["whitened_receipt"]["file"]).read_text(encoding="utf-8"))
    whitened_hash = sha256(ROOT / corrected["whitened_bounds"]["file"])
    whitened_receipt_verified = receipt["status"] == "passed" and receipt["summarySha256"] == whitened_hash and receipt["primaryGrid"] == 4 and receipt["nativeCellEvaluationCount"] == 5460 and receipt["unresolvedCellCount"] == 0 and receipt["transformWitnessCount"] == 200 and receipt["transformViolationCount"] == 0 and receipt["vertexIntervalViolationCount"] == 0 and receipt["originalProofValidity"] == "invalid_for_conservative_proof" and receipt["primaryIntersectionTightenedCount"] == 17 and receipt["primaryIntersectionUnchangedCount"] == 3
    amendment02_path = protocol_path.with_name("roszman1-whitened-grid-convergence-protocol-amendment-02.json")
    if not amendment02_path.is_file():
        raise ValueError("Missing direct stage-56 amendment 02")
    amendment02 = json.loads(amendment02_path.read_text(encoding="utf-8"))
    if amendment02["status"] != "frozen_before_roszman1_whitened_grid_convergence_results" or amendment02["previous_amendment"]["sha256"] != sha256(amendment_path):
        raise ValueError("Direct stage-56 amendment is not aligned with amendment 01")
    for key, info in amendment02["additional_inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Direct stage-56 input hash changed: {key}")
    ratio56 = json.loads((ROOT / amendment02["additional_inputs"]["ratio_bounds"]["file"]).read_text(encoding="utf-8"))
    receipt56 = json.loads((ROOT / amendment02["additional_inputs"]["ratio_receipt"]["file"]).read_text(encoding="utf-8"))
    ratio56_hash = sha256(ROOT / amendment02["additional_inputs"]["ratio_bounds"]["file"])
    stage56_receipt_verified = receipt56["status"] == "passed" and receipt56["summarySha256"] == ratio56_hash
    if not whitened_receipt_verified or not stage56_receipt_verified:
        raise ValueError("Corrected whitened receipt, original-invalid scope or stage-56 receipt mismatch")
    amendment03_path = protocol_path.with_name("roszman1-whitened-grid-convergence-protocol-amendment-03.json")
    if not amendment03_path.is_file():
        raise ValueError("Missing grid-8 outside-count amendment 03")
    amendment03 = json.loads(amendment03_path.read_text(encoding="utf-8"))
    if amendment03["status"] != "frozen_before_roszman1_whitened_grid_convergence_results" or amendment03["previous_amendment"]["sha256"] != sha256(amendment02_path):
        raise ValueError("Grid-8 outside-count amendment is not aligned with amendment 02")
    expected_structure = dict(protocol["expected_structure"])
    expected_structure["outside_cell_count"] = amendment03["correction"]["expected_outside_cell_count"]
    radius = 4.0
    folds = []
    for source_fold, whitened_fold, ratio56_fold in zip(source["folds"], whitened["folds"], ratio56["folds"]):
        if source_fold["fold"] != whitened_fold["fold"] or source_fold["fold"] != ratio56_fold["fold"]:
            raise ValueError("Frozen fold order changed")
        if not whitened_fold["prediction_envelope_available"]:
            points = [{
                "point_index": old["point_index"], "x": old["x"], "observed_y": old["observed_y"], "native_prediction": old["native_prediction"], "actual_absolute_residual": old["actual_absolute_residual"],
                "intersection_minimum": None, "intersection_maximum": None, "residual_upper_bound": None, "covered": None, "center_prediction_inside": None, "grid8_check": None,
            } for old in whitened_fold["points"]]
            folds.append({
                "fold": source_fold["fold"], "native_test_rmse": source_fold["test_metrics"]["rmse"], "prediction_envelope_available": False, "unavailable_reason": whitened_fold["unavailable_reason"],
                "candidate_directions": [], "envelopes": [], "points": points, "grid8_cover_count": 0, "grid8_partition_cell_count": 0, "evaluated_cell_count": 0, "outside_cell_count": 0, "unresolved_cell_count": 0,
                "grid8_unbounded_grid_count": 0, "nonempty_intersection_count": 0, "candidate_evaluation_count": 0, "candidate_grid8_containment_check_count": 0, "algebraic_extremizer_count": 0,
                "transform_witness_count": 0, "transform_violation_count": 0, "grid8_candidate_violation_count": 0, "intersection_candidate_violation_count": 0, "candidate_feasibility_failure_count": 0,
                "center_prediction_mismatch_count": 0, "point_grid8_consistency_check_count": 0, "covered_point_count": 0, "violation_point_count": 0, "unavailable_point_count": len(points), "grid8": None,
            })
            continue
        parameters = source_fold["native_parameters"]
        covariance = source_fold["training_jacobian"]["parameter_covariance_matrix"]
        factor = whitening(parameters, covariance, radius)["factor"]
        candidates = whitened_fold["candidate_directions"]
        envelopes = []
        counters = {key: 0 for key in ["nonempty_intersection_count", "transform_violation_count", "grid8_candidate_violation_count", "intersection_candidate_violation_count", "candidate_feasibility_failure_count", "center_prediction_mismatch_count"]}
        for baseline in whitened_fold["envelopes"]:
            x = float(baseline["x"])
            ratio56_baseline = next(item for item in ratio56_fold["envelopes"] if float(item["x"]) == x)
            if baseline["ratio_minimum"] != ratio56_baseline["intersection_minimum"] or baseline["ratio_maximum"] != ratio56_baseline["intersection_maximum"] or baseline["ratio_width"] != ratio56_baseline["intersection_width"]:
                raise ValueError("Corrected envelope no longer matches the direct stage-56 baseline")
            grid = evaluate_grid8(parameters, covariance, radius, x)
            lower = baseline["ratio_minimum"] if not grid["union_bounded"] else max(grid["union_minimum"], baseline["ratio_minimum"])
            upper = baseline["ratio_maximum"] if not grid["union_bounded"] else min(grid["union_maximum"], baseline["ratio_maximum"])
            width = outward(upper - lower, lower=False)
            grid4_old = baseline["grids"][2]
            grid4 = {key: grid4_old[key] for key in ["divisions", "union_bounded", "union_minimum", "union_maximum", "intersection_minimum", "intersection_maximum", "intersection_width", "intersection_to_ratio_width_ratio", "intersection_width_reduction", "intersection_tightened"]}
            tolerance = 1.0e-12 * (1 + abs(grid4["union_minimum"] or 0) + abs(grid4["union_maximum"] or 0))
            if grid4["union_bounded"] and (not grid["union_bounded"] or grid["union_minimum"] < grid4["union_minimum"] - tolerance or grid["union_maximum"] > grid4["union_maximum"] + tolerance):
                raise ValueError("Grid-8 union escaped the frozen grid-4 union")
            if lower < grid4["intersection_minimum"] - 1.0e-12 or upper > grid4["intersection_maximum"] + 1.0e-12:
                raise ValueError("Grid-8 intersection escaped the frozen grid-4 intersection")
            incremental_ratio = width / grid4["intersection_width"]
            plateau = math.isclose(incremental_ratio, 1.0, rel_tol=1.0e-12, abs_tol=1.0e-12)
            additional = not plateau and width < grid4["intersection_width"]
            reduction = grid4["intersection_width"] - width
            grid.update({
                "baseline_minimum": baseline["ratio_minimum"], "baseline_maximum": baseline["ratio_maximum"],
                "intersection_minimum": lower, "intersection_maximum": upper, "intersection_width": width,
                "grid8_to_ratio_width_ratio": width / baseline["ratio_width"],
                "grid8_to_grid4_width_ratio": incremental_ratio,
                "grid8_width_reduction_vs_grid4": reduction,
                "additional_tightened": additional,
                "plateau": plateau,
                "intersection_tightened": width < baseline["ratio_width"],
                "intersection_nonempty": lower <= upper,
                "largest_incremental_tightening": {
                    "fold": source_fold["fold"], "x": x, "grid8_to_grid4_width_ratio": incremental_ratio, "grid8_width_reduction_vs_grid4": reduction,
                    "grid4_minimum": grid4["intersection_minimum"], "grid4_maximum": grid4["intersection_maximum"],
                    "grid8_minimum": lower, "grid8_maximum": upper,
                },
            })
            center = native_center(parameters, x)
            counters["nonempty_intersection_count"] += grid["intersection_nonempty"]
            center_in_union = True if not grid["union_bounded"] else grid["union_minimum"] <= center <= grid["union_maximum"]
            counters["center_prediction_mismatch_count"] += not (center_in_union and lower <= center <= upper)
            evaluations = []
            for candidate in candidates:
                evaluations.append(evaluate_candidate(candidate, "full_covariance_support", parameters, factor, radius, x, grid))
            for candidate in ratio56_baseline["algebraic_extremizers"]:
                evaluations.append(evaluate_candidate(candidate, "algebraic_extremizer", parameters, factor, radius, x, grid))
            for candidate in evaluations:
                counters["transform_violation_count"] += not candidate["transform_valid"]
                counters["candidate_feasibility_failure_count"] += not candidate["feasible"]
                counters["grid8_candidate_violation_count"] += not candidate["grid8_check"]["inside_union"]
                counters["intersection_candidate_violation_count"] += not candidate["grid8_check"]["inside_intersection"]
            envelopes.append({
                "x": x, "center_prediction": center,
                "ratio_minimum": baseline["ratio_minimum"], "ratio_maximum": baseline["ratio_maximum"], "ratio_width": baseline["ratio_width"],
                "grid4_reference": grid4, "grid8": grid, "candidate_evaluations": evaluations,
            })
        if any(value for key, value in counters.items() if key != "nonempty_intersection_count") or counters["nonempty_intersection_count"] != len(envelopes):
            raise ValueError(f"Grid-8 consistency failure: fold {source_fold['fold']}: {counters}")
        points = []
        for old in whitened_fold["points"]:
            envelope = next(item for item in envelopes if item["x"] == old["x"])
            grid = envelope["grid8"]
            lower, upper = grid["intersection_minimum"], grid["intersection_maximum"]
            residual = outward(max(abs(old["observed_y"] - lower), abs(old["observed_y"] - upper)), lower=False)
            covered = old["actual_absolute_residual"] <= residual
            inside = lower <= old["native_prediction"] <= upper
            points.append({
                **old, "intersection_minimum": lower, "intersection_maximum": upper, "residual_upper_bound": residual,
                "covered": covered, "center_prediction_inside": inside,
                "grid8_check": {"residual_upper_bound": residual, "covered": covered, "center_prediction_inside": inside},
            })
        if any(not point["covered"] or not point["center_prediction_inside"] for point in points):
            raise ValueError("Grid-8 point arithmetic consistency failed")
        fold = {
            "fold": source_fold["fold"], "native_test_rmse": source_fold["test_metrics"]["rmse"], "prediction_envelope_available": True, "unavailable_reason": None,
            "candidate_directions": candidates, "envelopes": envelopes, "points": points,
            "grid8_cover_count": len(envelopes),
            "grid8_partition_cell_count": sum(envelope["grid8"]["partition_cell_count"] for envelope in envelopes),
            "evaluated_cell_count": sum(envelope["grid8"]["evaluated_cell_count"] for envelope in envelopes),
            "outside_cell_count": sum(envelope["grid8"]["outside_cell_count"] for envelope in envelopes),
            "unresolved_cell_count": sum(envelope["grid8"]["unresolved_cell_count"] for envelope in envelopes),
            "grid8_unbounded_grid_count": sum(not envelope["grid8"]["union_bounded"] for envelope in envelopes),
            **counters,
            "candidate_evaluation_count": sum(len(envelope["candidate_evaluations"]) for envelope in envelopes),
            "candidate_grid8_containment_check_count": sum(len(envelope["candidate_evaluations"]) for envelope in envelopes),
            "algebraic_extremizer_count": sum(len(envelope["candidate_evaluations"]) - len(candidates) for envelope in envelopes),
            "transform_witness_count": sum(len(envelope["candidate_evaluations"]) for envelope in envelopes),
            "point_grid8_consistency_check_count": len(points),
            "covered_point_count": sum(point["covered"] for point in points),
            "violation_point_count": sum(not point["covered"] for point in points),
            "unavailable_point_count": 0,
        }
        fold["grid8"] = fold_grid8_summary(fold)
        folds.append(fold)
    totals = {
        "fold_count": len(folds),
        "held_out_point_count": sum(len(fold["points"]) for fold in folds),
        "available_point_count": sum(fold["covered_point_count"] for fold in folds),
        "unavailable_point_count": sum(fold["unavailable_point_count"] for fold in folds),
        "unavailable_fold_ids": [fold["fold"] for fold in folds if not fold["prediction_envelope_available"]],
        "grid4_reference_count": sum(len(fold["envelopes"]) for fold in folds),
        "grid8_cover_count": sum(fold["grid8_cover_count"] for fold in folds),
        "grid8_partition_cell_count": sum(fold["grid8_partition_cell_count"] for fold in folds),
        "native_cell_evaluation_count": sum(fold["evaluated_cell_count"] for fold in folds),
        "outside_cell_count": sum(fold["outside_cell_count"] for fold in folds),
        "unresolved_cell_count": sum(fold["unresolved_cell_count"] for fold in folds),
        "grid8_unbounded_grid_count": sum(fold["grid8_unbounded_grid_count"] for fold in folds),
        "nonempty_intersection_count": sum(fold["nonempty_intersection_count"] for fold in folds),
        "candidate_direction_count": sum(len(fold["candidate_directions"]) for fold in folds),
        "algebraic_extremizer_count": sum(fold["algebraic_extremizer_count"] for fold in folds),
        "candidate_evaluation_count": sum(fold["candidate_evaluation_count"] for fold in folds),
        "candidate_grid8_containment_check_count": sum(fold["candidate_grid8_containment_check_count"] for fold in folds),
        "transform_witness_count": sum(fold["transform_witness_count"] for fold in folds),
        "transform_violation_count": sum(fold["transform_violation_count"] for fold in folds),
        "grid8_candidate_violation_count": sum(fold["grid8_candidate_violation_count"] for fold in folds),
        "intersection_candidate_violation_count": sum(fold["intersection_candidate_violation_count"] for fold in folds),
        "candidate_feasibility_failure_count": sum(fold["candidate_feasibility_failure_count"] for fold in folds),
        "center_prediction_mismatch_count": sum(fold["center_prediction_mismatch_count"] for fold in folds),
        "point_grid8_consistency_check_count": sum(fold["point_grid8_consistency_check_count"] for fold in folds),
        "covered_point_count": sum(fold["covered_point_count"] for fold in folds),
        "violation_point_count": sum(fold["violation_point_count"] for fold in folds),
        "refit_count": 0,
    }
    records = [envelope["grid8"] for fold in folds for envelope in fold["envelopes"]]
    totals.update({
        "grid8_bounded_grid_count": sum(record["union_bounded"] for record in records),
        "grid8_witness_cell_count": sum(record["witness_cell_count"] for record in records),
        "grid8_vertex_evaluation_count": sum(record["vertex_evaluation_count"] for record in records),
        "feasible_vertex_witness_count": sum(record["feasible_vertex_witness_count"] for record in records),
        "outer_vertex_witness_count": sum(record["outer_vertex_witness_count"] for record in records),
        "max_vertex_interval_gap": max((record["max_vertex_interval_gap"] for record in records), default=0.0),
        "grid8_additional_tightened_count": sum(record["additional_tightened"] for record in records),
        "grid8_plateau_count": sum(record["plateau"] for record in records),
        "grid8_intersection_tightened_count": sum(record["intersection_tightened"] for record in records),
        "grid8_intersection_unchanged_count": sum(not record["intersection_tightened"] for record in records),
        "min_grid8_to_grid4_width_ratio": min(record["grid8_to_grid4_width_ratio"] for record in records),
        "median_grid8_to_grid4_width_ratio": median([record["grid8_to_grid4_width_ratio"] for record in records]),
        "max_grid8_to_grid4_width_ratio": max(record["grid8_to_grid4_width_ratio"] for record in records),
        "min_grid8_to_stage56_width_ratio": min(record["grid8_to_ratio_width_ratio"] for record in records),
        "median_grid8_to_stage56_width_ratio": median([record["grid8_to_ratio_width_ratio"] for record in records]),
        "max_grid8_to_stage56_width_ratio": max(record["grid8_to_ratio_width_ratio"] for record in records),
        "max_grid8_width_reduction_vs_grid4": max(record["grid8_width_reduction_vs_grid4"] for record in records),
        "median_grid8_width_reduction_vs_grid4": median([record["grid8_width_reduction_vs_grid4"] for record in records]),
        "largest_grid8_incremental_tightening": max((record["largest_incremental_tightening"] for record in records), key=lambda item: item["grid8_width_reduction_vs_grid4"], default=None),
    })
    for key, value in expected_structure.items():
        if totals[key] != value:
            raise ValueError(f"Frozen structural expectation failed: {key}: {totals[key]} != {value}")
    return {
        "status": "computed_roszman1_whitened_grid_convergence",
        "protocol_sha256": sha256(protocol_path),
        "protocol_amendment_sha256": sha256(amendment_path),
        "protocol_amendment02_sha256": sha256(amendment02_path),
        "protocol_amendment03_sha256": sha256(amendment03_path),
        "native_identifiability_sha256": sha256(ROOT / protocol["inputs"]["native_identifiability"]["file"]),
        "whitened_bounds_sha256": whitened_hash,
        "stage56_bounds_sha256": ratio56_hash,
        "stage56_receipt_verified": stage56_receipt_verified,
        "whitened_receipt_verified": whitened_receipt_verified,
        "diagnostic_grid": 8,
        "analysis_scope": {**protocol["analysis_scope"], "outside_count_amendment": "03", "source_erratum": "whitened-cover-grid-erratum-01", "original_whitened_proof_validity": "invalid_for_conservative_proof", "corrected_negative_denominator_displacement": True, "baseline_radius": radius, "high_precision_decimal_digits": 80, "outward_rounding": True, "outward_relative_margin": 1.0e-24, "exact_rational_certificate": False, "probability_region": False, "historical_baseline_replaced": False},
        "known_answer": source.get("known_answer"),
        "historical_grid_totals": whitened["grid_totals"],
        "folds": folds,
        "totals": totals,
        "exact_global_optimum": None,
        "decision": protocol["decision"],
        "limitations": [
            "Grid-4/grid-8 ratios describe this frozen refinement sequence only and are not asymptotic errors, convergence proofs or global optima",
            "The whitened cover contains points outside the ball; outer vertices are not feasible extrema unless their norm and denominator pass the gates",
            "Unresolved denominator cells remain unresolved and produce unbounded unions, never finite reciprocal or vertex witnesses",
            "Fold 5 has no certified negative denominator and receives no cells, candidates, vertex witnesses or finite residual bounds",
            "The 200 transform witnesses, grid-8 candidate checks and vertex witnesses are consistency evidence, not a substitute for full cell coverage or an independent experiment",
            "High-precision outward-rounded intervals are not exact rational certificates or probability regions",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    actual = [envelope["grid8"]["grid8_to_grid4_width_ratio"] for fold in summary.get("folds", []) for envelope in fold.get("envelopes", [])]
    required = [envelope["grid8"]["grid8_to_grid4_width_ratio"] for fold in expected["folds"] for envelope in fold["envelopes"]]
    if actual != required:
        errors.append("Grid-8-to-grid-4 incremental width ratio mismatch")
    for key in ["grid8_candidate_violation_count", "intersection_candidate_violation_count", "transform_violation_count"]:
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
    fig, axes = plt.subplots(2, 2, figsize=(16.0, 11.5), constrained_layout=True)
    historical = summary["historical_grid_totals"]
    divisions = [item["divisions"] for item in historical] + [8]
    medians = [item["median_intersection_to_ratio_width_ratio"] for item in historical] + [summary["totals"]["median_grid8_to_stage56_width_ratio"]]
    axes[0, 0].plot(divisions, medians, marker="o", color="#316c9b")
    axes[0, 0].axhline(1, color="#555555", linestyle="--", linewidth=1)
    axes[0, 0].set_xticks(divisions)
    axes[0, 0].set_ylabel("Intersection / stage-56 width")
    axes[0, 0].set_title("A. Refinement sequence, not asymptotic convergence")
    axes[0, 0].grid(alpha=0.2)

    folds = summary["folds"][:4]
    additional = [fold["grid8"]["additional_tightened_count"] for fold in folds]
    plateau = [fold["grid8"]["plateau_count"] for fold in folds]
    axes[0, 1].bar([fold["fold"] for fold in folds], additional, color="#316c9b", label="additional tightening")
    axes[0, 1].bar([fold["fold"] for fold in folds], plateau, bottom=additional, color="#999999", label="plateau")
    axes[0, 1].set_xticks(range(1, 6))
    axes[0, 1].set_ylabel("Available x count")
    axes[0, 1].set_title("B. Grid-8 versus grid-4 outcomes")
    axes[0, 1].legend(frameon=False, fontsize=8)
    axes[0, 1].grid(axis="y", alpha=0.2)

    feasible = [fold["grid8"]["feasible_vertex_witness_count"] for fold in folds]
    outer = [fold["grid8"]["outer_vertex_witness_count"] for fold in folds]
    axes[1, 0].bar([fold["fold"] for fold in folds], feasible, color="#4f7b5b", label="feasible candidates")
    axes[1, 0].bar([fold["fold"] for fold in folds], outer, bottom=feasible, color="#b44b4b", label="outer-cover witnesses")
    axes[1, 0].set_xticks(range(1, 6))
    axes[1, 0].set_ylabel("Vertex witnesses")
    axes[1, 0].set_title("C. Outer vertices are not feasible extrema")
    axes[1, 0].legend(frameon=False, fontsize=8)
    axes[1, 0].grid(axis="y", alpha=0.2)

    available = [len(fold["points"]) if fold["prediction_envelope_available"] else 0 for fold in summary["folds"]]
    unavailable = [fold["unavailable_point_count"] for fold in summary["folds"]]
    axes[1, 1].bar(range(1, 6), available, color="#316c9b", label="available")
    axes[1, 1].bar(range(1, 6), unavailable, bottom=available, color="#b44b4b", label="unavailable")
    axes[1, 1].set_xticks(range(1, 6))
    axes[1, 1].set_ylabel("Held-out observations")
    axes[1, 1].set_title("D. Fold 5 receives no grid-8 bounds")
    axes[1, 1].legend(frameon=False, fontsize=8)
    axes[1, 1].grid(axis="y", alpha=0.2)

    totals = summary["totals"]
    fig.suptitle(f"Grid-8 diagnostics: {totals['grid8_partition_cell_count']} cells, {totals['grid8_additional_tightened_count']} additional tightenings, {totals['grid8_plateau_count']} plateaus", fontsize=15, y=1.045)
    fig.text(0.5, 1.012, "Incremental evidence only; no global convergence, exact optimum or fold-5 finite-bound claim.", ha="center", fontsize=9, color="#555555")
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
            errors.append("Missing whitened-grid convergence output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored whitened-grid convergence output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid whitened-grid convergence figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "grid8_cells": summary["totals"]["grid8_partition_cell_count"],
        "evaluated_cells": summary["totals"]["native_cell_evaluation_count"],
        "unresolved_cells": summary["totals"]["unresolved_cell_count"],
        "additional_tightened": summary["totals"]["grid8_additional_tightened_count"],
        "plateau": summary["totals"]["grid8_plateau_count"],
        "median_grid8_grid4_ratio": summary["totals"]["median_grid8_to_grid4_width_ratio"],
        "max_incremental_reduction": summary["totals"]["max_grid8_width_reduction_vs_grid4"],
        "vertex_evaluations": summary["totals"]["grid8_vertex_evaluation_count"],
        "feasible_vertices": summary["totals"]["feasible_vertex_witness_count"],
        "outer_vertices": summary["totals"]["outer_vertex_witness_count"],
        "unavailable": summary["totals"]["unavailable_point_count"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
