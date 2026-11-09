"""Validate and receipt the Chwirut1 native ellipsoid continuous-bounds deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_chwirut1_native_ellipsoid_continuous import FIGURE, PROTOCOL, analyze, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/chwirut1-native-ellipsoid-continuous-bounds.json"
REPORT = ROOT / "docs/CHWIRUT1_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Chwirut1原生椭球连续界_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-chwirut1-native-ellipsoid-continuous-word.json"
OUTPUT = ROOT / "validation/chwirut1-native-ellipsoid-continuous-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "held_out_point_count": 214,
        "unique_distance_count": 22,
        "unique_envelope_count": 22,
        "certified_fold_count": 5,
        "available_point_count": 214,
        "covered_point_count": 214,
        "violation_point_count": 0,
        "unavailable_point_count": 0,
        "center_prediction_envelope_mismatch_count": 0,
        "max_envelope_width": 170.14630922307612,
        "median_envelope_width": 19.222110234669167,
        "max_residual_upper_bound": 165.679601537622,
        "median_residual_upper_bound": 15.050994997990879,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Native ellipsoid total mismatch: {key}")
    if totals["unavailable_fold_ids"] or totals["certified_fold_ids"] != [1, 2, 3, 4, 5]:
        errors.append("Certified and unavailable fold sets changed")
    fold1 = summary["folds"][0]
    if not math.isclose(fold1["continuous_denominator"]["minimum"], 0.004322621973785059, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Fold-1 continuous denominator minimum changed")
    first = fold1["envelopes"][0]
    if not math.isclose(first["prediction_minimum"], 62.233292314545906, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(first["prediction_maximum"], 232.379601537622, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Fold-1 first prediction envelope changed")
    if summary["analysis_scope"]["probability_region"] or summary["analysis_scope"]["taylor_prediction_approximation"] or summary["analysis_scope"]["exact_rational_certificate"]:
        errors.append("Native ellipsoid analysis scope changed")
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
        raise ValueError("Native ellipsoid continuous Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": 5,
        "heldOutPointCount": 214,
        "uniqueEnvelopeCount": 22,
        "certifiedFoldCount": 5,
        "availablePointCount": 214,
        "coveredPointCount": 214,
        "violationPointCount": 0,
        "centerMismatchCount": 0,
        "maxEnvelopeWidth": totals["max_envelope_width"],
        "medianEnvelopeWidth": totals["median_envelope_width"],
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_chwirut1_native_ellipsoid_continuous.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "probabilityRegionClaimed": False,
        "exactRationalCertificateClaimed": False,
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
            raise ValueError("Native ellipsoid continuous receipt is stale")
        print("OK: native ellipsoid continuous receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
