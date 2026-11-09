"""Validate and receipt the frozen native cross-dataset synthesis deliverables."""

import argparse
import json
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_native_cross_dataset_synthesis import FIGURE, PROTOCOL, analyze, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "exports/native-cross-dataset-synthesis.json"
REPORT = ROOT / "docs/NATIVE_CROSS_DATASET_SYNTHESIS_2026-11-09.md"
WORD = ROOT / "papers/前沿共生三数据原生同折综合_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-native-cross-dataset-word.json"
OUTPUT = ROOT / "validation/native-cross-dataset-synthesis-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "dataset_count": 3,
        "fold_count": 15,
        "point_count": 407,
        "native_better_than_rational_fold_count": 11,
        "rational_better_than_native_fold_count": 4,
        "native_better_than_cubic_fold_count": 13,
        "cubic_better_than_native_fold_count": 2,
        "pooled_metric_mismatch_count": 0,
    }
    for key, value in expected.items():
        if totals[key] != value:
            errors.append(f"Synthesis total mismatch: {key}")
    if totals["overall_best_model_fold_counts"] != {"native": 10, "rational": 3, "cubic": 2, "tie": 0}:
        errors.append("Overall fold-winner counts changed")
    if totals["point_outcomes"] != {"native": 256, "rational": 151, "tie": 0}:
        errors.append("Paired point outcome counts changed")
    if totals["metric_direction_disagreement_fold_ids"] != ["roszman1:4"]:
        errors.append("Roszman1 fold-4 metric-direction counterexample is missing")
    if totals["point_fold_disagreement_fold_ids"] != []:
        errors.append("Point-versus-fold disagreement scope changed")
    if summary["cross_dataset_pooled_error_metrics"] is not None:
        errors.append("Forbidden cross-dataset pooled metric is present")
    for key, value in summary["decision"].items():
        if value is not False:
            errors.append(f"Decision scope changed: {key}")
    for path in [PROTOCOL, SUMMARY, REPORT, FIGURE, WORD, WORD_MANIFEST]:
        if not path.is_file():
            errors.append(f"Missing deliverable: {path.relative_to(ROOT)}")
    if errors:
        raise ValueError(errors)
    word_manifest = json.loads(WORD_MANIFEST.read_text(encoding="utf-8"))
    if word_manifest["sha256"] != sha256(WORD) or word_manifest["bytes"] != WORD.stat().st_size:
        raise ValueError("Native cross-dataset Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "datasetCount": totals["dataset_count"],
        "foldCount": totals["fold_count"],
        "pointCount": totals["point_count"],
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_native_cross_dataset_synthesis.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "crossDatasetPooledErrorMetrics": None,
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
            raise ValueError("Native cross-dataset synthesis receipt is stale")
        print("OK: native cross-dataset synthesis receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
