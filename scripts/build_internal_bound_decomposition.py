"""Read-only decomposition of internal ellipsoid bounds with independent actual residuals."""

import hashlib
import json
import statistics
from pathlib import Path

from build_external_bound_decomposition import decompose_points, maximum

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/internal-bound-decomposition-protocol.json"
OUT = ROOT / "exports/internal-bound-decomposition.json"
FIGURE = ROOT / "papers/23_内部界组成/fig23_internal_bound_decomposition.png"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize_case(comparison_case, prediction_case):
    if not comparison_case["comparison_available"]:
        raise ValueError("Cannot normalize an unavailable comparison case")
    if comparison_case["dataset"] != prediction_case["dataset"] or comparison_case["fold"] != prediction_case["fold"]:
        raise ValueError("Dataset or fold mismatch")
    comparisons = comparison_case["point_comparisons"]
    predictions = prediction_case["point_bounds"]
    if len(comparisons) != len(predictions):
        raise ValueError("Comparison and prediction point counts differ")
    lookup = {(point["x"], point["observed_y"]): point for point in predictions}
    normalized = []
    for point in comparisons:
        key = (point["x"], point["observed_y"])
        if key not in lookup:
            raise ValueError(f"Missing independent prediction for {key}")
        prediction = lookup[key]
        actual = abs(point["observed_y"] - prediction["snapshot_prediction_float"])
        normalized.append({
            "x": point["x"],
            "ellipsoid_available": True,
            "actual_absolute_residual": actual,
            "ellipsoid_prediction_shift_upper_bound_float": point["ellipsoid_prediction_shift_upper_bound_float"],
            "ellipsoid_absolute_residual_upper_bound_float": point["ellipsoid_absolute_residual_upper_bound_float"],
        })
    return {"fold": comparison_case["fold"], "point_results": normalized}


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_internal_bound_decomposition":
        raise ValueError("Internal bound-decomposition protocol is not frozen")
    paths = {key: ROOT / info["file"] for key, info in protocol["inputs"].items()}
    input_hashes = {key: sha256(path) for key, path in paths.items()}
    for key, info in protocol["inputs"].items():
        if input_hashes[key] != info["sha256"]:
            raise ValueError(f"Input hash changed: {paths[key]}")
    comparison = json.loads(paths["ellipsoid_comparison"].read_text(encoding="utf-8"))
    prediction = json.loads(paths["prediction_box"].read_text(encoding="utf-8"))
    prediction_cases = {(case["dataset"], case["fold"]): case for case in prediction["cases"]}
    threshold = protocol["decomposition_rule"]["shift_dominant_threshold"]
    datasets = []
    for dataset_id in ["hahn1", "thurber", "kirby2"]:
        records = []
        mismatches = []
        folds = []
        for case in comparison["cases"]:
            if case["dataset"] != dataset_id or not case["comparison_available"]:
                continue
            normalized = normalize_case(case, prediction_cases[(dataset_id, case["fold"])])
            fold_records, fold_mismatches = decompose_points({"folds": [normalized]}, threshold)
            records.extend(fold_records)
            mismatches.extend(fold_mismatches)
            shares = [item["shift_share"] for item in fold_records if item["shift_share"] is not None]
            folds.append({"fold": case["fold"], "available_point_count": len(fold_records), "median_shift_share": statistics.median(shares) if shares else None, "maximum_residual_upper_bound": maximum(fold_records)})
        shares = [item["shift_share"] for item in records if item["shift_share"] is not None]
        datasets.append({
            "id": dataset_id,
            "ellipsoid_available_point_count": len(records),
            "prediction_shift_dominant_point_count": sum(item["dominant"] == "prediction_shift_dominant" for item in records),
            "snapshot_residual_dominant_point_count": sum(item["dominant"] == "snapshot_residual_dominant" for item in records),
            "undefined_zero_bound_count": sum(item["dominant"] == "undefined_zero_bound" for item in records),
            "median_shift_share": statistics.median(shares) if shares else None,
            "maximum_residual_upper_bound": maximum(records),
            "bound_identity_mismatch_count": len(mismatches),
            "folds": folds,
            "points": records,
        })
    totals = {
        "ellipsoid_available_point_count": sum(item["ellipsoid_available_point_count"] for item in datasets),
        "unavailable_rooted_fold_count": sum(not case["comparison_available"] for case in comparison["cases"]),
        "prediction_shift_dominant_point_count": sum(item["prediction_shift_dominant_point_count"] for item in datasets),
        "snapshot_residual_dominant_point_count": sum(item["snapshot_residual_dominant_point_count"] for item in datasets),
        "undefined_zero_bound_count": sum(item["undefined_zero_bound_count"] for item in datasets),
        "bound_identity_mismatch_count": sum(item["bound_identity_mismatch_count"] for item in datasets),
    }
    return {
        "status": "computed_internal_bound_decomposition",
        "protocol_sha256": sha256(PROTOCOL),
        "input_sha256": input_hashes,
        "analysis_scope": {"post_hoc": True, "refit": False, "retuned": False, "shift_dominant_threshold": threshold, "actual_residual_source": "independent_prediction_snapshot"},
        "datasets": datasets,
        "totals": totals,
        "decision": {
            "universal_internal_external_ranking_claimed": False,
            "probability_calibration_claimed": False,
            "native_physical_model_claimed": False,
            "rooted_folds_treated_as_zero": False,
        },
        "limitations": [
            "This is a read-only post-hoc arithmetic decomposition, not a new prospective test",
            "The two rooted unavailable folds are not converted into zero points or successful bounds",
            "Shares are not probabilities, variance decomposition or physical-mechanism attribution",
            "Internal distributions do not establish a universal internal-versus-external ranking",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    totals = summary["totals"]
    expected = {"ellipsoid_available_point_count": 369, "unavailable_rooted_fold_count": 2, "bound_identity_mismatch_count": 0, "undefined_zero_bound_count": 0}
    for key, value in expected.items():
        if totals.get(key) != value:
            errors.append(f"Unexpected {key}: {totals.get(key)} != {value}")
    if totals["prediction_shift_dominant_point_count"] + totals["snapshot_residual_dominant_point_count"] + totals["undefined_zero_bound_count"] != 369:
        errors.append("Dominance counts do not sum to 369")
    for key in ["universal_internal_external_ranking_claimed", "probability_calibration_claimed", "native_physical_model_claimed", "rooted_folds_treated_as_zero"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def render_figure(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    datasets = summary["datasets"]
    labels = [item["id"].upper() for item in datasets]
    positions = np.arange(len(datasets))
    shift_counts = [item["prediction_shift_dominant_point_count"] for item in datasets]
    actual_counts = [item["snapshot_residual_dominant_point_count"] for item in datasets]
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), constrained_layout=True)
    axes[0].bar(positions, shift_counts, color="#316c9b", label="Prediction-shift dominant")
    axes[0].bar(positions, actual_counts, bottom=shift_counts, color="#876a32", label="Snapshot-residual dominant")
    axes[0].set_xticks(positions, labels)
    axes[0].set_ylabel("Available points")
    axes[0].set_title("Internal dominance counts; two rooted folds excluded")
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].grid(axis="y", alpha=0.2)
    distributions = [[point["shift_share"] for point in item["points"] if point["shift_share"] is not None] for item in datasets]
    axes[1].boxplot(distributions, tick_labels=labels, showmeans=True)
    axes[1].axhline(0.5, color="#b44b4b", linestyle="--", linewidth=1, label="Frozen 0.5 threshold")
    axes[1].set_ylim(0, 1.02)
    axes[1].set_ylabel("Prediction shift / residual upper bound")
    axes[1].set_title("Arithmetic shares are not probability contributions")
    axes[1].grid(axis="y", alpha=0.2)
    axes[1].legend(frameon=False, fontsize=8)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite internal bound-decomposition outputs")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_figure(summary)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "totals": summary["totals"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
