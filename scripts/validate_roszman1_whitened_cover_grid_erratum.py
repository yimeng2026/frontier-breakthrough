"""Validate and receipt the corrected whitened-cover erratum deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_roszman1_whitened_cover_grid_erratum import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/roszman1-whitened-cover-grid-corrected-01.json"
REPORT = ROOT / "docs/ROSZMAN1_WHITENED_COVER_GRID_ERRATUM_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Roszman1白化覆盖勘误_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-roszman1-whitened-cover-grid-erratum-word.json"
OUTPUT = ROOT / "validation/roszman1-whitened-cover-grid-erratum-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    for key, value in protocol["expected_structure"].items():
        if totals.get(key) != value:
            errors.append(f"Corrected whitened-cover total mismatch: {key}")
    expected_grids = [
        (1, 20, 0, 20, 1.0, 0.0),
        (2, 320, 17, 3, 0.7492639543331618, 0.08237420989575903),
        (4, 5120, 17, 3, 0.4474424821614995, 0.1610034968796093),
    ]
    for grid, expected in zip(summary["grid_totals"], expected_grids):
        divisions, cells, tightened, unchanged, median_ratio, max_reduction = expected
        if grid["divisions"] != divisions or grid["evaluated_cell_count"] != cells or grid["outside_cell_count"] != 0 or grid["unresolved_cell_count"] != 0 or grid["unbounded_grid_count"] != 0 or grid["intersection_tightened_count"] != tightened or grid["intersection_unchanged_count"] != unchanged or not math.isclose(grid["median_intersection_to_ratio_width_ratio"], median_ratio, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(grid["max_intersection_width_reduction"], max_reduction, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Corrected whitened grid inventory changed: {divisions}")
    for key, value in {"min_primary_intersection_to_ratio_width_ratio": 0.4116012169324781, "median_primary_intersection_to_ratio_width_ratio": 0.4474424821614995, "max_primary_intersection_to_ratio_width_ratio": 1.0, "max_primary_intersection_width_reduction": 0.1610034968796093, "median_primary_intersection_width_reduction": 0.11600841592067503}.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Corrected primary comparison changed: {key}")
    if totals["primary_intersection_tightened_count"] != 17 or totals["primary_intersection_unchanged_count"] != 3 or totals["bounded_grid_count"] != 60 or totals["unbounded_grid_count"] != 0:
        errors.append("Corrected primary inventory changed")
    largest = totals["largest_primary_intersection_tightening"]
    if largest["fold"] != 2 or largest["x"] != -1894.65 or largest["divisions"] != 4 or not math.isclose(largest["intersection_to_ratio_width_ratio"], 0.4116012169324781, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(largest["intersection_width_reduction"], 0.1610034968796093, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Largest corrected tightening case changed")
    if totals["vertex_evaluation_count"] != 1920 or totals["vertex_interval_violation_count"] != 0:
        errors.append("Corrected vertex audit inventory changed")
    candidates = [candidate for fold in summary["folds"][:4] for envelope in fold["envelopes"] for candidate in envelope["candidate_evaluations"]]
    if len(candidates) != 200 or any(not candidate["transform_valid"] or not candidate["feasible"] or candidate["whitened_norm"] > 4 + 1.0e-9 for candidate in candidates):
        errors.append("Corrected candidate transform witness changed")
    fold5 = summary["folds"][4]
    if fold5["prediction_envelope_available"] or fold5["envelopes"] or fold5["partition_cell_count"] != 0 or fold5["candidate_evaluation_count"] != 0 or len(fold5["points"]) != 5 or any(point["residual_upper_bound"] is not None for point in fold5["points"]):
        errors.append("Fold-5 finite-bound or cell prohibition changed")
    if summary["original_proof_validity"] != "invalid_for_conservative_proof" or not summary["ratio_receipt_verified"] or not summary["analysis_scope"]["original_results_invalid_for_cover"] or not summary["analysis_scope"]["corrected_negative_denominator_displacement"]:
        errors.append("Erratum validity or corrected sign scope changed")
    for key, value in summary["decision"].items():
        if value is not False:
            errors.append(f"Decision scope changed: {key}")
    for path in [PROTOCOL, SUMMARY, REPORT, FIGURE, WORD, WORD_MANIFEST]:
        if not path.is_file():
            errors.append(f"Missing deliverable: {path.relative_to(ROOT)}")
    if errors:
        raise ValueError(errors)
    manifest = json.loads(WORD_MANIFEST.read_text(encoding="utf-8"))
    if manifest["sha256"] != sha256(WORD) or manifest["bytes"] != WORD.stat().st_size:
        raise ValueError("Corrected whitened-cover Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "originalProofValidity": "invalid_for_conservative_proof",
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
        "vertexEvaluationCount": totals["vertex_evaluation_count"],
        "vertexIntervalViolationCount": totals["vertex_interval_violation_count"],
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
        "originalRunnerSha256": protocol["original_state"]["original_runner_sha256"],
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_roszman1_whitened_cover_grid_erratum.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "originalResultsUsedAsValidCover": False,
        "originalHistoryRewritten": False,
        "fold5GivenFiniteBound": False,
        "exactGlobalOptimumClaimed": False,
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
            raise ValueError("Corrected whitened-cover receipt is stale")
        print("OK: corrected whitened-cover receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
