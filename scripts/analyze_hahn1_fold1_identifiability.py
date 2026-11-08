"""Post-hoc local-identifiability diagnostics for the frozen Hahn1 grouped fits."""

import json
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import error_metrics, sha256
from analyze_grouped_stress import make_contiguous_folds
from analyze_hahn1_high_temperature import PARAMETER_NAMES, hahn_model, load_hahn_data

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/hahn1-fold1-identifiability-protocol.json"
SOURCE = ROOT / "validation/grouped-stress.json"
OUT = ROOT / "validation/hahn1-fold1-identifiability.json"
FIGURE = ROOT / "papers/09_Hahn1失效机制/fig09_hahn1_fold1_identifiability.png"


def hahn_jacobian(x, parameters):
    """Analytic Jacobian in the frozen b1,...,b7 parameter order."""
    x = np.asarray(x, dtype=float)
    values = np.asarray([parameters[name] for name in PARAMETER_NAMES], dtype=float)
    powers = np.column_stack([np.ones_like(x), x, x ** 2, x ** 3])
    numerator = powers @ values[:4]
    denominator = 1.0 + powers[:, 1:] @ values[4:]
    prediction = numerator / denominator
    jacobian = np.empty((x.size, 7), dtype=float)
    jacobian[:, :4] = powers / denominator[:, None]
    jacobian[:, 4:] = -prediction[:, None] * powers[:, 1:] / denominator[:, None]
    return jacobian


def denominator_values(x, parameters):
    x = np.asarray(x, dtype=float)
    values = np.asarray([parameters[name] for name in PARAMETER_NAMES], dtype=float)
    return 1.0 + values[4] * x + values[5] * x ** 2 + values[6] * x ** 3


def interval_regime(x_train, x_test):
    train_min, train_max = float(np.min(x_train)), float(np.max(x_train))
    test_min, test_max = float(np.min(x_test)), float(np.max(x_test))
    if test_max < train_min:
        regime = "low_x_extrapolation"
        distance = train_min - test_max
    elif test_min > train_max:
        regime = "high_x_extrapolation"
        distance = test_min - train_max
    else:
        regime = "contiguous_gap_with_training_on_both_sides"
        distance = 0.0
    return {
        "regime": regime,
        "train_x_min": train_min,
        "train_x_max": train_max,
        "test_x_min": test_min,
        "test_x_max": test_max,
        "extrapolation_distance_x": float(distance),
    }


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_post_hoc_identifiability_diagnostics":
        raise ValueError("Identifiability diagnostic protocol is not frozen")
    if sha256(SOURCE) != protocol["inputs"]["grouped_stress_sha256"]:
        raise ValueError("Grouped stress input hash changed")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    hahn = next(item for item in source["datasets"] if item["id"] == "hahn1")
    x, y = load_hahn_data(
        ROOT / protocol["inputs"]["raw_data_file"],
        protocol["inputs"]["raw_data_sha256"],
    )
    masks = make_contiguous_folds(x, 5)
    records = []
    for fold_index, ((train, test), frozen) in enumerate(zip(masks, hahn["folds"]), 1):
        if fold_index != frozen["fold"] or not frozen["optimizer_success"]:
            raise ValueError(f"Unexpected frozen fold state: {fold_index}")
        if int(train.sum()) != frozen["train_count"] or int(test.sum()) != frozen["test_count"]:
            raise ValueError(f"Fold counts changed: {fold_index}")
        if sorted(set(x[test].tolist())) != frozen["test_x_values"]:
            raise ValueError(f"Fold x values changed: {fold_index}")
        parameters = frozen["model_parameters"]
        values = [parameters[name] for name in PARAMETER_NAMES]
        train_prediction = hahn_model(x[train], *values)
        test_prediction = hahn_model(x[test], *values)
        train_residual = y[train] - train_prediction
        test_metrics = error_metrics(y[test], test_prediction)
        if test_metrics != frozen["model_metrics"]:
            raise ValueError(f"Frozen test metrics do not reproduce: {fold_index}")
        rss = float(train_residual @ train_residual)
        source_rss = min(attempt["rss"] for attempt in frozen["attempts"] if attempt["success"])
        if not np.isclose(rss, source_rss, rtol=1.0e-9, atol=1.0e-10):
            raise ValueError(f"Frozen training RSS does not reproduce: {fold_index}")

        jacobian = hahn_jacobian(x[train], parameters)
        column_norms = np.linalg.norm(jacobian, axis=0)
        if not np.isfinite(jacobian).all() or np.any(column_norms <= 0):
            raise ValueError(f"Degenerate Jacobian scaling: {fold_index}")
        scaled_jacobian = jacobian / column_norms
        raw_singular_values = np.linalg.svd(jacobian, compute_uv=False)
        scaled_singular_values = np.linalg.svd(scaled_jacobian, compute_uv=False)
        tolerance = max(jacobian.shape) * np.finfo(float).eps * scaled_singular_values[0]
        numerical_rank = int(np.sum(scaled_singular_values > tolerance))
        scaled_information = scaled_jacobian.T @ scaled_jacobian
        scaled_unit_covariance = np.linalg.pinv(scaled_information, rcond=1.0e-12, hermitian=True)
        sigma2 = rss / (int(train.sum()) - len(PARAMETER_NAMES))
        covariance = sigma2 * scaled_unit_covariance / np.outer(column_norms, column_norms)
        variances = np.diag(covariance)
        if not np.isfinite(variances).all() or np.any(variances <= 0):
            raise ValueError(f"Non-positive local parameter variance: {fold_index}")
        standard_errors = np.sqrt(variances)
        correlation = covariance / np.outer(standard_errors, standard_errors)
        correlation = np.clip(correlation, -1.0, 1.0)
        off_diagonal = np.abs(correlation - np.eye(len(PARAMETER_NAMES)))
        max_correlation = float(np.max(off_diagonal))
        parameter_records = []
        for index, name in enumerate(PARAMETER_NAMES):
            value = float(parameters[name])
            parameter_records.append({
                "name": name,
                "value": value,
                "local_standard_error": float(standard_errors[index]),
                "absolute_relative_standard_error": float(standard_errors[index] / abs(value)) if value != 0 else None,
            })

        test_jacobian = hahn_jacobian(x[test], parameters)
        scaled_test_jacobian = test_jacobian / column_norms
        unit_prediction_variances = np.einsum(
            "ij,jk,ik->i", scaled_test_jacobian, scaled_unit_covariance, scaled_test_jacobian,
        )
        prediction_variances = sigma2 * unit_prediction_variances
        variance_scale = max(1.0, float(np.max(np.abs(prediction_variances))))
        if not np.isfinite(prediction_variances).all() or np.any(prediction_variances < -1.0e-10 * variance_scale):
            raise ValueError(f"Invalid local prediction variance: {fold_index}")
        prediction_variances = np.maximum(prediction_variances, 0.0)
        prediction_sd = np.sqrt(prediction_variances)
        denominator_train = denominator_values(x[train], parameters)
        denominator_test = denominator_values(x[test], parameters)
        points = []
        test_indices = np.flatnonzero(test)
        for local_index, source_index in enumerate(test_indices):
            points.append({
                "source_index": int(source_index + 1),
                "x": float(x[source_index]),
                "y": float(y[source_index]),
                "model_prediction": float(test_prediction[local_index]),
                "residual": float(y[source_index] - test_prediction[local_index]),
                "local_linearized_prediction_standard_deviation": float(prediction_sd[local_index]),
                "denominator": float(denominator_test[local_index]),
            })
        records.append({
            "fold": fold_index,
            "train_count": int(train.sum()),
            "test_count": int(test.sum()),
            "model_parameters": parameters,
            "training_metrics": error_metrics(y[train], train_prediction),
            "test_metrics": test_metrics,
            "baseline_test_metrics": frozen["baseline_metrics"],
            "model_not_worse_than_baseline": frozen["model_not_worse_than_baseline"],
            "interval": interval_regime(x[train], x[test]),
            "training_jacobian": {
                "shape": list(jacobian.shape),
                "parameter_count": len(PARAMETER_NAMES),
                "raw_singular_values": raw_singular_values.tolist(),
                "scaled_singular_values": scaled_singular_values.tolist(),
                "scaled_condition_number": float(scaled_singular_values[0] / scaled_singular_values[-1]),
                "numerical_rank": numerical_rank,
                "numerical_rank_tolerance": float(tolerance),
                "column_norms": column_norms.tolist(),
                "training_residual_variance_estimate": float(sigma2),
                "parameter_correlation_matrix": correlation.tolist(),
                "max_absolute_off_diagonal_parameter_correlation": max_correlation,
                "parameters": parameter_records,
                "interpretation": "Local linearization at the frozen fit; rank and conditioning do not establish or refute global structural identifiability",
            },
            "held_out_prediction_sensitivity": {
                "median_local_standard_deviation": float(np.median(prediction_sd)),
                "max_local_standard_deviation": float(np.max(prediction_sd)),
                "interpretation": "Delta-method local sensitivity propagated from the fitting design, not a calibrated prediction interval",
            },
            "denominator": {
                "min_absolute_on_training_points": float(np.min(np.abs(denominator_train))),
                "min_absolute_on_held_out_points": float(np.min(np.abs(denominator_test))),
                "all_finite_on_training_and_held_out_points": bool(np.isfinite(denominator_train).all() and np.isfinite(denominator_test).all() and np.all(denominator_train != 0) and np.all(denominator_test != 0)),
            },
            "held_out_points": points,
        })
    return {
        "status": "computed_post_hoc_hahn1_local_identifiability_diagnostics",
        "protocol_sha256": sha256(PROTOCOL),
        "grouped_stress_sha256": sha256(SOURCE),
        "data_sha256": protocol["inputs"]["raw_data_sha256"],
        "analysis_scope": {
            "post_hoc": True,
            "preregistered": False,
            "refit": False,
            "new_model_or_parameters": False,
            "new_holdout_selection": False,
            "independent_validation": False,
        },
        "folds": records,
        "decision": {
            "fold_1_failure_reversed": False,
            "global_identifiability_proved": False,
            "physical_parameter_endogeneity_proved": False,
            "calibrated_prediction_intervals_produced": False,
            "interpretation": "Report measured conditioning and local sensitivity alongside the existing failure; do not convert a mechanism hypothesis into a new success claim",
        },
        "limitations": [
            "This is post-hoc diagnosis after observing fold 1 failure, not preregistered or independent validation",
            "Local Jacobians, covariances and delta-method sensitivities do not prove global structural identifiability or calibrated uncertainty",
            "Column-normalized condition numbers reduce unit-scale dominance but do not remove nonlinear parameter compensation",
            "A nonzero denominator excludes isolated poles only at evaluated points and does not guarantee stable extrapolation",
            "No new physical experiment, model revision or parameter-endogeneity claim is produced",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    if len(summary.get("folds", [])) != 5:
        errors.append("Expected five Hahn1 folds")
    if summary.get("analysis_scope", {}).get("refit") is not False:
        errors.append("Refitting is not permitted")
    if summary.get("decision", {}).get("fold_1_failure_reversed") is not False:
        errors.append("The fold 1 failure must remain")
    for fold in summary.get("folds", []):
        if len(fold["held_out_points"]) != fold["test_count"]:
            errors.append(f"Point count mismatch in fold {fold['fold']}")
        condition = fold["training_jacobian"]["scaled_condition_number"]
        if not np.isfinite(condition) or condition < 1:
            errors.append(f"Invalid condition number in fold {fold['fold']}")
        if fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"] < 0:
            errors.append(f"Negative prediction sensitivity in fold {fold['fold']}")
    if summary["folds"][0]["test_metrics"]["rmse"] <= summary["folds"][0]["baseline_test_metrics"]["rmse"]:
        errors.append("Fold 1 no longer matches the recorded failure")
    return errors


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing identifiability outputs")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    folds = summary["folds"]
    indices = [fold["fold"] for fold in folds]
    conditions = [fold["training_jacobian"]["scaled_condition_number"] for fold in folds]
    max_sd = [fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"] for fold in folds]
    test_rmse = [fold["test_metrics"]["rmse"] for fold in folds]
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 10.2), constrained_layout=True)
    colors = ["#b44b4b" if index == 1 else "#316c9b" for index in indices]
    axes[0, 0].bar(indices, conditions, color=colors)
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks(indices)
    axes[0, 0].set_xlabel("Contiguous fold")
    axes[0, 0].set_ylabel("Column-scaled Jacobian condition number")
    axes[0, 0].set_title("Local conditioning at each frozen training fit")
    axes[0, 0].grid(axis="y", which="both", alpha=0.2)

    axes[0, 1].plot(indices, max_sd, "o-", color="#316c9b", label="Max local prediction SD")
    axes[0, 1].plot(indices, test_rmse, "s--", color="#b44b4b", label="Observed test RMSE")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_xticks(indices)
    axes[0, 1].set_xlabel("Contiguous fold")
    axes[0, 1].set_ylabel("Response units (log scale)")
    axes[0, 1].set_title("Local sensitivity is not a calibrated error bar")
    axes[0, 1].grid(which="both", alpha=0.2)
    axes[0, 1].legend(frameon=False, fontsize=8)

    x, y = load_hahn_data(ROOT / "data/Hahn1.dat", summary["data_sha256"])
    train, test = make_contiguous_folds(x, 5)[0]
    parameters = folds[0]["model_parameters"]
    grid = np.linspace(0, 240, 1200)
    prediction = hahn_model(grid, *parameters.values())
    ax = axes[1, 0]
    ax.scatter(x[train & (x <= 240)], y[train & (x <= 240)], s=18, color="#316c9b", label="Fold 1 fitting observations (x≤240)")
    ax.scatter(x[test], y[test], s=30, color="#b44b4b", marker="s", label="Fold 1 held-out observations")
    ax.plot(grid, prediction, color="#20252b", lw=1.8, label="Frozen fold 1 rational fit")
    ax.set_yscale("symlog", linthresh=1.0)
    ax.set_xlabel("Temperature x (K)")
    ax.set_ylabel("Coefficient of thermal expansion y (symlog)")
    ax.set_title("Fold 1: low-temperature extrapolation failure")
    ax.grid(which="both", alpha=0.2)
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    correlation = np.asarray(folds[0]["training_jacobian"]["parameter_correlation_matrix"])
    image = axes[1, 1].imshow(np.abs(correlation), vmin=0, vmax=1, cmap="YlOrRd")
    axes[1, 1].set_xticks(range(7), PARAMETER_NAMES)
    axes[1, 1].set_yticks(range(7), PARAMETER_NAMES)
    axes[1, 1].set_title("Fold 1 absolute local parameter correlations")
    for row in range(7):
        for column in range(7):
            value = abs(correlation[row, column])
            axes[1, 1].text(column, row, f"{value:.3f}", ha="center", va="center", fontsize=7, color="white" if value > 0.55 else "#20252b")
    fig.colorbar(image, ax=axes[1, 1], shrink=0.8, label="Absolute correlation")
    fig.suptitle("Hahn1 post-hoc diagnostics: conditioning, sensitivity and the retained fold 1 failure", fontsize=14)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps({
        "output": str(OUT),
        "figure": str(FIGURE),
        "folds": [{
            "fold": fold["fold"],
            "regime": fold["interval"]["regime"],
            "scaled_condition_number": fold["training_jacobian"]["scaled_condition_number"],
            "numerical_rank": fold["training_jacobian"]["numerical_rank"],
            "max_abs_parameter_correlation": fold["training_jacobian"]["max_absolute_off_diagonal_parameter_correlation"],
            "max_local_prediction_sd": fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"],
            "test_rmse": fold["test_metrics"]["rmse"],
            "min_abs_denominator_test": fold["denominator"]["min_absolute_on_held_out_points"],
        } for fold in folds],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
