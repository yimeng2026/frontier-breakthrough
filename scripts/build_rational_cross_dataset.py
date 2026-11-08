"""Normalize three existing rational-model studies without refitting or hiding evidence levels."""

import json
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import sha256
from analyze_hahn1_high_temperature import PARAMETER_NAMES as CUBIC_NAMES, hahn_model
from rational_gate import assess_prediction_domain

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/rational-cross-dataset-protocol.json"
OUT = ROOT / "exports/rational-cross-dataset.json"
FIGURE = ROOT / "papers/12_跨数据集验收综合/fig12_rational_cross_dataset.png"


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_post_hoc_cross_dataset_synthesis":
        raise ValueError("Cross-dataset synthesis protocol is not frozen")
    inputs = {}
    hashes = {}
    for key, info in protocol["inputs"].items():
        path = ROOT / info["file"]
        digest = sha256(path)
        if digest != info["sha256"]:
            raise ValueError(f"Input hash changed: {path}")
        inputs[key] = json.loads(path.read_text(encoding="utf-8"))
        hashes[key] = digest

    datasets = []
    hahn = inputs["hahn1_identifiability"]
    hahn_folds = []
    for fold in hahn["folds"]:
        parameters = fold["model_parameters"]
        test_x = np.asarray([point["x"] for point in fold["held_out_points"]])
        domain = assess_prediction_domain(parameters, test_x, hahn_model, CUBIC_NAMES[:4], CUBIC_NAMES[4:])
        standard_errors = [item["local_standard_error"] for item in fold["training_jacobian"]["parameters"]]
        minimal = bool(fold["training_jacobian"]["numerical_rank"] == 7 and np.isfinite(standard_errors).all() and np.all(np.asarray(standard_errors) > 0))
        baseline = fold["test_metrics"]["rmse"] <= fold["baseline_test_metrics"]["rmse"]
        gate = bool(domain["domain_admissible"] and minimal and baseline)
        hahn_folds.append({
            "fold": fold["fold"],
            "assessment_type": "post_hoc_gate_reconstruction",
            "test_rmse": fold["test_metrics"]["rmse"],
            "training_rmse": fold["training_metrics"]["rmse"],
            "baseline_rmse": fold["baseline_test_metrics"]["rmse"],
            "rmse_over_baseline": fold["test_metrics"]["rmse"] / fold["baseline_test_metrics"]["rmse"],
            "root_count_in_held_out_interval": len(domain["real_roots_in_closed_interval"]),
            "roots_in_held_out_interval": domain["real_roots_in_closed_interval"],
            "domain_admissible": domain["domain_admissible"],
            "numerical_rank": fold["training_jacobian"]["numerical_rank"],
            "parameter_count": 7,
            "scaled_condition_number": fold["training_jacobian"]["scaled_condition_number"],
            "max_absolute_off_diagonal_parameter_correlation": fold["training_jacobian"]["max_absolute_off_diagonal_parameter_correlation"],
            "minimal_numerical_identifiability": minimal,
            "baseline_not_worse": baseline,
            "gate_consistent": gate,
        })
    datasets.append({
        "id": "hahn1",
        "model_class": "cubic/cubic",
        "baseline": "cubic_polynomial",
        "assessment_type": "post_hoc_gate_reconstruction",
        "folds": hahn_folds,
        "overall_all_folds_gate_consistent": all(fold["gate_consistent"] for fold in hahn_folds),
    })

    for dataset_id, model_class, baseline_name in [("thurber", "cubic/cubic", "cubic_polynomial"), ("kirby2", "quadratic/quadratic", "quadratic_polynomial")]:
        source = inputs[dataset_id]
        folds = []
        for fold in source["folds"]:
            domain = fold["domain_audit"]
            minimal = fold["identifiability"]["minimal_numerical_identifiability"]
            baseline = fold["test_metrics"]["rmse"] <= fold["baseline_test_metrics"]["rmse"]
            gate = bool(domain["domain_admissible"] and minimal and baseline)
            if gate != fold["decision"]["gated_limited_support"]:
                raise ValueError(f"Source decision mismatch: {dataset_id} fold {fold['fold']}")
            folds.append({
                "fold": fold["fold"],
                "assessment_type": "frozen_dataset_prospective_gate",
                "test_rmse": fold["test_metrics"]["rmse"],
                "training_rmse": fold["identifiability"]["training_metrics"]["rmse"],
                "baseline_rmse": fold["baseline_test_metrics"]["rmse"],
                "rmse_over_baseline": fold["test_metrics"]["rmse"] / fold["baseline_test_metrics"]["rmse"],
                "root_count_in_held_out_interval": len(domain["real_roots_in_closed_interval"]),
                "roots_in_held_out_interval": domain["real_roots_in_closed_interval"],
                "domain_admissible": domain["domain_admissible"],
                "numerical_rank": fold["identifiability"]["numerical_rank"],
                "parameter_count": len(fold["model_parameters"]),
                "scaled_condition_number": fold["identifiability"]["scaled_condition_number"],
                "max_absolute_off_diagonal_parameter_correlation": fold["identifiability"]["max_absolute_off_diagonal_parameter_correlation"],
                "minimal_numerical_identifiability": minimal,
                "baseline_not_worse": baseline,
                "gate_consistent": gate,
            })
        datasets.append({
            "id": dataset_id,
            "model_class": model_class,
            "baseline": baseline_name,
            "assessment_type": "frozen_dataset_prospective_gate",
            "folds": folds,
            "overall_all_folds_gate_consistent": all(fold["gate_consistent"] for fold in folds),
        })

    all_folds = [fold for dataset in datasets for fold in dataset["folds"]]
    totals = {
        "dataset_count": len(datasets),
        "fold_count": len(all_folds),
        "gate_consistent_fold_count": sum(fold["gate_consistent"] for fold in all_folds),
        "dataset_all_folds_count": sum(dataset["overall_all_folds_gate_consistent"] for dataset in datasets),
        "domain_failed_fold_count": sum(not fold["domain_admissible"] for fold in all_folds),
        "identifiability_failed_fold_count": sum(not fold["minimal_numerical_identifiability"] for fold in all_folds),
        "baseline_failed_fold_count": sum(not fold["baseline_not_worse"] for fold in all_folds),
        "pole_count_in_failed_domains": sum(fold["root_count_in_held_out_interval"] for fold in all_folds if not fold["domain_admissible"]),
        "post_hoc_fold_count": sum(fold["assessment_type"] == "post_hoc_gate_reconstruction" for fold in all_folds),
        "dataset_prospective_fold_count": sum(fold["assessment_type"] == "frozen_dataset_prospective_gate" for fold in all_folds),
        "interpretation": "Counts summarize these fifteen folds only and are not sensitivity, specificity or universal detection-accuracy estimates",
    }
    return {
        "status": "computed_post_hoc_rational_cross_dataset_synthesis",
        "protocol_sha256": sha256(PROTOCOL),
        "input_sha256": hashes,
        "analysis_scope": {"refit": False, "new_independent_experiment": False, "shared_kernel": "scripts/rational_gate.py"},
        "datasets": datasets,
        "totals": totals,
        "decision": {
            "universal_detection_accuracy_claimed": False,
            "universal_law_claimed": False,
            "global_identifiability_proved": False,
            "physical_parameter_endogeneity_proved": False,
        },
        "limitations": [
            "Hahn1 folds are post-hoc gate reconstructions; Thurber and Kirby2 retain their dataset-prospective labels",
            "Three NIST datasets and fifteen folds cannot establish universal detection accuracy or a model-family ranking",
            "Numerical roots and dense-grid checks do not constitute exact global algebraic certificates",
            "Local full rank and finite positive standard errors do not prove global structural identifiability or physical endogeneity",
            "No new fitting, physical experiment or external collaboration was performed for this synthesis",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    datasets = summary.get("datasets", [])
    folds = [fold for dataset in datasets for fold in dataset["folds"]]
    totals = summary.get("totals", {})
    if len(datasets) != 3 or len(folds) != 15:
        errors.append("Expected three datasets and fifteen folds")
    for fold in folds:
        expected = fold["domain_admissible"] and fold["minimal_numerical_identifiability"] and fold["baseline_not_worse"]
        if fold["gate_consistent"] != expected:
            errors.append(f"Gate mismatch: {fold}")
    if totals.get("gate_consistent_fold_count") != sum(fold["gate_consistent"] for fold in folds):
        errors.append("Fold total mismatch")
    if totals.get("dataset_all_folds_count") != sum(dataset["overall_all_folds_gate_consistent"] for dataset in datasets):
        errors.append("Dataset total mismatch")
    if summary["decision"]["universal_detection_accuracy_claimed"]:
        errors.append("Universal accuracy claim detected")
    return errors


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing cross-dataset synthesis")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.6), constrained_layout=True)
    for column, dataset in enumerate(summary["datasets"]):
        folds = dataset["folds"]
        indices = [fold["fold"] for fold in folds]
        colors = ["#b44b4b" if not fold["domain_admissible"] else "#316c9b" for fold in folds]
        ratios = [fold["rmse_over_baseline"] for fold in folds]
        axes[0, column].plot(indices, ratios, color="#69777f", lw=1.2)
        axes[0, column].scatter(indices, ratios, c=colors, s=48, zorder=3)
        axes[0, column].axhline(1.0, color="#876a32", ls="--", lw=1.2)
        axes[0, column].set_yscale("log")
        axes[0, column].set_xticks(indices)
        axes[0, column].set_xlabel("Contiguous fold")
        axes[0, column].set_title(f"{dataset['id']} · all-fold support = {dataset['overall_all_folds_gate_consistent']}")
        axes[0, column].grid(which="both", alpha=0.2)
        if column == 0:
            axes[0, column].set_ylabel("Model RMSE / baseline RMSE")
        conditions = [fold["scaled_condition_number"] for fold in folds]
        axes[1, column].bar(indices, conditions, color=colors)
        axes[1, column].set_yscale("log")
        axes[1, column].set_xticks(indices)
        axes[1, column].set_xlabel("Contiguous fold")
        axes[1, column].grid(axis="y", which="both", alpha=0.2)
        if column == 0:
            axes[1, column].set_ylabel("Scaled Jacobian condition number")
    fig.suptitle(f"Rational cross-dataset synthesis: {summary['totals']['gate_consistent_fold_count']}/15 folds gate-consistent; counts are not accuracy estimates", fontsize=13)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps({
        "output": str(OUT),
        "figure": str(FIGURE),
        "totals": summary["totals"],
        "datasets": [{"id": dataset["id"], "overall": dataset["overall_all_folds_gate_consistent"], "failed_folds": [fold["fold"] for fold in dataset["folds"] if not fold["gate_consistent"]]} for dataset in summary["datasets"]],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
