"""Validate and receipt the Roszman1 native ellipsoid singularity deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_roszman1_native_ellipsoid_continuous import FIGURE, PROTOCOL, analyze, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/roszman1-native-ellipsoid-continuous-bounds.json"
REPORT = ROOT / "docs/ROSZMAN1_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Roszman1原生椭球奇异界_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-roszman1-native-ellipsoid-continuous-word.json"
OUTPUT = ROOT / "validation/roszman1-native-ellipsoid-continuous-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "held_out_point_count": 25,
        "unique_x_count": 25,
        "unique_envelope_count": 20,
        "certified_fold_count": 4,
        "available_point_count": 20,
        "covered_point_count": 20,
        "violation_point_count": 0,
        "unavailable_point_count": 5,
        "center_prediction_envelope_mismatch_count": 0,
        "minimum_critical_sign_radius": 2.828350890156889,
        "minimum_critical_sign_radius_fold": 5,
        "max_envelope_width": 0.867292251653464,
        "median_envelope_width": 0.3543650116278472,
        "max_residual_upper_bound": 0.4433913282171526,
        "median_residual_upper_bound": 0.1853990741468824,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"Roszman1 ellipsoid total mismatch: {key}")
    if totals["certified_fold_ids"] != [1, 2, 3, 4] or totals["unavailable_fold_ids"] != [5]:
        errors.append("Certified and unavailable fold sets changed")
    if any(not fold["negative_control"]["half_radius_accepted"] or not fold["negative_control"]["exact_radius_rejected"] for fold in summary["folds"]):
        errors.append("Critical-sign negative control failed")
    fold5 = summary["folds"][4]
    if fold5["prediction_envelope_available"] or not math.isclose(fold5["sign_certificate"]["endpoint_results"][1]["maximum"], 103.08875349466264, rel_tol=1.0e-12, abs_tol=1.0e-12):
        errors.append("Fold-5 crossing result changed")
    if summary["analysis_scope"]["probability_region"] or summary["analysis_scope"]["taylor_prediction_approximation"] or summary["analysis_scope"]["exact_rational_certificate"]:
        errors.append("Roszman1 ellipsoid analysis scope changed")
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
        raise ValueError("Roszman1 ellipsoid Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": 5,
        "heldOutPointCount": 25,
        "uniqueEnvelopeCount": 20,
        "certifiedFoldCount": 4,
        "availablePointCount": 20,
        "coveredPointCount": 20,
        "violationPointCount": 0,
        "unavailablePointCount": 5,
        "centerMismatchCount": 0,
        "minimumCriticalSignRadius": totals["minimum_critical_sign_radius"],
        "maxEnvelopeWidth": totals["max_envelope_width"],
        "medianEnvelopeWidth": totals["median_envelope_width"],
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_roszman1_native_ellipsoid_continuous.py"),
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
            raise ValueError("Roszman1 ellipsoid receipt is stale")
        print("OK: Roszman1 ellipsoid receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
