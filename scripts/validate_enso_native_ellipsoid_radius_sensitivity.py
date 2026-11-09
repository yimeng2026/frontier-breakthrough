"""Validate and receipt the ENSO native Fourier radius-sensitivity deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_enso_native_ellipsoid_radius_sensitivity import AMENDMENT, FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/enso-native-ellipsoid-radius-sensitivity.json"
REPORT = ROOT / "docs/ENSO_NATIVE_ELLIPSOID_RADIUS_SENSITIVITY_2026-11-09.md"
WORD = ROOT / "papers/前沿共生ENSO原生椭球半径敏感性_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-enso-native-ellipsoid-radius-sensitivity-word.json"
OUTPUT = ROOT / "validation/enso-native-ellipsoid-radius-sensitivity-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "radius_count": 6,
        "case_count": 30,
        "held_out_point_count_per_radius": 168,
        "unique_month_count_per_radius": 168,
        "maximum_point_evaluations": 1008,
        "maximum_envelope_evaluations": 1008,
        "actual_envelope_evaluation_count": 942,
        "certified_case_count": 28,
        "available_point_count": 942,
        "covered_point_count": 942,
        "violation_point_count": 0,
        "unavailable_point_count": 66,
        "unavailable_case_count": 2,
        "center_prediction_envelope_mismatch_count": 0,
        "max_envelope_width": 141.13543485416332,
        "median_envelope_width": 15.14954765223098,
        "max_residual_upper_bound": 75.54732074215885,
        "median_residual_upper_bound": 10.615255931469495,
        "minimum_critical_period_radius": 26.76683884611663,
        "minimum_critical_period_radius_fold": 4,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"ENSO radius-sensitivity total mismatch: {key}")
    if totals["fold_held_out_point_counts"] != [34, 34, 34, 33, 33] or totals["fold_unique_month_counts"] != [34, 34, 34, 33, 33]:
        errors.append("Fold-specific observation counts changed")
    if totals["unavailable_case_ids"] != ["enso:4:r32", "enso:5:r32"] or totals["minimum_critical_period_parameter"] != "b4":
        errors.append("Radius-32 unavailable cases or limiting period changed")
    if [fold["max_certified_grid_radius"] for fold in summary["folds"]] != [32, 32, 32, 16, 16]:
        errors.append("Grid-certified maxima changed")
    if any(not fold["negative_control"]["half_radius_accepted"] or not fold["negative_control"]["exact_radius_rejected"] for fold in summary["folds"]):
        errors.append("Critical-period negative control failed")
    fold4 = summary["folds"][3]["cases"][-1]
    fold5 = summary["folds"][4]["cases"][-1]
    if fold4["prediction_envelope_available"] or fold5["prediction_envelope_available"] or not math.isclose(fold4["period_certificate"]["b4_minimum"], -8.73550962456259, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(fold5["period_certificate"]["b4_minimum"], -0.015584026358234438, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Radius-32 period-crossing results changed")
    expected_widths = [4.410482339192611, 8.820964678385213, 17.64192935677042, 35.28385871354083, 70.56771742708166, 141.13543485416332]
    expected_medians = [3.2911091036929068, 6.582218207385804, 13.164436414771593, 26.32887282954318, 52.65774565908636, 109.85401163093286]
    for record, maximum, median in zip(summary["radius_summaries"], expected_widths, expected_medians):
        if not math.isclose(record["max_envelope_width"], maximum, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(record["median_envelope_width"], median, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Radius width summary changed: {record['radius']}")
    baseline = summary["baseline"]
    if not baseline["matches_frozen_baseline"] or baseline["exact_fold_projection_match_count"] != 5 or baseline["certified_fold_count"] != 5 or baseline["available_point_count"] != 168 or baseline["covered_point_count"] != 168 or baseline["violation_point_count"] != 0 or baseline["unavailable_point_count"] != 0:
        errors.append("Radius-4 baseline mismatch")
    correction = summary["analysis_scope"]["count_correction"]
    if correction["original_maximum_evaluations"] != 5040 or correction["corrected_maximum_evaluations"] != 1008 or not correction["original_protocol_preserved"]:
        errors.append("Count-correction scope changed")
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
        raise ValueError("ENSO radius-sensitivity Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "caseCount": 30,
        "maximumPointEvaluations": 1008,
        "maximumEnvelopeEvaluations": 1008,
        "actualEnvelopeEvaluations": 942,
        "availablePointCount": 942,
        "coveredPointCount": 942,
        "violationPointCount": 0,
        "unavailablePointCount": 66,
        "unavailableCaseIds": ["enso:4:r32", "enso:5:r32"],
        "minimumCriticalPeriodRadius": totals["minimum_critical_period_radius"],
        "minimumCriticalPeriodRadiusFold": 4,
        "maxEnvelopeWidth": totals["max_envelope_width"],
        "maxResidualUpperBound": totals["max_residual_upper_bound"],
        "baselineMatches": True,
        "baselineFoldProjectionMatchCount": 5,
        "originalProtocolPreserved": True,
        "protocolSha256": sha256(PROTOCOL),
        "amendmentSha256": sha256(AMENDMENT),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_enso_native_ellipsoid_radius_sensitivity.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "optimalRadiusSelected": False,
        "gridMaximumCalledExactSafeMaximum": False,
        "positivePeriodUsedAsPhysicalProof": False,
        "jointNonlinearOptimumClaimed": False,
        "centerConsistencyUsedAsExternalValidation": False,
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
            raise ValueError("ENSO radius-sensitivity receipt is stale")
        print("OK: ENSO radius-sensitivity receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
