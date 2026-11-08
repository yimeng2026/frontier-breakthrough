"""Read-only same-point decomposition of frozen external residual bounds."""

import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/external-bound-decomposition-protocol.json"
OUT = ROOT / "exports/external-bound-decomposition.json"
FIGURE = ROOT / "papers/22_外部界组成对照/fig22_external_bound_decomposition.png"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decompose_points(summary, threshold):
    records = []
    mismatches = []
    for case in summary["folds"]:
        for point in case["point_results"]:
            if not point["ellipsoid_available"]:
                continue
            actual = point["actual_absolute_residual"]
            shift = point["ellipsoid_prediction_shift_upper_bound_float"]
            bound = point["ellipsoid_absolute_residual_upper_bound_float"]
            if bound < 0:
                raise ValueError("Negative stored residual bound")
            if not math.isclose(actual + shift, bound, rel_tol=1.0e-8, abs_tol=1.0e-9):
                mismatches.append({"fold": case["fold"], "x": point["x"], "actual": actual, "shift": shift, "bound": bound})
            share = None if bound == 0 else shift / bound
            dominant = "undefined_zero_bound" if share is None else ("prediction_shift_dominant" if share >= threshold else "snapshot_residual_dominant")
            records.append({"fold": case["fold"], "x": point["x"], "actual_absolute_residual": actual, "prediction_shift": shift, "residual_upper_bound": bound, "shift_share": share, "dominant": dominant})
    return records, mismatches


def maximum(records):
    return max(records, key=lambda item: item["residual_upper_bound"]) if records else None


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_external_bound_decomposition":
        raise ValueError("Bound-decomposition protocol is not frozen")
    threshold = protocol["decomposition_rule"]["shift_dominant_threshold"]
    datasets = []
    input_hashes = {}
    dataset_ids = protocol.get("dataset_ids", ["filip", "mgh17", "gauss1"])
    for dataset_id in dataset_ids:
        info = protocol["inputs"][dataset_id]
        path = ROOT / info["file"]
        input_hashes[dataset_id] = sha256(path)
        if input_hashes[dataset_id] != info["sha256"]:
            raise ValueError(f"Input hash changed: {path}")
        source = json.loads(path.read_text(encoding="utf-8"))
        records, mismatches = decompose_points(source, threshold)
        shares = [item["shift_share"] for item in records if item["shift_share"] is not None]
        folds = []
        for case in source["folds"]:
            fold_records = [item for item in records if item["fold"] == case["fold"]]
            fold_shares = [item["shift_share"] for item in fold_records if item["shift_share"] is not None]
            folds.append({"fold": case["fold"], "available_point_count": len(fold_records), "median_shift_share": statistics.median(fold_shares) if fold_shares else None, "maximum_residual_upper_bound": maximum(fold_records)})
        datasets.append({
            "id": dataset_id,
            "point_count": source["totals"]["point_count"],
            "ellipsoid_available_point_count": len(records),
            "ellipsoid_unavailable_point_count": source["totals"]["point_count"] - len(records),
            "prediction_shift_dominant_point_count": sum(item["dominant"] == "prediction_shift_dominant" for item in records),
            "snapshot_residual_dominant_point_count": sum(item["dominant"] == "snapshot_residual_dominant" for item in records),
            "undefined_zero_bound_count": sum(item["dominant"] == "undefined_zero_bound" for item in records),
            "median_shift_share": statistics.median(shares) if shares else None,
            "maximum_residual_upper_bound": maximum(records),
            "bound_identity_mismatch_count": len(mismatches),
            "folds": folds,
            "points": records,
        })
    mechanism_info = protocol["inputs"]["gauss1_mechanism"]
    mechanism_path = ROOT / mechanism_info["file"]
    input_hashes["gauss1_mechanism"] = sha256(mechanism_path)
    if input_hashes["gauss1_mechanism"] != mechanism_info["sha256"]:
        raise ValueError("Gauss1 mechanism hash changed")
    mechanism = json.loads(mechanism_path.read_text(encoding="utf-8"))
    gauss1 = next(item for item in datasets if item["id"] == "gauss1")
    checks = []
    for old_case in mechanism["folds"]:
        old = old_case["maximum_residual_upper_bound"]
        if old is None:
            continue
        new = next(case["maximum_residual_upper_bound"] for case in gauss1["folds"] if case["fold"] == old_case["fold"])
        comparisons = [
            old["x"] == new["x"],
            math.isclose(old["value"], new["residual_upper_bound"], rel_tol=1.0e-8, abs_tol=1.0e-9),
            math.isclose(old["actual_absolute_residual"], new["actual_absolute_residual"], rel_tol=1.0e-8, abs_tol=1.0e-9),
            math.isclose(old["prediction_shift"], new["prediction_shift"], rel_tol=1.0e-8, abs_tol=1.0e-9),
            math.isclose(old["shift_share"], new["shift_share"], rel_tol=1.0e-8, abs_tol=1.0e-9),
        ]
        checks.append({"fold": old_case["fold"], "match": all(comparisons)})
    totals = {
        "point_count": sum(item["point_count"] for item in datasets),
        "ellipsoid_available_point_count": sum(item["ellipsoid_available_point_count"] for item in datasets),
        "ellipsoid_unavailable_point_count": sum(item["ellipsoid_unavailable_point_count"] for item in datasets),
        "prediction_shift_dominant_point_count": sum(item["prediction_shift_dominant_point_count"] for item in datasets),
        "snapshot_residual_dominant_point_count": sum(item["snapshot_residual_dominant_point_count"] for item in datasets),
        "undefined_zero_bound_count": sum(item["undefined_zero_bound_count"] for item in datasets),
        "bound_identity_mismatch_count": sum(item["bound_identity_mismatch_count"] for item in datasets),
    }
    return {
        "status": "computed_external_bound_decomposition",
        "protocol_sha256": sha256(protocol_path),
        "input_sha256": input_hashes,
        "analysis_scope": {"post_hoc": True, "refit": False, "retuned": False, "shift_dominant_threshold": threshold},
        "datasets": datasets,
        "totals": totals,
        "gauss1_regression": {"check_count": len(checks), "mismatch_count": sum(not item["match"] for item in checks), "checks": checks},
        "decision": {
            "universal_dataset_ranking_claimed": False,
            "probability_calibration_claimed": False,
            "native_physical_model_claimed": False,
            "unavailable_points_treated_as_zero": False,
        },
        "limitations": [
            "This is a read-only post-hoc arithmetic decomposition of stored bounds",
            "Shares are not probabilities, variance decomposition or physical-mechanism attribution",
            "The 60 unavailable points are retained separately and have no fabricated bounds or shares",
            "Dataset-specific distributions do not establish a universal ranking or native-model validity",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    totals = summary["totals"]
    expected = {"point_count": 365, "ellipsoid_available_point_count": 305, "ellipsoid_unavailable_point_count": 60, "bound_identity_mismatch_count": 0, "undefined_zero_bound_count": 0}
    for key, value in expected.items():
        if totals.get(key) != value:
            errors.append(f"Unexpected {key}: {totals.get(key)} != {value}")
    if totals["prediction_shift_dominant_point_count"] + totals["snapshot_residual_dominant_point_count"] + totals["undefined_zero_bound_count"] != totals["ellipsoid_available_point_count"]:
        errors.append("Dominance counts do not sum to available points")
    if summary["gauss1_regression"]["check_count"] != 4 or summary["gauss1_regression"]["mismatch_count"] != 0:
        errors.append("Gauss1 mechanism regression failed")
    for key in ["universal_dataset_ranking_claimed", "probability_calibration_claimed", "native_physical_model_claimed", "unavailable_points_treated_as_zero"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def render_figure(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    datasets = summary["datasets"]
    labels = [item["id"].upper() for item in datasets]
    positions = np.arange(len(datasets))
    shift_counts = [item["prediction_shift_dominant_point_count"] for item in datasets]
    actual_counts = [item["snapshot_residual_dominant_point_count"] for item in datasets]
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), constrained_layout=True)
    axes[0].bar(positions, shift_counts, color="#316c9b", label="Prediction-shift dominant")
    axes[0].bar(positions, actual_counts, bottom=shift_counts, color="#876a32", label="Snapshot-residual dominant")
    axes[0].set_xticks(positions, labels)
    axes[0].set_ylabel("Available points")
    axes[0].set_title("Same-point dominance counts; unavailable points excluded")
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].grid(axis="y", alpha=0.2)
    distributions = [[point["shift_share"] for point in item["points"] if point["shift_share"] is not None] for item in datasets]
    axes[1].boxplot(distributions, tick_labels=labels, showmeans=True)
    axes[1].axhline(0.5, color="#b44b4b", linestyle="--", linewidth=1, label="Frozen 0.5 threshold")
    axes[1].set_ylim(0, 1.02)
    axes[1].set_ylabel("Prediction shift / residual upper bound")
    axes[1].set_title("Arithmetic shares are not probability contributions")
    axes[1].grid(axis="y", alpha=0.2)
    axes[1].legend(frameon=False, fontsize=8)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite external bound-decomposition outputs")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_figure(summary)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "totals": summary["totals"], "gauss1_regression": summary["gauss1_regression"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
