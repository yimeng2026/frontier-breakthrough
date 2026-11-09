"""Validate and receipt the ENSO native identifiability deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_enso_native_identifiability import FIGURE, PROTOCOL, analyze, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/enso-native-identifiability.json"
REPORT = ROOT / "docs/ENSO_NATIVE_IDENTIFIABILITY_2026-11-09.md"
WORD = ROOT / "papers/前沿共生ENSO原生参数可识别性_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-enso-native-identifiability-word.json"
OUTPUT = ROOT / "validation/enso-native-identifiability-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "held_out_point_count": 168,
        "full_numerical_rank_fold_count": 5,
        "local_diagnostic_failure_count": 0,
        "max_scaled_condition_number": 6.896240781966828,
        "max_absolute_off_diagonal_parameter_correlation": 0.9187090249098154,
        "max_local_prediction_standard_deviation": 1.0603474415430074,
        "native_test_rmse_minimum": 2.3729570605012986,
        "native_test_rmse_maximum": 3.448449143701017,
        "max_b4_b7_absolute_correlation": 0.554759714593918,
        "max_cross_harmonic_block_absolute_correlation": 0.5591238742033899,
        "max_annual_long_block_absolute_correlation": 0.15212841448706105,
        "max_b4_own_amplitude_absolute_correlation": 0.9043681838935033,
        "max_b7_own_amplitude_absolute_correlation": 0.9187090249098154,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"ENSO identifiability total mismatch: {key}")
    if [fold["train_count"] - 9 for fold in summary["folds"]] != [125, 125, 125, 126, 126]:
        errors.append("Fold-specific residual degrees of freedom changed")
    if not math.isclose(summary["parameter_stability"]["b4"]["range"], 3.1263085397655743, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(summary["parameter_stability"]["b7"]["range"], 1.9460668828939873, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Frozen period ranges changed")
    fold4 = summary["folds"][3]
    period_se = {entry["name"]: entry["absolute_relative_standard_error"] for entry in fold4["training_jacobian"]["parameters"]}
    if not math.isclose(period_se["b4"], 0.037359660053584605, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(period_se["b7"], 0.025260794231141546, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Fold-4 period relative standard errors changed")
    if summary["known_answer"]["optimizer_within_certified_tolerances"] or not summary["known_answer"]["certified_forward_rss_check_passed"] or summary["known_answer"]["used_as_holdout"]:
        errors.append("Known-answer evidence layering changed")
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
        raise ValueError("ENSO native identifiability Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": 5,
        "heldOutPointCount": 168,
        "fullRankFoldCount": 5,
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_enso_native_identifiability.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "globalIdentifiabilityClaimed": False,
        "newPhysicalPeriodsClaimed": False,
        "calibratedIntervalsClaimed": False,
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
            raise ValueError("ENSO native identifiability receipt is stale")
        print("OK: ENSO native identifiability receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
