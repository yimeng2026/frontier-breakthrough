"""Recompute and synthesize three frozen native ellipsoid envelope studies."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/native-ellipsoid-cross-model-synthesis-protocol.json"
OUT = ROOT / "exports/native-ellipsoid-cross-model-synthesis.json"
FIGURE = ROOT / "papers/56_三模型原生椭球包络综合/fig56_native_ellipsoid_cross_model_synthesis.png"
LABELS = {
    "chwirut1": "Chwirut1 native exponential",
    "roszman1": "Roszman1 native arctangent",
    "enso": "ENSO native Fourier",
}
CERTIFICATES = {
    "chwirut1": "positive exponential denominator over each frozen interval",
    "roszman1": "negative x-b4 denominator at both endpoints; crossing is unavailable",
    "enso": "strictly positive b4 and b7 Fourier periods in the selected ellipsoid",
}
NULL_POINT_FIELDS = [
    "prediction_minimum", "prediction_maximum", "residual_upper_bound", "covered",
    "envelope_width", "center_prediction_inside",
]


def median(values):
    return float(np.median(values)) if values else None


def recompute_fold(dataset_id, source_fold):
    points = source_fold["points"]
    envelopes = source_fold["envelopes"]
    envelope_by_x = {}
    for envelope in envelopes:
        x = float(envelope["x"])
        if x in envelope_by_x:
            raise ValueError(f"Duplicate envelope coordinate: {dataset_id}:{source_fold['fold']}:{x}")
        if not math.isfinite(envelope["prediction_minimum"]) or not math.isfinite(envelope["prediction_maximum"]) or envelope["prediction_minimum"] > envelope["prediction_maximum"]:
            raise ValueError(f"Invalid frozen envelope: {dataset_id}:{source_fold['fold']}:{x}")
        envelope_by_x[x] = envelope
    available = 0
    covered = 0
    violations = 0
    unavailable = 0
    mismatch = 0
    for point in points:
        is_available = point["residual_upper_bound"] is not None
        if is_available:
            available += 1
            covered += point["covered"] is True
            violations += point["covered"] is False
            x = float(point["x"])
            if x not in envelope_by_x:
                raise ValueError(f"Available point lacks an envelope: {dataset_id}:{source_fold['fold']}:{x}")
            envelope = envelope_by_x[x]
            for key in ["prediction_minimum", "prediction_maximum", "envelope_width"]:
                if point[key] != envelope[key]:
                    raise ValueError(f"Point-envelope mismatch: {dataset_id}:{source_fold['fold']}:{x}:{key}")
            lower = point["prediction_minimum"]
            upper = point["prediction_maximum"]
            residual_bound = point["residual_upper_bound"]
            if any(point[key] is None for key in NULL_POINT_FIELDS):
                raise ValueError(f"Available point has null fields: {dataset_id}:{source_fold['fold']}:{x}")
            if lower > upper or not lower <= point["native_prediction"] <= upper:
                mismatch += 1
            if residual_bound < point["actual_absolute_residual"] or not point["covered"] or not point["center_prediction_inside"]:
                mismatch += 1
            if not math.isclose(point["envelope_width"], upper - lower, rel_tol=1.0e-12, abs_tol=1.0e-12):
                raise ValueError(f"Envelope-width identity failed: {dataset_id}:{source_fold['fold']}:{x}")
        else:
            unavailable += 1
            if any(point[key] is not None for key in NULL_POINT_FIELDS):
                raise ValueError(f"Unavailable point received a bound: {dataset_id}:{source_fold['fold']}:{point['point_index']}")
    widths = [envelope["envelope_width"] for envelope in envelopes]
    residual_bounds = [point["residual_upper_bound"] for point in points if point["residual_upper_bound"] is not None]
    coverage = {
        "available_point_count": available,
        "covered_point_count": covered,
        "violation_point_count": violations,
        "unavailable_point_count": unavailable,
        "center_prediction_envelope_mismatch_count": mismatch,
    }
    metrics = {
        "max_envelope_width": max(widths) if widths else None,
        "median_envelope_width": median(widths),
        "max_residual_upper_bound": max(residual_bounds) if residual_bounds else None,
        "median_residual_upper_bound": median(residual_bounds),
    }
    source_mismatch = int(coverage != source_fold["coverage"])
    source_mismatch += sum(metrics[key] != source_fold[key] for key in metrics)
    available_flag = source_fold["prediction_envelope_available"]
    if available_flag != bool(envelopes) or available + unavailable != len(points) or covered + violations != available:
        raise ValueError(f"Frozen fold availability or point accounting changed: {dataset_id}:{source_fold['fold']}")
    return {
        "fold": source_fold["fold"],
        "fold_id": f"{dataset_id}:{source_fold['fold']}",
        "point_count": len(points),
        "native_test_rmse": source_fold["native_test_rmse"],
        "prediction_envelope_available": available_flag,
        "coverage": coverage,
        "envelope_count": len(envelopes),
        **metrics,
        "recomputed_source_mismatch_count": source_mismatch,
    }


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_native_ellipsoid_cross_model_synthesis":
        raise ValueError("Native ellipsoid cross-model protocol is not frozen")
    datasets = []
    for dataset_id in ["chwirut1", "roszman1", "enso"]:
        bounds_info = protocol["inputs"][f"{dataset_id}_bounds"]
        receipt_info = protocol["inputs"][f"{dataset_id}_receipt"]
        source_path = ROOT / bounds_info["file"]
        receipt_path = ROOT / receipt_info["file"]
        source_hash = sha256(source_path)
        receipt_hash = sha256(receipt_path)
        if source_hash != bounds_info["sha256"] or receipt_hash != receipt_info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {dataset_id}")
        source = json.loads(source_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        source_receipt_verified = receipt["status"] == "passed" and receipt["summarySha256"] == source_hash
        if not source_receipt_verified:
            raise ValueError(f"Frozen source receipt does not match: {dataset_id}")
        folds = [recompute_fold(dataset_id, fold) for fold in source["folds"]]
        widths = [envelope["envelope_width"] for fold in source["folds"] for envelope in fold["envelopes"]]
        residual_bounds = [point["residual_upper_bound"] for fold in source["folds"] for point in fold["points"] if point["residual_upper_bound"] is not None]
        coverage = {
            key: sum(fold["coverage"][key] for fold in folds)
            for key in ["available_point_count", "covered_point_count", "violation_point_count", "unavailable_point_count", "center_prediction_envelope_mismatch_count"]
        }
        totals = {
            "fold_count": len(folds),
            "held_out_point_count": sum(fold["point_count"] for fold in folds),
            "certified_fold_count": sum(fold["prediction_envelope_available"] for fold in folds),
            "certified_fold_ids": [fold["fold"] for fold in folds if fold["prediction_envelope_available"]],
            "unavailable_fold_ids": [fold["fold"] for fold in folds if not fold["prediction_envelope_available"]],
            **coverage,
            "unique_envelope_count": sum(fold["envelope_count"] for fold in folds),
            "max_envelope_width": max(widths) if widths else None,
            "median_envelope_width": median(widths),
            "max_residual_upper_bound": max(residual_bounds) if residual_bounds else None,
            "median_residual_upper_bound": median(residual_bounds),
        }
        source_mismatch = sum(fold["recomputed_source_mismatch_count"] for fold in folds)
        for key in [
            "fold_count", "held_out_point_count", "certified_fold_count", "certified_fold_ids", "unavailable_fold_ids",
            "available_point_count", "covered_point_count", "violation_point_count", "unavailable_point_count",
            "center_prediction_envelope_mismatch_count", "unique_envelope_count", "max_envelope_width",
            "median_envelope_width", "max_residual_upper_bound", "median_residual_upper_bound",
        ]:
            source_mismatch += totals[key] != source["totals"][key]
        for fold in folds:
            if fold["prediction_envelope_available"]:
                fold["normalization"] = {
                    "max_width_to_dataset_median": fold["max_envelope_width"] / totals["median_envelope_width"],
                    "max_residual_to_dataset_median": fold["max_residual_upper_bound"] / totals["median_residual_upper_bound"],
                }
            else:
                fold["normalization"] = {
                    "max_width_to_dataset_median": None,
                    "max_residual_to_dataset_median": None,
                }
        scope_specific = {}
        if dataset_id == "chwirut1":
            related = source["analysis_scope"]["related_prior_dataset"]
            scope_specific = {
                "related_prior_dataset": related["name"],
                "same_study": related["same_study"],
                "same_native_model_family": related["same_native_model_family"],
                "independent_model_family_test": related["independent_model_family_or_laboratory_replication"],
            }
        elif dataset_id == "roszman1":
            scope_specific = {
                "minimum_critical_sign_radius": source["totals"]["minimum_critical_sign_radius"],
                "minimum_critical_sign_radius_fold": source["totals"]["minimum_critical_sign_radius_fold"],
                "fold5_native_test_rmse": folds[4]["native_test_rmse"],
                "fold5_unavailable_point_count": folds[4]["coverage"]["unavailable_point_count"],
            }
        else:
            scope_specific = {
                "minimum_critical_period_radius": source["totals"]["minimum_critical_period_radius"],
                "minimum_critical_period_radius_fold": source["totals"]["minimum_critical_period_radius_fold"],
                "minimum_critical_period_parameter": source["totals"]["minimum_critical_period_parameter"],
            }
        expected = protocol["expected_structure"]["per_dataset"][dataset_id]
        actual = {
            "folds": totals["fold_count"],
            "points": totals["held_out_point_count"],
            "available": totals["available_point_count"],
            "unavailable": totals["unavailable_point_count"],
            "envelopes": totals["unique_envelope_count"],
        }
        if actual != expected:
            raise ValueError(f"Frozen per-dataset structure changed: {dataset_id}: {actual}")
        datasets.append({
            "id": dataset_id,
            "label": LABELS[dataset_id],
            "certificate": CERTIFICATES[dataset_id],
            "unit_scope": "Model-specific response units; raw values are never pooled across datasets",
            "source_file": bounds_info["file"],
            "source_sha256": source_hash,
            "receipt_file": receipt_info["file"],
            "receipt_sha256": receipt_hash,
            "source_receipt_verified": source_receipt_verified,
            "recomputed_source_mismatch_count": source_mismatch,
            "folds": folds,
            "totals": totals,
            "normalization_scope": "Each fold maximum is divided only by this dataset's available-point median; descriptive, not a score",
            "scope_specific": scope_specific,
            "known_answer": source.get("known_answer"),
        })
        if source_mismatch:
            raise ValueError(f"Frozen source projection mismatch: {dataset_id}: {source_mismatch}")

    totals = {
        "dataset_count": len(datasets),
        "fold_count": sum(dataset["totals"]["fold_count"] for dataset in datasets),
        "held_out_point_count": sum(dataset["totals"]["held_out_point_count"] for dataset in datasets),
        "certified_fold_count": sum(dataset["totals"]["certified_fold_count"] for dataset in datasets),
        "available_point_count": sum(dataset["totals"]["available_point_count"] for dataset in datasets),
        "covered_point_count": sum(dataset["totals"]["covered_point_count"] for dataset in datasets),
        "violation_point_count": sum(dataset["totals"]["violation_point_count"] for dataset in datasets),
        "unavailable_point_count": sum(dataset["totals"]["unavailable_point_count"] for dataset in datasets),
        "unique_envelope_count": sum(dataset["totals"]["unique_envelope_count"] for dataset in datasets),
        "center_prediction_envelope_mismatch_count": sum(dataset["totals"]["center_prediction_envelope_mismatch_count"] for dataset in datasets),
        "source_receipt_verified_count": sum(dataset["source_receipt_verified"] for dataset in datasets),
        "source_projection_mismatch_count": sum(dataset["recomputed_source_mismatch_count"] for dataset in datasets),
        "unavailable_fold_ids": [fold["fold_id"] for dataset in datasets for fold in dataset["folds"] if not fold["prediction_envelope_available"]],
        "refit_count": 0,
        "baseline_radius": protocol["baseline_rule"]["radius"],
    }
    expected = protocol["expected_structure"]
    for key in [
        "dataset_count", "fold_count", "held_out_point_count", "certified_fold_count", "available_point_count",
        "covered_point_count", "violation_point_count", "unavailable_point_count", "unique_envelope_count",
        "center_prediction_envelope_mismatch_count", "refit_count", "baseline_radius",
    ]:
        if totals[key] != expected[key]:
            raise ValueError(f"Frozen structural expectation failed: {key}")
    return {
        "status": "computed_native_ellipsoid_cross_model_synthesis",
        "protocol_sha256": sha256(protocol_path),
        "analysis_scope": {
            **protocol["analysis_scope"],
            "refit": False,
            "post_hoc": True,
            "all_frozen_folds_and_points_retained": True,
            "source_receipts_verified": True,
            "normalization_is_probability": False,
            "joint_nonlinear_optimum": False,
        },
        "datasets": datasets,
        "totals": totals,
        "cross_dataset_pooled_error_metrics": None,
        "cross_dataset_pooled_envelope_widths": None,
        "cross_dataset_pooled_residual_upper_bounds": None,
        "cross_dataset_stability_score": None,
        "universal_model_winner": None,
        "probability_coverage": None,
        "decision": protocol["decision"],
        "limitations": [
            "Three datasets provide fifteen related diagnostic folds, not independent probability samples or a universal model ranking",
            "Availability and center-consistency counts are arithmetic diagnostics, not probability coverage or external scientific validation",
            "Raw widths, residual bounds, RMSE values, parameters and covariance matrices remain in model-specific units and are never pooled",
            "Within-dataset normalization describes relative dispersion only and is not a calibrated uncertainty, physical effect size or stability score",
            "Roszman1 fold 5 retains five unavailable points and null bounds; low RMSE does not remove its denominator crossing",
            "Chwirut1 shares its study and native model family with Chwirut2; positive denominators do not make wide bounds highly informative",
            "ENSO positive periods do not establish unique or physical periods; optimizer mismatch and certified forward evaluation remain separate from holdout evidence",
            "The envelopes are conservative model-specific relaxations, not joint nonlinear optima or independent physical experiments",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    actual_ratios = [fold.get("normalization") for dataset in summary.get("datasets", []) for fold in dataset.get("folds", [])]
    expected_ratios = [fold["normalization"] for dataset in expected["datasets"] for fold in dataset["folds"]]
    if actual_ratios != expected_ratios:
        errors.append("Within-dataset normalization ratio mismatch")
    if summary.get("totals", {}).get("unavailable_point_count") != 5 or summary.get("totals", {}).get("unavailable_fold_ids") != ["roszman1:5"]:
        errors.append("Unavailable fold or point accounting mismatch")
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
    datasets = summary["datasets"]
    colors = {"chwirut1": "#316c9b", "roszman1": "#b44b4b", "enso": "#4f7b5b"}
    fig, axes = plt.subplots(2, 2, figsize=(16.0, 11.5), constrained_layout=True)
    ids = [dataset["id"] for dataset in datasets]
    x = np.arange(len(ids))
    available = [dataset["totals"]["available_point_count"] for dataset in datasets]
    unavailable = [dataset["totals"]["unavailable_point_count"] for dataset in datasets]
    axes[0, 0].bar(x, available, color=[colors[dataset_id] for dataset_id in ids], label="available")
    axes[0, 0].bar(x, unavailable, bottom=available, color="#b44b4b", label="unavailable")
    for index, dataset in enumerate(datasets):
        axes[0, 0].text(index, dataset["totals"]["held_out_point_count"] + 5, f"{dataset['totals']['held_out_point_count']} points\n{dataset['totals']['unique_envelope_count']} envelopes", ha="center", fontsize=9)
    axes[0, 0].set_xticks(x, ids)
    axes[0, 0].set_ylim(0, 255)
    axes[0, 0].set_ylabel("Frozen held-out points")
    axes[0, 0].set_title("A. Complete point accounting, not success rates")
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 0].grid(axis="y", alpha=0.2)

    for dataset in datasets:
        folds = dataset["folds"]
        numbers = [fold["fold"] for fold in folds]
        fractions = [fold["coverage"]["available_point_count"] / fold["point_count"] for fold in folds]
        axes[0, 1].plot(numbers, fractions, "o-", color=colors[dataset["id"]], label=dataset["id"])
    axes[0, 1].set_xticks([1, 2, 3, 4, 5])
    axes[0, 1].set_ylim(-0.05, 1.08)
    axes[0, 1].set_xlabel("Frozen fold")
    axes[0, 1].set_ylabel("Available points / fold points")
    axes[0, 1].set_title("B. Roszman1 fold 5 remains unavailable")
    axes[0, 1].grid(alpha=0.2)
    axes[0, 1].legend(frameon=False, fontsize=8)

    for dataset in datasets:
        folds = dataset["folds"]
        numbers = [fold["fold"] for fold in folds]
        width_ratios = [fold["normalization"]["max_width_to_dataset_median"] if fold["prediction_envelope_available"] else np.nan for fold in folds]
        residual_ratios = [fold["normalization"]["max_residual_to_dataset_median"] if fold["prediction_envelope_available"] else np.nan for fold in folds]
        axes[1, 0].plot(numbers, width_ratios, "o-", color=colors[dataset["id"]], label=dataset["id"])
        axes[1, 1].plot(numbers, residual_ratios, "o-", color=colors[dataset["id"]], label=dataset["id"])
    for axis, title, ylabel in [
        (axes[1, 0], "C. Fold maximum width / own-dataset median", "Within-dataset width ratio (log)"),
        (axes[1, 1], "D. Fold maximum residual bound / own-dataset median", "Within-dataset residual-bound ratio (log)"),
    ]:
        axis.set_yscale("log")
        axis.set_xticks([1, 2, 3, 4, 5])
        axis.set_xlabel("Frozen fold")
        axis.set_ylabel(ylabel)
        axis.set_title(title)
        axis.grid(which="both", alpha=0.2)
        axis.legend(frameon=False, fontsize=8)

    fig.suptitle("Native ellipsoid envelopes: 3 models, 15 folds, 407 points, 210 available envelopes", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Within-dataset normalization only. No pooled raw widths or errors, probability coverage, universal winner or stability score.",
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
            errors.append("Missing native ellipsoid cross-model synthesis")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored native ellipsoid cross-model synthesis is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid native ellipsoid cross-model figure")
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "datasets": summary["totals"]["dataset_count"],
        "folds": summary["totals"]["fold_count"],
        "points": summary["totals"]["held_out_point_count"],
        "available": summary["totals"]["available_point_count"],
        "unavailable": summary["totals"]["unavailable_point_count"],
        "envelopes": summary["totals"]["unique_envelope_count"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
