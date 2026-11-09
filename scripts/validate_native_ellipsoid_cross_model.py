"""Validate and receipt the native ellipsoid cross-model synthesis."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_native_ellipsoid_cross_model import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "exports/native-ellipsoid-cross-model-synthesis.json"
REPORT = ROOT / "docs/NATIVE_ELLIPSOID_CROSS_MODEL_SYNTHESIS_2026-11-09.md"
WORD = ROOT / "papers/前沿共生三模型原生椭球包络综合_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-native-ellipsoid-cross-model-word.json"
OUTPUT = ROOT / "validation/native-ellipsoid-cross-model-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "dataset_count": 3,
        "fold_count": 15,
        "held_out_point_count": 407,
        "certified_fold_count": 14,
        "available_point_count": 402,
        "covered_point_count": 402,
        "violation_point_count": 0,
        "unavailable_point_count": 5,
        "unique_envelope_count": 210,
        "center_prediction_envelope_mismatch_count": 0,
        "source_receipt_verified_count": 3,
        "source_projection_mismatch_count": 0,
        "refit_count": 0,
        "baseline_radius": 4,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Native ellipsoid cross-model total mismatch: {key}")
    if totals["unavailable_fold_ids"] != ["roszman1:5"]:
        errors.append("Roszman1 fold-5 unavailable state changed")
    expected_raw = {
        "chwirut1": [170.14630922307612, 19.222110234669167, 165.679601537622, 15.050994997990879],
        "roszman1": [0.867292251653464, 0.3543650116278472, 0.4433913282171526, 0.1853990741468824],
        "enso": [17.64192935677042, 13.164436414771593, 14.576765863967406, 8.516811559710845],
    }
    for dataset in summary["datasets"]:
        actual = [dataset["totals"][key] for key in ["max_envelope_width", "median_envelope_width", "max_residual_upper_bound", "median_residual_upper_bound"]]
        for key, value, target in zip(["max_envelope_width", "median_envelope_width", "max_residual_upper_bound", "median_residual_upper_bound"], actual, expected_raw[dataset["id"]]):
            if not math.isclose(value, target, rel_tol=1.0e-12, abs_tol=1.0e-12):
                errors.append(f"Raw model metric changed: {dataset['id']}:{key}")
        if not dataset["source_receipt_verified"] or dataset["recomputed_source_mismatch_count"]:
            errors.append(f"Frozen source receipt or projection failed: {dataset['id']}")
    chwirut_fold1 = summary["datasets"][0]["folds"][0]
    if not math.isclose(chwirut_fold1["normalization"]["max_width_to_dataset_median"], 8.85159366718222, rel_tol=1.0e-12, abs_tol=1.0e-12) or not math.isclose(chwirut_fold1["normalization"]["max_residual_to_dataset_median"], 11.007883635582775, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Chwirut1 fold-1 within-dataset ratios changed")
    roszman_fold5 = summary["datasets"][1]["folds"][4]
    if roszman_fold5["prediction_envelope_available"] or roszman_fold5["coverage"]["unavailable_point_count"] != 5 or not math.isclose(roszman_fold5["native_test_rmse"], 0.006228106060478816, rel_tol=1.0e-12, abs_tol=1.0e-12) or any(roszman_fold5["normalization"].values()):
        errors.append("Roszman1 fold-5 low-RMSE/no-envelope counterexample changed")
    for key in ["cross_dataset_pooled_error_metrics", "cross_dataset_pooled_envelope_widths", "cross_dataset_pooled_residual_upper_bounds", "cross_dataset_stability_score", "universal_model_winner", "probability_coverage"]:
        if summary[key] is not None:
            errors.append(f"Forbidden aggregate is present: {key}")
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
        raise ValueError("Native ellipsoid cross-model Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "datasetCount": 3,
        "foldCount": 15,
        "heldOutPointCount": 407,
        "certifiedFoldCount": 14,
        "availablePointCount": 402,
        "coveredPointCount": 402,
        "violationPointCount": 0,
        "unavailablePointCount": 5,
        "uniqueEnvelopeCount": 210,
        "sourceReceiptVerifiedCount": 3,
        "sourceProjectionMismatchCount": 0,
        "unavailableFoldIds": ["roszman1:5"],
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_native_ellipsoid_cross_model.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "crossDatasetPooledErrorMetrics": None,
        "crossDatasetPooledEnvelopeWidths": None,
        "crossDatasetStabilityScore": None,
        "universalModelWinner": None,
        "probabilityCoverageClaimed": False,
        "jointNonlinearOptimumClaimed": False,
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
            raise ValueError("Native ellipsoid cross-model receipt is stale")
        print("OK: native ellipsoid cross-model receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
