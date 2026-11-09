"""Validate and receipt the ENSO full-ellipsoid Lipschitz deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_enso_full_ellipsoid_lipschitz import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/enso-full-ellipsoid-lipschitz-intersection.json"
REPORT = ROOT / "docs/ENSO_FULL_ELLIPSOID_LIPSCHITZ_INTERSECTION_2026-11-09.md"
WORD = ROOT / "papers/前沿共生ENSO全椭球Lipschitz交集_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-enso-full-ellipsoid-lipschitz-word.json"
OUTPUT = ROOT / "validation/enso-full-ellipsoid-lipschitz-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "held_out_point_count": 168,
        "alternative_bound_count": 168,
        "intersection_bound_count": 168,
        "candidate_evaluation_count": 672,
        "alternative_tighter_count": 13,
        "alternative_wider_count": 155,
        "alternative_equal_count": 0,
        "intersection_tightened_count": 13,
        "intersection_unchanged_count": 155,
        "intersection_bound_changed_count": 13,
        "nonempty_intersection_count": 168,
        "alternative_candidate_violation_count": 0,
        "intersection_candidate_violation_count": 0,
        "independent_candidate_violation_count": 0,
        "candidate_feasibility_failure_count": 0,
        "center_prediction_mismatch_count": 0,
        "min_alternative_to_independent_width_ratio": 0.509592261709032,
        "median_alternative_to_independent_width_ratio": 2.3027937209620504,
        "max_alternative_to_independent_width_ratio": 4.223063026835401,
        "min_intersection_to_independent_width_ratio": 0.509592261709032,
        "median_intersection_to_independent_width_ratio": 1.0,
        "max_intersection_to_independent_width_ratio": 1.0,
        "max_intersection_width_reduction": 8.086192176366756,
        "median_intersection_width_reduction": 0.0,
        "max_alternative_remainder_support": 21.020182747647624,
        "refit_count": 0,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Full-ellipsoid Lipschitz total mismatch: {key}")
    if [fold["alternative_tighter_count"] for fold in summary["folds"]] != [13, 0, 0, 0, 0] or [fold["alternative_wider_count"] for fold in summary["folds"]] != [21, 34, 34, 33, 33] or [fold["intersection_tightened_count"] for fold in summary["folds"]] != [13, 0, 0, 0, 0]:
        errors.append("Fold-specific alternative or intersection counts changed")
    largest = totals["largest_intersection_tightening"]
    if largest["x"] != 4.0 or not math.isclose(largest["intersection_to_independent_width_ratio"], 0.5359035647336762, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(largest["intersection_width_reduction"], 8.086192176366756, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Largest intersection-tightening case changed")
    if not summary["independent_receipt_verified"] or not summary["slice_receipt_verified"]:
        errors.append("Independent or slice receipt verification changed")
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
        raise ValueError("Full-ellipsoid Lipschitz Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": 5,
        "alternativeBoundCount": 168,
        "intersectionBoundCount": 168,
        "candidateEvaluationCount": 672,
        "alternativeTighterCount": 13,
        "alternativeWiderCount": 155,
        "intersectionTightenedCount": 13,
        "intersectionUnchangedCount": 155,
        "nonemptyIntersectionCount": 168,
        "alternativeCandidateViolationCount": 0,
        "intersectionCandidateViolationCount": 0,
        "independentCandidateViolationCount": 0,
        "centerPredictionMismatchCount": 0,
        "medianAlternativeToIndependentWidthRatio": totals["median_alternative_to_independent_width_ratio"],
        "medianIntersectionToIndependentWidthRatio": 1.0,
        "maxIntersectionWidthReduction": totals["max_intersection_width_reduction"],
        "largestIntersectionTightening": largest,
        "independentReceiptVerified": True,
        "sliceReceiptVerified": True,
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_enso_full_ellipsoid_lipschitz.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "intersectionIsGlobalOptimum": False,
        "alternativeAlwaysTighterClaimed": False,
        "candidateChecksReplaceAnalyticProof": False,
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
            raise ValueError("Full-ellipsoid Lipschitz receipt is stale")
        print("OK: full-ellipsoid Lipschitz receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
