"""Validate and receipt the ENSO conditional-period slice deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_enso_conditional_period_slice import AMENDMENT, FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/enso-conditional-period-slice-bounds.json"
REPORT = ROOT / "docs/ENSO_CONDITIONAL_PERIOD_SLICE_BOUNDS_2026-11-09.md"
WORD = ROOT / "papers/前沿共生ENSO条件周期切片界_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-enso-conditional-period-slice-word.json"
OUTPUT = ROOT / "validation/enso-conditional-period-slice-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "held_out_point_count": 168,
        "slice_envelope_count": 168,
        "candidate_direction_count": 20,
        "candidate_evaluation_count": 672,
        "slice_violation_evaluation_count": 199,
        "slice_violating_envelope_count": 95,
        "full_independent_violation_count": 0,
        "slice_containment_violation_count": 0,
        "candidate_feasibility_failure_count": 0,
        "center_prediction_mismatch_count": 0,
        "conditional_matrix_failure_count": 0,
        "min_slice_to_independent_width_ratio": 0.23676362992169442,
        "median_slice_to_independent_width_ratio": 0.31983975629460537,
        "max_slice_to_independent_width_ratio": 0.42975805719497473,
        "max_width_reduction": 13.283611289252011,
        "median_width_reduction": 8.909069289620417,
        "max_slice_violation_exceedance": 2.3416912445042737,
        "refit_count": 0,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Conditional-period slice total mismatch: {key}")
    if totals["slice_global_validity"] != "falsified_by_feasible_candidate":
        errors.append("Slice full-region validity state changed")
    if [fold["slice_violation_evaluation_count"] for fold in summary["folds"]] != [56, 4, 0, 57, 82] or [fold["slice_violating_envelope_count"] for fold in summary["folds"]] != [28, 4, 0, 30, 33]:
        errors.append("Fold-specific candidate violations changed")
    if summary["folds"][2]["largest_violation_witness"] is not None:
        errors.append("Fold-3 zero-witness state changed")
    witness = totals["largest_violation_witness"]
    if witness["fold"] != 4 or witness["direction"] != "b4_minus" or witness["x"] != 134.0 or not witness["feasible"] or not witness["inside_independent_baseline"] or not math.isclose(witness["prediction"], 15.689547030796437, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Largest feasible slice-export witness changed")
    if not summary["baseline_receipt_verified"] or summary["baseline_envelope_match_count"] != 168:
        errors.append("Stage-47 baseline receipt or envelope mapping changed")
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
        raise ValueError("Conditional-period slice Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": 5,
        "sliceEnvelopeCount": 168,
        "candidateDirectionCount": 20,
        "candidateEvaluationCount": 672,
        "sliceViolationEvaluationCount": 199,
        "sliceViolatingEnvelopeCount": 95,
        "fullIndependentViolationCount": 0,
        "sliceContainmentViolationCount": 0,
        "candidateFeasibilityFailureCount": 0,
        "medianSliceToIndependentWidthRatio": totals["median_slice_to_independent_width_ratio"],
        "maxWidthReduction": totals["max_width_reduction"],
        "maxSliceViolationExceedance": totals["max_slice_violation_exceedance"],
        "largestWitness": {"fold": 4, "direction": "b4_minus", "x": 134.0, "prediction": witness["prediction"], "insideIndependentBaseline": True},
        "baselineReceiptVerified": True,
        "baselineEnvelopeMatchCount": 168,
        "protocolSha256": sha256(PROTOCOL),
        "amendmentSha256": sha256(AMENDMENT),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_enso_conditional_period_slice.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "sliceBoundCalledFullEllipsoidBound": False,
        "jointFullNonlinearOptimumClaimed": False,
        "zeroWitnessCalledSafetyProof": False,
        "marginalBlockCalledConditionalSlice": False,
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
            raise ValueError("Conditional-period slice receipt is stale")
        print("OK: conditional-period slice receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
