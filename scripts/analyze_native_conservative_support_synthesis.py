"""Read-only synthesis of the three latest conservative-support studies."""

import argparse
import json
from pathlib import Path

from analyze_chwirut_holdout import sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/native-conservative-support-synthesis-protocol.json"
OUT = ROOT / "exports/native-conservative-support-synthesis.json"
FIGURE = ROOT / "papers/62_三模型保守支撑综合/fig62_native_conservative_support_synthesis.png"


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_native_conservative_support_synthesis":
        raise ValueError("Native conservative-support synthesis protocol is not frozen")
    for key, info in protocol["inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {key}")
    sources = {
        dataset_id: json.loads((ROOT / protocol["inputs"][f"{dataset_id}_bounds"]["file"]).read_text(encoding="utf-8"))
        for dataset_id in ["chwirut1", "roszman1", "enso"]
    }
    datasets = []
    for dataset_id in ["chwirut1", "roszman1", "enso"]:
        source = sources[dataset_id]
        receipt = json.loads((ROOT / protocol["inputs"][f"{dataset_id}_receipt"]["file"]).read_text(encoding="utf-8"))
        source_hash = sha256(ROOT / protocol["inputs"][f"{dataset_id}_bounds"]["file"])
        receipt_verified = receipt["status"] == "passed" and receipt["summarySha256"] == source_hash
        if not receipt_verified:
            raise ValueError(f"Frozen source receipt mismatch: {dataset_id}")
        source_totals = source["totals"]
        if dataset_id == "chwirut1":
            totals = {
                "held_out_point_count": source_totals["held_out_point_count"],
                "available_point_count": source_totals["covered_point_count"],
                "unavailable_point_count": 0,
                "unique_envelope_count": source_totals["unique_distance_count"],
                "tightened_envelope_count": source_totals["intersection_tightened_count"],
                "unchanged_envelope_count": source_totals["intersection_unchanged_count"],
                "nonempty_intersection_count": source_totals["nonempty_intersection_count"],
                "candidate_evaluation_count": source_totals["candidate_evaluation_count"],
                "candidate_violation_count": source_totals["alternative_candidate_violation_count"] + source_totals["intersection_candidate_violation_count"] + source_totals["independent_candidate_violation_count"],
                "center_prediction_mismatch_count": source_totals["center_prediction_mismatch_count"],
            }
            ratio_summary = {
                "minimum": source_totals["min_intersection_to_independent_width_ratio"],
                "median": source_totals["median_intersection_to_independent_width_ratio"],
                "maximum": source_totals["max_intersection_to_independent_width_ratio"],
                "max_width_reduction": source_totals["max_intersection_width_reduction"],
                "scope": "Chwirut1 log alternative/intersection relative to stage-44 independent envelope; not cross-model comparable",
            }
            baseline = "Stage-44 independent exponential/denominator interval"
            method = "Denominator secants and three frozen log tangents with full covariance support"
            related = source["related_prior_dataset"]
            known_answer = None
            expected = {
                "held_out_point_count": 214,
                "unique_envelope_count": 22,
                "tightened_envelope_count": 22,
                "candidate_evaluation_count": 132,
                "nonempty_intersection_count": 22,
            }
        elif dataset_id == "roszman1":
            totals = {
                "held_out_point_count": source_totals["held_out_point_count"],
                "available_point_count": source_totals["available_point_count"],
                "unavailable_point_count": source_totals["unavailable_point_count"],
                "unavailable_fold_ids": source_totals["unavailable_fold_ids"],
                "unique_envelope_count": source_totals["intersection_bound_count"],
                "tightened_envelope_count": source_totals["intersection_tightened_count"],
                "unchanged_envelope_count": source_totals["intersection_unchanged_count"],
                "nonempty_intersection_count": source_totals["nonempty_intersection_count"],
                "candidate_evaluation_count": source_totals["candidate_evaluation_count"],
                "candidate_violation_count": source_totals["alternative_candidate_violation_count"] + source_totals["intersection_candidate_violation_count"] + source_totals["independent_candidate_violation_count"],
                "center_prediction_mismatch_count": source_totals["center_prediction_mismatch_count"],
            }
            ratio_summary = {
                "minimum": source_totals["min_intersection_to_independent_width_ratio"],
                "median": source_totals["median_intersection_to_independent_width_ratio"],
                "maximum": source_totals["max_intersection_to_independent_width_ratio"],
                "max_width_reduction": source_totals["max_intersection_width_reduction"],
                "scope": "Roszman1 joint-linear alternative/intersection relative to stage-46 independent envelope; not cross-model comparable",
            }
            baseline = "Stage-46 independent linear/arctangent interval"
            method = "Joint ellipsoid support for b1-b2*x with the frozen arctangent interval"
            related = None
            known_answer = source.get("known_answer")
            expected = {
                "held_out_point_count": 25,
                "available_point_count": 20,
                "unavailable_point_count": 5,
                "unavailable_fold_ids": [5],
                "tightened_envelope_count": 20,
                "candidate_evaluation_count": 160,
                "nonempty_intersection_count": 20,
            }
        else:
            totals = {
                "held_out_point_count": source_totals["held_out_point_count"],
                "available_point_count": source_totals["held_out_point_count"],
                "unavailable_point_count": 0,
                "unique_envelope_count": source_totals["triple_intersection_bound_count"],
                "tightened_envelope_count": source_totals["triple_tightened_count"],
                "unchanged_envelope_count": source_totals["triple_unchanged_count"],
                "nonempty_intersection_count": source_totals["nonempty_triple_intersection_count"],
                "candidate_evaluation_count": source_totals["candidate_evaluation_count"],
                "candidate_violation_count": source_totals["phase_candidate_violation_count"] + source_totals["triple_candidate_violation_count"],
                "center_prediction_mismatch_count": source_totals["center_prediction_mismatch_count"],
            }
            ratio_summary = {
                "minimum": source_totals["min_triple_to_lipschitz_width_ratio"],
                "median": source_totals["median_triple_to_lipschitz_width_ratio"],
                "maximum": source_totals["max_triple_to_lipschitz_width_ratio"],
                "max_width_reduction": source_totals["max_triple_width_reduction"],
                "scope": "ENSO phase/triple intersection relative to stage-51 Lipschitz intersection; not cross-model comparable",
            }
            baseline = "Stage-51 Lipschitz intersection"
            method = "Exact trigonometric interval arithmetic and product intervals with a triple intersection"
            related = None
            known_answer = source["known_answer"]
            expected = {
                "held_out_point_count": 168,
                "unique_envelope_count": 168,
                "tightened_envelope_count": 37,
                "unchanged_envelope_count": 131,
                "candidate_evaluation_count": 672,
                "nonempty_intersection_count": 168,
            }
        mismatch_count = sum(totals[key] != value for key, value in expected.items())
        if mismatch_count:
            raise ValueError(f"Frozen source projection mismatch: {dataset_id}: {mismatch_count}")
        datasets.append({
            "id": dataset_id,
            "source_file": protocol["inputs"][f"{dataset_id}_bounds"]["file"],
            "source_sha256": source_hash,
            "source_receipt_verified": receipt_verified,
            "source_projection_mismatch_count": mismatch_count,
            "baseline": baseline,
            "method": method,
            "totals": totals,
            "ratio_summary": ratio_summary,
            "largest_tightening": source_totals["largest_triple_tightening"] if dataset_id == "enso" else source_totals["largest_intersection_tightening"],
            "related_prior_dataset": related,
            "known_answer": known_answer,
            "folds": source["folds"],
        })
    totals = {
        "dataset_count": len(datasets),
        "held_out_point_count": sum(dataset["totals"]["held_out_point_count"] for dataset in datasets),
        "available_point_count": sum(dataset["totals"]["available_point_count"] for dataset in datasets),
        "unavailable_point_count": sum(dataset["totals"]["unavailable_point_count"] for dataset in datasets),
        "unavailable_fold_ids": ["roszman1:5"],
        "unique_envelope_count": sum(dataset["totals"]["unique_envelope_count"] for dataset in datasets),
        "tightened_envelope_count": sum(dataset["totals"]["tightened_envelope_count"] for dataset in datasets),
        "unchanged_envelope_count": sum(dataset["totals"]["unchanged_envelope_count"] for dataset in datasets),
        "nonempty_intersection_count": sum(dataset["totals"]["nonempty_intersection_count"] for dataset in datasets),
        "candidate_evaluation_count": sum(dataset["totals"]["candidate_evaluation_count"] for dataset in datasets),
        "candidate_violation_count": sum(dataset["totals"]["candidate_violation_count"] for dataset in datasets),
        "center_prediction_mismatch_count": sum(dataset["totals"]["center_prediction_mismatch_count"] for dataset in datasets),
        "source_receipt_verified_count": sum(dataset["source_receipt_verified"] for dataset in datasets),
        "source_projection_mismatch_count": sum(dataset["source_projection_mismatch_count"] for dataset in datasets),
        "refit_count": 0,
    }
    expected = protocol["expected_structure"]
    for key, value in expected.items():
        if totals[key] != value:
            raise ValueError(f"Frozen structural expectation failed: {key}")
    return {
        "status": "computed_native_conservative_support_synthesis",
        "protocol_sha256": sha256(protocol_path),
        "analysis_scope": protocol["analysis_scope"],
        "datasets": datasets,
        "totals": totals,
        "cross_dataset_pooled_error_metrics": None,
        "cross_dataset_raw_widths": None,
        "unified_stability_score": None,
        "probability_coverage": None,
        "global_optimum": None,
        "decision": protocol["decision"],
        "limitations": [
            "The three baselines are model-specific and are not interchangeable; no raw width, RMSE, covariance or residual-bound pooling is performed",
            "Inventory counts of tightened and unchanged envelopes are not probabilities, calibrated coverage or a unified stability score",
            "All 964 candidate evaluations are implementation-consistency checks, not a global optimality proof or independent physical experiment",
            "Roszman1 fold 5 retains five unavailable points and is not counted as available or tightened",
            "Chwirut1 shares its study and native model family with Chwirut2 and is not independent replication",
            "ENSO positive periods and candidate containment do not prove unique physical periods or external scientific validity",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    for key in ["tightened_envelope_count", "unchanged_envelope_count", "candidate_evaluation_count", "candidate_violation_count"]:
        if summary.get("totals", {}).get(key) != expected["totals"][key]:
            errors.append(f"Aggregate count mismatch: {key}")
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
    import numpy as np

    output_path = Path(output_path)
    datasets = summary["datasets"]
    labels = [dataset["id"] for dataset in datasets]
    colors = ["#316c9b", "#876a32", "#4f7b5b"]
    positions = np.arange(len(labels))
    fig, axes = plt.subplots(2, 2, figsize=(16.0, 11.5), constrained_layout=True)

    tightened = [dataset["totals"]["tightened_envelope_count"] for dataset in datasets]
    unchanged = [dataset["totals"]["unchanged_envelope_count"] for dataset in datasets]
    axes[0, 0].bar(positions, tightened, color=colors, label="tightened")
    axes[0, 0].bar(positions, unchanged, bottom=tightened, color="#999999", label="unchanged")
    for index, dataset in enumerate(datasets):
        axes[0, 0].text(index, dataset["totals"]["unique_envelope_count"] + 5, f"{dataset['totals']['unique_envelope_count']} envelopes", ha="center", fontsize=9)
    axes[0, 0].set_xticks(positions, labels)
    axes[0, 0].set_ylim(0, 205)
    axes[0, 0].set_ylabel("Unique-envelope count")
    axes[0, 0].set_title("A. Inventory, not a probability or unified score")
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 0].grid(axis="y", alpha=0.2)

    width = 0.22
    for index, dataset in enumerate(datasets):
        ratio = dataset["ratio_summary"]
        axes[0, 1].plot([index - width, index + width], [ratio["minimum"], ratio["maximum"]], color=colors[index], linewidth=2)
        axes[0, 1].scatter(index, ratio["median"], color=colors[index], s=48, zorder=3)
        axes[0, 1].text(index, ratio["maximum"] * 1.08, f"median {ratio['median']:.3f}", ha="center", fontsize=8)
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_xticks(positions, labels)
    axes[0, 1].set_ylabel("Within-model width ratio (log)")
    axes[0, 1].set_title("B. Model-specific baselines; no direct ranking")
    axes[0, 1].grid(which="both", alpha=0.2)

    candidates = [dataset["totals"]["candidate_evaluation_count"] for dataset in datasets]
    bars = axes[1, 0].bar(positions, candidates, color=colors, width=0.55)
    for bar, value in zip(bars, candidates):
        axes[1, 0].text(bar.get_x() + bar.get_width() / 2, value + 15, str(value), ha="center", fontsize=9)
    axes[1, 0].set_ylim(0, 760)
    axes[1, 0].set_xticks(positions, labels)
    axes[1, 0].set_ylabel("Candidate evaluations")
    axes[1, 0].set_title("C. Consistency checks, not global optimizers")
    axes[1, 0].grid(axis="y", alpha=0.2)

    available = [dataset["totals"]["available_point_count"] for dataset in datasets]
    unavailable = [dataset["totals"]["unavailable_point_count"] for dataset in datasets]
    axes[1, 1].bar(positions, available, color=colors, label="available")
    axes[1, 1].bar(positions, unavailable, bottom=available, color="#b44b4b", label="unavailable")
    axes[1, 1].set_xticks(positions, labels)
    axes[1, 1].set_ylabel("Held-out observations")
    axes[1, 1].set_title("D. Roszman1 fold 5 remains unavailable")
    axes[1, 1].legend(frameon=False, fontsize=8)
    axes[1, 1].grid(axis="y", alpha=0.2)

    totals = summary["totals"]
    fig.suptitle(f"Conservative support synthesis: {totals['unique_envelope_count']} envelopes, {totals['tightened_envelope_count']} tightened, {totals['unchanged_envelope_count']} unchanged", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Three model-specific baselines and receipts. No raw-width pooling, unified stability score, global optimum or independent-experiment claim.",
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
            errors.append("Missing native conservative-support synthesis")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored native conservative-support synthesis is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid native conservative-support figure")
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "envelopes": summary["totals"]["unique_envelope_count"],
        "tightened": summary["totals"]["tightened_envelope_count"],
        "unchanged": summary["totals"]["unchanged_envelope_count"],
        "candidates": summary["totals"]["candidate_evaluation_count"],
        "unavailable": summary["totals"]["unavailable_point_count"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
