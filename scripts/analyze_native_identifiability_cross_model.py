"""Synthesize three frozen native local-identifiability studies without refitting."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/native-identifiability-cross-model-protocol.json"
OUT = ROOT / "exports/native-identifiability-cross-model-synthesis.json"
FIGURE = ROOT / "papers/49_三模型局部可识别性综合/fig49_native_identifiability_cross_model.png"
LABELS = {
    "roszman1": "Roszman1 native arctangent",
    "chwirut1": "Chwirut1 native exponential",
    "enso": "ENSO native Fourier",
}


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_native_identifiability_cross_model_synthesis":
        raise ValueError("Native identifiability cross-model protocol is not frozen")
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
            jacobian = case["training_jacobian"]
            sensitivity = case["held_out_prediction_sensitivity"]
            max_sd = sensitivity["max_local_standard_deviation"]
            rmse = case["test_metrics"]["rmse"]
            if max_sd is None or rmse is None or not math.isfinite(max_sd) or not math.isfinite(rmse) or max_sd < 0 or rmse <= 0:
                raise ValueError(f"Invalid sensitivity/RMSE input: {dataset_id}:{case['fold']}")
            ratio = max_sd / rmse
            folds.append({
                "fold": case["fold"],
                "fold_id": f"{dataset_id}:{case['fold']}",
                "train_count": case["train_count"],
                "test_count": case["test_count"],
                "residual_degrees_of_freedom": case["train_count"] - info["parameter_count"],
                "numerical_rank": jacobian["numerical_rank"],
                "scaled_condition_number": jacobian["scaled_condition_number"],
                "max_absolute_off_diagonal_parameter_correlation": jacobian["max_absolute_off_diagonal_parameter_correlation"],
                "max_local_prediction_standard_deviation": max_sd,
                "native_test_rmse": rmse,
                "sensitivity_to_rmse_ratio": ratio,
                "sensitivity_exceeds_rmse": ratio > 1,
                "sensitivity_equals_rmse": ratio == 1,
                "local_covariance_valid": jacobian["local_covariance_valid"],
            })
        conditions = [fold["scaled_condition_number"] for fold in folds]
        correlations = [fold["max_absolute_off_diagonal_parameter_correlation"] for fold in folds]
        ratios = [fold["sensitivity_to_rmse_ratio"] for fold in folds]
        summary = {
            "min_scaled_condition_number": min(conditions),
            "median_scaled_condition_number": float(np.median(conditions)),
            "max_scaled_condition_number": max(conditions),
            "median_fold_max_parameter_correlation": float(np.median(correlations)),
            "max_absolute_off_diagonal_parameter_correlation": max(correlations),
            "min_sensitivity_to_rmse_ratio": min(ratios),
            "median_sensitivity_to_rmse_ratio": float(np.median(ratios)),
            "max_sensitivity_to_rmse_ratio": max(ratios),
            "max_local_prediction_standard_deviation": source["totals"]["max_local_prediction_standard_deviation"],
            "native_test_rmse_minimum": source["totals"]["native_test_rmse_minimum"],
            "native_test_rmse_maximum": source["totals"]["native_test_rmse_maximum"],
            "full_numerical_rank_fold_count": sum(fold["numerical_rank"] == info["parameter_count"] for fold in folds),
            "local_diagnostic_failure_count": sum(not fold["local_covariance_valid"] for fold in folds),
            "sensitivity_exceeds_rmse_fold_count": sum(fold["sensitivity_exceeds_rmse"] for fold in folds),
        }
        scope_specific = {}
        known_answer = None
        if dataset_id == "roszman1":
            scope_specific = {
                "max_condition_fold_id": max(folds, key=lambda fold: fold["scaled_condition_number"])["fold_id"],
                "max_sensitivity_ratio_fold_id": max(folds, key=lambda fold: fold["sensitivity_to_rmse_ratio"])["fold_id"],
                "parameter_scope": "Raw arctangent parameter ranges are preserved; stable RMSE does not imply parameter uniqueness",
            }
        elif dataset_id == "chwirut1":
            scope_specific = {
                "minimum_absolute_denominator": source["totals"]["minimum_absolute_denominator"],
                "pole_inside_observed_range_fold_count": source["totals"]["pole_inside_observed_range_fold_count"],
                "fold1_b2_absolute_relative_standard_error": source["folds"][0]["training_jacobian"]["parameters"][1]["absolute_relative_standard_error"],
                "fold1_native_test_rmse": source["folds"][0]["test_metrics"]["rmse"],
                "related_prior_dataset": source["analysis_scope"]["related_prior_dataset"],
            }
        elif dataset_id == "enso":
            scope_specific = {
                "fold4_b4_absolute_relative_standard_error": source["folds"][3]["training_jacobian"]["parameters"][3]["absolute_relative_standard_error"],
                "fold4_b7_absolute_relative_standard_error": source["folds"][3]["training_jacobian"]["parameters"][6]["absolute_relative_standard_error"],
                "fold4_native_test_rmse": source["folds"][3]["test_metrics"]["rmse"],
                "max_cross_harmonic_block_absolute_correlation": source["totals"]["max_cross_harmonic_block_absolute_correlation"],
                "max_annual_long_block_absolute_correlation": source["totals"]["max_annual_long_block_absolute_correlation"],
                "max_b4_own_amplitude_absolute_correlation": source["totals"]["max_b4_own_amplitude_absolute_correlation"],
                "max_b7_own_amplitude_absolute_correlation": source["totals"]["max_b7_own_amplitude_absolute_correlation"],
            }
            known_answer = source["known_answer"]
        datasets.append({
            "id": dataset_id,
            "label": LABELS[dataset_id],
            "source_file": info["file"],
            "source_sha256": actual_hash,
            "parameter_count": info["parameter_count"],
            "held_out_point_count": info["held_out_point_count"],
            "folds": folds,
            "summary": summary,
            "parameter_stability": source["parameter_stability"],
            "scope_specific": scope_specific,
            "known_answer": known_answer,
        })

    folds = [fold for dataset in datasets for fold in dataset["folds"]]
    totals = {
        "dataset_count": len(datasets),
        "fold_count": len(folds),
        "held_out_point_count": sum(dataset["held_out_point_count"] for dataset in datasets),
        "full_numerical_rank_fold_count": sum(dataset["summary"]["full_numerical_rank_fold_count"] for dataset in datasets),
        "local_diagnostic_failure_count": sum(dataset["summary"]["local_diagnostic_failure_count"] for dataset in datasets),
        "sensitivity_exceeds_rmse_fold_count": sum(fold["sensitivity_exceeds_rmse"] for fold in folds),
        "sensitivity_exceeds_rmse_fold_ids": [fold["fold_id"] for fold in folds if fold["sensitivity_exceeds_rmse"]],
        "sensitivity_equals_rmse_fold_ids": [fold["fold_id"] for fold in folds if fold["sensitivity_equals_rmse"]],
        "max_sensitivity_to_rmse_ratio": max(fold["sensitivity_to_rmse_ratio"] for fold in folds),
        "max_sensitivity_to_rmse_ratio_fold_id": max(folds, key=lambda fold: fold["sensitivity_to_rmse_ratio"])["fold_id"],
    }
    expected = protocol["expected_structure"]
    actual = {
        "dataset_count": totals["dataset_count"],
        "total_fold_count": totals["fold_count"],
        "total_held_out_point_count": totals["held_out_point_count"],
        "parameter_counts": [dataset["parameter_count"] for dataset in datasets],
        "full_numerical_rank_fold_count": totals["full_numerical_rank_fold_count"],
        "local_diagnostic_failure_count": totals["local_diagnostic_failure_count"],
    }
    for key, value in actual.items():
        if value != expected[key]:
            raise ValueError(f"Frozen structural expectation failed: {key}")
    return {
        "status": "computed_native_identifiability_cross_model_synthesis",
        "protocol_sha256": sha256(protocol_path),
        "analysis_scope": {
            "refit": False,
            "retuned": False,
            "covariance_recomputed": False,
            "post_hoc": True,
            "all_frozen_folds_retained": True,
            "cross_model_error_pooling": False,
            "cross_model_parameter_pooling": False,
            "condition_number_used_as_quality_score": False,
            "global_identifiability": False,
            "calibrated_coverage": False,
        },
        "datasets": datasets,
        "totals": totals,
        "cross_model_pooled_error_metrics": None,
        "cross_model_stability_score": None,
        "decision": {
            "universal_stability_score_claimed": False,
            "condition_number_quality_ranking_claimed": False,
            "global_identifiability_claimed": False,
            "physical_endogeneity_claimed": False,
            "calibrated_coverage_claimed": False,
            "cross_model_pooled_metric_claimed": False,
            "new_physical_periods_claimed": False,
            "independent_experiment_claimed": False,
            "independent_model_family_replication_claimed": False,
            "rational_bounds_transferred_to_native": False,
            "failed_folds_hidden": False,
        },
        "limitations": [
            "Fifteen folds are three groups of related diagnostics, not independent probability samples or a universal model-quality ranking",
            "Condition numbers depend on parameterization, design and scaling and cannot be compared as a single physical stability score",
            "Sensitivity/RMSE ratios are descriptive dimensionless comparisons, not calibrated coverage or error probabilities",
            "Raw parameter ranges, covariance matrices and residual errors retain their native units and are never pooled across models",
            "Chwirut1 shares its study and native model family with Chwirut2; ENSO optimizer mismatch remains separate from certified forward evaluation",
            "Local full rank and finite covariance do not prove global identifiability, physical endogeneity, new periods or native deterministic bounds",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    actual_ratios = [fold.get("sensitivity_to_rmse_ratio") for dataset in summary.get("datasets", []) for fold in dataset.get("folds", [])]
    expected_ratios = [fold["sensitivity_to_rmse_ratio"] for dataset in expected["datasets"] for fold in dataset["folds"]]
    if len(actual_ratios) != len(expected_ratios) or any(
        actual is None or not math.isclose(actual, wanted, rel_tol=1.0e-12, abs_tol=1.0e-12)
        for actual, wanted in zip(actual_ratios, expected_ratios)
    ):
        errors.append("Sensitivity/RMSE ratio mismatch")
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

    output_path = Path(output_path)
    colors = {"roszman1": "#316c9b", "chwirut1": "#4f7b5b", "enso": "#876a32"}
    fig, axes = plt.subplots(2, 2, figsize=(15.5, 10.5), constrained_layout=True)
    for dataset in summary["datasets"]:
        folds = dataset["folds"]
        numbers = [fold["fold"] for fold in folds]
        color = colors[dataset["id"]]
        axes[0, 0].plot(numbers, [fold["scaled_condition_number"] for fold in folds], "o-", color=color, label=dataset["id"])
        axes[0, 1].plot(numbers, [fold["sensitivity_to_rmse_ratio"] for fold in folds], "o-", color=color, label=dataset["id"])
        axes[1, 0].plot(numbers, [fold["max_absolute_off_diagonal_parameter_correlation"] for fold in folds], "o-", color=color, label=dataset["id"])
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks([1, 2, 3, 4, 5])
    axes[0, 0].set_xlabel("Frozen fold")
    axes[0, 0].set_ylabel("Scaled Jacobian condition number (log)")
    axes[0, 0].set_title("A. Local conditioning; not a model-quality score")
    axes[0, 0].grid(which="both", alpha=0.2)
    axes[0, 0].legend(frameon=False, fontsize=8)

    axes[0, 1].axhline(1.0, color="#b44b4b", linestyle="--", linewidth=1, label="sensitivity = RMSE")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_xticks([1, 2, 3, 4, 5])
    axes[0, 1].set_xlabel("Frozen fold")
    axes[0, 1].set_ylabel("Max local prediction SD / actual RMSE (log)")
    axes[0, 1].set_title("B. Three folds above 1; not calibrated coverage")
    axes[0, 1].grid(which="both", alpha=0.2)
    axes[0, 1].legend(frameon=False, fontsize=8)
    for dataset in summary["datasets"]:
        for fold in dataset["folds"]:
            if fold["sensitivity_exceeds_rmse"]:
                alignment = {"xytext": (-6, 6), "ha": "right"} if fold["fold"] == 5 else {"xytext": (6, 6), "ha": "left"}
                axes[0, 1].annotate(fold["fold_id"], (fold["fold"], fold["sensitivity_to_rmse_ratio"]), textcoords="offset points", fontsize=8, **alignment)

    axes[1, 0].set_ylim(0, 1.05)
    axes[1, 0].set_xticks([1, 2, 3, 4, 5])
    axes[1, 0].set_xlabel("Frozen fold")
    axes[1, 0].set_ylabel("Max |off-diagonal correlation|")
    axes[1, 0].set_title("C. Local parameter compensation by model")
    axes[1, 0].grid(alpha=0.2)
    axes[1, 0].legend(frameon=False, fontsize=8)

    ids = [dataset["id"] for dataset in summary["datasets"]]
    points = [dataset["held_out_point_count"] for dataset in summary["datasets"]]
    parameters = [dataset["parameter_count"] for dataset in summary["datasets"]]
    bars = axes[1, 1].bar(ids, points, color=[colors[dataset_id] for dataset_id in ids], width=0.55)
    for bar, point_count, parameter_count in zip(bars, points, parameters):
        axes[1, 1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 4, f"{point_count} points\n{parameter_count} parameters", ha="center", va="bottom", fontsize=9)
    axes[1, 1].set_ylim(0, max(points) * 1.22)
    axes[1, 1].set_ylabel("Held-out observations (inventory only)")
    axes[1, 1].set_title("D. Different designs and parameterizations; no error pooling")
    axes[1, 1].grid(axis="y", alpha=0.2)

    fig.suptitle("Frozen native local-identifiability synthesis: 3 models, 15 folds, 407 observations", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Read-only synthesis. No refit, covariance recomputation, pooled error metric, calibrated coverage or universal stability score.",
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
            errors.append("Missing cross-model identifiability synthesis")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored cross-model identifiability synthesis is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid cross-model identifiability figure")
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "datasets": summary["totals"]["dataset_count"],
        "folds": summary["totals"]["fold_count"],
        "points": summary["totals"]["held_out_point_count"],
        "sensitivity_exceeds_rmse_folds": summary["totals"]["sensitivity_exceeds_rmse_fold_ids"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
