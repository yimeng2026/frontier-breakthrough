"""Exploratory numerical pole localization for the frozen Hahn1 fold fits."""

import json
from pathlib import Path

import numpy as np

from analyze_chwirut_holdout import sha256
from analyze_grouped_stress import make_contiguous_folds
from analyze_hahn1_fold1_identifiability import denominator_values
from analyze_hahn1_high_temperature import PARAMETER_NAMES, load_hahn_data
from rational_gate import rational_root_records

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/hahn1-frozen-denominator-roots-protocol.json"
SOURCE = ROOT / "validation/hahn1-fold1-identifiability.json"
OUT = ROOT / "validation/hahn1-frozen-denominator-roots.json"


def polynomial_root_records(parameters):
    return rational_root_records(parameters, PARAMETER_NAMES[:4], PARAMETER_NAMES[4:])


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_exploratory_root_localization":
        raise ValueError("Root-localization protocol is not frozen")
    if sha256(SOURCE) != protocol["inputs"]["diagnostic_sha256"]:
        raise ValueError("Identifiability diagnostic input hash changed")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    x, y = load_hahn_data(
        ROOT / protocol["inputs"]["raw_data_file"],
        protocol["inputs"]["raw_data_sha256"],
    )
    masks = make_contiguous_folds(x, 5)
    folds = []
    for (train, test), frozen in zip(masks, source["folds"]):
        parameters = frozen["model_parameters"]
        all_roots = polynomial_root_records(parameters)
        real_roots = []
        for root in all_roots:
            if not root["is_real"]:
                continue
            root_x = root["root_x"]
            nearest_train_x = float(x[train][np.argmin(np.abs(x[train] - root_x))])
            nearest_test_x = float(x[test][np.argmin(np.abs(x[test] - root_x))])
            enriched = dict(root)
            enriched.update({
                "within_held_out_closed_interval": bool(frozen["interval"]["test_x_min"] <= root_x <= frozen["interval"]["test_x_max"]),
                "strictly_between_minimum_and_maximum_held_out_x": bool(frozen["interval"]["test_x_min"] < root_x < frozen["interval"]["test_x_max"]),
                "within_full_observed_x_range": bool(np.min(x) <= root_x <= np.max(x)),
                "nearest_training_observation_x": nearest_train_x,
                "nearest_training_observation_distance_x": float(abs(nearest_train_x - root_x)),
                "nearest_held_out_observation_x": nearest_test_x,
                "nearest_held_out_observation_distance_x": float(abs(nearest_test_x - root_x)),
            })
            real_roots.append(enriched)
        folds.append({
            "fold": frozen["fold"],
            "model_parameters": parameters,
            "held_out_interval": frozen["interval"],
            "all_numerical_roots": all_roots,
            "real_roots": real_roots,
            "real_root_count_in_held_out_closed_interval": sum(root["within_held_out_closed_interval"] for root in real_roots),
            "test_rmse": frozen["test_metrics"]["rmse"],
            "baseline_test_rmse": frozen["baseline_test_metrics"]["rmse"],
        })
    return {
        "status": "computed_exploratory_frozen_hahn1_denominator_roots",
        "protocol_sha256": sha256(PROTOCOL),
        "diagnostic_sha256": sha256(SOURCE),
        "data_sha256": protocol["inputs"]["raw_data_sha256"],
        "analysis_scope": {
            "exploratory_follow_up": True,
            "preregistered": False,
            "refit": False,
            "new_model_or_parameters": False,
            "exact_algebraic_proof": False,
        },
        "folds": folds,
        "decision": {
            "fold_1_failure_reversed": False,
            "certified_full_fit_proof_applied_to_fold_parameters": False,
            "interpretation": "Different fold-specific coefficients require separate denominator audits; numerical roots explain local blow-up without ranking the whole rational family",
        },
        "limitations": [
            "Numerical roots and residuals are not exact algebraic certificates",
            "A simple-pole diagnosis requires the reported nonzero numerator and derivative at the numerical root; no removable singularity is assumed",
            "The earlier certified full-fit denominator proof applies to different coefficients and cannot be transferred to these fold fits",
            "Root localization is post-hoc mechanism evidence and does not make the failed fold successful",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def main():
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite: {OUT}")
    summary = analyze()
    first = summary["folds"][0]
    if first["test_rmse"] <= first["baseline_test_rmse"]:
        raise ValueError("Fold 1 failure changed")
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUT),
        "folds": [{
            "fold": fold["fold"],
            "real_roots": [{
                "root_x": root["root_x"],
                "within_held_out_closed_interval": root["within_held_out_closed_interval"],
                "numerator_at_root": root["numerator_at_root"],
                "denominator_derivative_at_root": root["denominator_derivative_at_root"],
                "absolute_denominator_residual": root["absolute_denominator_residual"],
                "nearest_training_observation_distance_x": root["nearest_training_observation_distance_x"],
                "nearest_held_out_observation_distance_x": root["nearest_held_out_observation_distance_x"],
            } for root in fold["real_roots"]],
        } for fold in summary["folds"]],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
