"""Validate and receipt the ENSO phase-interval triple-intersection deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_enso_phase_interval_triple import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/enso-phase-interval-triple-intersection.json"
REPORT = ROOT / "docs/ENSO_PHASE_INTERVAL_TRIPLE_INTERSECTION_2026-11-09.md"
WORD = ROOT / "papers/前沿共生ENSO三角区间三重交集_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-enso-phase-interval-triple-word.json"
OUTPUT = ROOT / "validation/enso-phase-interval-triple-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "held_out_point_count": 168,
        "phase_alternative_bound_count": 168,
        "triple_intersection_bound_count": 168,
        "candidate_evaluation_count": 672,
        "phase_tighter_than_independent_count": 29,
        "phase_wider_than_independent_count": 139,
        "phase_equal_to_independent_count": 0,
        "phase_tighter_than_lipschitz_count": 29,
        "phase_wider_than_lipschitz_count": 139,
        "phase_equal_to_lipschitz_count": 0,
        "triple_tightened_count": 37,
        "triple_unchanged_count": 131,
        "triple_bound_changed_count": 37,
        "nonempty_triple_intersection_count": 168,
        "phase_candidate_violation_count": 0,
        "triple_candidate_violation_count": 0,
        "candidate_feasibility_failure_count": 0,
        "center_prediction_mismatch_count": 0,
        "min_phase_to_independent_width_ratio": 0.4830267389227753,
        "median_phase_to_independent_width_ratio": 1.5386143812259636,
        "max_phase_to_independent_width_ratio": 2.679921227049432,
        "min_phase_to_lipschitz_width_ratio": 0.7474092252857671,
        "median_phase_to_lipschitz_width_ratio": 1.5386143812259636,
        "max_phase_to_lipschitz_width_ratio": 2.679921227049432,
        "min_triple_to_lipschitz_width_ratio": 0.7474092252857671,
        "median_triple_to_lipschitz_width_ratio": 1.0,
        "max_triple_to_lipschitz_width_ratio": 1.0,
        "max_triple_width_reduction": 4.371401855122352,
        "median_triple_width_reduction": 0.0,
        "max_phase_remainder_width": 27.65244413188313,
        "refit_count": 0,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Phase-interval triple total mismatch: {key}")
    if [fold["phase_tighter_than_lipschitz_count"] for fold in summary["folds"]] != [28, 1, 0, 0, 0] or [fold["triple_tightened_count"] for fold in summary["folds"]] != [29, 8, 0, 0, 0]:
        errors.append("Fold-specific phase or triple tightening counts changed")
    largest = totals["largest_triple_tightening"]
    if largest["x"] != 25.0 or not math.isclose(largest["triple_to_lipschitz_width_ratio"], 0.7474092252857671, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(largest["triple_width_reduction"], 4.371401855122352, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Largest triple-tightening case changed")
    if not summary["independent_receipt_verified"] or not summary["slice_receipt_verified"] or not summary["lipschitz_receipt_verified"]:
        errors.append("Independent, slice or Lipschitz receipt verification changed")
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
        raise ValueError("Phase-interval triple Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": 5,
        "phaseAlternativeBoundCount": 168,
        "tripleIntersectionBoundCount": 168,
        "candidateEvaluationCount": 672,
        "phaseTighterThanLipschitzCount": 29,
        "phaseWiderThanLipschitzCount": 139,
        "tripleTightenedCount": 37,
        "tripleUnchangedCount": 131,
        "nonemptyTripleIntersectionCount": 168,
        "phaseCandidateViolationCount": 0,
        "tripleCandidateViolationCount": 0,
        "centerPredictionMismatchCount": 0,
        "medianPhaseToLipschitzWidthRatio": totals["median_phase_to_lipschitz_width_ratio"],
        "medianTripleToLipschitzWidthRatio": 1.0,
        "maxTripleWidthReduction": totals["max_triple_width_reduction"],
        "largestTripleTightening": largest,
        "independentReceiptVerified": True,
        "sliceReceiptVerified": True,
        "lipschitzReceiptVerified": True,
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_enso_phase_interval_triple.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "phaseAlternativeIsGlobalOptimum": False,
        "tripleIntersectionIsGlobalOptimum": False,
        "candidateChecksReplaceIntervalProof": False,
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
            raise ValueError("Phase-interval triple receipt is stale")
        print("OK: phase-interval triple receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
