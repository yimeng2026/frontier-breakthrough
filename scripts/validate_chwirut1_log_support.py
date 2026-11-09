"""Validate and receipt the Chwirut1 log-support deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_chwirut1_log_support import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/chwirut1-log-support-intersection.json"
REPORT = ROOT / "docs/CHWIRUT1_LOG_SUPPORT_INTERSECTION_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Chwirut1对数支撑交集_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-chwirut1-log-support-word.json"
OUTPUT = ROOT / "validation/chwirut1-log-support-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "held_out_point_count": 214,
        "unique_distance_count": 22,
        "log_alternative_bound_count": 22,
        "intersection_bound_count": 22,
        "candidate_direction_count": 30,
        "candidate_evaluation_count": 132,
        "alternative_tighter_count": 22,
        "alternative_wider_count": 0,
        "alternative_equal_count": 0,
        "intersection_tightened_count": 22,
        "intersection_unchanged_count": 0,
        "intersection_bound_changed_count": 22,
        "nonempty_intersection_count": 22,
        "alternative_candidate_violation_count": 0,
        "intersection_candidate_violation_count": 0,
        "independent_candidate_violation_count": 0,
        "candidate_feasibility_failure_count": 0,
        "center_prediction_mismatch_count": 0,
        "covered_point_count": 214,
        "violation_point_count": 0,
        "min_alternative_to_independent_width_ratio": 0.18339974265720144,
        "median_alternative_to_independent_width_ratio": 0.25654045819729265,
        "max_alternative_to_independent_width_ratio": 0.9848648012815463,
        "min_intersection_to_independent_width_ratio": 0.18339974265720144,
        "median_intersection_to_independent_width_ratio": 0.25654045819729265,
        "max_intersection_to_independent_width_ratio": 0.9848648012815463,
        "max_intersection_width_reduction": 20.935447900396312,
        "median_intersection_width_reduction": 10.731072587476168,
        "refit_count": 0,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Chwirut1 log-support total mismatch: {key}")
    if [fold["alternative_tighter_count"] for fold in summary["folds"]] != [5, 5, 4, 4, 4] or [fold["intersection_tightened_count"] for fold in summary["folds"]] != [5, 5, 4, 4, 4]:
        errors.append("Fold-specific log-support tightening counts changed")
    if totals["tangent_winner_counts"] != {"d_min": 7, "d_center": 7, "d_max": 8}:
        errors.append("Tangent-winner counts changed")
    largest = totals["largest_intersection_tightening"]
    if largest["x"] != 1.5 or largest["tangent_winner"] != "d_max" or not math.isclose(largest["intersection_to_independent_width_ratio"], 0.2130823595991901, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Largest log-support tightening case changed")
    if not summary["independent_receipt_verified"]:
        errors.append("Independent baseline receipt verification changed")
    related = summary["related_prior_dataset"]
    if related["name"] != "Chwirut2" or not related["same_study"] or not related["same_native_model_family"] or related["independent_model_family_or_laboratory_replication"]:
        errors.append("Related-study scope changed")
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
        raise ValueError("Chwirut1 log-support Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": 5,
        "heldOutPointCount": 214,
        "uniqueDistanceCount": 22,
        "logAlternativeBoundCount": 22,
        "intersectionBoundCount": 22,
        "candidateDirectionCount": 30,
        "candidateEvaluationCount": 132,
        "alternativeTighterCount": 22,
        "alternativeWiderCount": 0,
        "intersectionTightenedCount": 22,
        "intersectionUnchangedCount": 0,
        "nonemptyIntersectionCount": 22,
        "alternativeCandidateViolationCount": 0,
        "intersectionCandidateViolationCount": 0,
        "independentCandidateViolationCount": 0,
        "centerPredictionMismatchCount": 0,
        "coveredPointCount": 214,
        "violationPointCount": 0,
        "medianIntersectionToIndependentWidthRatio": totals["median_intersection_to_independent_width_ratio"],
        "maxIntersectionWidthReduction": totals["max_intersection_width_reduction"],
        "tangentWinnerCounts": totals["tangent_winner_counts"],
        "largestIntersectionTightening": largest,
        "independentReceiptVerified": True,
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_chwirut1_log_support.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "logAlternativeIsGlobalOptimum": False,
        "intersectionIsGlobalOptimum": False,
        "candidateChecksReplaceLogProof": False,
        "independentModelFamilyReplicationClaimed": False,
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
            raise ValueError("Chwirut1 log-support receipt is stale")
        print("OK: Chwirut1 log-support receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
