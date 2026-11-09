"""Validate and receipt the sensitivity-threshold coverage deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_native_sensitivity_threshold_coverage import FIGURE, PROTOCOL, analyze, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "exports/native-sensitivity-threshold-coverage.json"
REPORT = ROOT / "docs/NATIVE_SENSITIVITY_THRESHOLD_COVERAGE_2026-11-09.md"
WORD = ROOT / "papers/前沿共生三模型敏感度阈值覆盖_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-native-sensitivity-threshold-coverage-word.json"
OUTPUT = ROOT / "validation/native-sensitivity-threshold-coverage-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    if totals["point_count"] != 407 or totals["fold_count"] != 15 or totals["evaluation_count"] != 1221:
        errors.append("Point, fold or evaluation count changed")
    expected = {
        "1": (85, 322, 1),
        "2": (181, 226, 2),
        "4": (283, 124, 3),
    }
    for threshold, (covered, violation, zero_folds) in expected.items():
        record = totals["thresholds"][threshold]
        if record["covered_count"] != covered or record["violation_count"] != violation or record["zero_violation_fold_count"] != zero_folds:
            errors.append(f"Threshold totals changed: {threshold}")
    expected_datasets = {
        "roszman1": {"1": 12, "2": 16, "4": 21},
        "chwirut1": {"1": 37, "2": 101, "4": 146},
        "enso": {"1": 36, "2": 64, "4": 116},
    }
    for dataset in summary["datasets"]:
        for threshold, covered in expected_datasets[dataset["id"]].items():
            if dataset["thresholds"][threshold]["covered_count"] != covered:
                errors.append(f"Dataset threshold coverage changed: {dataset['id']}:{threshold}")
    if not math.isclose(totals["max_residual_to_sensitivity_ratio"], 25.724483321809334, rel_tol=1.0e-12, abs_tol=1.0e-12) or totals["max_ratio_point_id"] != "chwirut1:3:30":
        errors.append("Maximum point ratio changed")
    if totals["zero_sensitivity_point_count"] != 0:
        errors.append("Zero-sensitivity scope changed")
    roszman = next(dataset for dataset in summary["datasets"] if dataset["id"] == "roszman1")
    if roszman["folds"][4]["thresholds"]["1"]["covered_count"] != 5 or not math.isclose(roszman["folds"][4]["max_residual_to_sensitivity_ratio"], 0.7393687714886938, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Roszman1 fold-5 aggregation counterexample changed")
    if summary["cross_model_probability_coverage_score"] is not None:
        errors.append("Forbidden cross-model probability score is present")
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
        raise ValueError("Sensitivity-threshold coverage Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "pointCount": 407,
        "foldCount": 15,
        "evaluationCount": 1221,
        "coveredCounts": {"1": 85, "2": 181, "4": 283},
        "violationCounts": {"1": 322, "2": 226, "4": 124},
        "maxRatioPointId": "chwirut1:3:30",
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_native_sensitivity_threshold_coverage.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "probabilityCoverageClaimed": False,
        "confidenceIntervalClaimed": False,
        "nativeDeterministicBoundsClaimed": False,
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
            raise ValueError("Sensitivity-threshold coverage receipt is stale")
        print("OK: sensitivity-threshold coverage receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
