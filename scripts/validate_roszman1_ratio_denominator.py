"""Validate and receipt the Roszman1 ratio-denominator deliverables."""

import argparse
import json
import math
from decimal import Decimal
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_roszman1_ratio_denominator import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/roszman1-ratio-denominator-intersection.json"
REPORT = ROOT / "docs/ROSZMAN1_RATIO_DENOMINATOR_INTERSECTION_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Roszman1比值分母联合区间_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-roszman1-ratio-denominator-word.json"
OUTPUT = ROOT / "validation/roszman1-ratio-denominator-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    for key, value in protocol["expected_structure"].items():
        if totals.get(key) != value:
            errors.append(f"Ratio-denominator total mismatch: {key}")
    expected_scalars = {
        "min_alternative_to_joint_alternative_width_ratio": 0.9633926606308423,
        "median_alternative_to_joint_alternative_width_ratio": 0.9807825850555489,
        "max_alternative_to_joint_alternative_width_ratio": 0.9897287413772524,
        "min_intersection_to_joint_linear_width_ratio": 0.9633926606308423,
        "median_intersection_to_joint_linear_width_ratio": 0.9807825850555489,
        "max_intersection_to_joint_linear_width_ratio": 0.9897287413772524,
        "max_intersection_width_reduction": 0.008362313007168387,
        "median_intersection_width_reduction": 0.0051117231924135,
        "max_ratio_interval_width_reduction": 0.07692375150746189,
        "median_ratio_interval_width_reduction": 0.026730900411437608,
    }
    for key, value in expected_scalars.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Ratio-denominator comparison changed: {key}")
    largest = totals["largest_intersection_tightening"]
    if largest["x"] != -1208.68 or not math.isclose(largest["intersection_width_reduction"], 0.008362313007168387, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(largest["intersection_to_joint_linear_width_ratio"], 0.9633926606308423, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Largest final intersection tightening changed")
    ratio_largest = totals["largest_ratio_tightening"]
    if ratio_largest["x"] != -996.31 or not math.isclose(ratio_largest["ratio_interval_width_reduction"], 0.07692375150746189, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Largest ratio interval tightening changed")
    fold5 = summary["folds"][4]
    if fold5["prediction_envelope_available"] or fold5["envelopes"] or fold5["candidate_directions"] or fold5["candidate_evaluation_count"] != 0 or fold5["algebraic_extremizer_count"] != 0 or len(fold5["points"]) != 5 or any(point["residual_upper_bound"] is not None for point in fold5["points"]):
        errors.append("Fold-5 finite-bound or candidate prohibition changed")
    if not summary["independent_receipt_verified"] or not summary["joint_linear_receipt_verified"]:
        errors.append("A frozen source receipt is not verified")
    source = json.loads((ROOT / protocol["inputs"]["native_identifiability"]["file"]).read_text(encoding="utf-8"))
    matrix = source["folds"][1]["training_jacobian"]["parameter_covariance_matrix"]
    cross_difference_exact = Decimal(str(matrix[2][3])) - Decimal(str(matrix[3][2]))
    cross_difference = float(cross_difference_exact)
    if cross_difference_exact != Decimal("-1e-12"):
        errors.append("Frozen fold-2 covariance storage-asymmetry witness changed")
    witnesses = [witness for fold in summary["folds"] for envelope in fold["envelopes"] for witness in envelope["algebraic_extremizers"]]
    if len(witnesses) != 40 or any(not witness["feasible"] or not math.isclose(witness["ellipsoid_quadratic"], 16.0, rel_tol=1.0e-10, abs_tol=1.0e-10) or witness["denominator"] >= 0 or abs(float(witness["ratio_minus_root"])) > 1.0e-12 for witness in witnesses):
        errors.append("An algebraic extremizer is infeasible or inconsistent with its root")
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
        raise ValueError("Ratio-denominator Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": totals["fold_count"],
        "heldOutPointCount": totals["held_out_point_count"],
        "availablePointCount": totals["available_point_count"],
        "unavailablePointCount": totals["unavailable_point_count"],
        "unavailableFoldIds": totals["unavailable_fold_ids"],
        "ratioIntervalCount": totals["ratio_interval_count"],
        "ratioAlternativeBoundCount": totals["ratio_alternative_bound_count"],
        "intersectionBoundCount": totals["intersection_bound_count"],
        "algebraicExtremizerCount": totals["algebraic_extremizer_count"],
        "supportCandidateEvaluationCount": totals["support_candidate_evaluation_count"],
        "candidateEvaluationCount": totals["candidate_evaluation_count"],
        "nonemptyIntersectionCount": totals["nonempty_intersection_count"],
        "ratioCandidateViolationCount": totals["ratio_candidate_violation_count"],
        "alternativeCandidateViolationCount": totals["alternative_candidate_violation_count"],
        "intersectionCandidateViolationCount": totals["intersection_candidate_violation_count"],
        "independentCandidateViolationCount": totals["independent_candidate_violation_count"],
        "jointLinearCandidateViolationCount": totals["joint_linear_candidate_violation_count"],
        "extremizerFeasibilityFailureCount": totals["extremizer_feasibility_failure_count"],
        "candidateFeasibilityFailureCount": totals["candidate_feasibility_failure_count"],
        "centerPredictionMismatchCount": totals["center_prediction_mismatch_count"],
        "coveredPointCount": totals["covered_point_count"],
        "violationPointCount": totals["violation_point_count"],
        "ratioIntervalTightenedCount": totals["ratio_interval_tightened_count"],
        "alternativeTighterCount": totals["alternative_tighter_count"],
        "intersectionTightenedCount": totals["intersection_tightened_count"],
        "intersectionUnchangedCount": totals["intersection_unchanged_count"],
        "medianIntersectionToJointLinearWidthRatio": totals["median_intersection_to_joint_linear_width_ratio"],
        "maxIntersectionWidthReduction": totals["max_intersection_width_reduction"],
        "maxRatioIntervalWidthReduction": totals["max_ratio_interval_width_reduction"],
        "largestIntersectionTightening": largest,
        "largestRatioTightening": ratio_largest,
        "sourceReceiptVerifiedCount": 2,
        "sourceProjectionMismatchCount": 0,
        "fold2StoredCrossCovarianceDifference": cross_difference,
        "quadraticFormsUseSymmetricPart": True,
        "stableReciprocalRootUsed": True,
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_roszman1_ratio_denominator.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "fold5GivenFiniteBound": False,
        "fullNonlinearGlobalOptimumClaimed": False,
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
            raise ValueError("Ratio-denominator receipt is stale")
        print("OK: ratio-denominator receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
