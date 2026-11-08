"""Grouped contiguous-x stress tests for the three previously fitted model families."""

import json
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import chwirut_model, error_metrics, fit_chwirut, fit_linear, load_chwirut_data, sha256
from analyze_eckerle4_two_tail import eckerle_model, fit_gaussian, load_eckerle_data
from analyze_hahn1_high_temperature import fit_cubic_baseline, fit_rational, hahn_model, load_hahn_data

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/grouped-stress.json"
FIGURE = ROOT / "papers/08_跨数据集压力测试/fig08_grouped_stress.png"


def make_contiguous_folds(x, count=5):
    x = np.asarray(x, dtype=float)
    unique = np.unique(x)
    groups = np.array_split(unique, count)
    folds = []
    for index in range(count):
        test = np.isin(x, groups[index])
        train = ~test
        folds.append((train, test))
    return folds


def analyze():
    protocol = json.loads((ROOT / "validation/grouped-stress-protocol.json").read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_grouped_stress_analysis":
        raise ValueError("Grouped stress protocol is not frozen")
    chwirut_protocol = json.loads((ROOT / "validation/chwirut-holdout-protocol.json").read_text(encoding="utf-8"))
    eckerle_protocol = json.loads((ROOT / "validation/eckerle4-two-tail-protocol.json").read_text(encoding="utf-8"))
    hahn_protocol = json.loads((ROOT / "validation/hahn1-high-temperature-protocol.json").read_text(encoding="utf-8"))
    x_chwirut, y_chwirut = load_chwirut_data(ROOT / "data/Chwirut2.dat", chwirut_protocol["data"]["sha256"])
    x_eckerle, y_eckerle = load_eckerle_data(ROOT / "data/Eckerle4.dat", eckerle_protocol["data"]["sha256"])
    x_hahn, y_hahn = load_hahn_data(ROOT / "data/Hahn1.dat", hahn_protocol["data"]["sha256"])
    configurations = {
        "chwirut": {
            "x": x_chwirut, "y": y_chwirut,
            "fit": lambda a, b: fit_chwirut(a, b, chwirut_protocol["model"]["starts"]),
            "predict": lambda p, x: chwirut_model(x, *p.values()),
            "baseline_degree": 1,
            "title": "Chwirut exponential",
        },
        "eckerle4": {
            "x": x_eckerle, "y": y_eckerle,
            "fit": lambda a, b: fit_gaussian(a, b, eckerle_protocol),
            "predict": lambda p, x: eckerle_model(x, *p.values()),
            "baseline_degree": 1,
            "title": "Eckerle Gaussian",
        },
        "hahn1": {
            "x": x_hahn, "y": y_hahn,
            "fit": lambda a, b: fit_rational(a, b, hahn_protocol["model"]["starts"]),
            "predict": lambda p, x: hahn_model(x, *p.values()),
            "baseline_degree": 3,
            "title": "Hahn rational",
        },
    }
    datasets = []
    for key, config in configurations.items():
        x, y = config["x"], config["y"]
        folds = []
        for fold_index, (train, test) in enumerate(make_contiguous_folds(x), 1):
            baseline_coefficients = np.polyfit(x[train], y[train], config["baseline_degree"])
            baseline_prediction = np.polyval(baseline_coefficients, x[test])
            baseline_metrics = error_metrics(y[test], baseline_prediction)
            try:
                best, attempts = config["fit"](x[train], y[train])
                prediction = config["predict"](best["parameters"], x[test])
                if not np.isfinite(prediction).all():
                    raise ValueError("Non-finite model prediction")
                model_metrics = error_metrics(y[test], prediction)
                record = {
                    "fold": fold_index,
                    "train_count": int(train.sum()),
                    "test_count": int(test.sum()),
                    "test_x_values": sorted(set(x[test].tolist())),
                    "optimizer_success": True,
                    "model_parameters": best["parameters"],
                    "model_metrics": model_metrics,
                    "baseline_metrics": baseline_metrics,
                    "attempts": attempts,
                }
            except Exception as error:
                record = {
                    "fold": fold_index,
                    "train_count": int(train.sum()),
                    "test_count": int(test.sum()),
                    "test_x_values": sorted(set(x[test].tolist())),
                    "optimizer_success": False,
                    "error": str(error),
                    "model_metrics": {"rmse": None, "mae": None, "max_absolute_residual": None},
                    "baseline_metrics": baseline_metrics,
                }
            record["model_not_worse_than_baseline"] = bool(
                record["optimizer_success"] and record["model_metrics"]["rmse"] <= record["baseline_metrics"]["rmse"]
            )
            folds.append(record)
        finite = all(fold["optimizer_success"] for fold in folds)
        all_not_worse = all(fold["model_not_worse_than_baseline"] for fold in folds)
        rmse_values = [fold["model_metrics"]["rmse"] for fold in folds if fold["optimizer_success"]]
        worst = max(folds, key=lambda fold: fold["model_metrics"]["rmse"] if fold["optimizer_success"] else float("inf"))
        datasets.append({
            "id": key,
            "title": config["title"],
            "folds": folds,
            "median_model_rmse": float(np.median(rmse_values)) if rmse_values else None,
            "worst_fold": {
                "fold": worst["fold"],
                "model_rmse": worst["model_metrics"]["rmse"],
                "baseline_rmse": worst["baseline_metrics"]["rmse"],
                "optimizer_success": worst["optimizer_success"],
            },
            "decision": {
                "robust_limited_support": finite and all_not_worse,
                "all_folds_finite": finite,
                "all_folds_not_worse_than_baseline": all_not_worse,
                "universal_law_claimed": False,
            },
        })
    return {
        "status": "computed_grouped_contiguous_x_stress_diagnostics",
        "protocol_sha256": sha256(ROOT / "validation/grouped-stress-protocol.json"),
        "datasets": datasets,
        "overall_robust_limited_support": all(item["decision"]["robust_limited_support"] for item in datasets),
        "limitations": [
            "Five contiguous grouped folds per dataset are stress diagnostics, not universal model-family rankings or independent experiments",
            "Contiguous folds include interpolation and extrapolation regimes; a good median cannot hide a failing interval",
            "Optimizer failures and non-finite predictions are failures, not missing successes",
            "Parameters fitted on four groups are never selected using the held-out group",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    if len(summary["datasets"]) != 3:
        errors.append("Expected three datasets")
    if sum(len(item["folds"]) for item in summary["datasets"]) != 15:
        errors.append("Expected fifteen folds")
    for item in summary["datasets"]:
        finite = all(fold["optimizer_success"] for fold in item["folds"])
        all_not_worse = all(fold["model_not_worse_than_baseline"] for fold in item["folds"])
        if item["decision"]["robust_limited_support"] != (finite and all_not_worse):
            errors.append(f"Decision mismatch for {item['id']}")
        if item["decision"]["universal_law_claimed"]:
            errors.append(f"Universal claim detected for {item['id']}")
    if summary["overall_robust_limited_support"] != all(item["decision"]["robust_limited_support"] for item in summary["datasets"]):
        errors.append("Overall decision mismatch")
    return errors


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite: {OUT}")
    if FIGURE.exists():
        raise FileExistsError(f"Refusing to overwrite: {FIGURE}")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), constrained_layout=True)
    for ax, item in zip(axes, summary["datasets"]):
        folds = item["folds"]
        indices = [fold["fold"] for fold in folds]
        model = [fold["model_metrics"]["rmse"] for fold in folds]
        baseline = [fold["baseline_metrics"]["rmse"] for fold in folds]
        ax.plot(indices, model, "o-", color="#316c9b", label="Model")
        ax.plot(indices, baseline, "s--", color="#876a32", label="Baseline")
        worst = item["worst_fold"]["fold"]
        ax.scatter([worst], [item["worst_fold"]["model_rmse"]], marker="x", s=100, color="#b44b4b", zorder=5, label="Worst fold")
        ax.set_yscale("log")
        ax.set_xticks(indices)
        ax.set_title(item["title"])
        ax.set_xlabel("Contiguous fold")
        ax.set_ylabel("Test RMSE (log scale)")
        ax.grid(True, which="both", alpha=0.2)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Grouped stress diagnostics: every fold and every failure is retained", fontsize=13)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "overall_robust_limited_support": summary["overall_robust_limited_support"], "datasets": [{"id": item["id"], "decision": item["decision"], "worst_fold": item["worst_fold"]} for item in summary["datasets"]]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
