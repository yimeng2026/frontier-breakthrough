"""Conservative native Roszman1 bounds from full ellipsoid-covering grids."""

import argparse
import itertools
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
PROTOCOL = ROOT / "validation/roszman1-ellipsoid-cover-grid-protocol.json"
OUT = ROOT / "validation/roszman1-ellipsoid-cover-grid.json"
FIGURE = ROOT / "papers/64_Roszman1椭球覆盖盒细分/fig64_roszman1_ellipsoid_cover_grid.png"
PARAMETER_NAMES = ["b1", "b2", "b3", "b4"]


def coordinate_cover(parameters, covariance, radius):
    lower = []
    upper = []
    supports = []
    for index, name in enumerate(PARAMETER_NAMES):
        vector = [int(index == column) for column in range(4)]
        support = support_value(covariance, vector, radius)
        center = mp.mpf(str(parameters[name]))
        lower.append(outward(center - support, lower=True))
        upper.append(outward(center + support, lower=False))
        supports.append(float(support))
    return {"lower": lower, "upper": upper, "coordinate_supports": supports, "ellipsoid_subset_of_box": True}


def native_box_interval(lower, upper, x):
    """Natural interval for the original native model on one coordinate box."""
    if len(lower) != 4 or len(upper) != 4 or any(a > b for a, b in zip(lower, upper)):
        raise ValueError("Coordinate cell must be ordered")
    x = mp.mpf(str(x))
    b1 = [mp.mpf(str(lower[0])), mp.mpf(str(upper[0]))]
    b2 = [mp.mpf(str(lower[1])), mp.mpf(str(upper[1]))]
    b3 = [mp.mpf(str(lower[2])), mp.mpf(str(upper[2]))]
    b4 = [mp.mpf(str(lower[3])), mp.mpf(str(upper[3]))]
    denominator = [x - b4[1], x - b4[0]]
    if denominator[1] >= 0:
        raise ValueError("Native cell requires a certified negative denominator with nonzero sign")
    linear = [a - b * x for a in b1 for b in b2]
    ratio = [a / d for a in b3 for d in denominator]
    ratio_minimum = min(ratio)
    ratio_maximum = max(ratio)
    atan_minimum = mp.atan(ratio_minimum)
    atan_maximum = mp.atan(ratio_maximum)
    prediction_minimum = outward(min(linear) - atan_maximum / mp.pi, lower=True)
    prediction_maximum = outward(max(linear) - atan_minimum / mp.pi, lower=False)
    return {
        "linear_minimum": float(min(linear)),
        "linear_maximum": float(max(linear)),
        "denominator_minimum": float(denominator[0]),
        "denominator_maximum": float(denominator[1]),
        "ratio_minimum": float(ratio_minimum),
        "ratio_maximum": float(ratio_maximum),
        "prediction_minimum": prediction_minimum,
        "prediction_maximum": prediction_maximum,
    }


def grid_bounds(parameters, covariance, radius, x, divisions):
    if divisions not in [1, 2, 4]:
        raise ValueError("Grid divisions are frozen to 1, 2 or 4")
    cover = coordinate_cover(parameters, covariance, radius)
    cells = []
    for indices in itertools.product(range(divisions), repeat=4):
        lower = []
        upper = []
        for axis, index in enumerate(indices):
            left = mp.mpf(str(cover["lower"][axis]))
            right = mp.mpf(str(cover["upper"][axis]))
            cell_lower = left + index * (right - left) / divisions
            cell_upper = left + (index + 1) * (right - left) / divisions
            lower.append(float(cell_lower))
            upper.append(float(cell_upper))
        interval = native_box_interval(lower, upper, x)
        cells.append({"indices": list(indices), "lower": lower, "upper": upper, **interval})
    return {
        "divisions": divisions,
        "cover": cover,
        "cells": cells,
        "cell_evaluation_count": len(cells),
        "union_minimum": min(cell["prediction_minimum"] for cell in cells),
        "union_maximum": max(cell["prediction_maximum"] for cell in cells),
    }


def native_center(parameters, x):
    x_mp = mp.mpf(str(x))
    value = mp.mpf(str(parameters["b1"])) - mp.mpf(str(parameters["b2"])) * x_mp - mp.atan(mp.mpf(str(parameters["b3"])) / (x_mp - mp.mpf(str(parameters["b4"])))) / mp.pi
    center = float(value)
    if not math.isclose(center, float(native_model(float(x), *[parameters[name] for name in PARAMETER_NAMES])), rel_tol=1.0e-12, abs_tol=1.0e-12):
        raise ValueError("Center prediction differs from the frozen native model")
    return center


def evaluate_candidate(candidate, kind, x, cover, grids):
    exact = candidate["exact_parameters"]
    values = [float(exact[name]) for name in PARAMETER_NAMES]
    denominator = float(mp.mpf(str(x)) - mp.mpf(str(exact["b4"])))
    prediction = float(native_model(float(x), *values))
    cover_inside = all(lower <= value <= upper for lower, value, upper in zip(cover["lower"], values, cover["upper"]))
    feasible = candidate["feasible"] and denominator < 0 and cover_inside and math.isfinite(prediction) and math.isclose(candidate["ellipsoid_quadratic"], 16.0, rel_tol=1.0e-10, abs_tol=1.0e-10)
    checks = []
    for grid in grids:
        checks.append({
            "divisions": grid["divisions"],
            "inside_union": grid["union_minimum"] <= prediction <= grid["union_maximum"],
            "inside_intersection": grid["intersection_minimum"] <= prediction <= grid["intersection_maximum"],
        })
    return {
        "kind": kind,
        "direction": candidate["direction"],
        "prediction": prediction,
        "ellipsoid_quadratic": candidate["ellipsoid_quadratic"],
        "denominator": denominator,
        "feasible": feasible,
        "cover_box_inside": cover_inside,
        "grid_checks": checks,
    }


def median(values):
    return float(np.median(values)) if values else None


def intersection_record(grid, baseline, fold, x):
    lower = max(grid["union_minimum"], baseline["intersection_minimum"])
    upper = min(grid["union_maximum"], baseline["intersection_maximum"])
    width = outward(upper - lower, lower=False)
    ratio = width / baseline["intersection_width"]
    return {
        **grid,
        "baseline_minimum": baseline["intersection_minimum"],
        "baseline_maximum": baseline["intersection_maximum"],
        "intersection_minimum": lower,
        "intersection_maximum": upper,
        "intersection_width": width,
        "intersection_to_ratio_width_ratio": ratio,
        "intersection_width_reduction": baseline["intersection_width"] - width,
        "intersection_tightened": width < baseline["intersection_width"],
        "intersection_nonempty": lower <= upper,
        "largest_intersection_tightening": {
            "fold": fold,
            "x": float(x),
            "divisions": grid["divisions"],
            "intersection_to_ratio_width_ratio": ratio,
            "intersection_width_reduction": baseline["intersection_width"] - width,
            "baseline_minimum": baseline["intersection_minimum"],
            "baseline_maximum": baseline["intersection_maximum"],
            "union_minimum": grid["union_minimum"],
            "union_maximum": grid["union_maximum"],
            "intersection_minimum": lower,
            "intersection_maximum": upper,
        },
    }


def primary_summary(fold):
    records = [envelope["grids"][2] for envelope in fold["envelopes"]]
    if not records:
        return None
    return {
        "divisions": 4,
        "cell_evaluation_count": sum(record["cell_evaluation_count"] for record in records),
        "intersection_tightened_count": sum(record["intersection_tightened"] for record in records),
        "intersection_unchanged_count": sum(not record["intersection_tightened"] for record in records),
        "min_intersection_to_ratio_width_ratio": min(record["intersection_to_ratio_width_ratio"] for record in records),
        "median_intersection_to_ratio_width_ratio": median([record["intersection_to_ratio_width_ratio"] for record in records]),
        "max_intersection_to_ratio_width_ratio": max(record["intersection_to_ratio_width_ratio"] for record in records),
        "largest_intersection_tightening": max((record["largest_intersection_tightening"] for record in records), key=lambda item: item["intersection_width_reduction"]),
    }


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_roszman1_ellipsoid_cover_grid":
        raise ValueError("Roszman1 ellipsoid-cover grid protocol is not frozen")
    for key, info in protocol["inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {key}")
    source = json.loads((ROOT / protocol["inputs"]["native_identifiability"]["file"]).read_text(encoding="utf-8"))
    ratio = json.loads((ROOT / protocol["inputs"]["ratio_bounds"]["file"]).read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / protocol["inputs"]["ratio_receipt"]["file"]).read_text(encoding="utf-8"))
    ratio_hash = sha256(ROOT / protocol["inputs"]["ratio_bounds"]["file"])
    ratio_receipt_verified = receipt["status"] == "passed" and receipt["summarySha256"] == ratio_hash
    if not ratio_receipt_verified:
        raise ValueError("Stage-56 ratio receipt mismatch")
    radius = 4.0
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
                "candidate_directions": [], "envelopes": [], "points": points, "grid_cover_count": 0, "cell_evaluation_count": 0, "nonempty_intersection_count": 0,
                "candidate_evaluation_count": 0, "candidate_grid_containment_check_count": 0, "algebraic_extremizer_count": 0,
                "grid_candidate_violation_count": 0, "intersection_candidate_violation_count": 0, "cover_box_candidate_violation_count": 0,
                "candidate_feasibility_failure_count": 0, "center_prediction_mismatch_count": 0, "point_grid_consistency_check_count": 0,
                "covered_point_count": 0, "violation_point_count": 0, "unavailable_point_count": len(points), "primary": None,
            })
            continue
        parameters = source_fold["native_parameters"]
        covariance = source_fold["training_jacobian"]["parameter_covariance_matrix"]
        candidates = ratio_fold["candidate_directions"]
        envelopes = []
        counters = {key: 0 for key in ["nonempty_intersection_count", "grid_candidate_violation_count", "intersection_candidate_violation_count", "cover_box_candidate_violation_count", "candidate_feasibility_failure_count", "center_prediction_mismatch_count"]}
        for baseline in ratio_fold["envelopes"]:
            x = float(baseline["x"])
            grids = [intersection_record(grid_bounds(parameters, covariance, radius, x, divisions), baseline, source_fold["fold"], x) for divisions in [1, 2, 4]]
            center = native_center(parameters, x)
            for grid in grids:
                counters["nonempty_intersection_count"] += grid["intersection_nonempty"]
                counters["center_prediction_mismatch_count"] += not (grid["union_minimum"] <= center <= grid["union_maximum"] and grid["intersection_minimum"] <= center <= grid["intersection_maximum"])
            evaluations = []
            for candidate in candidates:
                evaluations.append(evaluate_candidate(candidate, "full_covariance_support", x, grids[0]["cover"], grids))
            for candidate in baseline["algebraic_extremizers"]:
                evaluations.append(evaluate_candidate(candidate, "algebraic_extremizer", x, grids[0]["cover"], grids))
            for candidate in evaluations:
                counters["candidate_feasibility_failure_count"] += not candidate["feasible"]
                counters["cover_box_candidate_violation_count"] += not candidate["cover_box_inside"]
                for check in candidate["grid_checks"]:
                    counters["grid_candidate_violation_count"] += not check["inside_union"]
                    counters["intersection_candidate_violation_count"] += not check["inside_intersection"]
            envelopes.append({
                "x": x,
                "center_prediction": center,
                "ratio_minimum": baseline["intersection_minimum"],
                "ratio_maximum": baseline["intersection_maximum"],
                "ratio_width": baseline["intersection_width"],
                "grids": grids,
                "candidate_evaluations": evaluations,
            })
        if any(value for key, value in counters.items() if key != "nonempty_intersection_count") or counters["nonempty_intersection_count"] != len(envelopes) * 3:
            raise ValueError(f"Ellipsoid-cover grid consistency failure: fold {source_fold['fold']}: {counters}")
        points = []
        for old in ratio_fold["points"]:
            envelope = next(item for item in envelopes if item["x"] == old["x"])
            checks = []
            for grid in envelope["grids"]:
                lower, upper = grid["intersection_minimum"], grid["intersection_maximum"]
                residual = outward(max(abs(old["observed_y"] - lower), abs(old["observed_y"] - upper)), lower=False)
                checks.append({
                    "divisions": grid["divisions"], "residual_upper_bound": residual,
                    "covered": old["actual_absolute_residual"] <= residual,
                    "center_prediction_inside": lower <= old["native_prediction"] <= upper,
                })
            primary = envelope["grids"][2]
            lower, upper = primary["intersection_minimum"], primary["intersection_maximum"]
            residual = outward(max(abs(old["observed_y"] - lower), abs(old["observed_y"] - upper)), lower=False)
            points.append({
                **old, "intersection_minimum": lower, "intersection_maximum": upper, "residual_upper_bound": residual,
                "covered": old["actual_absolute_residual"] <= residual,
                "center_prediction_inside": lower <= old["native_prediction"] <= upper,
                "grid_checks": checks,
            })
        if any(not point["covered"] or not point["center_prediction_inside"] or any(not check["covered"] or not check["center_prediction_inside"] for check in point["grid_checks"]) for point in points):
            raise ValueError("Point/grid arithmetic consistency failed")
        fold = {
            "fold": source_fold["fold"], "native_test_rmse": source_fold["test_metrics"]["rmse"], "prediction_envelope_available": True, "unavailable_reason": None,
            "candidate_directions": candidates, "envelopes": envelopes, "points": points,
            "grid_cover_count": sum(len(envelope["grids"]) for envelope in envelopes),
            "cell_evaluation_count": sum(grid["cell_evaluation_count"] for envelope in envelopes for grid in envelope["grids"]),
            **counters,
            "candidate_evaluation_count": sum(len(envelope["candidate_evaluations"]) for envelope in envelopes),
            "candidate_grid_containment_check_count": sum(len(candidate["grid_checks"]) for envelope in envelopes for candidate in envelope["candidate_evaluations"]),
            "algebraic_extremizer_count": sum(len(envelope["candidate_evaluations"]) - len(candidates) for envelope in envelopes),
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
        "cell_evaluation_count": sum(fold["cell_evaluation_count"] for fold in folds),
        "nonempty_intersection_count": sum(fold["nonempty_intersection_count"] for fold in folds),
        "candidate_direction_count": sum(len(fold["candidate_directions"]) for fold in folds),
        "algebraic_extremizer_count": sum(fold["algebraic_extremizer_count"] for fold in folds),
        "candidate_evaluation_count": sum(fold["candidate_evaluation_count"] for fold in folds),
        "candidate_grid_containment_check_count": sum(fold["candidate_grid_containment_check_count"] for fold in folds),
        "grid_candidate_violation_count": sum(fold["grid_candidate_violation_count"] for fold in folds),
        "intersection_candidate_violation_count": sum(fold["intersection_candidate_violation_count"] for fold in folds),
        "cover_box_candidate_violation_count": sum(fold["cover_box_candidate_violation_count"] for fold in folds),
        "candidate_feasibility_failure_count": sum(fold["candidate_feasibility_failure_count"] for fold in folds),
        "center_prediction_mismatch_count": sum(fold["center_prediction_mismatch_count"] for fold in folds),
        "point_grid_consistency_check_count": sum(fold["point_grid_consistency_check_count"] for fold in folds),
        "covered_point_count": sum(fold["covered_point_count"] for fold in folds),
        "violation_point_count": sum(fold["violation_point_count"] for fold in folds),
        "refit_count": 0,
    }
    grid_totals = []
    for divisions in [1, 2, 4]:
        records = [envelope["grids"][[1, 2, 4].index(divisions)] for fold in folds for envelope in fold["envelopes"]]
        largest = max((record["largest_intersection_tightening"] for record in records), key=lambda item: item["intersection_width_reduction"], default=None)
        grid_totals.append({
            "divisions": divisions,
            "grid_count": len(records),
            "cell_evaluation_count": sum(record["cell_evaluation_count"] for record in records),
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
        "status": "computed_roszman1_ellipsoid_cover_grid",
        "protocol_sha256": sha256(protocol_path),
        "native_identifiability_sha256": sha256(ROOT / protocol["inputs"]["native_identifiability"]["file"]),
        "ratio_bounds_sha256": ratio_hash,
        "ratio_receipt_verified": ratio_receipt_verified,
        "primary_grid": 4,
        "analysis_scope": {**protocol["analysis_scope"], "baseline_radius": radius, "high_precision_decimal_digits": 80, "outward_rounding": True, "outward_relative_margin": 1.0e-24, "exact_rational_certificate": False, "probability_region": False, "historical_baseline_replaced": False},
        "known_answer": source.get("known_answer"),
        "folds": folds,
        "grid_totals": grid_totals,
        "totals": totals,
        "exact_global_optimum": None,
        "decision": protocol["decision"],
        "limitations": [
            "Coordinate boxes and grids are outer covers of the ellipsoid, not samples or exact nonlinear prediction images",
            "Grid bounds are conservative for the original native model over the full ellipsoid but are not exact global optima",
            "The primary grid was frozen before seeing results; all wider unions and unchanged intersections are retained",
            "Fold 5 has no certified negative denominator and receives no cells, candidates, grid bounds or finite residual upper bounds",
            "The 200 candidate evaluations and 600 grid checks are witnesses, not a substitute for the cover proof or an independent experiment",
            "High-precision outward-rounded intervals are not exact rational certificates or probability regions",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    actual = [envelope["grids"][2]["intersection_to_ratio_width_ratio"] for fold in summary.get("folds", []) for envelope in fold.get("envelopes", [])]
    required = [envelope["grids"][2]["intersection_to_ratio_width_ratio"] for fold in expected["folds"] for envelope in fold["envelopes"]]
    if actual != required:
        errors.append("Primary intersection-to-stage56 width ratio mismatch")
    for key in ["grid_candidate_violation_count", "intersection_candidate_violation_count", "cover_box_candidate_violation_count"]:
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
    colors = ["#316c9b", "#4f7b5b", "#876a32", "#6a4c93"]
    for fold, color in zip(summary["folds"][:4], colors):
        axes[0, 0].scatter([fold["fold"]] * len(fold["envelopes"]), [envelope["grids"][2]["intersection_to_ratio_width_ratio"] for envelope in fold["envelopes"]], color=color, s=24, alpha=0.75)
    axes[0, 0].axhline(1, color="#555555", linestyle="--", linewidth=1)
    axes[0, 0].set_xticks(range(1, 6))
    axes[0, 0].set_ylabel("Grid-4 intersection / stage-56 width")
    axes[0, 0].set_title("A. Primary intersections never widen")
    axes[0, 0].grid(alpha=0.2)

    grid_totals = summary["grid_totals"]
    axes[0, 1].plot([item["divisions"] for item in grid_totals], [item["median_intersection_to_ratio_width_ratio"] for item in grid_totals], marker="o", color="#316c9b", label="median")
    axes[0, 1].plot([item["divisions"] for item in grid_totals], [item["max_intersection_to_ratio_width_ratio"] for item in grid_totals], marker="s", color="#876a32", label="maximum")
    axes[0, 1].axhline(1, color="#555555", linestyle="--", linewidth=1)
    axes[0, 1].set_xticks([1, 2, 4])
    axes[0, 1].set_ylabel("Intersection / stage-56 width")
    axes[0, 1].set_title("B. All three frozen grids retained")
    axes[0, 1].legend(frameon=False, fontsize=8)
    axes[0, 1].grid(alpha=0.2)

    axes[1, 0].bar([str(item["divisions"]) for item in grid_totals], [item["cell_evaluation_count"] for item in grid_totals], color=["#999999", "#4f7b5b", "#316c9b"])
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_xlabel("Divisions per dimension")
    axes[1, 0].set_ylabel("Native cell evaluations (log)")
    axes[1, 0].set_title("C. Complete partitions, not random samples")
    axes[1, 0].grid(axis="y", which="both", alpha=0.2)

    available = [len(fold["points"]) if fold["prediction_envelope_available"] else 0 for fold in summary["folds"]]
    unavailable = [fold["unavailable_point_count"] for fold in summary["folds"]]
    axes[1, 1].bar(range(1, 6), available, color="#316c9b", label="available")
    axes[1, 1].bar(range(1, 6), unavailable, bottom=available, color="#b44b4b", label="unavailable")
    axes[1, 1].set_xticks(range(1, 6))
    axes[1, 1].set_ylabel("Held-out observations")
    axes[1, 1].set_title("D. Fold 5 remains unavailable")
    axes[1, 1].legend(frameon=False, fontsize=8)
    axes[1, 1].grid(axis="y", alpha=0.2)

    totals = summary["totals"]
    fig.suptitle(f"Roszman1 full ellipsoid-cover grids: {totals['cell_evaluation_count']} cells, {totals['candidate_evaluation_count']} candidates, {totals['candidate_grid_containment_check_count']} grid checks", fontsize=15, y=1.045)
    fig.text(0.5, 1.012, "Conservative original-model cover; no exact global optimum, probability or fold-5 finite-bound claim.", ha="center", fontsize=9, color="#555555")
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
            errors.append("Missing Roszman1 ellipsoid-cover grid output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored Roszman1 ellipsoid-cover grid output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid Roszman1 ellipsoid-cover grid figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "grid_covers": summary["totals"]["grid_cover_count"],
        "cell_evaluations": summary["totals"]["cell_evaluation_count"],
        "candidate_evaluations": summary["totals"]["candidate_evaluation_count"],
        "candidate_grid_checks": summary["totals"]["candidate_grid_containment_check_count"],
        "primary_tightened": summary["totals"]["primary_intersection_tightened_count"],
        "primary_unchanged": summary["totals"]["primary_intersection_unchanged_count"],
        "primary_median_ratio": summary["totals"]["median_primary_intersection_to_ratio_width_ratio"],
        "unavailable": summary["totals"]["unavailable_point_count"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
