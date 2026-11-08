"""Audit maximum residual-bound points against full-point compositions."""

import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/maximum-full-composition-protocol.json"
OUT = ROOT / "exports/maximum-full-composition-audit.json"
FIGURE = ROOT / "papers/34_最大界与全点组成/fig34_maximum_full_composition.png"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_maximum_full_composition_audit":
        raise ValueError("Maximum/full composition protocol is not frozen")
    source_path = ROOT / protocol["input"]["file"]
    if sha256(source_path) != protocol["input"]["sha256"]:
        raise ValueError("Maximum/full composition input hash changed")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    datasets = []
    for item in source["datasets"]:
        shares = [point["shift_share"] for point in item["points"] if point["shift_share"] is not None]
        bounds = [point["residual_upper_bound"] for point in item["points"] if point["shift_share"] is not None]
        maximum = item["maximum_residual_upper_bound"]
        if not shares or maximum is None or len(shares) != item["ellipsoid_available_point_count"]:
            raise ValueError(f"Expected defined shares for every available point: {item['id']}")
        shift_count = item["prediction_shift_dominant_point_count"]
        actual_count = item["snapshot_residual_dominant_point_count"]
        if shift_count > actual_count:
            majority = "prediction_shift_dominant"
        elif actual_count > shift_count:
            majority = "snapshot_residual_dominant"
        else:
            majority = "tie_no_single_majority"
        median_share = statistics.median(shares)
        median_bound = statistics.median(bounds)
        if median_bound <= 0:
            raise ValueError(f"Non-positive median bound: {item['id']}")
        maximum_share = maximum["shift_share"]
        maximum_bound = maximum["residual_upper_bound"]
        less_or_equal = sum(share <= maximum_share for share in shares)
        datasets.append({
            "id": item["id"],
            "scope": item["scope"],
            "available_point_count": len(shares),
            "prediction_shift_dominant_point_count": shift_count,
            "snapshot_residual_dominant_point_count": actual_count,
            "majority_dominant": majority,
            "maximum_dominant": maximum["dominant"],
            "maximum_matches_majority": maximum["dominant"] == majority if majority != "tie_no_single_majority" else None,
            "median_shift_share": median_share,
            "maximum_shift_share": maximum_share,
            "maximum_share_minus_median": maximum_share - median_share,
            "share_less_than_or_equal_maximum_count": less_or_equal,
            "maximum_share_descriptive_percentile": less_or_equal / len(shares),
            "median_residual_upper_bound": median_bound,
            "maximum_residual_upper_bound": maximum_bound,
            "bound_max_to_median_ratio": maximum_bound / median_bound,
            "maximum_point": maximum,
        })
    below = [item["id"] for item in datasets if item["maximum_shift_share"] < item["median_shift_share"]]
    above = [item["id"] for item in datasets if item["maximum_shift_share"] > item["median_shift_share"]]
    maximum_actual = [item["id"] for item in datasets if item["maximum_dominant"] == "snapshot_residual_dominant"]
    largest = max(datasets, key=lambda item: item["bound_max_to_median_ratio"])
    totals = {
        "dataset_count": len(datasets),
        "maximum_matches_majority_count": sum(item["maximum_matches_majority"] is True for item in datasets),
        "maximum_majority_mismatch_dataset_ids": [item["id"] for item in datasets if item["maximum_matches_majority"] is False],
        "maximum_prediction_shift_dominant_count": sum(item["maximum_dominant"] == "prediction_shift_dominant" for item in datasets),
        "maximum_snapshot_residual_dominant_count": len(maximum_actual),
        "maximum_snapshot_residual_dominant_dataset_ids": maximum_actual,
        "maximum_share_below_median_count": len(below),
        "maximum_share_below_median_dataset_ids": below,
        "maximum_share_above_median_dataset_ids": above,
        "largest_bound_to_median_ratio_dataset_id": largest["id"],
        "largest_bound_to_median_ratio": largest["bound_max_to_median_ratio"],
    }
    return {
        "status": "computed_maximum_full_composition_audit",
        "protocol_sha256": sha256(PROTOCOL),
        "input_sha256": sha256(source_path),
        "analysis_scope": {"post_hoc": True, "refit": False, "retuned": False, "descriptive_not_probabilistic": True},
        "datasets": datasets,
        "totals": totals,
        "decision": {
            "unified_mechanism_claimed": False,
            "probability_representativeness_claimed": False,
            "maximum_point_used_as_typical_claimed": False,
            "single_scalar_ranking_claimed": False,
        },
        "limitations": [
            "Maximum-bound points are extremes and are not typical observations",
            "Descriptive percentiles, medians and ratios are not probabilities or physical causal contributions",
            "Class agreement between a maximum point and the majority does not imply representative magnitude",
            "Unavailable points remain excluded and no universal dataset ranking is established",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = json.loads(PROTOCOL.read_text(encoding="utf-8"))["expected"]
    totals = summary["totals"]
    for key, value in expected.items():
        if key == "largest_bound_to_median_ratio":
            if not math.isclose(totals.get(key, 0), value, rel_tol=1.0e-10, abs_tol=1.0e-12):
                errors.append(f"Unexpected {key}: {totals.get(key)} != {value}")
        elif totals.get(key) != value:
            errors.append(f"Unexpected {key}: {totals.get(key)} != {value}")
    for item in summary["datasets"]:
        if not math.isclose(item["maximum_share_descriptive_percentile"], item["share_less_than_or_equal_maximum_count"] / item["available_point_count"], rel_tol=1.0e-12):
            errors.append(f"Percentile mismatch: {item['id']}")
        if not math.isclose(item["bound_max_to_median_ratio"], item["maximum_residual_upper_bound"] / item["median_residual_upper_bound"], rel_tol=1.0e-12):
            errors.append(f"Bound ratio mismatch: {item['id']}")
        if not math.isclose(item["maximum_share_minus_median"], item["maximum_shift_share"] - item["median_shift_share"], rel_tol=1.0e-12, abs_tol=1.0e-15):
            errors.append(f"Median gap mismatch: {item['id']}")
    for key in ["unified_mechanism_claimed", "probability_representativeness_claimed", "maximum_point_used_as_typical_claimed", "single_scalar_ranking_claimed"]:
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
    colors = ["#316c9b" if item["maximum_matches_majority"] else "#b44b4b" for item in datasets]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    axes[0].bar(positions, [1] * len(datasets), color=colors)
    axes[0].set_xticks(positions, labels, rotation=25)
    axes[0].set_yticks([0, 1], ["Mismatch", "Match"])
    axes[0].set_ylim(0, 1.15)
    axes[0].set_title("Maximum-point class vs majority (8/9 match)")
    axes[0].grid(axis="y", alpha=0.2)
    for item in datasets:
        x = item["id"]
        index = labels.index(x.upper())
        median = item["median_shift_share"]
        maximum = item["maximum_shift_share"]
        axes[1].plot([index, index], [median, maximum], color="#9aa4aa", linewidth=1)
    axes[1].scatter(positions, [item["median_shift_share"] for item in datasets], marker="o", color="#316c9b", label="Median share")
    axes[1].scatter(positions, [item["maximum_shift_share"] for item in datasets], marker="D", color="#876a32", label="Maximum-bound-point share")
    axes[1].set_xticks(positions, labels, rotation=25)
    axes[1].set_ylim(0, 1.04)
    axes[1].set_title("Maximum-point share is not the median (6 below)")
    axes[1].legend(frameon=False, fontsize=8, loc="lower left")
    axes[1].grid(axis="y", alpha=0.2)
    axes[2].bar(positions, [item["bound_max_to_median_ratio"] for item in datasets], color="#876a32")
    axes[2].set_yscale("log")
    axes[2].set_xticks(positions, labels, rotation=25)
    axes[2].set_ylabel("Maximum bound / median bound (log scale)")
    axes[2].set_title("Bound-width ratios remain dataset-specific")
    axes[2].grid(axis="y", which="both", alpha=0.2)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite maximum/full composition audit outputs")
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
