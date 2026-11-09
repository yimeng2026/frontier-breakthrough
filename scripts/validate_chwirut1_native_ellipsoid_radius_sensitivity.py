"""Validate and receipt the Chwirut1 ellipsoid radius-sensitivity deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_chwirut1_native_ellipsoid_radius_sensitivity import FIGURE, PROTOCOL, analyze, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/chwirut1-native-ellipsoid-radius-sensitivity.json"
REPORT = ROOT / "docs/CHWIRUT1_NATIVE_ELLIPSOID_RADIUS_SENSITIVITY_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Chwirut1原生椭球半径敏感性_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-chwirut1-native-ellipsoid-radius-sensitivity-word.json"
AMENDMENT = ROOT / "validation/chwirut1-native-ellipsoid-radius-sensitivity-protocol-amendment-02.json"
OUTPUT = ROOT / "validation/chwirut1-native-ellipsoid-radius-sensitivity-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "radius_count": 5,
        "case_count": 25,
        "held_out_point_count_per_case": 214,
        "unique_distance_count": 22,
        "maximum_point_evaluations": 1070,
        "maximum_envelope_evaluations": 110,
        "actual_envelope_evaluation_count": 105,
        "unavailable_case_count": 1,
        "center_prediction_envelope_mismatch_count": 0,
        "minimum_critical_radius": 7.415973756136996,
        "minimum_critical_radius_fold": 1,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Radius-sensitivity total mismatch: {key}")
    if totals["unavailable_case_ids"] != ["chwirut1:1:r8"]:
        errors.append("Radius-8 unavailable case changed")
    if [fold["max_certified_grid_radius"] for fold in summary["folds"]] != [4, 8, 8, 8, 8]:
        errors.append("Grid-certified maxima changed")
    if any(not fold["negative_control"]["half_radius_accepted"] or not fold["negative_control"]["exact_radius_rejected"] for fold in summary["folds"]):
        errors.append("Critical-radius negative control failed")
    baseline = summary["baseline"]
    if not baseline["matches_frozen_baseline"] or baseline["certified_fold_count"] != 5 or baseline["available_point_count"] != 214 or baseline["covered_point_count"] != 214 or baseline["violation_point_count"] != 0 or baseline["unavailable_point_count"] != 0:
        raise ValueError("Radius-4 baseline mismatch")
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
        raise ValueError("Radius-sensitivity Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "caseCount": 25,
        "maximumPointEvaluations": 1070,
        "maximumEnvelopeEvaluations": 110,
        "actualEnvelopeEvaluations": 105,
        "unavailableCaseIds": ["chwirut1:1:r8"],
        "minimumCriticalRadius": totals["minimum_critical_radius"],
        "minimumCriticalRadiusFold": 1,
        "baselineMatches": True,
        "protocolSha256": sha256(PROTOCOL),
        "amendmentSha256": sha256(AMENDMENT),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_chwirut1_native_ellipsoid_radius_sensitivity.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "optimalRadiusSelected": False,
        "gridMaximumCalledExactSafeMaximum": False,
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
            raise ValueError("Radius-sensitivity receipt is stale")
        print("OK: radius-sensitivity receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
