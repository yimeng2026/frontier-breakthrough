"""Decompose frozen Roszman1 fold-4 native/rational error contributions."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-native-fold4-error-decomposition-protocol.json"
OUT = ROOT / "validation/roszman1-native-fold4-error-decomposition.json"
FIGURE = ROOT / "papers/46_Roszman1第4折误差分解/fig46_roszman1_fold4_error_decomposition.png"


def winner(delta):
    if delta < 0:
        return "native"
    if delta > 0:
        return "rational"
    return "tie"


def remaining_direction(value, native_is_better_when_negative=True):
    if value < 0:
        return "native" if native_is_better_when_negative else "rational"
    if value > 0:
        return "rational" if native_is_better_when_negative else "native"
    return "tie"


def group_summary(points, name):
    selected = [point for point in points if point["absolute_winner"] == name]
    weight_sum = math.fsum(point["weight"] for point in selected)
    return {
        "point_indices": [point["index"] for point in selected],
        "count": len(selected),
        "absolute_delta_sum": math.fsum(point["absolute_delta"] for point in selected),
        "squared_delta_sum": math.fsum(point["squared_delta"] for point in selected),
        "weight_sum": weight_sum,
        "mean_weight": weight_sum / len(selected) if selected else None,
    }


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_roszman1_native_fold4_error_decomposition":
        raise ValueError("Roszman1 fold-4 error-decomposition protocol is not frozen")
    paths = {}
    for name, info in protocol["inputs"].items():
        path = ROOT / info["file"]
        if sha256(path) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {name}")
        paths[name] = path
    source = json.loads(paths["native_holdout"].read_text(encoding="utf-8"))
    synthesis = json.loads(paths["cross_dataset_synthesis"].read_text(encoding="utf-8"))
    fold = next(case for case in source["folds"] if case["fold"] == protocol["target"]["fold"])
    synthesis_dataset = next(item for item in synthesis["datasets"] if item["id"] == "roszman1")
    synthesis_fold = next(case for case in synthesis_dataset["folds"] if case["fold"] == protocol["target"]["fold"])
    if synthesis_fold["native_vs_rational_direction"]["rmse"] != "native" or synthesis_fold["native_vs_rational_direction"]["mae"] != "rational":
        raise ValueError("Frozen cross-dataset metric-direction witness changed")
    if len(fold["point_results"]) != protocol["target"]["point_count"]:
        raise ValueError("Frozen Roszman1 fold-4 point count changed")

    points = []
    for index, old in enumerate(fold["point_results"], start=1):
        native_prediction = old["native_prediction"]
        rational_prediction = old["rational_snapshot_prediction"]
        if native_prediction is None or rational_prediction is None:
            raise ValueError("Fold-4 decomposition requires complete paired predictions")
        native_residual = old["observed_y"] - native_prediction
        rational_residual = old["observed_y"] - rational_prediction
        native_absolute = abs(native_residual)
        rational_absolute = abs(rational_residual)
        if not all(math.isfinite(value) for value in [native_residual, rational_residual, native_absolute, rational_absolute]):
            raise ValueError("Non-finite fold-4 residual")
        if not math.isclose(native_absolute, old["native_absolute_residual"], rel_tol=1.0e-12, abs_tol=1.0e-15):
            raise ValueError("Stored native residual mismatch")
        if not math.isclose(rational_absolute, old["rational_absolute_residual"], rel_tol=1.0e-12, abs_tol=1.0e-15):
            raise ValueError("Stored rational residual mismatch")
        delta = native_absolute - rational_absolute
        weight = native_absolute + rational_absolute
        squared_delta = native_absolute ** 2 - rational_absolute ** 2
        points.append({
            "index": index,
            "x": old["x"],
            "observed_y": old["observed_y"],
            "native_prediction": native_prediction,
            "rational_prediction": rational_prediction,
            "native_residual": native_residual,
            "rational_residual": rational_residual,
            "native_absolute_residual": native_absolute,
            "rational_absolute_residual": rational_absolute,
            "absolute_delta": delta,
            "weight": weight,
            "squared_delta": squared_delta,
            "absolute_winner": winner(delta),
        })

    observed = np.array([point["observed_y"] for point in points], dtype=float)
    native_prediction = np.array([point["native_prediction"] for point in points], dtype=float)
    rational_prediction = np.array([point["rational_prediction"] for point in points], dtype=float)
    native_residual = observed - native_prediction
    rational_residual = observed - rational_prediction
    native_mae = float(np.mean(np.abs(native_residual)))
    rational_mae = float(np.mean(np.abs(rational_residual)))
    native_mse = float(np.mean(native_residual ** 2))
    rational_mse = float(np.mean(rational_residual ** 2))
    native_rmse = math.sqrt(native_mse)
    rational_rmse = math.sqrt(rational_mse)
    mismatch_count = 0
    for model, rmse, mae in [
        ("native", native_rmse, native_mae),
        ("rational_candidate", rational_rmse, rational_mae),
    ]:
        frozen = fold[f"{model}_test_metrics"]
        if not math.isclose(rmse, frozen["rmse"], rel_tol=1.0e-12, abs_tol=1.0e-15):
            mismatch_count += 1
        if not math.isclose(mae, frozen["mae"], rel_tol=1.0e-12, abs_tol=1.0e-15):
            mismatch_count += 1
    if not native_rmse < rational_rmse or not native_mae > rational_mae:
        raise ValueError("Expected native-lower-RMSE and rational-lower-MAE directions are absent")

    absolute_delta_sum = math.fsum(point["absolute_delta"] for point in points)
    squared_delta_sum = math.fsum(point["squared_delta"] for point in points)
    identity_errors = [abs(point["squared_delta"] - point["absolute_delta"] * point["weight"]) for point in points]
    identity_mismatch_count = sum(
        not math.isclose(point["squared_delta"], point["absolute_delta"] * point["weight"], rel_tol=1.0e-12, abs_tol=1.0e-15)
        for point in points
    )
    if absolute_delta_sum <= 0 or squared_delta_sum >= 0:
        raise ValueError("Aggregate delta signs do not reproduce the frozen metric reversal")
    aggregate = {
        "absolute_delta_sum": absolute_delta_sum,
        "squared_delta_sum": squared_delta_sum,
        "native_mae": native_mae,
        "rational_mae": rational_mae,
        "native_mse": native_mse,
        "rational_mse": rational_mse,
        "native_rmse": native_rmse,
        "rational_rmse": rational_rmse,
        "native_mae_minus_rational_mae": native_mae - rational_mae,
        "native_mse_minus_rational_mse": native_mse - rational_mse,
        "absolute_delta_sum_divided_by_point_count": absolute_delta_sum / len(points),
        "squared_delta_sum_divided_by_point_count": squared_delta_sum / len(points),
        "weight_identity_max_absolute_error": max(identity_errors),
        "weight_identity_mismatch_count": identity_mismatch_count,
        "frozen_metric_mismatch_count": mismatch_count,
        "native_rmse_lower": True,
        "rational_mae_lower": True,
    }
    groups = {name: group_summary(points, name) for name in ["native", "rational", "tie"]}
    leave_one_out = []
    for point in points:
        remaining_absolute = absolute_delta_sum - point["absolute_delta"]
        remaining_squared = squared_delta_sum - point["squared_delta"]
        reverses_mae = remaining_absolute <= 0
        reverses_rmse = remaining_squared >= 0
        leave_one_out.append({
            "point_index": point["index"],
            "x": point["x"],
            "remaining_absolute_delta_sum": remaining_absolute,
            "remaining_squared_delta_sum": remaining_squared,
            "remaining_mae_direction": remaining_direction(remaining_absolute),
            "remaining_rmse_direction": remaining_direction(remaining_squared),
            "reverses_rational_mae": reverses_mae,
            "reverses_native_rmse": reverses_rmse,
            "reverses_either_direction": reverses_mae or reverses_rmse,
            "reverses_both_directions": reverses_mae and reverses_rmse,
            "refit_performed": False,
        })
    totals = {
        "point_count": len(points),
        "native_absolute_winner_count": sum(point["absolute_winner"] == "native" for point in points),
        "rational_absolute_winner_count": sum(point["absolute_winner"] == "rational" for point in points),
        "absolute_tie_count": sum(point["absolute_winner"] == "tie" for point in points),
        "leave_one_out_reverses_rational_mae_count": sum(record["reverses_rational_mae"] for record in leave_one_out),
        "leave_one_out_reverses_native_rmse_count": sum(record["reverses_native_rmse"] for record in leave_one_out),
        "leave_one_out_reverses_either_count": sum(record["reverses_either_direction"] for record in leave_one_out),
        "leave_one_out_reverses_both_count": sum(record["reverses_both_directions"] for record in leave_one_out),
        "per_point_absolute_squared_direction_disagreement_count": sum(
            (point["absolute_delta"] < 0) != (point["squared_delta"] < 0)
            or (point["absolute_delta"] > 0) != (point["squared_delta"] > 0)
            for point in points
        ),
    }
    target = protocol["target"]
    if totals["native_absolute_winner_count"] != target["native_absolute_residual_winner_count"] or totals["rational_absolute_winner_count"] != target["rational_absolute_residual_winner_count"]:
        raise ValueError("Frozen point-winner counts changed")
    if identity_mismatch_count or mismatch_count:
        raise ValueError("Frozen metric or weight identity check failed")

    return {
        "status": "computed_roszman1_native_fold4_error_decomposition",
        "protocol_sha256": sha256(protocol_path),
        "native_holdout_sha256": sha256(paths["native_holdout"]),
        "cross_dataset_synthesis_sha256": sha256(paths["cross_dataset_synthesis"]),
        "analysis_scope": {
            "dataset": "roszman1",
            "fold": 4,
            "refit": False,
            "retuned": False,
            "post_hoc": True,
            "arithmetic_decomposition_only": True,
            "leave_one_out_refit": False,
            "all_points_retained": True,
            "per_point_absolute_squared_preference_can_differ": False,
            "aggregate_absolute_squared_direction_can_differ": True,
            "probability_analysis": False,
            "physical_mechanism_identified": False,
        },
        "points": points,
        "groups": groups,
        "aggregate": aggregate,
        "leave_one_out": leave_one_out,
        "totals": totals,
        "decision": {
            "per_point_absolute_squared_direction_disagreement_claimed": False,
            "leave_one_out_refitting_performed": False,
            "statistical_significance_claimed": False,
            "physical_mechanism_claimed": False,
            "probability_calibration_claimed": False,
            "native_deterministic_bounds_claimed": False,
            "rational_bounds_transferred_to_native": False,
            "universal_model_ranking_claimed": False,
            "independent_experiment_claimed": False,
            "failed_points_hidden": False,
        },
        "limitations": [
            "Five held-out observations support arithmetic diagnosis only, not statistical significance or a universal model-selection rule",
            "Leave-one-out records subtract stored metric contributions and do not represent five refitted models",
            "Residual-sum weights explain how squared errors emphasize larger residuals; they are not probabilities or physical causal contributions",
            "The same pair of absolute residuals has the same per-point preference under absolute and squared loss; only aggregate directions can reverse",
            "No native deterministic bound, probability calibration, independent experiment or new physical mechanism is established",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    if summary.get("aggregate", {}).get("absolute_delta_sum") != expected["aggregate"]["absolute_delta_sum"] or summary.get("aggregate", {}).get("squared_delta_sum") != expected["aggregate"]["squared_delta_sum"]:
        errors.append("Aggregate delta mismatch")
    if summary.get("leave_one_out") != expected["leave_one_out"]:
        errors.append("Leave-one-out metric arithmetic mismatch")
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
    points = summary["points"]
    indices = np.arange(1, len(points) + 1)
    native_color = "#316c9b"
    rational_color = "#876a32"
    colors = [native_color if point["absolute_winner"] == "native" else rational_color for point in points]
    fig, axes = plt.subplots(2, 2, figsize=(15.5, 10.5), constrained_layout=True)
    width = 0.36
    axes[0, 0].bar(indices - width / 2, [point["native_absolute_residual"] for point in points], width=width, label="native", color=native_color)
    axes[0, 0].bar(indices + width / 2, [point["rational_absolute_residual"] for point in points], width=width, label="rational", color=rational_color)
    axes[0, 0].set_xticks(indices)
    axes[0, 0].set_xlabel("Frozen observation index within fold 4")
    axes[0, 0].set_ylabel("Absolute residual")
    axes[0, 0].set_title("A. Paired absolute residuals; no point removed")
    axes[0, 0].legend(frameon=False)
    axes[0, 0].grid(axis="y", alpha=0.2)

    axes[0, 1].bar(indices, [point["absolute_delta"] for point in points], color=colors)
    axes[0, 1].axhline(0, color="#444444", linewidth=0.9)
    axes[0, 1].set_xticks(indices)
    axes[0, 1].set_xlabel("Frozen observation index")
    axes[0, 1].set_ylabel("Native minus rational |residual|")
    axes[0, 1].set_title("B. Absolute-loss delta: positive total favors rational MAE")
    axes[0, 1].grid(axis="y", alpha=0.2)

    axes[1, 0].bar(indices, [point["squared_delta"] for point in points], color=colors)
    axes[1, 0].axhline(0, color="#444444", linewidth=0.9)
    axes[1, 0].set_xticks(indices)
    axes[1, 0].set_xlabel("Frozen observation index")
    axes[1, 0].set_ylabel("Native minus rational squared residual")
    axes[1, 0].set_title("C. Squared-loss delta: negative total favors native RMSE")
    axes[1, 0].grid(axis="y", alpha=0.2)
    axes[1, 0].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

    for point in points:
        axes[1, 1].scatter(point["absolute_delta"], point["weight"], s=75, color=native_color if point["absolute_winner"] == "native" else rational_color, zorder=3)
        axes[1, 1].annotate(str(point["index"]), (point["absolute_delta"], point["weight"]), xytext=(6, 6), textcoords="offset points", fontsize=10)
    axes[1, 1].axvline(0, color="#444444", linewidth=0.9)
    axes[1, 1].set_xlabel("Absolute-loss delta (negative favors native)")
    axes[1, 1].set_ylabel("Weight = native |residual| + rational |residual|")
    axes[1, 1].set_title("D. Squared delta = absolute delta × weight")
    axes[1, 1].grid(alpha=0.2)
    from matplotlib.lines import Line2D
    axes[1, 1].legend(handles=[
        Line2D([0], [0], marker="o", color="none", markerfacecolor=native_color, markersize=8, label="native smaller |residual|"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=rational_color, markersize=8, label="rational smaller |residual|"),
    ], frameon=False, fontsize=8, loc="best")

    fig.suptitle("Roszman1 fold 4: native lower RMSE but rational lower MAE", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Five frozen held-out predictions. Arithmetic decomposition only; no refit, probability claim or physical mechanism identification.",
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
            errors.append("Missing fold-4 decomposition output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored fold-4 decomposition is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid fold-4 decomposition figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "points": summary["totals"]["point_count"],
        "absolute_delta_sum": summary["aggregate"]["absolute_delta_sum"],
        "squared_delta_sum": summary["aggregate"]["squared_delta_sum"],
        "leave_one_out_reverses_either_count": summary["totals"]["leave_one_out_reverses_either_count"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
