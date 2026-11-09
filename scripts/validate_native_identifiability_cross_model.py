"""Validate and receipt the cross-model identifiability synthesis deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_native_identifiability_cross_model import FIGURE, PROTOCOL, analyze, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "exports/native-identifiability-cross-model-synthesis.json"
REPORT = ROOT / "docs/NATIVE_IDENTIFIABILITY_CROSS_MODEL_2026-11-09.md"
WORD = ROOT / "papers/前沿共生三模型局部可识别性综合_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-native-identifiability-cross-model-word.json"
OUTPUT = ROOT / "validation/native-identifiability-cross-model-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "dataset_count": 3,
        "fold_count": 15,
        "held_out_point_count": 407,
        "full_numerical_rank_fold_count": 15,
        "local_diagnostic_failure_count": 0,
        "sensitivity_exceeds_rmse_fold_count": 3,
        "max_sensitivity_to_rmse_ratio": 2.6972635478072906,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Cross-model synthesis total mismatch: {key}")
    if totals["sensitivity_exceeds_rmse_fold_ids"] != ["roszman1:1", "roszman1:5", "chwirut1:1"] or totals["sensitivity_equals_rmse_fold_ids"]:
        errors.append("Sensitivity/RMSE counterexample set changed")
    expected_conditions = {"roszman1": 90.74335888809009, "chwirut1": 28.674083116404475, "enso": 6.896240781966828}
    for dataset in summary["datasets"]:
        if not math.isclose(dataset["summary"]["max_scaled_condition_number"], expected_conditions[dataset["id"]], rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Maximum condition changed: {dataset['id']}")
    if summary["cross_model_pooled_error_metrics"] is not None or summary["cross_model_stability_score"] is not None:
        errors.append("Forbidden cross-model pooled metric or stability score is present")
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
        raise ValueError("Cross-model identifiability Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "datasetCount": 3,
        "foldCount": 15,
        "heldOutPointCount": 407,
        "fullRankFoldCount": 15,
        "sensitivityExceedsRmseFoldIds": ["roszman1:1", "roszman1:5", "chwirut1:1"],
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_native_identifiability_cross_model.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "crossModelPooledErrorMetrics": None,
        "crossModelStabilityScore": None,
        "calibratedCoverageClaimed": False,
        "globalIdentifiabilityClaimed": False,
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
            raise ValueError("Cross-model identifiability synthesis receipt is stale")
        print("OK: cross-model identifiability synthesis receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
