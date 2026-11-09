"""Synthesize three frozen native/rational holdout studies without refitting."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import error_metrics, sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/native-cross-dataset-synthesis-protocol.json"
OUT = ROOT / "exports/native-cross-dataset-synthesis.json"
FIGURE = ROOT / "papers/45_三数据原生同折综合/fig45_native_cross_dataset_synthesis.png"
LABELS = {
    "roszman1": "Roszman1 native arctangent",
    "enso": "ENSO native Fourier",
    "chwirut1": "Chwirut1 native exponential",
}
METRICS = ["rmse", "mae", "max_absolute_residual"]


def direction(native_value, rational_value):
    if native_value < rational_value:
        return "native"
    if rational_value < native_value:
        return "rational"
    return "tie"


def point_outcomes(points):
    counts = {"native": 0, "rational": 0, "tie": 0}
    for point in points:
        native_prediction = point["native_prediction"]
        rational_prediction = point["rational_snapshot_prediction"]
        if native_prediction is None or rational_prediction is None:
            raise ValueError("Missing paired point predictions cannot be discarded")
        native_residual = abs(point["observed_y"] - native_prediction)
        rational_residual = abs(point["observed_y"] - rational_prediction)
        if not math.isfinite(native_residual) or not math.isfinite(rational_residual):
            raise ValueError("Non-finite paired point residual")
        if not math.isclose(native_residual, point["native_absolute_residual"], rel_tol=1.0e-12, abs_tol=1.0e-12):
            raise ValueError("Stored native absolute residual does not match its prediction")
        if not math.isclose(rational_residual, point["rational_absolute_residual"], rel_tol=1.0e-12, abs_tol=1.0e-12):
            raise ValueError("Stored rational absolute residual does not match its prediction")
        counts[direction(native_residual, rational_residual)] += 1
    return counts


def pooled_metrics(source):
    observed = np.array([
        point["observed_y"]
        for fold in source["folds"]
        for point in fold["point_results"]
    ], dtype=float)
    native = np.array([
        point["native_prediction"]
        for fold in source["folds"]
        for point in fold["point_results"]
    ], dtype=float)
    rational = np.array([
        point["rational_snapshot_prediction"]
        for fold in source["folds"]
        for point in fold["point_results"]
    ], dtype=float)
    if not np.all(np.isfinite(native)) or not np.all(np.isfinite(rational)):
        raise ValueError("Pooled metrics require complete finite paired predictions")
    return {
        "native": error_metrics(observed, native),
        "rational": error_metrics(observed, rational),
    }


def pooled_mismatch_count(source, recomputed):
    mismatches = 0
    for model in ["native", "rational"]:
        frozen_model = "rational_candidate" if model == "rational" else "native"
        for metric in METRICS:
            if not math.isclose(
                recomputed[model][metric],
                source["pooled"][frozen_model][metric],
                rel_tol=1.0e-11,
                abs_tol=1.0e-12,
            ):
                mismatches += 1
    return mismatches


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_native_cross_dataset_synthesis":
        raise ValueError("Native cross-dataset synthesis protocol is not frozen")

    datasets = []
    for dataset_id, info in protocol["inputs"].items():
        source_path = ROOT / info["file"]
        actual_hash = sha256(source_path)
        if actual_hash != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {dataset_id}")
        source = json.loads(source_path.read_text(encoding="utf-8"))
        if len(source["folds"]) != info["fold_count"] or source["totals"]["point_count"] != info["point_count"]:
            raise ValueError(f"Frozen input structure changed: {dataset_id}")

        fold_records = []
        dataset_point_counts = {"native": 0, "rational": 0, "tie": 0}
        for fold in source["folds"]:
            if not fold["optimizer_success"] or not fold["test_predictions_finite"]:
                raise ValueError(f"This paired synthesis requires successful finite predictions: {dataset_id}:{fold['fold']}")
            native_metrics = fold["native_test_metrics"]
            rational_metrics = fold["rational_candidate_test_metrics"]
            cubic_metrics = fold["cubic_baseline_test_metrics"]
            if any(
                native_metrics[metric] is None or rational_metrics[metric] is None
                or not math.isfinite(native_metrics[metric]) or not math.isfinite(rational_metrics[metric])
                for metric in METRICS
            ):
                raise ValueError(f"Missing paired fold metric: {dataset_id}:{fold['fold']}")
            if native_metrics["rmse"] <= 0 or rational_metrics["rmse"] <= 0:
                raise ValueError(f"RMSE ratio requires positive values: {dataset_id}:{fold['fold']}")

            metric_directions = {
                metric: direction(native_metrics[metric], rational_metrics[metric])
                for metric in METRICS
            }
            counts = point_outcomes(fold["point_results"])
            for key in counts:
                dataset_point_counts[key] += counts[key]
            majority = "native" if counts["native"] > counts["rational"] else "rational" if counts["rational"] > counts["native"] else "tie"
            rmse_values = {
                "native": native_metrics["rmse"],
                "rational": rational_metrics["rmse"],
                "cubic": cubic_metrics["rmse"],
            }
            if any(value is None or not math.isfinite(value) for value in rmse_values.values()):
                raise ValueError(f"Missing overall fold-winner input: {dataset_id}:{fold['fold']}")
            best_value = min(rmse_values.values())
            winners = [model for model, value in rmse_values.items() if value == best_value]
            overall_winner = winners[0] if len(winners) == 1 else "tie"
            fold_records.append({
                "fold": fold["fold"],
                "fold_id": f"{dataset_id}:{fold['fold']}",
                "point_count": len(fold["point_results"]),
                "native_rmse": native_metrics["rmse"],
                "rational_rmse": rational_metrics["rmse"],
                "cubic_rmse": cubic_metrics["rmse"],
                "native_to_rational_rmse_ratio": native_metrics["rmse"] / rational_metrics["rmse"],
                "native_better_than_rational": metric_directions["rmse"] == "native",
                "native_better_than_cubic": direction(native_metrics["rmse"], cubic_metrics["rmse"]) == "native",
                "overall_winner": overall_winner,
                "native_vs_rational_direction": metric_directions,
                "metric_direction_disagreement": (
                    metric_directions["rmse"] != metric_directions["mae"]
                    or metric_directions["rmse"] != metric_directions["max_absolute_residual"]
                ),
                "point_outcomes": counts,
                "point_majority_winner": majority,
                "point_fold_disagreement": majority != "tie" and majority != metric_directions["rmse"],
            })

        ratios = [fold["native_to_rational_rmse_ratio"] for fold in fold_records]
        recomputed = pooled_metrics(source)
        mismatch_count = pooled_mismatch_count(source, recomputed)
        overall_counts = {model: sum(fold["overall_winner"] == model for fold in fold_records) for model in ["native", "rational", "cubic", "tie"]}
        dataset = {
            "id": dataset_id,
            "label": LABELS[dataset_id],
            "source_file": info["file"],
            "source_sha256": actual_hash,
            "folds": fold_records,
            "ratio_summary": {
                "minimum": min(ratios),
                "median": float(np.median(ratios)),
                "maximum": max(ratios),
                "scope": "Five within-dataset fold ratios; descriptive and not independent samples",
            },
            "point_outcomes": dataset_point_counts,
            "pooled": {
                **recomputed,
                "cubic": None,
                "frozen_metric_mismatch_count": mismatch_count,
                "scope": source["pooled"]["scope"],
            },
            "totals": {
                "fold_count": len(fold_records),
                "point_count": sum(fold["point_count"] for fold in fold_records),
                "native_optimizer_failure_count": source["totals"]["native_optimizer_failure_count"],
                "native_better_than_rational_fold_count": sum(fold["native_better_than_rational"] for fold in fold_records),
                "rational_better_than_native_fold_count": sum(fold["native_vs_rational_direction"]["rmse"] == "rational" for fold in fold_records),
                "native_better_than_cubic_fold_count": sum(fold["native_better_than_cubic"] for fold in fold_records),
                "cubic_better_than_native_fold_count": sum(fold["native_rmse"] > fold["cubic_rmse"] for fold in fold_records),
                "overall_best_model_fold_counts": overall_counts,
                "metric_direction_disagreement_count": sum(fold["metric_direction_disagreement"] for fold in fold_records),
                "point_fold_disagreement_count": sum(fold["point_fold_disagreement"] for fold in fold_records),
            },
            "known_answer": {
                "optimizer_within_certified_tolerances": source["known_answer"]["within_certified_tolerances"],
                "certified_forward_rss_check_passed": source["known_answer"].get("certified_forward_rss_check_passed"),
                "evidence_class": source["known_answer"]["evidence_class"],
                "original_tolerances_relaxed": source["known_answer"].get("original_tolerances_relaxed", False),
            },
            "analysis_scope": source["analysis_scope"],
        }
        datasets.append(dataset)

    folds = [fold for dataset in datasets for fold in dataset["folds"]]
    total_point_outcomes = {
        key: sum(dataset["point_outcomes"][key] for dataset in datasets)
        for key in ["native", "rational", "tie"]
    }
    overall_counts = {
        model: sum(fold["overall_winner"] == model for fold in folds)
        for model in ["native", "rational", "cubic", "tie"]
    }
    optimizer_pass = [dataset["id"] for dataset in datasets if dataset["known_answer"]["optimizer_within_certified_tolerances"]]
    forward_only = [
        dataset["id"] for dataset in datasets
        if not dataset["known_answer"]["optimizer_within_certified_tolerances"]
        and dataset["known_answer"]["certified_forward_rss_check_passed"] is True
    ]
    totals = {
        "dataset_count": len(datasets),
        "fold_count": len(folds),
        "point_count": sum(fold["point_count"] for fold in folds),
        "native_optimizer_failure_count": sum(dataset["totals"]["native_optimizer_failure_count"] for dataset in datasets),
        "missing_point_prediction_count": 0,
        "native_better_than_rational_fold_count": sum(fold["native_better_than_rational"] for fold in folds),
        "rational_better_than_native_fold_count": sum(fold["native_vs_rational_direction"]["rmse"] == "rational" for fold in folds),
        "native_rational_tie_fold_count": sum(fold["native_vs_rational_direction"]["rmse"] == "tie" for fold in folds),
        "native_better_than_cubic_fold_count": sum(fold["native_better_than_cubic"] for fold in folds),
        "cubic_better_than_native_fold_count": sum(fold["native_rmse"] > fold["cubic_rmse"] for fold in folds),
        "overall_best_model_fold_counts": overall_counts,
        "native_rational_sweep_dataset_count": sum(dataset["totals"]["rational_better_than_native_fold_count"] == 0 for dataset in datasets),
        "native_cubic_sweep_dataset_count": sum(dataset["totals"]["cubic_better_than_native_fold_count"] == 0 for dataset in datasets),
        "native_overall_sweep_dataset_count": sum(dataset["totals"]["overall_best_model_fold_counts"]["native"] == 5 for dataset in datasets),
        "rational_beats_native_fold_ids": [fold["fold_id"] for fold in folds if fold["native_vs_rational_direction"]["rmse"] == "rational"],
        "cubic_beats_native_fold_ids": [fold["fold_id"] for fold in folds if fold["native_rmse"] > fold["cubic_rmse"]],
        "metric_direction_disagreement_fold_ids": [fold["fold_id"] for fold in folds if fold["metric_direction_disagreement"]],
        "point_fold_disagreement_fold_ids": [fold["fold_id"] for fold in folds if fold["point_fold_disagreement"]],
        "point_outcomes": total_point_outcomes,
        "pooled_metric_mismatch_count": sum(dataset["pooled"]["frozen_metric_mismatch_count"] for dataset in datasets),
        "optimizer_known_answer_pass_dataset_ids": optimizer_pass,
        "optimizer_miss_but_certified_forward_pass_dataset_ids": forward_only,
    }
    expected = protocol["expected_structure"]
    structural_actual = {
        "dataset_count": totals["dataset_count"],
        "total_fold_count": totals["fold_count"],
        "total_point_count": totals["point_count"],
        "native_optimizer_failure_count": totals["native_optimizer_failure_count"],
        "missing_native_or_rational_point_prediction_count": totals["missing_point_prediction_count"],
    }
    for key, value in structural_actual.items():
        if value != expected[key]:
            raise ValueError(f"Frozen structural expectation failed: {key}")

    return {
        "status": "computed_native_cross_dataset_synthesis",
        "protocol_sha256": sha256(protocol_path),
        "analysis_scope": {
            "refit": False,
            "retuned": False,
            "new_data": False,
            "post_hoc": True,
            "same_frozen_points": True,
            "cross_dataset_error_pooling": False,
            "descriptive_counts_are_probabilities": False,
            "known_answer_used_as_holdout": False,
            "native_deterministic_bounds_computed": False,
            "rational_bounds_transferred_to_native": False,
        },
        "datasets": datasets,
        "totals": totals,
        "cross_dataset_pooled_error_metrics": None,
        "decision": {
            "native_always_beats_rational": False,
            "native_always_beats_cubic": False,
            "native_deterministic_bounds_claimed": False,
            "rational_bounds_transferred_to_native": False,
            "probability_calibration_claimed": False,
            "independent_experiment_claimed": False,
            "independent_model_family_replication_claimed": False,
            "new_physical_mechanism_claimed": False,
            "universal_model_ranking_claimed": False,
            "cross_dataset_pooled_metric_claimed": False,
            "descriptive_probability_claimed": False,
            "failed_or_disagreeing_folds_hidden": False,
        },
        "limitations": [
            "Three datasets and fifteen folds are a descriptive post-hoc sample, not independent probability draws",
            "Raw residuals and parameter values have different units and observation designs and are never pooled across datasets",
            "Fold RMSE, unweighted pointwise winners, MAE and maximum residual answer different questions and may disagree",
            "Chwirut1 shares its study and native model family with Chwirut2 and is not an independent model-family replication",
            "ENSO optimizer known-answer mismatch remains separate from certified-parameter forward evaluation and holdout evidence",
            "No native deterministic error bound or probability interval is produced and no rational certificate is transferred",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    if summary.get("totals", {}).get("native_better_than_rational_fold_count") != expected["totals"]["native_better_than_rational_fold_count"]:
        errors.append("Fold-win count mismatch")
    actual_ratios = [
        fold.get("native_to_rational_rmse_ratio")
        for dataset in summary.get("datasets", [])
        for fold in dataset.get("folds", [])
    ]
    expected_ratios = [
        fold["native_to_rational_rmse_ratio"]
        for dataset in expected["datasets"]
        for fold in dataset["folds"]
    ]
    if len(actual_ratios) != len(expected_ratios) or any(
        actual is None or not math.isclose(actual, wanted, rel_tol=1.0e-12, abs_tol=1.0e-12)
        for actual, wanted in zip(actual_ratios, expected_ratios)
    ):
        errors.append("Ratio mismatch")
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
    colors = {"roszman1": "#316c9b", "enso": "#876a32", "chwirut1": "#4f7b5b"}
    fig, axes = plt.subplots(2, 2, figsize=(15.5, 10.5), constrained_layout=True)
    for dataset in summary["datasets"]:
        folds = dataset["folds"]
        axes[0, 0].plot(
            [fold["fold"] for fold in folds],
            [fold["native_to_rational_rmse_ratio"] for fold in folds],
            marker="o", linewidth=1.8, label=dataset["id"], color=colors[dataset["id"]],
        )
    axes[0, 0].axhline(1.0, color="#b44b4b", linestyle="--", linewidth=1.2, label="equal RMSE")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks([1, 2, 3, 4, 5])
    axes[0, 0].set_xlabel("Frozen held-out fold")
    axes[0, 0].set_ylabel("Native / rational RMSE (log scale)")
    axes[0, 0].set_title("A. Same-fold ratios; below 1 favors native")
    axes[0, 0].grid(alpha=0.22, which="both")
    axes[0, 0].legend(frameon=False, fontsize=8, ncol=2)

    dataset_ids = [dataset["id"] for dataset in summary["datasets"]]
    x = np.arange(len(dataset_ids))
    width = 0.25
    model_colors = {"native": "#316c9b", "rational": "#876a32", "cubic": "#666666"}
    for index, model in enumerate(["native", "rational", "cubic"]):
        values = [dataset["totals"]["overall_best_model_fold_counts"][model] for dataset in summary["datasets"]]
        axes[0, 1].bar(x + (index - 1) * width, values, width=width, label=model, color=model_colors[model])
    axes[0, 1].set_xticks(x, dataset_ids)
    axes[0, 1].set_ylim(0, 5.5)
    axes[0, 1].set_ylabel("Number of five folds")
    axes[0, 1].set_title("B. Overall fold winner: all three candidates")
    axes[0, 1].legend(frameon=False)
    axes[0, 1].grid(axis="y", alpha=0.2)

    width = 0.35
    native_points = [dataset["point_outcomes"]["native"] for dataset in summary["datasets"]]
    rational_points = [dataset["point_outcomes"]["rational"] for dataset in summary["datasets"]]
    axes[1, 0].bar(x - width / 2, native_points, width=width, label="native smaller |residual|", color="#316c9b")
    axes[1, 0].bar(x + width / 2, rational_points, width=width, label="rational smaller |residual|", color="#876a32")
    axes[1, 0].set_xticks(x, dataset_ids)
    axes[1, 0].set_ylabel("Held-out observations (descriptive count)")
    axes[1, 0].set_title("C. Paired point outcomes; not probabilities")
    axes[1, 0].legend(frameon=False, fontsize=8)
    axes[1, 0].grid(axis="y", alpha=0.2)

    metric_labels = ["RMSE", "MAE", "max |residual|"]
    metric_keys = ["rmse", "mae", "max_absolute_residual"]
    for index, (label, key) in enumerate(zip(metric_labels, metric_keys)):
        values = [sum(fold["native_vs_rational_direction"][key] == "native" for fold in dataset["folds"]) for dataset in summary["datasets"]]
        axes[1, 1].bar(x + (index - 1) * width, values, width=width, label=label)
    axes[1, 1].set_xticks(x, dataset_ids)
    axes[1, 1].set_ylim(0, 5.5)
    axes[1, 1].set_ylabel("Folds where native error is smaller")
    axes[1, 1].set_title("D. Winner direction depends on the metric")
    axes[1, 1].legend(frameon=False)
    axes[1, 1].grid(axis="y", alpha=0.2)

    fig.suptitle("Frozen native-versus-rational synthesis: 3 datasets, 15 folds, 407 paired observations", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Read-only post-hoc synthesis. No refit, no cross-dataset error pooling, no probability ranking; certified full fits are excluded.",
        ha="center", fontsize=9, color="#555555",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify stored output and figure without rewriting them")
    args = parser.parse_args()
    summary = analyze()
    errors = validate_summary(summary)
    if args.check:
        if not OUT.exists():
            errors.append("Missing synthesis output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored synthesis output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid synthesis figure")
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
        "points": summary["totals"]["point_count"],
        "native_better_than_rational_folds": summary["totals"]["native_better_than_rational_fold_count"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
