"""Validate and receipt the Roszman1 whitened-cover grid deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_roszman1_whitened_cover_grid import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = ROOT / "validation/roszman1-whitened-cover-grid-protocol-amendment-01.json"
SUMMARY = ROOT / "validation/roszman1-whitened-cover-grid.json"
REPORT = ROOT / "docs/ROSZMAN1_WHITENED_COVER_GRID_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Roszman1协方差白化覆盖_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-roszman1-whitened-cover-grid-word.json"
OUTPUT = ROOT / "validation/roszman1-whitened-cover-grid-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    for key, value in protocol["expected_structure"].items():
        if totals.get(key) != value:
            errors.append(f"Whitened-cover total mismatch: {key}")
    expected_grids = [
        (1, 20, 0, 20, 1.0, 0.0),
        (2, 320, 17, 3, 0.9725019816013325, 0.03030886019159007),
        (4, 5120, 20, 0, 0.820642571296398, 0.09000651529949602),
    ]
    for grid, expected in zip(summary["grid_totals"], expected_grids):
        divisions, cells, tightened, unchanged, median_ratio, max_reduction = expected
        if grid["divisions"] != divisions or grid["partition_cell_count"] != cells or grid["evaluated_cell_count"] != cells or grid["outside_cell_count"] != 0 or grid["unresolved_cell_count"] != 0 or grid["unbounded_grid_count"] != 0 or grid["intersection_tightened_count"] != tightened or grid["intersection_unchanged_count"] != unchanged or not math.isclose(grid["median_intersection_to_ratio_width_ratio"], median_ratio, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(grid["max_intersection_width_reduction"], max_reduction, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Whitened grid inventory changed: {divisions}")
    if totals["bounded_grid_count"] != 60 or totals["unbounded_grid_count"] != 0 or totals["primary_intersection_tightened_count"] != 20 or totals["primary_intersection_unchanged_count"] != 0:
        errors.append("Bounded-grid or primary tightening inventory changed")
    for key, value in {"min_primary_intersection_to_ratio_width_ratio": 0.6017404632164725, "median_primary_intersection_to_ratio_width_ratio": 0.820642571296398, "max_primary_intersection_to_ratio_width_ratio": 0.9868322264831045, "max_primary_intersection_width_reduction": 0.09000651529949602, "median_primary_intersection_width_reduction": 0.03675877579167666}.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Primary whitened comparison changed: {key}")
    largest = totals["largest_primary_intersection_tightening"]
    if largest["fold"] != 1 or largest["x"] != -3373.14 or largest["divisions"] != 4 or not math.isclose(largest["intersection_to_ratio_width_ratio"], 0.6018748712046076, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(largest["intersection_width_reduction"], 0.09000651529949602, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Largest whitened tightening case changed")
    for fold in summary["folds"][:4]:
        for envelope in fold["envelopes"]:
            for grid in envelope["grids"]:
                if len(grid["cells"]) != grid["divisions"] ** 4 or grid["evaluated_cell_count"] + grid["outside_cell_count"] + grid["unresolved_cell_count"] != len(grid["cells"]) or not math.isclose(grid["outside_boundary_tolerance"], 1.7e-11, rel_tol=1.0e-12, abs_tol=1.0e-24) or grid["cholesky_reconstruction_max_error"] > 1.0e-30:
                    errors.append(f"Whitened cell accounting changed: fold {fold['fold']} x={envelope['x']} grid={grid['divisions']}")
    candidates = [candidate for fold in summary["folds"][:4] for envelope in fold["envelopes"] for candidate in envelope["candidate_evaluations"]]
    if len(candidates) != 200 or any(not candidate["transform_valid"] or not candidate["feasible"] or candidate["whitened_norm"] > 4 + 1.0e-9 or candidate["max_scaled_reconstruction_error"] > 1.0e-10 for candidate in candidates):
        errors.append("Candidate whitening or reconstruction witness changed")
    fold5 = summary["folds"][4]
    if fold5["prediction_envelope_available"] or fold5["envelopes"] or fold5["partition_cell_count"] != 0 or fold5["candidate_evaluation_count"] != 0 or len(fold5["points"]) != 5 or any(point["residual_upper_bound"] is not None for point in fold5["points"]):
        errors.append("Fold-5 finite-bound or cell prohibition changed")
    if not summary["ratio_receipt_verified"] or summary["analysis_scope"]["outside_boundary_amendment"] != "01" or summary["analysis_scope"]["outside_boundary_tolerance_relative"] != 1.0e-12:
        errors.append("Source receipt or boundary amendment scope changed")
    for key, value in summary["decision"].items():
        if value is not False:
            errors.append(f"Decision scope changed: {key}")
    for path in [PROTOCOL, AMENDMENT, SUMMARY, REPORT, FIGURE, WORD, WORD_MANIFEST]:
        if not path.is_file():
            errors.append(f"Missing deliverable: {path.relative_to(ROOT)}")
    if errors:
        raise ValueError(errors)
    manifest = json.loads(WORD_MANIFEST.read_text(encoding="utf-8"))
    if manifest["sha256"] != sha256(WORD) or manifest["bytes"] != WORD.stat().st_size:
        raise ValueError("Whitened-cover Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": totals["fold_count"],
        "heldOutPointCount": totals["held_out_point_count"],
        "availablePointCount": totals["available_point_count"],
        "unavailablePointCount": totals["unavailable_point_count"],
        "unavailableFoldIds": totals["unavailable_fold_ids"],
        "gridCoverCount": totals["grid_cover_count"],
        "partitionCellCount": totals["partition_cell_count"],
        "nativeCellEvaluationCount": totals["native_cell_evaluation_count"],
        "outsideCellCount": totals["outside_cell_count"],
        "unresolvedCellCount": totals["unresolved_cell_count"],
        "boundedGridCount": totals["bounded_grid_count"],
        "unboundedGridCount": totals["unbounded_grid_count"],
        "nonemptyIntersectionCount": totals["nonempty_intersection_count"],
        "candidateEvaluationCount": totals["candidate_evaluation_count"],
        "candidateGridContainmentCheckCount": totals["candidate_grid_containment_check_count"],
        "transformWitnessCount": totals["transform_witness_count"],
        "transformViolationCount": totals["transform_violation_count"],
        "gridCandidateViolationCount": totals["grid_candidate_violation_count"],
        "intersectionCandidateViolationCount": totals["intersection_candidate_violation_count"],
        "candidateFeasibilityFailureCount": totals["candidate_feasibility_failure_count"],
        "centerPredictionMismatchCount": totals["center_prediction_mismatch_count"],
        "pointGridConsistencyCheckCount": totals["point_grid_consistency_check_count"],
        "coveredPointCount": totals["covered_point_count"],
        "violationPointCount": totals["violation_point_count"],
        "primaryGrid": summary["primary_grid"],
        "primaryIntersectionTightenedCount": totals["primary_intersection_tightened_count"],
        "primaryIntersectionUnchangedCount": totals["primary_intersection_unchanged_count"],
        "minPrimaryIntersectionToRatioWidthRatio": totals["min_primary_intersection_to_ratio_width_ratio"],
        "medianPrimaryIntersectionToRatioWidthRatio": totals["median_primary_intersection_to_ratio_width_ratio"],
        "maxPrimaryIntersectionToRatioWidthRatio": totals["max_primary_intersection_to_ratio_width_ratio"],
        "maxPrimaryIntersectionWidthReduction": totals["max_primary_intersection_width_reduction"],
        "medianPrimaryIntersectionWidthReduction": totals["median_primary_intersection_width_reduction"],
        "largestPrimaryIntersectionTightening": largest,
        "gridTotals": summary["grid_totals"],
        "ratioReceiptVerified": True,
        "sourceProjectionMismatchCount": 0,
        "outsideBoundaryAmendment": "01",
        "outsideBoundaryToleranceRelative": 1.0e-12,
        "protocolSha256": sha256(PROTOCOL),
        "protocolAmendmentSha256": sha256(AMENDMENT),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_roszman1_whitened_cover_grid.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "fold5GivenFiniteBound": False,
        "exactGlobalOptimumClaimed": False,
        "candidateChecksReplaceCoverProof": False,
        "visualQaClaimed": False,
        "scientificTruthClaimed": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    receipt = build_receipt()
    if args.check:
        if not OUTPUT.exists() or json.loads(OUTPUT.read_text(encoding="utf-8")) != receipt:
            raise ValueError("Whitened-cover receipt is stale")
        print("OK: whitened-cover receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
