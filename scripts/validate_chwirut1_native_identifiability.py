"""Validate and receipt the Chwirut1 native identifiability deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_chwirut1_native_identifiability import FIGURE, PROTOCOL, analyze, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/chwirut1-native-identifiability.json"
REPORT = ROOT / "docs/CHWIRUT1_NATIVE_IDENTIFIABILITY_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Chwirut1原生参数可识别性_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-chwirut1-native-identifiability-word.json"
OUTPUT = ROOT / "validation/chwirut1-native-identifiability-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "held_out_point_count": 214,
        "full_numerical_rank_fold_count": 5,
        "local_diagnostic_failure_count": 0,
        "max_scaled_condition_number": 28.674083116404475,
        "max_absolute_off_diagonal_parameter_correlation": 0.9794131139106378,
        "max_local_prediction_standard_deviation": 14.836682306268235,
        "native_test_rmse_minimum": 1.3682100460705144,
        "native_test_rmse_maximum": 14.465526570336303,
        "minimum_absolute_denominator": 0.009384279096904605,
        "pole_inside_observed_range_fold_count": 0,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Chwirut1 identifiability total mismatch: {key}")
    if [fold["test_count"] for fold in summary["folds"]] != [57, 54, 51, 23, 29]:
        errors.append("Frozen fold observation counts changed")
    if [fold["training_jacobian"]["shape"][0] - 3 for fold in summary["folds"]] != [154, 157, 160, 188, 182]:
        errors.append("Fold-specific residual degrees of freedom changed")
    fold1_b2 = summary["folds"][0]["training_jacobian"]["parameters"][1]
    if not math.isclose(fold1_b2["absolute_relative_standard_error"], 1.7106283204180401, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Fold-1 b2 local relative standard error changed")
    if any(fold["denominator_diagnostics"]["zero_denominator_count"] or fold["denominator_diagnostics"]["pole_inside_observed_closed_range"] for fold in summary["folds"]):
        errors.append("Frozen denominator or pole-location result changed")
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
        raise ValueError("Chwirut1 native identifiability Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": 5,
        "heldOutPointCount": 214,
        "fullRankFoldCount": 5,
        "poleInsideObservedRangeFoldCount": 0,
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_chwirut1_native_identifiability.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "globalIdentifiabilityClaimed": False,
        "calibratedIntervalsClaimed": False,
        "independentReplicationClaimed": False,
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
            raise ValueError("Chwirut1 native identifiability receipt is stale")
        print("OK: Chwirut1 native identifiability receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
