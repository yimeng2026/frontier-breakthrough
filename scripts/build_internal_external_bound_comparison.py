"""Compare frozen internal and external same-point bound decompositions."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/internal-external-bound-comparison-protocol.json"
OUT = ROOT / "exports/internal-external-bound-comparison.json"
FIGURE = ROOT / "papers/24_内外部界组成对照/fig24_internal_external_bound_comparison.png"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_internal_external_bound_comparison":
        raise ValueError("Internal/external comparison protocol is not frozen")
    sources = {}
    input_hashes = {}
    for scope in ["internal", "external"]:
        info = protocol["inputs"][scope]
        path = ROOT / info["file"]
        input_hashes[scope] = sha256(path)
        if input_hashes[scope] != info["sha256"]:
            raise ValueError(f"Input hash changed: {path}")
        sources[scope] = json.loads(path.read_text(encoding="utf-8"))
        totals = sources[scope]["totals"]
        if totals["bound_identity_mismatch_count"] or totals["undefined_zero_bound_count"]:
            raise ValueError(f"Source consistency failure in {scope}")
    if sources["internal"]["totals"]["ellipsoid_available_point_count"] != 369 or sources["external"]["totals"]["ellipsoid_available_point_count"] != 305:
        raise ValueError("Unexpected available point counts")
    datasets = []
    for scope in ["internal", "external"]:
        for item in sources[scope]["datasets"]:
            datasets.append({
                "id": item["id"],
                "scope": scope,
                "ellipsoid_available_point_count": item["ellipsoid_available_point_count"],
                "prediction_shift_dominant_point_count": item["prediction_shift_dominant_point_count"],
                "snapshot_residual_dominant_point_count": item["snapshot_residual_dominant_point_count"],
                "undefined_zero_bound_count": item["undefined_zero_bound_count"],
                "median_shift_share": item["median_shift_share"],
                "maximum_residual_upper_bound": item["maximum_residual_upper_bound"],
                "points": item["points"],
            })
    internal_totals = sources["internal"]["totals"]
    external_totals = sources["external"]["totals"]
    totals = {
        "ellipsoid_available_point_count": internal_totals["ellipsoid_available_point_count"] + external_totals["ellipsoid_available_point_count"],
        "prediction_shift_dominant_point_count": internal_totals["prediction_shift_dominant_point_count"] + external_totals["prediction_shift_dominant_point_count"],
        "snapshot_residual_dominant_point_count": internal_totals["snapshot_residual_dominant_point_count"] + external_totals["snapshot_residual_dominant_point_count"],
        "undefined_zero_bound_count": 0,
        "bound_identity_mismatch_count": 0,
        "external_unavailable_point_count": external_totals["ellipsoid_unavailable_point_count"],
        "internal_unavailable_rooted_fold_count": internal_totals["unavailable_rooted_fold_count"],
    }
    return {
        "status": "computed_internal_external_bound_comparison",
        "protocol_sha256": sha256(PROTOCOL),
        "input_sha256": input_hashes,
        "analysis_scope": {
            "post_hoc": True,
            "refit": False,
            "retuned": False,
            "internal_available_point_count": 369,
            "external_available_point_count": 305,
            "external_total_point_count": external_totals["point_count"],
            "shift_dominant_threshold": 0.5,
        },
        "datasets": datasets,
        "totals": totals,
        "decision": {
            "combined_success_rate_claimed": False,
            "universal_internal_external_ranking_claimed": False,
            "probability_calibration_claimed": False,
            "scope_difference_erased": False,
        },
        "limitations": [
            "The 674 available points are descriptive and not a universal sample or probability estimate",
            "Two internal rooted unavailable folds and 60 external unavailable points remain separate",
            "Arithmetic shares are not probabilities, variance decomposition or physical-mechanism attribution",
            "No universal internal-versus-external ranking or combined success rate is established",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    totals = summary["totals"]
    expected = {
        "ellipsoid_available_point_count": 674,
        "prediction_shift_dominant_point_count": 482,
        "snapshot_residual_dominant_point_count": 192,
        "external_unavailable_point_count": 60,
        "internal_unavailable_rooted_fold_count": 2,
        "bound_identity_mismatch_count": 0,
        "undefined_zero_bound_count": 0,
    }
    for key, value in expected.items():
        if totals.get(key) != value:
            errors.append(f"Unexpected {key}: {totals.get(key)} != {value}")
    if sum(item["ellipsoid_available_point_count"] for item in summary["datasets"]) != 674:
        errors.append("Dataset available-point totals do not sum to 674")
    for key in ["combined_success_rate_claimed", "universal_internal_external_ranking_claimed", "probability_calibration_claimed", "scope_difference_erased"]:
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
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.6), constrained_layout=True)
    for axis in axes:
        axis.axvline(2.5, color="#888888", linestyle=":", linewidth=1)
    axes[0].bar(positions, shift_counts, color="#316c9b", label="Prediction-shift dominant")
    axes[0].bar(positions, actual_counts, bottom=shift_counts, color="#876a32", label="Snapshot-residual dominant")
    axes[0].set_xticks(positions, labels, rotation=15)
    axes[0].set_ylabel("Available points")
    axes[0].set_title("Internal (left of divider) vs external bound composition")
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].grid(axis="y", alpha=0.2)
    distributions = [[point["shift_share"] for point in item["points"] if point["shift_share"] is not None] for item in datasets]
    axes[1].boxplot(distributions, tick_labels=labels, showmeans=True)
    axes[1].axhline(0.5, color="#b44b4b", linestyle="--", linewidth=1, label="Frozen 0.5 threshold")
    axes[1].set_ylim(0, 1.02)
    axes[1].set_ylabel("Prediction shift / residual upper bound")
    axes[1].set_title("Six distributions; arithmetic shares are not probabilities")
    axes[1].tick_params(axis="x", rotation=15)
    axes[1].grid(axis="y", alpha=0.2)
    axes[1].legend(frameon=False, fontsize=8)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite internal/external comparison outputs")
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
