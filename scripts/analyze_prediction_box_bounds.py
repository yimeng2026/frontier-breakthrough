"""Compute exact pointwise residual bounds inside certified denominator boxes."""

import hashlib
import json
from pathlib import Path

from rational_format import bounded_text
from prediction_box_bounds import pointwise_prediction_bound

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/rational-prediction-box-protocol.json"
OUT = ROOT / "validation/rational-prediction-box-bounds.json"
FIGURE = ROOT / "papers/15_参数盒预测界/fig15_prediction_box_bounds.png"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_prediction_box_bound_analysis":
        raise ValueError("Prediction-box protocol is not frozen")
    inputs, hashes = {}, {}
    for key, info in protocol["inputs"].items():
        path = ROOT / info["file"]
        digest = sha256(path)
        if digest != info["sha256"]:
            raise ValueError(f"Input hash changed: {path}")
        inputs[key] = json.loads(path.read_text(encoding="utf-8"))
        hashes[key] = digest
    return protocol, inputs, hashes


def analyze():
    protocol, inputs, hashes = load_inputs()
    box = inputs["parameter_box"]
    cases = []
    for frozen in box["cases"]:
        dataset, fold = frozen["dataset"], frozen["fold"]
        source = next(item for item in inputs[dataset]["folds"] if item["fold"] == fold)
        parameters = source["model_parameters"]
        denominator_names = frozen["denominator_parameter_order"]
        numerator_names = [name for name in parameters if name not in denominator_names]
        numerator_coefficients = [parameters[name] for name in numerator_names]
        radius = frozen["certified_radius_lower_bound_float"]
        scales = frozen["local_standard_error_scales"]
        denominator_coefficients = frozen["denominator_coefficients"]
        available = bool(frozen["snapshot_safe"] and frozen["certified_region_safe"] and radius > 0)
        points = []
        if available:
            for observation in source["held_out_points"]:
                bound = pointwise_prediction_bound(
                    numerator_coefficients, observation["x"], denominator_coefficients,
                    scales, radius, observation["y"],
                )
                points.append({
                    "x": observation["x"],
                    "observed_y": observation["y"],
                    "snapshot_prediction_rational": bounded_text(bound["snapshot_prediction"]),
                    "snapshot_prediction_float": float(bound["snapshot_prediction"]),
                    "snapshot_denominator_rational": bounded_text(bound["snapshot_denominator"]),
                    "denominator_perturbation_bound_rational": bounded_text(bound["denominator_perturbation_bound"]),
                    "denominator_lower_bound_rational": bounded_text(bound["denominator_lower_bound"]),
                    "denominator_lower_bound_float": float(bound["denominator_lower_bound"]),
                    "prediction_shift_upper_bound_rational": bounded_text(bound["prediction_shift_upper_bound"]),
                    "prediction_shift_upper_bound_float": float(bound["prediction_shift_upper_bound"]),
                    "absolute_residual_upper_bound_rational": bounded_text(bound["absolute_residual_upper_bound"]),
                    "absolute_residual_upper_bound_float": float(bound["absolute_residual_upper_bound"]),
                })
        points.sort(key=lambda point: point["x"])
        cases.append({
            "dataset": dataset,
            "fold": fold,
            "closed_interval": frozen["closed_interval"],
            "certified_radius_lower_bound_float": radius,
            "bounds_available": available,
            "unavailable_reason": None if available else "The snapshot has a root or lacks a certified positive denominator box",
            "numerator_coefficients": numerator_coefficients,
            "denominator_coefficients": denominator_coefficients,
            "local_standard_error_scales": scales,
            "point_bounds": points,
            "max_prediction_shift_upper_bound_float": max((point["prediction_shift_upper_bound_float"] for point in points), default=None),
            "max_absolute_residual_upper_bound_float": max((point["absolute_residual_upper_bound_float"] for point in points), default=None),
            "scope": "Exact conservative bounds at these observed x points for every denominator in the certified box; no probability or continuous-x claim",
        })
    bounded = [case for case in cases if case["bounds_available"]]
    totals = {
        "fold_count": len(cases),
        "bounded_fold_count": len(bounded),
        "unbounded_rooted_fold_count": sum(not case["bounds_available"] for case in cases),
        "bounded_point_count": sum(len(case["point_bounds"]) for case in cases),
        "max_prediction_shift_upper_bound_float": max((case["max_prediction_shift_upper_bound_float"] for case in bounded), default=None),
        "max_absolute_residual_upper_bound_float": max((case["max_absolute_residual_upper_bound_float"] for case in bounded), default=None),
    }
    return {
        "status": "computed_exact_rational_prediction_box_bounds",
        "protocol_sha256": sha256(PROTOCOL),
        "input_sha256": hashes,
        "cases": cases,
        "totals": totals,
        "decision": {
            "probabilistic_interval_claimed": False,
            "continuous_x_bound_claimed": False,
            "rooted_cases_silently_bounded": False,
            "rmse_bound_claimed": False,
            "measured_uncertainty_claimed": False,
        },
        "limitations": [
            "Bounds are deterministic and conservative for every denominator in each certified box at the supplied observation points",
            "Numerator coefficients remain fixed; numerator and model-structure errors are outside this bound",
            "No probabilistic interval, RMSE bound, calibration, continuous-x error bound or physical measurement uncertainty is claimed",
            "Rooted snapshots and cases without a positive denominator certificate do not receive this bound",
            "Large finite upper bounds remain valid bounds but may be uninformative for practical prediction",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    cases = summary.get("cases", [])
    if len(cases) != 15:
        errors.append("Expected fifteen prediction-box cases")
    for case in cases:
        if not case["bounds_available"]:
            if case["point_bounds"]:
                errors.append(f"Unavailable case has bounds: {case['dataset']} fold {case['fold']}")
            continue
        for point in case["point_bounds"]:
            if point["denominator_lower_bound_float"] <= 0:
                errors.append(f"Non-positive denominator bound: {case['dataset']} fold {case['fold']}")
            if point["prediction_shift_upper_bound_float"] < 0 or point["absolute_residual_upper_bound_float"] < 0:
                errors.append(f"Negative prediction bound: {case['dataset']} fold {case['fold']}")
    totals = summary.get("totals", {})
    if totals.get("bounded_fold_count") != sum(case["bounds_available"] for case in cases):
        errors.append("Bounded fold count mismatch")
    if totals.get("bounded_point_count") != sum(len(case["point_bounds"]) for case in cases):
        errors.append("Bounded point count mismatch")
    for key in ["probabilistic_interval_claimed", "continuous_x_bound_claimed", "rooted_cases_silently_bounded", "rmse_bound_claimed", "measured_uncertainty_claimed"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing prediction-box bounds")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cases = summary["cases"]
    labels = [f"{case['dataset'][0].upper()}{case['fold']}" for case in cases]
    shift = [case["max_prediction_shift_upper_bound_float"] if case["bounds_available"] else 1.0e-12 for case in cases]
    residual = [case["max_absolute_residual_upper_bound_float"] if case["bounds_available"] else 1.0e-12 for case in cases]
    fig, ax = plt.subplots(figsize=(13.5, 5.8), constrained_layout=True)
    ax.plot(range(len(cases)), shift, "o-", color="#316c9b", label="Max prediction-shift upper bound")
    ax.plot(range(len(cases)), residual, "s--", color="#876a32", label="Max observed-residual upper bound")
    for index, case in enumerate(cases):
        if not case["bounds_available"]:
            ax.scatter(index, 1.0e-12, marker="x", s=90, color="#b44b4b", zorder=5)
            ax.text(index, 1.0e-11, "rooted", ha="center", va="bottom", fontsize=7, color="#b44b4b", rotation=90)
    ax.set_yscale("log")
    ax.set_xticks(range(len(cases)), labels, rotation=90)
    ax.set_ylabel("Exact conservative upper bound (log scale)")
    ax.set_xlabel("Dataset fold")
    ax.set_title("Pointwise bounds for every denominator in each certified box")
    ax.grid(which="both", alpha=0.2)
    ax.legend(frameon=False, fontsize=8)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps({
        "output": str(OUT),
        "figure": str(FIGURE),
        "totals": summary["totals"],
        "cases": [{"dataset": case["dataset"], "fold": case["fold"], "max_shift": case["max_prediction_shift_upper_bound_float"], "max_residual": case["max_absolute_residual_upper_bound_float"]} for case in cases],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
