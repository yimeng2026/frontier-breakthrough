"""Audit fixed local-sensitivity multiples at frozen held-out points."""

import argparse
import json
import math
from pathlib import Path

from analyze_chwirut_holdout import sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/native-sensitivity-threshold-coverage-protocol.json"
OUT = ROOT / "exports/native-sensitivity-threshold-coverage.json"
FIGURE = ROOT / "papers/50_三模型敏感度阈值覆盖/fig50_native_sensitivity_threshold_coverage.png"
LABELS = {
    "roszman1": "Roszman1 native arctangent",
    "chwirut1": "Chwirut1 native exponential",
    "enso": "ENSO native Fourier",
}


def evaluate_point(absolute_residual, local_standard_deviation, thresholds):
    if absolute_residual < 0 or local_standard_deviation < 0:
        raise ValueError("Absolute residual and local standard deviation must be nonnegative")
    ratio = absolute_residual / local_standard_deviation if local_standard_deviation > 0 else None
    covered = {
        str(threshold): bool(absolute_residual <= threshold * local_standard_deviation)
        for threshold in thresholds
    }
    return {
        "residual_to_sensitivity_ratio": ratio,
        "covered_by_threshold": covered,
        "failed_thresholds": [threshold for threshold in thresholds if not covered[str(threshold)]],
    }


def threshold_record(folds, threshold):
    point_count = sum(fold["test_count"] for fold in folds)
    covered = sum(fold["thresholds"][str(threshold)]["covered_count"] for fold in folds)
    return {
        "point_count": point_count,
        "covered_count": covered,
        "violation_count": point_count - covered,
        "zero_violation_fold_count": sum(fold["thresholds"][str(threshold)]["zero_violation"] for fold in folds),
    }


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_native_sensitivity_threshold_coverage":
        raise ValueError("Native sensitivity threshold coverage protocol is not frozen")
    thresholds = protocol["rules"]["thresholds"]
    datasets = []
    for dataset_id, info in protocol["inputs"].items():
        source_path = ROOT / info["file"]
        actual_hash = sha256(source_path)
        if actual_hash != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {dataset_id}")
        source = json.loads(source_path.read_text(encoding="utf-8"))
        if len(source["folds"]) != 5 or source["totals"]["held_out_point_count"] != info["held_out_point_count"]:
            raise ValueError(f"Frozen local-diagnostic structure changed: {dataset_id}")
        folds = []
        for case in source["folds"]:
            points = []
            for point_index, old in enumerate(case["held_out_points"], start=1):
                residual = old["residual"]
                local_sd = old["local_linearized_prediction_standard_deviation"]
                if residual is None or local_sd is None or not math.isfinite(residual) or not math.isfinite(local_sd):
                    raise ValueError(f"Missing point residual or sensitivity: {dataset_id}:{case['fold']}:{point_index}")
                absolute_residual = abs(residual)
                evaluation = evaluate_point(absolute_residual, local_sd, thresholds)
                points.append({
                    "point_index": point_index,
                    "point_id": f"{dataset_id}:{case['fold']}:{point_index}",
                    "x": old["x"],
                    "observed_y": old["observed_y"],
                    "native_prediction": old["native_prediction"],
                    "residual": residual,
                    "absolute_residual": absolute_residual,
                    "local_standard_deviation": local_sd,
                    **evaluation,
                })
            fold_thresholds = {}
            for threshold in thresholds:
                covered = sum(point["covered_by_threshold"][str(threshold)] for point in points)
                fold_thresholds[str(threshold)] = {
                    "point_count": len(points),
                    "covered_count": covered,
                    "violation_count": len(points) - covered,
                    "zero_violation": covered == len(points),
                }
            defined_ratios = [point["residual_to_sensitivity_ratio"] for point in points if point["residual_to_sensitivity_ratio"] is not None]
            folds.append({
                "fold": case["fold"],
                "fold_id": f"{dataset_id}:{case['fold']}",
                "test_count": len(points),
                "thresholds": fold_thresholds,
                "max_residual_to_sensitivity_ratio": max(defined_ratios) if defined_ratios else None,
                "max_ratio_point_index": max(points, key=lambda point: point["residual_to_sensitivity_ratio"] if point["residual_to_sensitivity_ratio"] is not None else -1)["point_index"],
                "zero_sensitivity_point_count": sum(point["local_standard_deviation"] == 0 for point in points),
                "points": points,
            })
        dataset_thresholds = {str(threshold): threshold_record(folds, threshold) for threshold in thresholds}
        scope_specific = {}
        known_answer = None
        if dataset_id == "roszman1":
            scope_specific = {"parameter_scope": "Raw arctangent parameter ranges retained separately from threshold counts"}
        elif dataset_id == "chwirut1":
            scope_specific = {
                "minimum_absolute_denominator": source["totals"]["minimum_absolute_denominator"],
                "pole_inside_observed_range_fold_count": source["totals"]["pole_inside_observed_range_fold_count"],
                "related_prior_dataset": source["analysis_scope"]["related_prior_dataset"],
            }
        elif dataset_id == "enso":
            known_answer = source["known_answer"]
            scope_specific = {
                "b4_range": source["parameter_stability"]["b4"]["range"],
                "b7_range": source["parameter_stability"]["b7"]["range"],
                "period_scope": "Threshold counts do not identify physical periods or calibrated period intervals",
            }
        datasets.append({
            "id": dataset_id,
            "label": LABELS[dataset_id],
            "source_file": info["file"],
            "source_sha256": actual_hash,
            "held_out_point_count": info["held_out_point_count"],
            "folds": folds,
            "thresholds": dataset_thresholds,
            "parameter_stability": source["parameter_stability"],
            "scope_specific": scope_specific,
            "known_answer": known_answer,
        })

    all_folds = [fold for dataset in datasets for fold in dataset["folds"]]
    total_thresholds = {str(threshold): threshold_record(all_folds, threshold) for threshold in thresholds}
    violations = {
        str(threshold): [
            point["point_id"]
            for dataset in datasets
            for fold in dataset["folds"]
            for point in fold["points"]
            if not point["covered_by_threshold"][str(threshold)]
        ]
        for threshold in thresholds
    }
    defined_points = [
        (point["residual_to_sensitivity_ratio"], point["point_id"])
        for dataset in datasets
        for fold in dataset["folds"]
        for point in fold["points"]
        if point["residual_to_sensitivity_ratio"] is not None
    ]
    max_ratio, max_ratio_id = max(defined_points, key=lambda item: item[0])
    totals = {
        "dataset_count": len(datasets),
        "fold_count": len(all_folds),
        "point_count": sum(dataset["held_out_point_count"] for dataset in datasets),
        "threshold_count": len(thresholds),
        "evaluation_count": sum(dataset["held_out_point_count"] for dataset in datasets) * len(thresholds),
        "missing_residual_count": 0,
        "missing_standard_deviation_count": 0,
        "zero_sensitivity_point_count": sum(fold["zero_sensitivity_point_count"] for fold in all_folds),
        "thresholds": total_thresholds,
        "violation_point_ids_by_threshold": violations,
        "max_residual_to_sensitivity_ratio": max_ratio,
        "max_ratio_point_id": max_ratio_id,
    }
    expected = protocol["expected_structure"]
    actual = {
        "dataset_count": totals["dataset_count"],
        "total_fold_count": totals["fold_count"],
        "total_point_count": totals["point_count"],
        "threshold_count": totals["threshold_count"],
        "total_evaluation_count": totals["evaluation_count"],
        "missing_residual_count": totals["missing_residual_count"],
        "missing_standard_deviation_count": totals["missing_standard_deviation_count"],
    }
    for key, value in actual.items():
        if value != expected[key]:
            raise ValueError(f"Frozen structural expectation failed: {key}")
    return {
        "status": "computed_native_sensitivity_threshold_coverage",
        "protocol_sha256": sha256(protocol_path),
        "analysis_scope": {
            "refit": False,
            "covariance_recomputed": False,
            "post_hoc": True,
            "all_frozen_points_retained": True,
            "thresholds_frozen_before_results": thresholds,
            "probability_coverage": False,
            "confidence_interval": False,
            "native_deterministic_bound": False,
            "cross_model_physical_score": False,
        },
        "datasets": datasets,
        "totals": totals,
        "cross_model_probability_coverage_score": None,
        "decision": {
            "probability_coverage_claimed": False,
            "confidence_interval_claimed": False,
            "threshold_optimized": False,
            "violations_hidden": False,
            "native_deterministic_bounds_claimed": False,
            "global_identifiability_claimed": False,
            "physical_endogeneity_claimed": False,
            "new_physical_periods_claimed": False,
            "independent_experiment_claimed": False,
            "cross_model_probability_score_claimed": False,
        },
        "limitations": [
            "Fixed-threshold counts are arithmetic audits, not probabilities, confidence intervals, credible intervals or expected coverage",
            "Local linearized standard deviations are not calibrated prediction errors or deterministic residual bounds",
            "Counts within and across datasets retain different response units and observation designs and have no pooled physical interpretation",
            "Chwirut1 shares its study and native model family with Chwirut2; ENSO period variation and known-answer mismatch remain separate",
            "All violations and zero-deviation cases are retained; no threshold is optimized after seeing results",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    for threshold in ["1", "2", "4"]:
        if summary.get("totals", {}).get("thresholds", {}).get(threshold, {}).get("covered_count") != expected["totals"]["thresholds"][threshold]["covered_count"]:
            errors.append(f"Coverage count mismatch at threshold {threshold}")
    for key, value in summary.get("decision", {}).items():
        if key in expected["decision"] and value != expected["decision"][key]:
            errors.append(f"Overclaim or decision-scope mismatch: {key}")
    if summary != expected:
        errors.append("Summary content differs from deterministic frozen-input recomputation")
    return errors


def render_figure(summary, output_path=FIGURE):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_path = Path(output_path)
    thresholds = [1, 2, 4]
    ids = [dataset["id"] for dataset in summary["datasets"]]
    colors = {"roszman1": "#316c9b", "chwirut1": "#4f7b5b", "enso": "#876a32"}
    fig, axes = plt.subplots(2, 2, figsize=(16.0, 12.0), constrained_layout=True)
    x = np.arange(len(ids))
    width = 0.25
    for index, threshold in enumerate(thresholds):
        values = [dataset["thresholds"][str(threshold)]["covered_count"] for dataset in summary["datasets"]]
        axes[0, 0].bar(x + (index - 1) * width, values, width=width, label=f"{threshold}× local SD")
    axes[0, 0].set_xticks(x, ids)
    axes[0, 0].set_ylabel("Covered observations (raw count)")
    axes[0, 0].set_title("A. Fixed-threshold coverage; not probability")
    axes[0, 0].legend(frameon=False)
    axes[0, 0].grid(axis="y", alpha=0.2)

    fold_ids = [fold["fold_id"] for dataset in summary["datasets"] for fold in dataset["folds"]]
    violations = np.array([
        [fold["thresholds"][str(threshold)]["violation_count"] for threshold in thresholds]
        for dataset in summary["datasets"] for fold in dataset["folds"]
    ])
    image = axes[0, 1].imshow(violations, aspect="auto", cmap="YlOrRd")
    axes[0, 1].set_xticks(range(3), ["1×", "2×", "4×"])
    axes[0, 1].set_yticks(range(len(fold_ids)), fold_ids, fontsize=8)
    axes[0, 1].set_title("B. Violation counts by fold and multiplier")
    for row in range(violations.shape[0]):
        for column in range(violations.shape[1]):
            text_color = "#ffffff" if violations[row, column] >= 20 else "#222222"
            axes[0, 1].text(column, row, str(violations[row, column]), ha="center", va="center", fontsize=7, color=text_color, fontweight="bold")
    fig.colorbar(image, ax=axes[0, 1], label="Violating points")

    for dataset in summary["datasets"]:
        folds = dataset["folds"]
        axes[1, 0].plot(
            [fold["fold"] for fold in folds],
            [fold["max_residual_to_sensitivity_ratio"] for fold in folds],
            "o-", label=dataset["id"], color=colors[dataset["id"]],
        )
    for threshold, color in [(1, "#b44b4b"), (2, "#876a32"), (4, "#4f7b5b")]:
        axes[1, 0].axhline(threshold, color=color, linestyle="--", linewidth=1, label=f"{threshold}× threshold")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_xticks([1, 2, 3, 4, 5])
    axes[1, 0].set_xlabel("Frozen fold")
    axes[1, 0].set_ylabel("Maximum |residual| / local SD (log)")
    axes[1, 0].set_title("C. Largest point ratio in each fold")
    axes[1, 0].grid(which="both", alpha=0.2)
    axes[1, 0].legend(frameon=False, fontsize=7, ncol=2)

    for index, threshold in enumerate(thresholds):
        values = [dataset["thresholds"][str(threshold)]["zero_violation_fold_count"] for dataset in summary["datasets"]]
        axes[1, 1].bar(x + (index - 1) * width, values, width=width, label=f"{threshold}× local SD")
    axes[1, 1].set_xticks(x, ids)
    axes[1, 1].set_ylim(0, 5.5)
    axes[1, 1].set_ylabel("Folds with zero violations")
    axes[1, 1].set_title("D. Complete folds remain visible beside violations")
    axes[1, 1].legend(frameon=False)
    axes[1, 1].grid(axis="y", alpha=0.2)

    fig.suptitle("Frozen local-sensitivity thresholds: 407 points, 15 folds, 1221 arithmetic evaluations", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Fixed 1×, 2× and 4× multipliers. No refit, threshold optimization, probability interval or deterministic native error bound.",
        ha="center", fontsize=9, color="#555555",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    summary = analyze()
    errors = validate_summary(summary)
    if args.check:
        if not OUT.exists():
            errors.append("Missing sensitivity threshold coverage output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored sensitivity threshold coverage output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid sensitivity threshold coverage figure")
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "points": summary["totals"]["point_count"],
        "evaluations": summary["totals"]["evaluation_count"],
        "thresholds": {key: summary["totals"]["thresholds"][key] for key in ["1", "2", "4"]},
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
