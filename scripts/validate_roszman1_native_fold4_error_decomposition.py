"""Validate and receipt the Roszman1 fold-4 decomposition deliverables."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256
from analyze_roszman1_native_fold4_error_decomposition import FIGURE, PROTOCOL, analyze, validate_summary

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "validation/roszman1-native-fold4-error-decomposition.json"
REPORT = ROOT / "docs/ROSZMAN1_NATIVE_FOLD4_ERROR_DECOMPOSITION_2026-11-09.md"
WORD = ROOT / "papers/前沿共生Roszman1第4折误差分解_图文完整版.docx"
WORD_MANIFEST = ROOT / "validation/frontier-roszman1-fold4-decomposition-word.json"
OUTPUT = ROOT / "validation/roszman1-native-fold4-error-decomposition-check.json"


def build_receipt():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    totals = summary["totals"]
    expected_totals = {
        "point_count": 5,
        "native_absolute_winner_count": 3,
        "rational_absolute_winner_count": 2,
        "absolute_tie_count": 0,
        "leave_one_out_reverses_rational_mae_count": 2,
        "leave_one_out_reverses_native_rmse_count": 0,
        "leave_one_out_reverses_either_count": 2,
        "leave_one_out_reverses_both_count": 0,
        "per_point_absolute_squared_direction_disagreement_count": 0,
    }
    for key, value in expected_totals.items():
        if totals[key] != value:
            errors.append(f"Fold-4 total mismatch: {key}")
    if not math.isclose(summary["aggregate"]["absolute_delta_sum"], 0.0004619751217002088, rel_tol=1.0e-12, abs_tol=1.0e-15):
        errors.append("Absolute delta total changed")
    if not math.isclose(summary["aggregate"]["squared_delta_sum"], -1.317350030774099e-05, rel_tol=1.0e-12, abs_tol=1.0e-18):
        errors.append("Squared delta total changed")
    if summary["groups"]["native"]["point_indices"] != [1, 2, 3] or summary["groups"]["rational"]["point_indices"] != [4, 5]:
        errors.append("Fold-4 point groups changed")
    if [record["point_index"] for record in summary["leave_one_out"] if record["reverses_rational_mae"]] != [4, 5]:
        errors.append("MAE leave-one-out reversal set changed")
    if any(record["reverses_native_rmse"] or record["refit_performed"] for record in summary["leave_one_out"]):
        errors.append("RMSE reversal or refit scope changed")
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
        raise ValueError("Roszman1 fold-4 Word manifest is stale")
    return {
        "status": "passed",
        "errorCount": 0,
        "pointCount": totals["point_count"],
        "maeReversingPointIndices": [4, 5],
        "rmseReversingPointIndices": [],
        "protocolSha256": sha256(PROTOCOL),
        "summarySha256": sha256(SUMMARY),
        "analysisRunnerSha256": sha256(ROOT / "scripts/analyze_roszman1_native_fold4_error_decomposition.py"),
        "figureSha256": sha256(FIGURE),
        "reportSha256": sha256(REPORT),
        "wordSha256": sha256(WORD),
        "wordManifestSha256": sha256(WORD_MANIFEST),
        "leaveOneOutRefitClaimed": False,
        "statisticalSignificanceClaimed": False,
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
            raise ValueError("Roszman1 fold-4 decomposition receipt is stale")
        print("OK: Roszman1 fold-4 decomposition receipt is current")
    else:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
