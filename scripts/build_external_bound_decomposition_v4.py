"""Build the preserved six-dataset external bound decomposition."""

import json
from pathlib import Path

import build_external_bound_decomposition as base

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/external-bound-decomposition-v4-protocol.json"
OUT = ROOT / "exports/external-bound-decomposition-v4.json"
FIGURE = ROOT / "papers/32_外部六组界组成/fig32_external_bound_decomposition_v4.png"


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    summary = base.analyze(PROTOCOL)
    related_scope = protocol["scope_rule"]["related_dataset_scope"]
    periodic_scope = protocol["scope_rule"]["periodic_candidate_scope"]
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
        "point_count": 761,
        "ellipsoid_available_point_count": 527,
        "ellipsoid_unavailable_point_count": 234,
        "prediction_shift_dominant_point_count": 250,
        "snapshot_residual_dominant_point_count": 277,
        "bound_identity_mismatch_count": 0,
        "undefined_zero_bound_count": 0,
    }
    for key, value in expected.items():
        if totals.get(key) != value:
            errors.append(f"Unexpected {key}: {totals.get(key)} != {value}")
    if summary["gauss1_regression"]["check_count"] != 4 or summary["gauss1_regression"]["mismatch_count"] != 0:
        errors.append("Gauss1 mechanism regression failed")
    if summary["analysis_scope"].get("chwirut1_independent_model_family_test") is not False:
        errors.append("Chwirut1 related-model-family scope was lost")
    if summary["analysis_scope"].get("enso_native_periodic_model_claimed") is not False:
        errors.append("ENSO periodic-candidate scope was lost")
    for key in ["universal_dataset_ranking_claimed", "probability_calibration_claimed", "native_physical_model_claimed", "unavailable_points_treated_as_zero"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite external bound-decomposition v4 outputs")
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
