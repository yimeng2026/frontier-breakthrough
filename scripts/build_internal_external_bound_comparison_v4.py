"""Build the preserved nine-dataset internal/external bound comparison."""

import json
from pathlib import Path

import build_internal_external_bound_comparison as base

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/internal-external-bound-comparison-v4-protocol.json"
OUT = ROOT / "exports/internal-external-bound-comparison-v4.json"
FIGURE = ROOT / "papers/33_九组界组成对照/fig33_internal_external_bound_comparison_v4.png"


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    summary = base.analyze(PROTOCOL)
    related_scope = protocol["comparison_rule"]["related_dataset_scope"]
    periodic_scope = protocol["comparison_rule"]["periodic_candidate_scope"]
    summary["analysis_scope"]["chwirut1_independent_model_family_test"] = False
    summary["analysis_scope"]["related_dataset_scope"] = related_scope
    summary["analysis_scope"]["enso_native_periodic_model_claimed"] = False
    summary["analysis_scope"]["periodic_candidate_scope"] = periodic_scope
    summary["limitations"].extend([related_scope, periodic_scope])
    summary["comparison_wrapper_sha256"] = base.sha256(Path(__file__).resolve())
    return summary


def validate_summary(summary):
    errors = []
    totals = summary["totals"]
    expected = {
        "ellipsoid_available_point_count": 896,
        "prediction_shift_dominant_point_count": 594,
        "snapshot_residual_dominant_point_count": 302,
        "external_unavailable_point_count": 234,
        "internal_unavailable_rooted_fold_count": 2,
        "bound_identity_mismatch_count": 0,
        "undefined_zero_bound_count": 0,
    }
    for key, value in expected.items():
        if totals.get(key) != value:
            errors.append(f"Unexpected {key}: {totals.get(key)} != {value}")
    if len(summary["datasets"]) != 9:
        errors.append("Expected nine datasets")
    if sum(item["ellipsoid_available_point_count"] for item in summary["datasets"]) != 896:
        errors.append("Dataset available-point totals do not sum to 896")
    if summary["analysis_scope"].get("chwirut1_independent_model_family_test") is not False:
        errors.append("Chwirut1 related-model-family scope was lost")
    if summary["analysis_scope"].get("enso_native_periodic_model_claimed") is not False:
        errors.append("ENSO periodic-candidate scope was lost")
    for key in ["combined_success_rate_claimed", "universal_internal_external_ranking_claimed", "probability_calibration_claimed", "scope_difference_erased"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite internal/external comparison v4 outputs")
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
