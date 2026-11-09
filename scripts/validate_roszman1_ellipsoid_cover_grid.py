"""Validate and receipt the Roszman1 ellipsoid-cover grid deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_roszman1_ellipsoid_cover_grid import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/roszman1-ellipsoid-cover-grid.json"
REPORT = ROOT / "docs/ROSZMAN1_ELLIPSOID_COVER_GRID_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Roszman1椭球覆盖盒细分_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-roszman1-ellipsoid-cover-grid-word.json"
OUTPUT = ROOT / "validation/roszman1-ellipsoid-cover-grid-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    for key, value in protocol["expected_structure"].items():
        if totals.get(key) != value:
            errors.append(f"Ellipsoid-cover total mismatch: {key}")
    expected_grids = [(1, 20), (2, 320), (4, 5120)]
    if [item["divisions"] for item in summary["grid_totals"]] != [1, 2, 4]:
        errors.append("Frozen grid order changed")
    for grid, (divisions, cells) in zip(summary["grid_totals"], expected_grids):
        if grid["cell_evaluation_count"] != cells or grid["intersection_tightened_count"] != 0 or grid["intersection_unchanged_count"] != 20 or grid["min_intersection_to_ratio_width_ratio"] != 1.0 or grid["median_intersection_to_ratio_width_ratio"] != 1.0 or grid["max_intersection_to_ratio_width_ratio"] != 1.0 or grid["max_intersection_width_reduction"] != 0.0 or grid["median_intersection_width_reduction"] != 0.0:
            errors.append(f"Unchanged-grid inventory changed: {divisions}")
    if totals["primary_intersection_tightened_count"] != 0 or totals["primary_intersection_unchanged_count"] != 20 or totals["median_primary_intersection_to_ratio_width_ratio"] != 1.0 or totals["max_primary_intersection_width_reduction"] != 0.0:
        errors.append("Primary negative result changed")
    largest = totals["largest_primary_intersection_tightening"]
    if largest["fold"] != 1 or largest["x"] != -4868.68 or largest["divisions"] != 4 or not math.isclose(largest["baseline_minimum"], 0.15990186031404804, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(largest["baseline_maximum"], 0.32462525917805096, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(largest["union_minimum"], -0.19096232821715253, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(largest["union_maximum"], 0.6763299234363112, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Representative unchanged grid case changed")
    cell_count = 0
    for fold in summary["folds"][:4]:
        for envelope in fold["envelopes"]:
            for grid in envelope["grids"]:
                cells = grid["cells"]
                cell_count += len(cells)
                if len(cells) != grid["divisions"] ** 4 or not grid["cover"]["ellipsoid_subset_of_box"] or grid["union_minimum"] != min(cell["prediction_minimum"] for cell in cells) or grid["union_maximum"] != max(cell["prediction_maximum"] for cell in cells) or any(cell["denominator_maximum"] >= 0 for cell in cells):
                    errors.append(f"Cell coverage or native union mismatch: fold {fold['fold']} x={envelope['x']} grid={grid['divisions']}")
    if cell_count != 5460:
        errors.append("Recomputed native cell count changed")
    fold5 = summary["folds"][4]
    if fold5["prediction_envelope_available"] or fold5["envelopes"] or fold5["cell_evaluation_count"] != 0 or fold5["candidate_evaluation_count"] != 0 or len(fold5["points"]) != 5 or any(point["residual_upper_bound"] is not None for point in fold5["points"]):
        errors.append("Fold-5 finite-bound or cell prohibition changed")
    if not summary["ratio_receipt_verified"]:
        errors.append("Stage-56 receipt verification changed")
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
        raise ValueError("Ellipsoid-cover grid Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": totals["fold_count"],
        "heldOutPointCount": totals["held_out_point_count"],
        "availablePointCount": totals["available_point_count"],
        "unavailablePointCount": totals["unavailable_point_count"],
        "unavailableFoldIds": totals["unavailable_fold_ids"],
        "gridCoverCount": totals["grid_cover_count"],
        "cellEvaluationCount": totals["cell_evaluation_count"],
        "nonemptyIntersectionCount": totals["nonempty_intersection_count"],
        "candidateDirectionCount": totals["candidate_direction_count"],
        "algebraicExtremizerCount": totals["algebraic_extremizer_count"],
        "candidateEvaluationCount": totals["candidate_evaluation_count"],
        "candidateGridContainmentCheckCount": totals["candidate_grid_containment_check_count"],
        "gridCandidateViolationCount": totals["grid_candidate_violation_count"],
        "intersectionCandidateViolationCount": totals["intersection_candidate_violation_count"],
        "coverBoxCandidateViolationCount": totals["cover_box_candidate_violation_count"],
        "candidateFeasibilityFailureCount": totals["candidate_feasibility_failure_count"],
        "centerPredictionMismatchCount": totals["center_prediction_mismatch_count"],
        "pointGridConsistencyCheckCount": totals["point_grid_consistency_check_count"],
        "coveredPointCount": totals["covered_point_count"],
        "violationPointCount": totals["violation_point_count"],
        "primaryGrid": summary["primary_grid"],
        "primaryIntersectionTightenedCount": totals["primary_intersection_tightened_count"],
        "primaryIntersectionUnchangedCount": totals["primary_intersection_unchanged_count"],
        "intersectionTightenedCount": sum(item["intersection_tightened_count"] for item in summary["grid_totals"]),
        "intersectionUnchangedCount": sum(item["intersection_unchanged_count"] for item in summary["grid_totals"]),
        "medianPrimaryIntersectionToRatioWidthRatio": totals["median_primary_intersection_to_ratio_width_ratio"],
        "largestPrimaryIntersectionTightening": largest,
        "gridTotals": summary["grid_totals"],
        "ratioReceiptVerified": True,
        "sourceProjectionMismatchCount": 0,
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_roszman1_ellipsoid_cover_grid.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "fold5GivenFiniteBound": False,
        "exactGlobalOptimumClaimed": False,
        "gridImprovementClaimed": False,
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
            raise ValueError("Ellipsoid-cover grid receipt is stale")
        print("OK: ellipsoid-cover grid receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
