"""Build the preserved seven-dataset internal/external bound comparison."""

import json
from pathlib import Path

import build_internal_external_bound_comparison as base

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/internal-external-bound-comparison-v2-protocol.json"
OUT = ROOT / "exports/internal-external-bound-comparison-v2.json"
FIGURE = ROOT / "papers/27_七组界组成对照/fig27_internal_external_bound_comparison_v2.png"


def analyze():
    summary = base.analyze(PROTOCOL)
    summary["comparison_wrapper_sha256"] = base.sha256(Path(__file__).resolve())
    return summary


def validate_summary(summary):
    errors = []
    totals = summary["totals"]
    expected = {
        "ellipsoid_available_point_count": 678,
        "prediction_shift_dominant_point_count": 486,
        "snapshot_residual_dominant_point_count": 192,
        "external_unavailable_point_count": 70,
        "internal_unavailable_rooted_fold_count": 2,
        "bound_identity_mismatch_count": 0,
        "undefined_zero_bound_count": 0,
    }
    for key, value in expected.items():
        if totals.get(key) != value:
            errors.append(f"Unexpected {key}: {totals.get(key)} != {value}")
    if len(summary["datasets"]) != 7:
        errors.append("Expected seven datasets")
    if sum(item["ellipsoid_available_point_count"] for item in summary["datasets"]) != 678:
        errors.append("Dataset available-point totals do not sum to 678")
    for key in ["combined_success_rate_claimed", "universal_internal_external_ranking_claimed", "probability_calibration_claimed", "scope_difference_erased"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite internal/external comparison v2 outputs")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    previous = base.FIGURE
    base.FIGURE = FIGURE
    try:
        base.render_figure(summary)
    finally:
        base.FIGURE = previous
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "totals": summary["totals"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
