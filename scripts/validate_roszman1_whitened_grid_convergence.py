"""Validate and receipt the Roszman1 whitened-grid convergence deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_roszman1_whitened_grid_convergence import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
AMENDMENT01 = ROOT / "validation/roszman1-whitened-grid-convergence-protocol-amendment-01.json"
AMENDMENT02 = ROOT / "validation/roszman1-whitened-grid-convergence-protocol-amendment-02.json"
AMENDMENT03 = ROOT / "validation/roszman1-whitened-grid-convergence-protocol-amendment-03.json"
SUMMARY = ROOT / "validation/roszman1-whitened-grid-convergence.json"
REPORT = ROOT / "docs/ROSZMAN1_WHITENED_GRID_CONVERGENCE_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Roszman1白化网格收敛与共享见证_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-roszman1-whitened-grid-convergence-word.json"
OUTPUT = ROOT / "validation/roszman1-whitened-grid-convergence-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    for key, value in protocol["expected_structure"].items():
        if key == "outside_cell_count":
            continue
        if totals.get(key) != value:
            errors.append(f"Grid-8 total mismatch: {key}")
    if totals["outside_cell_count"] != 30400 or totals["native_cell_evaluation_count"] != 51520 or totals["unresolved_cell_count"] != 0 or totals["grid8_bounded_grid_count"] != 20 or totals["grid8_unbounded_grid_count"] != 0:
        errors.append("Grid-8 outside, evaluated or bounded inventory changed")
    for key, value in {
        "grid8_additional_tightened_count": 20,
        "grid8_plateau_count": 0,
        "grid8_intersection_tightened_count": 20,
        "grid8_intersection_unchanged_count": 0,
        "grid8_witness_cell_count": 40,
        "grid8_vertex_evaluation_count": 640,
        "feasible_vertex_witness_count": 44,
        "outer_vertex_witness_count": 596,
    }.items():
        if totals[key] != value:
            errors.append(f"Grid-8 incremental or witness inventory changed: {key}")
    for key, value in {
        "min_grid8_to_grid4_width_ratio": 0.5689019258394808,
        "median_grid8_to_grid4_width_ratio": 0.5874946735203854,
        "max_grid8_to_grid4_width_ratio": 0.9973128703348878,
        "min_grid8_to_stage56_width_ratio": 0.23782425541084196,
        "median_grid8_to_stage56_width_ratio": 0.2598357981530852,
        "max_grid8_to_stage56_width_ratio": 0.9973128703348878,
        "max_grid8_width_reduction_vs_grid4": 0.04639800457926707,
        "median_grid8_width_reduction_vs_grid4": 0.03936782523607183,
        "max_vertex_interval_gap": 0.02667802751626147,
    }.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Grid-8 comparison changed: {key}")
    largest = totals["largest_grid8_incremental_tightening"]
    if largest["fold"] != 2 or largest["x"] != -1894.65 or not math.isclose(largest["grid8_to_grid4_width_ratio"], 0.5880361478467961, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(largest["grid8_width_reduction_vs_grid4"], 0.04639800457926707, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Largest incremental tightening case changed")
    for fold in summary["folds"][:4]:
        for envelope in fold["envelopes"]:
            grid = envelope["grid8"]
            if "cells" in grid or grid["partition_cell_count"] != 4096 or grid["evaluated_cell_count"] != 2576 or grid["outside_cell_count"] != 1520 or grid["unresolved_cell_count"] != 0 or grid["vertex_evaluation_count"] != 32 or any(witness["vertex_interval_violation_count"] for witness in grid["vertex_witnesses"]):
                errors.append(f"Grid-8 cell or vertex gate changed: fold {fold['fold']} x={envelope['x']}")
    candidates = [candidate for fold in summary["folds"][:4] for envelope in fold["envelopes"] for candidate in envelope["candidate_evaluations"]]
    if len(candidates) != 200 or any(not candidate["transform_valid"] or not candidate["feasible"] or candidate["whitened_norm"] > 4 + 1.0e-9 for candidate in candidates):
        errors.append("Grid-8 candidate transform witness changed")
    fold5 = summary["folds"][4]
    if fold5["prediction_envelope_available"] or fold5["envelopes"] or fold5["grid8_partition_cell_count"] != 0 or fold5["candidate_evaluation_count"] != 0 or len(fold5["points"]) != 5 or any(point["residual_upper_bound"] is not None for point in fold5["points"]):
        errors.append("Fold-5 finite-bound or cell prohibition changed")
    if not summary["whitened_receipt_verified"] or not summary["stage56_receipt_verified"] or summary["analysis_scope"]["outside_count_amendment"] != "03" or summary["analysis_scope"]["original_whitened_proof_validity"] != "invalid_for_conservative_proof" or not summary["analysis_scope"]["corrected_negative_denominator_displacement"]:
        errors.append("Corrected source, stage-56 receipt or outside amendment scope changed")
    for key, value in summary["decision"].items():
        if value is not False:
            errors.append(f"Decision scope changed: {key}")
    for path in [PROTOCOL, AMENDMENT01, AMENDMENT02, AMENDMENT03, SUMMARY, REPORT, FIGURE, WORD, WORD_MANIFEST]:
        if not path.is_file():
            errors.append(f"Missing deliverable: {path.relative_to(ROOT)}")
    if errors:
        raise ValueError(errors)
    manifest = json.loads(WORD_MANIFEST.read_text(encoding="utf-8"))
    if manifest["sha256"] != sha256(WORD) or manifest["bytes"] != WORD.stat().st_size:
        raise ValueError("Grid-8 convergence Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": totals["fold_count"],
        "heldOutPointCount": totals["held_out_point_count"],
        "availablePointCount": totals["available_point_count"],
        "unavailablePointCount": totals["unavailable_point_count"],
        "unavailableFoldIds": totals["unavailable_fold_ids"],
        "grid4ReferenceCount": totals["grid4_reference_count"],
        "grid8CoverCount": totals["grid8_cover_count"],
        "grid8PartitionCellCount": totals["grid8_partition_cell_count"],
        "nativeCellEvaluationCount": totals["native_cell_evaluation_count"],
        "outsideCellCount": totals["outside_cell_count"],
        "unresolvedCellCount": totals["unresolved_cell_count"],
        "grid8BoundedGridCount": totals["grid8_bounded_grid_count"],
        "grid8UnboundedGridCount": totals["grid8_unbounded_grid_count"],
        "nonemptyIntersectionCount": totals["nonempty_intersection_count"],
        "candidateDirectionCount": totals["candidate_direction_count"],
        "algebraicExtremizerCount": totals["algebraic_extremizer_count"],
        "candidateEvaluationCount": totals["candidate_evaluation_count"],
        "candidateGrid8ContainmentCheckCount": totals["candidate_grid8_containment_check_count"],
        "transformWitnessCount": totals["transform_witness_count"],
        "transformViolationCount": totals["transform_violation_count"],
        "grid8CandidateViolationCount": totals["grid8_candidate_violation_count"],
        "intersectionCandidateViolationCount": totals["intersection_candidate_violation_count"],
        "candidateFeasibilityFailureCount": totals["candidate_feasibility_failure_count"],
        "centerPredictionMismatchCount": totals["center_prediction_mismatch_count"],
        "pointGrid8ConsistencyCheckCount": totals["point_grid8_consistency_check_count"],
        "coveredPointCount": totals["covered_point_count"],
        "violationPointCount": totals["violation_point_count"],
        "grid8AdditionalTightenedCount": totals["grid8_additional_tightened_count"],
        "grid8PlateauCount": totals["grid8_plateau_count"],
        "grid8WitnessCellCount": totals["grid8_witness_cell_count"],
        "grid8VertexEvaluationCount": totals["grid8_vertex_evaluation_count"],
        "feasibleVertexWitnessCount": totals["feasible_vertex_witness_count"],
        "outerVertexWitnessCount": totals["outer_vertex_witness_count"],
        "vertexIntervalViolationCount": 0,
        "maxVertexIntervalGap": totals["max_vertex_interval_gap"],
        "minGrid8ToGrid4WidthRatio": totals["min_grid8_to_grid4_width_ratio"],
        "medianGrid8ToGrid4WidthRatio": totals["median_grid8_to_grid4_width_ratio"],
        "maxGrid8ToGrid4WidthRatio": totals["max_grid8_to_grid4_width_ratio"],
        "medianGrid8ToStage56WidthRatio": totals["median_grid8_to_stage56_width_ratio"],
        "maxGrid8WidthReductionVsGrid4": totals["max_grid8_width_reduction_vs_grid4"],
        "medianGrid8WidthReductionVsGrid4": totals["median_grid8_width_reduction_vs_grid4"],
        "largestGrid8IncrementalTightening": largest,
        "historicalGridTotals": summary["historical_grid_totals"],
        "whitenedReceiptVerified": True,
        "stage56ReceiptVerified": True,
        "sourceProjectionMismatchCount": 0,
        "originalProofValidity": "invalid_for_conservative_proof",
        "outsideCountAmendment": "03",
        "protocolSha256": sha256(PROTOCOL),
        "protocolAmendment01Sha256": sha256(AMENDMENT01),
        "protocolAmendment02Sha256": sha256(AMENDMENT02),
        "protocolAmendment03Sha256": sha256(AMENDMENT03),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_roszman1_whitened_grid_convergence.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "grid8CalledGlobalOptimum": False,
        "plateauCalledConvergenceProof": False,
        "outerVerticesCalledFeasible": False,
        "fold5GivenFiniteBound": False,
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
            raise ValueError("Grid-8 convergence receipt is stale")
        print("OK: grid-8 convergence receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
