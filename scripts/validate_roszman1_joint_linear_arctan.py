"""Validate and receipt the Roszman1 joint-linear arctangent deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_roszman1_joint_linear_arctan import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/roszman1-joint-linear-arctan-intersection.json"
REPORT = ROOT / "docs/ROSZMAN1_JOINT_LINEAR_ARCTAN_INTERSECTION_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Roszman1联合线性反正切交集_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-roszman1-joint-linear-arctan-word.json"
OUTPUT = ROOT / "validation/roszman1-joint-linear-arctan-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "held_out_point_count": 25,
        "available_point_count": 20,
        "unavailable_point_count": 5,
        "joint_alternative_bound_count": 20,
        "intersection_bound_count": 20,
        "candidate_direction_count": 32,
        "candidate_evaluation_count": 160,
        "alternative_tighter_count": 20,
        "alternative_wider_count": 0,
        "alternative_equal_count": 0,
        "intersection_tightened_count": 20,
        "intersection_unchanged_count": 0,
        "intersection_bound_changed_count": 20,
        "nonempty_intersection_count": 20,
        "alternative_candidate_violation_count": 0,
        "intersection_candidate_violation_count": 0,
        "independent_candidate_violation_count": 0,
        "candidate_feasibility_failure_count": 0,
        "center_prediction_mismatch_count": 0,
        "covered_point_count": 20,
        "violation_point_count": 0,
        "min_alternative_to_independent_width_ratio": 0.19187755106005555,
        "median_alternative_to_independent_width_ratio": 0.690796188558053,
        "max_alternative_to_independent_width_ratio": 0.8481295584778804,
        "min_intersection_to_independent_width_ratio": 0.19187755106005555,
        "median_intersection_to_independent_width_ratio": 0.690796188558053,
        "max_intersection_to_independent_width_ratio": 0.8481295584778804,
        "max_intersection_width_reduction": 0.7008593776977347,
        "median_intersection_width_reduction": 0.1044602805149246,
        "refit_count": 0,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Roszman1 joint-linear total mismatch: {key}")
    if totals["unavailable_fold_ids"] != [5]:
        errors.append("Unavailable fold set changed")
    if [fold["alternative_tighter_count"] for fold in summary["folds"]] != [5, 5, 5, 5, 0] or [fold["intersection_tightened_count"] for fold in summary["folds"]] != [5, 5, 5, 5, 0]:
        errors.append("Fold-specific joint-linear tightening counts changed")
    largest = totals["largest_intersection_tightening"]
    if largest["x"] != -4868.68 or not math.isclose(largest["intersection_to_independent_width_ratio"], 0.19189941295847002, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(largest["intersection_width_reduction"], 0.7008593776977347, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Largest joint-linear tightening case changed")
    fold5 = summary["folds"][4]
    if fold5["prediction_envelope_available"] or fold5["envelopes"] or fold5["candidate_evaluation_count"] != 0 or any(point["residual_upper_bound"] is not None for point in fold5["points"]):
        errors.append("Fold-5 finite-bound prohibition changed")
    if not summary["independent_receipt_verified"]:
        errors.append("Independent baseline receipt verification changed")
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
        raise ValueError("Roszman1 joint-linear Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": 5,
        "heldOutPointCount": 25,
        "availablePointCount": 20,
        "unavailablePointCount": 5,
        "unavailableFoldIds": [5],
        "jointAlternativeBoundCount": 20,
        "intersectionBoundCount": 20,
        "candidateDirectionCount": 32,
        "candidateEvaluationCount": 160,
        "alternativeTighterCount": 20,
        "alternativeWiderCount": 0,
        "intersectionTightenedCount": 20,
        "intersectionUnchangedCount": 0,
        "nonemptyIntersectionCount": 20,
        "alternativeCandidateViolationCount": 0,
        "intersectionCandidateViolationCount": 0,
        "independentCandidateViolationCount": 0,
        "candidateFeasibilityFailureCount": 0,
        "centerPredictionMismatchCount": 0,
        "coveredPointCount": 20,
        "violationPointCount": 0,
        "medianIntersectionToIndependentWidthRatio": totals["median_intersection_to_independent_width_ratio"],
        "maxIntersectionWidthReduction": totals["max_intersection_width_reduction"],
        "largestIntersectionTightening": largest,
        "independentReceiptVerified": True,
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_roszman1_joint_linear_arctan.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "jointAlternativeIsGlobalOptimum": False,
        "intersectionIsGlobalOptimum": False,
        "fold5GivenFiniteBound": False,
        "candidateChecksReplaceSupportProof": False,
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
            raise ValueError("Roszman1 joint-linear receipt is stale")
        print("OK: Roszman1 joint-linear receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
