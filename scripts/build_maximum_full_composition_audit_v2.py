"""Build the preserved ten-dataset maximum/full-composition audit."""

import json
import math
from pathlib import Path

import build_maximum_full_composition_audit as base

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/maximum-full-composition-v2-protocol.json"
OUT = ROOT / "exports/maximum-full-composition-audit-v2.json"
FIGURE = ROOT / "papers/38_十组最大界与全点组成/fig38_maximum_full_composition_v2.png"


def with_frozen_protocol(action):
    saved = base.PROTOCOL
    base.PROTOCOL = PROTOCOL
    try:
        return action()
    finally:
        base.PROTOCOL = saved


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    summary = with_frozen_protocol(base.analyze)
    scope = protocol["scope_rule"]
    summary["analysis_scope"]["source_dataset_count"] = 10
    summary["analysis_scope"]["historical_nine_dataset_audit_preserved"] = True
    summary["analysis_scope"]["roszman1_native_arctangent_model_claimed"] = False
    summary["analysis_scope"]["roszman1_independent_physical_experiment"] = False
    summary["analysis_scope"]["roszman1_candidate_scope"] = scope["roszman1_candidate_scope"]
    summary["limitations"].extend([scope["roszman1_candidate_scope"], scope["historical_preservation"], scope["post_hoc_scope"]])
    summary["comparison_wrapper_sha256"] = base.sha256(Path(__file__).resolve())
    return summary


def validate_summary(summary):
    errors = with_frozen_protocol(lambda: base.validate_summary(summary))
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    expected = protocol["dataset_expectations"]["roszman1"]
    item = next((item for item in summary["datasets"] if item["id"] == "roszman1"), None)
    if item is None:
        errors.append("Missing Roszman1 extreme audit")
    else:
        for key, value in expected.items():
            actual = item.get(key)
            if isinstance(value, float):
                if not isinstance(actual, (int, float)) or not math.isclose(actual, value, rel_tol=1.0e-12, abs_tol=1.0e-15):
                    errors.append(f"Unexpected Roszman1 {key}: {actual} != {value}")
            elif actual != value:
                errors.append(f"Unexpected Roszman1 {key}: {actual} != {value}")
    for key in ["roszman1_native_arctangent_model_claimed", "roszman1_independent_physical_experiment"]:
        if summary["analysis_scope"].get(key) is not False:
            errors.append(f"Roszman1 scope was lost: {key}")
    if summary["analysis_scope"].get("historical_nine_dataset_audit_preserved") is not True:
        errors.append("Nine-dataset historical preservation was lost")
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
    totals = summary["totals"]
    fig, axes = plt.subplots(1, 3, figsize=(19, 5.8), constrained_layout=True)
    axes[0].bar(positions, [1] * len(datasets), color=colors)
    axes[0].set_xticks(positions, labels, rotation=25)
    axes[0].set_yticks([0, 1], ["Mismatch", "Match"])
    axes[0].set_ylim(0, 1.15)
    axes[0].set_title(f"Maximum-point class vs majority ({totals['maximum_matches_majority_count']}/{totals['dataset_count']} match)")
    axes[0].grid(axis="y", alpha=0.2)
    for item in datasets:
        index = labels.index(item["id"].upper())
        axes[1].plot([index, index], [item["median_shift_share"], item["maximum_shift_share"]], color="#9aa4aa", linewidth=1)
    axes[1].scatter(positions, [item["median_shift_share"] for item in datasets], marker="o", color="#316c9b", label="Median share")
    axes[1].scatter(positions, [item["maximum_shift_share"] for item in datasets], marker="D", color="#876a32", label="Maximum-bound-point share")
    axes[1].set_xticks(positions, labels, rotation=25)
    axes[1].set_ylim(0, 1.04)
    axes[1].set_title(f"Maximum-point share is not the median ({totals['maximum_share_below_median_count']} below)")
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
        raise FileExistsError("Refusing to overwrite maximum/full-composition audit v2 outputs")
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
