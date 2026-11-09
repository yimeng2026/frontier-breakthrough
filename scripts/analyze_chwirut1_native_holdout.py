"""Compare native Chwirut1 exponential and frozen rational candidates on identical folds."""

import json
import math
import warnings
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

from analyze_chwirut_holdout import error_metrics, sha256
from external_coverage import load_observations

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/chwirut1-native-holdout-protocol.json"
OUT = ROOT / "validation/chwirut1-native-holdout.json"
FIGURE = ROOT / "papers/42_Chwirut1原生指数对照/fig42_chwirut1_native_holdout.png"
PARAMETER_NAMES = ["b1", "b2", "b3"]


def native_model(x, b1, b2, b3):
    x = np.asarray(x, dtype=float)
    denominator = b2 + b3 * x
    if np.any(denominator == 0):
        return np.full(x.shape, np.nan, dtype=float)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return np.exp(-b1 * x) / denominator


def parameter_dict(parameters):
    return {name: float(value) for name, value in zip(PARAMETER_NAMES, parameters)}


def fit_native(x, y, starts):
    attempts = []
    for start_index, start in enumerate(starts, start=1):
        p0 = [start[name] for name in PARAMETER_NAMES]
        record = {"start_index": start_index, "start": start, "evaluation_success": False}
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                parameters, _, info, message, ierr = curve_fit(
                    native_model, x, y, p0=p0, method="lm", maxfev=200000, full_output=True,
                )
            prediction = native_model(x, *parameters)
            residual = np.asarray(y) - prediction
            rss = float(np.sum(residual ** 2)) if np.all(np.isfinite(prediction)) else math.inf
            success = bool(np.all(np.isfinite(parameters)) and np.all(np.isfinite(prediction)) and math.isfinite(rss))
            record.update({
                "parameters": parameter_dict(parameters),
                "training_rss": rss if math.isfinite(rss) else None,
                "optimizer_reported_success": ierr in {1, 2, 3, 4},
                "optimizer_message": message,
                "optimizer_nfev": int(info.get("nfev", 0)),
                "warnings": [str(item.message) for item in caught],
                "evaluation_success": success,
            })
        except Exception as error:
            record.update({"error_type": type(error).__name__, "error": str(error)})
        attempts.append(record)
    viable = [record for record in attempts if record["evaluation_success"]]
    best = min(viable, key=lambda record: record["training_rss"]) if viable else None
    return best, attempts


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_chwirut1_native_holdout":
        raise ValueError("Native Chwirut1 holdout protocol is not frozen")
    amendment_path = ROOT / "validation/chwirut1-native-holdout-protocol-amendment-01.json"
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    if amendment["original_protocol"]["sha256"] != sha256(protocol_path):
        raise ValueError("Chwirut1 metadata amendment does not match the original protocol")
    data_info = protocol["inputs"]["data"]
    candidate_info = protocol["inputs"]["rational_candidate"]
    candidate_path = ROOT / candidate_info["file"]
    if sha256(candidate_path) != candidate_info["sha256"]:
        raise ValueError("Frozen rational candidate input hash changed")
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    x, y = load_observations(ROOT / data_info["file"], data_info["observations"], data_info["sha256"])
    if len(np.unique(x)) != data_info["unique_predictor_values"]:
        raise ValueError("Frozen unique-distance count changed")

    starts = protocol["native_rule"]["starts"]
    best_full, full_attempts = fit_native(x, y, starts)
    known_rule = protocol["known_answer_rule"]
    if best_full is None:
        known_parameters = None
        known_rss = None
        parameter_matches = False
        rss_match = False
    else:
        known_parameters = best_full["parameters"]
        known_rss = best_full["training_rss"]
        parameter_matches = all(
            math.isclose(
                known_parameters[name], certified,
                rel_tol=known_rule["parameter_relative_tolerance"],
                abs_tol=known_rule["parameter_absolute_tolerance"],
            )
            for name, certified in known_rule["certified_parameters"].items()
        )
        rss_match = math.isclose(known_rss, known_rule["certified_rss"], rel_tol=0, abs_tol=known_rule["rss_absolute_tolerance"])
    known_answer = {
        "optimizer_success": best_full is not None,
        "within_certified_tolerances": bool(parameter_matches and rss_match),
        "parameters": known_parameters,
        "certified_parameters": known_rule["certified_parameters"],
        "rss": known_rss,
        "certified_rss": known_rule["certified_rss"],
        "parameter_checks_passed": parameter_matches,
        "rss_check_passed": rss_match,
        "evidence_class": known_rule["evidence_class"],
        "attempts": full_attempts,
    }

    folds = []
    for fold_number in range(1, protocol["fold_rule"]["count"] + 1):
        test_x = protocol["fold_rule"]["unique_x"][str(fold_number)]
        test_indices = np.flatnonzero(np.isin(x, test_x))
        train_mask = np.ones(len(x), dtype=bool)
        train_mask[test_indices] = False
        if np.any(np.isin(x[train_mask], test_x)):
            raise ValueError(f"A frozen distance crosses fitting and test sets: {fold_number}")
        old = next(case for case in candidate["folds"] if case["fold"] == fold_number)
        if [point["x"] for point in old["point_results"]] != [float(value) for value in x[test_indices]]:
            raise ValueError(f"Frozen Chwirut1 point assignment changed: {fold_number}")
        if any(point["observed_y"] != y[index] for index, point in zip(test_indices, old["point_results"])):
            raise ValueError(f"Observed Chwirut1 response mismatch in fold {fold_number}")
        best, attempts = fit_native(x[train_mask], y[train_mask], starts)
        if best is None:
            parameters = None
            prediction = np.full(len(test_indices), np.nan)
        else:
            parameters = np.array([best["parameters"][name] for name in PARAMETER_NAMES])
            prediction = native_model(x[test_indices], *parameters)
        success = bool(best is not None and np.all(np.isfinite(prediction)))
        metrics = error_metrics(y[test_indices], prediction) if success else None
        points = []
        for index, old_point in zip(test_indices, old["point_results"]):
            finite = bool(np.isfinite(prediction[len(points)]))
            native_prediction = float(prediction[len(points)]) if finite else None
            points.append({
                "x": float(x[index]),
                "observed_y": float(y[index]),
                "native_prediction": native_prediction,
                "native_absolute_residual": abs(float(y[index]) - native_prediction) if finite else None,
                "rational_snapshot_prediction": old_point["snapshot_prediction"],
                "rational_absolute_residual": old_point["actual_absolute_residual"],
            })
        folds.append({
            "fold": fold_number,
            "optimizer_success": success,
            "test_predictions_finite": bool(np.all(np.isfinite(prediction))),
            "selected_start": best["start_index"] if best is not None else None,
            "training_rss": best["training_rss"] if best is not None else None,
            "native_parameters": best["parameters"] if best is not None else None,
            "attempts": attempts,
            "native_test_metrics": metrics,
            "rational_candidate_test_metrics": old["test_metrics"],
            "cubic_baseline_test_metrics": old["baseline_test_metrics"],
            "native_rmse_minus_rational": metrics["rmse"] - old["test_metrics"]["rmse"] if success else None,
            "native_better_than_rational": metrics["rmse"] < old["test_metrics"]["rmse"] if success else None,
            "native_better_than_cubic_baseline": metrics["rmse"] < old["baseline_test_metrics"]["rmse"] if success else None,
            "point_results": points,
        })

    all_success = all(fold["optimizer_success"] for fold in folds)
    if all_success:
        pooled_y = np.array([point["observed_y"] for fold in folds for point in fold["point_results"]])
        pooled_native = np.array([point["native_prediction"] for fold in folds for point in fold["point_results"]])
        pooled_rational = np.array([point["rational_snapshot_prediction"] for fold in folds for point in fold["point_results"]])
        pooled = {
            "native": error_metrics(pooled_y, pooled_native),
            "rational_candidate": error_metrics(pooled_y, pooled_rational),
            "cubic_baseline": None,
            "scope": "All 214 held-out predictions; per-point cubic-baseline predictions were not present in the frozen input",
        }
    else:
        pooled = {"native": None, "rational_candidate": None, "cubic_baseline": None, "scope": "Pooled metrics suppressed because at least one native fold failed"}
    stability = {}
    for name in PARAMETER_NAMES:
        available = [(fold["fold"], fold["native_parameters"][name]) for fold in folds if fold["native_parameters"] is not None]
        values = [value for _, value in available]
        stability[name] = {
            "folds": [fold for fold, _ in available],
            "values": values,
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
            "median": float(np.median(values)) if values else None,
            "range": max(values) - min(values) if values else None,
            "missing_fold_numbers": [fold["fold"] for fold in folds if fold["native_parameters"] is None],
        }
    totals = {
        "fold_count": len(folds),
        "point_count": sum(len(fold["point_results"]) for fold in folds),
        "unique_distance_count": len(np.unique(x)),
        "native_optimizer_failure_count": sum(not fold["optimizer_success"] for fold in folds),
        "native_better_than_rational_fold_count": sum(fold["native_better_than_rational"] is True for fold in folds),
        "rational_better_than_native_fold_count": sum(fold["native_better_than_rational"] is False for fold in folds),
        "native_rational_tie_fold_count": sum(fold["native_rmse_minus_rational"] == 0 for fold in folds),
        "native_better_than_cubic_baseline_fold_count": sum(fold["native_better_than_cubic_baseline"] is True for fold in folds),
        "cubic_baseline_better_than_native_fold_count": sum(fold["native_better_than_cubic_baseline"] is False for fold in folds),
        "known_answer_within_certified_tolerances": known_answer["within_certified_tolerances"],
    }
    return {
        "status": "computed_chwirut1_native_holdout",
        "protocol_sha256": sha256(protocol_path),
        "metadata_amendment_sha256": sha256(amendment_path),
        "data_sha256": sha256(ROOT / data_info["file"]),
        "candidate_input_sha256": sha256(candidate_path),
        "analysis_scope": {
            "native_model": True,
            "candidate_results_frozen_before_native_fit": True,
            "same_holdout_points": True,
            "repeated_x_never_crosses_fitting_and_test": True,
            "post_hoc_model_family_comparison": True,
            "known_answer_is_holdout": False,
            "native_deterministic_bounds_computed": False,
            "rational_bounds_transferred_to_native": False,
            "independent_physical_experiment": False,
            "independent_model_family_test": False,
            "related_prior_dataset": protocol["dataset_scope"]["related_prior_dataset"],
        },
        "known_answer": known_answer,
        "folds": folds,
        "parameter_stability": stability,
        "pooled": pooled,
        "totals": totals,
        "decision": protocol["decision"],
        "limitations": [
            "The full-data NIST certified-fit reproduction checks implementation only and is not holdout evidence",
            "Chwirut1 shares its study and native model family with Chwirut2; this is not an independent model-family or laboratory replication test",
            "Native and rational fold-level RMSE comparisons are descriptive and do not establish a universal model ranking",
            "No rational denominator, ellipsoid, box or continuous-safety claim is transferred to the native exponential model",
            "Parameter variation across folds is descriptive and is not a posterior distribution or independent physical estimate",
            "Optimizer failures, non-finite predictions, repeated observations and fold-level losses are retained rather than hidden",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    known = summary["known_answer"]
    if not known["optimizer_success"] or not known["within_certified_tolerances"]:
        errors.append("NIST Chwirut1 known-answer reproduction failed")
    if known["evidence_class"] != "known_answer_reproduction_not_holdout":
        errors.append("Known-answer evidence scope changed")
    if len(summary["folds"]) != 5 or summary["totals"]["point_count"] != 214 or summary["totals"]["unique_distance_count"] != 22:
        errors.append("Expected five folds, 214 points and 22 distances")
    amendment = json.loads((ROOT / "validation/chwirut1-native-holdout-protocol-amendment-01.json").read_text(encoding="utf-8"))
    if [len(fold["point_results"]) for fold in summary["folds"]] != amendment["correction"]["corrected_observation_counts"]:
        errors.append("Frozen Chwirut1 fold sizes changed")
    for fold in summary["folds"]:
        if fold["optimizer_success"]:
            y = np.array([point["observed_y"] for point in fold["point_results"]])
            prediction = np.array([point["native_prediction"] for point in fold["point_results"]])
            expected = error_metrics(y, prediction)
            for key, value in expected.items():
                if not math.isclose(fold["native_test_metrics"][key], value, rel_tol=1.0e-12, abs_tol=1.0e-12):
                    errors.append(f"Native Chwirut1 metric mismatch: fold {fold['fold']} {key}")
        elif fold["native_test_metrics"] is not None:
            errors.append(f"Failed Chwirut1 fold has fabricated metrics: {fold['fold']}")
    if summary["totals"]["native_optimizer_failure_count"] != sum(not fold["optimizer_success"] for fold in summary["folds"]):
        errors.append("Native Chwirut1 optimizer failure count mismatch")
    for key in ["native_physical_law_validated", "native_probability_calibration_claimed", "native_deterministic_bounds_claimed", "rational_bounds_transferred_to_native", "independent_physical_experiment_claimed", "independent_model_family_claimed", "certified_full_fit_used_as_holdout", "failed_fits_hidden"]:
        if summary["decision"].get(key) is not False:
            errors.append(f"Overclaim detected: {key}")
    return errors


def render_figure(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    folds = summary["folds"]
    numbers = [fold["fold"] for fold in folds]
    fig, axes = plt.subplots(1, 3, figsize=(17.5, 5.4), constrained_layout=True)
    series = [
        ("native_test_metrics", "Native exponential", "#316c9b"),
        ("rational_candidate_test_metrics", "Frozen cubic/cubic", "#876a32"),
        ("cubic_baseline_test_metrics", "Frozen cubic baseline", "#666666"),
    ]
    for key, label, color in series:
        axes[0].plot(numbers, [fold[key]["rmse"] if fold[key] is not None else np.nan for fold in folds], marker="o", label=label, color=color)
    axes[0].set_yscale("log")
    axes[0].set_xticks(numbers)
    axes[0].set_xlabel("Frozen held-out fold")
    axes[0].set_ylabel("RMSE (log scale)")
    axes[0].set_title("Identical 214 observations; certified fit excluded")
    axes[0].grid(alpha=0.2, which="both")
    axes[0].legend(frameon=False, fontsize=8)
    ratios = [fold["native_test_metrics"]["rmse"] / fold["rational_candidate_test_metrics"]["rmse"] if fold["optimizer_success"] else np.nan for fold in folds]
    axes[1].plot(numbers, ratios, marker="o", color="#316c9b")
    axes[1].axhline(1.0, color="#b44b4b", linestyle="--", linewidth=1, label="Equal RMSE")
    axes[1].set_yscale("log")
    axes[1].set_xticks(numbers)
    axes[1].set_xlabel("Frozen held-out fold")
    axes[1].set_ylabel("Native / rational RMSE")
    axes[1].set_title(f"Native lower in {summary['totals']['native_better_than_rational_fold_count']} of 5 folds")
    axes[1].grid(alpha=0.2, which="both")
    axes[1].legend(frameon=False, fontsize=8)
    for name, color in zip(PARAMETER_NAMES, ["#316c9b", "#876a32", "#6a4c93"]):
        median = summary["parameter_stability"][name]["median"]
        axes[2].plot(numbers, [fold["native_parameters"][name] / median if fold["native_parameters"] is not None else np.nan for fold in folds], marker="o", color=color, label=name)
    axes[2].axhline(1.0, color="#777777", linestyle=":", linewidth=1)
    axes[2].set_xticks(numbers)
    axes[2].set_xlabel("Frozen held-out fold")
    axes[2].set_ylabel("Parameter / five-fold median")
    axes[2].set_title("Parameter variation is not independent replication")
    axes[2].grid(alpha=0.2)
    axes[2].legend(frameon=False, fontsize=8)
    fig.suptitle("Chwirut1 native exponential vs frozen rational candidate; related study scope retained", fontsize=12)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite native Chwirut1 holdout outputs")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    render_figure(summary)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "totals": summary["totals"], "pooled": summary["pooled"], "parameterStability": summary["parameter_stability"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
