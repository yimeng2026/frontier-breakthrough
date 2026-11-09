"""Validate and receipt the ENSO native Fourier ellipsoid deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_enso_native_ellipsoid_continuous import FIGURE, PROTOCOL, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/enso-native-ellipsoid-continuous-bounds.json"
REPORT = ROOT / "docs/ENSO_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md"
WORD = ROOT / "papers/前沿共生ENSO原生椭球连续界_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-enso-native-ellipsoid-continuous-word.json"
OUTPUT = ROOT / "validation/enso-native-ellipsoid-continuous-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected = {
        "fold_count": 5,
        "held_out_point_count": 168,
        "unique_month_count": 168,
        "unique_envelope_count": 168,
        "certified_fold_count": 5,
        "available_point_count": 168,
        "covered_point_count": 168,
        "violation_point_count": 0,
        "unavailable_point_count": 0,
        "center_prediction_envelope_mismatch_count": 0,
        "minimum_critical_period_radius": 26.76683884611663,
        "minimum_critical_period_radius_fold": 4,
        "max_envelope_width": 17.64192935677042,
        "median_envelope_width": 13.164436414771593,
        "max_residual_upper_bound": 14.576765863967406,
        "median_residual_upper_bound": 8.516811559710845,
    }
    for key, value in expected.items():
        if not math.isclose(totals[key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            errors.append(f"ENSO ellipsoid total mismatch: {key}")
    if totals["certified_fold_ids"] != [1, 2, 3, 4, 5] or totals["unavailable_fold_ids"] or totals["minimum_critical_period_parameter"] != "b4":
        errors.append("ENSO certified fold set or limiting period changed")
    fold_expectations = [
        (44.24270315517963, 42.87224878516176, "b7", 38.30870432929572, 25.91199124399239),
        (53.72625759184087, 79.34049700978231, "b4", 40.64863190548021, 25.410341549486436),
        (45.06878982541118, 79.92390637464327, "b4", 40.81040457277938, 25.566525872737678),
        (26.76683884611663, 39.587037163194125, "b4", 38.0037866239862, 24.2810144640915),
        (31.988981288629372, 43.769289589273214, "b4", 39.58548395275371, 24.198418746301474),
    ]
    for fold, expected_fold in zip(summary["folds"], fold_expectations):
        critical = fold["critical_period"]
        certificate = fold["period_certificate"]
        actual = [critical["b4_radius"], critical["b7_radius"], critical["limiting_parameter"], certificate["b4_minimum"], certificate["b7_minimum"]]
        for key, value in zip(["b4_radius", "b7_radius", "limiting_parameter", "b4_minimum", "b7_minimum"], actual):
            target = expected_fold[["b4_radius", "b7_radius", "limiting_parameter", "b4_minimum", "b7_minimum"].index(key)]
            if key == "limiting_parameter":
                if value != target:
                    errors.append(f"ENSO fold {fold['fold']} limiting period changed")
            elif not math.isclose(value, target, rel_tol=1.0e-12, abs_tol=1.0e-12):
                errors.append(f"ENSO fold {fold['fold']} mismatch: {key}")
        control = fold["negative_control"]
        if not control["half_radius_accepted"] or not control["exact_radius_rejected"] or not fold["prediction_envelope_available"]:
            errors.append(f"ENSO critical-period negative control failed: {fold['fold']}")
    for key in ["probability_region", "taylor_or_fixed_period_approximation", "exact_rational_certificate", "actual_coverage_is_external_validation", "new_period_mechanism"]:
        if summary["analysis_scope"][key]:
            errors.append(f"ENSO analysis scope changed: {key}")
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
        raise ValueError("ENSO ellipsoid Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "foldCount": 5,
        "heldOutPointCount": 168,
        "uniqueEnvelopeCount": 168,
        "certifiedFoldCount": 5,
        "availablePointCount": 168,
        "coveredPointCount": 168,
        "violationPointCount": 0,
        "unavailablePointCount": 0,
        "centerMismatchCount": 0,
        "minimumCriticalPeriodRadius": totals["minimum_critical_period_radius"],
        "maxEnvelopeWidth": totals["max_envelope_width"],
        "medianEnvelopeWidth": totals["median_envelope_width"],
        "maxResidualUpperBound": totals["max_residual_upper_bound"],
        "medianResidualUpperBound": totals["median_residual_upper_bound"],
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_enso_native_ellipsoid_continuous.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "probabilityRegionClaimed": False,
        "fixedPeriodOrTaylorSubstitution": False,
        "exactRationalCertificateClaimed": False,
        "jointOptimalEnvelopeClaimed": False,
        "positivePeriodUsedAsPhysicalProof": False,
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
            raise ValueError("ENSO ellipsoid receipt is stale")
        print("OK: ENSO ellipsoid receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
