"""Validate and receipt the three-model conservative-support synthesis."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_native_conservative_support_synthesis import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "exports/native-conservative-support-synthesis.json"
REPORT = ROOT / "docs/NATIVE_CONSERVATIVE_SUPPORT_SYNTHESIS_2026-11-09.md"
WORD = ROOT / "papers/前沿共生三模型保守支撑综合_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-native-conservative-support-synthesis-word.json"
OUTPUT = ROOT / "validation/native-conservative-support-synthesis-check.json"
EXPECTED_TOTALS = {
    "dataset_count": 3,
    "held_out_point_count": 407,
    "available_point_count": 402,
    "unavailable_point_count": 5,
    "unique_envelope_count": 210,
    "tightened_envelope_count": 79,
    "unchanged_envelope_count": 131,
    "nonempty_intersection_count": 210,
    "candidate_evaluation_count": 964,
    "candidate_violation_count": 0,
    "center_prediction_mismatch_count": 0,
    "source_receipt_verified_count": 3,
    "source_projection_mismatch_count": 0,
    "refit_count": 0,
}
EXPECTED_CASES = {
    "chwirut1": (2, 1.5, 20.935447900396312, 0.2130823595991901),
    "roszman1": (1, -4868.68, 0.7008593776977347, 0.19189941295847002),
    "enso": (1, 25.0, 4.371401855122352, 0.7474092252857671),
}
EXPECTED_MEDIANS = {
    "chwirut1": 0.25654045819729265,
    "roszman1": 0.690796188558053,
    "enso": 1.0,
}


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    for key, value in EXPECTED_TOTALS.items():
        if totals.get(key) != value:
            errors.append(f"Conservative-support total mismatch: {key}")
    if totals.get("unavailable_fold_ids") != ["roszman1:5"]:
        errors.append("Roszman1 fold-5 unavailable identity changed")
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source_receipts = {}
    for dataset in summary["datasets"]:
        identifier = dataset["id"]
        info = protocol["inputs"][f"{identifier}_receipt"]
        path = ROOT / info["file"]
        receipt = json.loads(path.read_text(encoding="utf-8"))
        source_receipts[identifier] = {
            "file": info["file"],
            "sha256": sha256(path),
            "summarySha256": receipt["summarySha256"],
        }
        if sha256(path) != info["sha256"] or receipt["status"] != "passed" or receipt["summarySha256"] != dataset["source_sha256"]:
            errors.append(f"Frozen source receipt mismatch: {identifier}")
        if not dataset["source_receipt_verified"] or dataset["source_projection_mismatch_count"] != 0:
            errors.append(f"Source projection gate changed: {identifier}")
        if not math.isclose(dataset["ratio_summary"]["median"], EXPECTED_MEDIANS[identifier], rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Within-model median ratio changed: {identifier}")
        fold_id, x, reduction, ratio = EXPECTED_CASES[identifier]
        fold = dataset["folds"][fold_id - 1]
        largest_key = "largest_triple_tightening" if identifier == "enso" else "largest_intersection_tightening"
        largest = fold[largest_key]
        reduction_key = "triple_width_reduction" if identifier == "enso" else "intersection_width_reduction"
        ratio_key = "triple_to_lipschitz_width_ratio" if identifier == "enso" else "intersection_to_independent_width_ratio"
        if fold["fold"] != fold_id or largest["x"] != x or not math.isclose(largest[reduction_key], reduction, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(largest[ratio_key], ratio, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Largest tightening case changed: {identifier}")
        if largest != dataset["largest_tightening"]:
            errors.append(f"Dataset-level largest tightening projection changed: {identifier}")
    tangent_counts = {key: sum(fold["tangent_winner_counts"][key] for fold in summary["datasets"][0]["folds"]) for key in ["d_min", "d_center", "d_max"]}
    if tangent_counts != {"d_min": 7, "d_center": 7, "d_max": 8}:
        errors.append("Chwirut1 tangent inventory changed")
    fold5 = summary["datasets"][1]["folds"][4]
    if fold5["fold"] != 5 or fold5["prediction_envelope_available"] or fold5["envelopes"] or fold5["candidate_evaluation_count"] != 0 or len(fold5["points"]) != 5 or any(point["residual_upper_bound"] is not None or point["intersection_minimum"] is not None or point["intersection_maximum"] is not None for point in fold5["points"]):
        errors.append("Roszman1 fold-5 finite-bound prohibition changed")
    for key in ["cross_dataset_pooled_error_metrics", "cross_dataset_raw_widths", "unified_stability_score", "probability_coverage", "global_optimum"]:
        if summary.get(key) is not None:
            errors.append(f"Forbidden aggregate is no longer null: {key}")
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
        raise ValueError("Conservative-support synthesis Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "datasetCount": totals["dataset_count"],
        "heldOutPointCount": totals["held_out_point_count"],
        "availablePointCount": totals["available_point_count"],
        "unavailablePointCount": totals["unavailable_point_count"],
        "unavailableFoldIds": totals["unavailable_fold_ids"],
        "uniqueEnvelopeCount": totals["unique_envelope_count"],
        "tightenedEnvelopeCount": totals["tightened_envelope_count"],
        "unchangedEnvelopeCount": totals["unchanged_envelope_count"],
        "nonemptyIntersectionCount": totals["nonempty_intersection_count"],
        "candidateEvaluationCount": totals["candidate_evaluation_count"],
        "candidateViolationCount": totals["candidate_violation_count"],
        "centerPredictionMismatchCount": totals["center_prediction_mismatch_count"],
        "sourceReceiptVerifiedCount": totals["source_receipt_verified_count"],
        "sourceProjectionMismatchCount": totals["source_projection_mismatch_count"],
        "refitCount": totals["refit_count"],
        "withinDatasetRatioMedians": EXPECTED_MEDIANS,
        "largestTighteningCases": {dataset["id"]: dataset["largest_tightening"] for dataset in summary["datasets"]},
        "sourceReceipts": source_receipts,
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_native_conservative_support_synthesis.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "crossDatasetPooledErrorMetrics": None,
        "crossDatasetRawWidths": None,
        "unifiedStabilityScore": None,
        "probabilityCoverage": None,
        "globalOptimum": None,
        "fold5GivenFiniteBound": False,
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
            raise ValueError("Conservative-support synthesis receipt is stale")
        print("OK: conservative-support synthesis receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
