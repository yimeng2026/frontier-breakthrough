"""Certify ENSO fixed-period joint coefficient slices and test full-region export."""

import argparse
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np

from analyze_chwirut_holdout import sha256
from analyze_enso_native_ellipsoid_continuous import PARAMETER_NAMES
from analyze_enso_native_holdout import native_model
from analyze_roszman1_native_ellipsoid_continuous import outward, support_value

mp.mp.dps = 80
ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/enso-conditional-period-slice-protocol.json"
AMENDMENT = ROOT / "validation/enso-conditional-period-slice-protocol-amendment-01.json"
OUT = ROOT / "validation/enso-conditional-period-slice-bounds.json"
FIGURE = ROOT / "papers/57_ENSO条件周期切片界/fig57_enso_conditional_period_slice_bounds.png"
COEFFICIENTS = ["b1", "b2", "b3", "b5", "b6", "b8", "b9"]
COEFFICIENT_INDICES = [0, 1, 2, 4, 5, 7, 8]
PERIOD_INDICES = [3, 6]
DIRECTIONS = [("b4_minus", "b4", -1), ("b4_plus", "b4", 1), ("b7_minus", "b7", -1), ("b7_plus", "b7", 1)]


def _conditional_matrix(covariance):
    matrix = mp.matrix([[mp.mpf(str(value)) for value in row] for row in covariance])
    mp.cholesky(matrix)
    c_cc = mp.matrix([[matrix[row, column] for column in COEFFICIENT_INDICES] for row in COEFFICIENT_INDICES])
    c_cp = mp.matrix([[matrix[row, column] for column in PERIOD_INDICES] for row in COEFFICIENT_INDICES])
    c_pp = mp.matrix([[matrix[row, column] for column in PERIOD_INDICES] for row in PERIOD_INDICES])
    c_pc = mp.matrix([[matrix[row, column] for column in COEFFICIENT_INDICES] for row in PERIOD_INDICES])
    determinant = c_pp[0, 0] * c_pp[1, 1] - c_pp[0, 1] * c_pp[1, 0]
    if determinant <= 0:
        raise ValueError("Period covariance block must be positive definite")
    c_pp_inverse = mp.matrix([[c_pp[1, 1], -c_pp[0, 1]], [-c_pp[1, 0], c_pp[0, 0]]]) / determinant
    conditional = c_cc - c_cp * c_pp_inverse * c_pc
    conditional = (conditional + conditional.T) * mp.mpf("0.5")
    mp.cholesky(conditional)
    return conditional


def conditional_covariance(covariance):
    conditional = _conditional_matrix(covariance)
    return [[float(conditional[row, column]) for column in range(7)] for row in range(7)]


def trigonometric_vector(parameters, x):
    x = mp.mpf(str(x))
    annual = 2 * mp.pi * x / 12
    long_1 = 2 * mp.pi * x / mp.mpf(str(parameters["b4"]))
    long_2 = 2 * mp.pi * x / mp.mpf(str(parameters["b7"]))
    return [mp.mpf("1"), mp.cos(annual), mp.sin(annual), mp.cos(long_1), mp.sin(long_1), mp.cos(long_2), mp.sin(long_2)]


def fourier_value(parameters, x):
    vector = trigonometric_vector(parameters, x)
    return sum((mp.mpf(str(parameters[name])) * value for name, value in zip(COEFFICIENTS, vector)), mp.mpf("0"))


def slice_envelope(parameters, covariance, radius, x, conditional=None):
    conditional = _conditional_matrix(covariance) if conditional is None else conditional
    vector = trigonometric_vector(parameters, x)
    support_rows = [[conditional[row, column] for column in range(7)] for row in range(7)]
    support = support_value(support_rows, vector, radius)
    center = fourier_value(parameters, x)
    native = float(native_model(float(x), *[float(parameters[name]) for name in PARAMETER_NAMES]))
    if not math.isclose(float(center), native, rel_tol=1.0e-12, abs_tol=1.0e-12):
        raise ValueError("High-precision center prediction differs from the original native model")
    lower = outward(center - support, lower=True)
    upper = outward(center + support, lower=False)
    return {
        "x": float(x),
        "center_prediction": float(center),
        "slice_support": float(support),
        "prediction_minimum": lower,
        "prediction_maximum": upper,
        "envelope_width": outward(upper - lower, lower=False),
    }


def ellipsoid_quadratic(center, parameters, covariance):
    matrix = mp.matrix([[mp.mpf(str(value)) for value in row] for row in covariance])
    delta = mp.matrix([mp.mpf(str(parameters[name])) - mp.mpf(str(center[name])) for name in PARAMETER_NAMES])
    solved = mp.lu_solve(matrix, delta)
    return float((delta.T * solved)[0])


def period_candidates(parameters, covariance, radius):
    candidates = []
    matrix = mp.matrix([[mp.mpf(str(value)) for value in row] for row in covariance])
    for direction, period, sign in DIRECTIONS:
        index = PARAMETER_NAMES.index(period)
        vector = [0] * len(PARAMETER_NAMES)
        vector[index] = 1
        displacement = support_value(covariance, vector, radius)
        displacement_vector = [mp.mpf(str(radius)) * matrix[row, index] / mp.sqrt(matrix[index, index]) for row in range(len(PARAMETER_NAMES))]
        exact = {name: mp.mpf(str(parameters[name])) + sign * displacement_vector[row] for row, name in enumerate(PARAMETER_NAMES)}
        exact_parameters = {name: mp.nstr(exact[name], 80) for name in PARAMETER_NAMES}
        quadratic = ellipsoid_quadratic(parameters, exact_parameters, covariance)
        feasible = math.isclose(quadratic, radius ** 2, rel_tol=1.0e-10, abs_tol=1.0e-10) and exact["b4"] > 0 and exact["b7"] > 0
        candidates.append({
            "direction": direction,
            "period": period,
            "sign": sign,
            "displacement": float(displacement),
            "displacement_vector": [float(value) for value in displacement_vector],
            "parameters": {name: float(exact[name]) for name in PARAMETER_NAMES},
            "exact_parameters": exact_parameters,
            "ellipsoid_quadratic": quadratic,
            "feasible": feasible,
        })
    return candidates


def median(values):
    return float(np.median(values)) if values else None


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_enso_conditional_period_slice_bounds":
        raise ValueError("Conditional-period slice protocol is not frozen")
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    if amendment["original_protocol"]["sha256"] != sha256(protocol_path):
        raise ValueError("Support-direction amendment original protocol hash mismatch")
    for key, info in protocol["inputs"].items():
        if sha256(ROOT / info["file"]) != info["sha256"]:
            raise ValueError(f"Frozen input hash changed: {key}")
    source = json.loads((ROOT / protocol["inputs"]["native_identifiability"]["file"]).read_text(encoding="utf-8"))
    baseline = json.loads((ROOT / protocol["inputs"]["baseline_bounds"]["file"]).read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / protocol["inputs"]["baseline_receipt"]["file"]).read_text(encoding="utf-8"))
    baseline_hash = sha256(ROOT / protocol["inputs"]["baseline_bounds"]["file"])
    baseline_receipt_verified = receipt["status"] == "passed" and receipt["summarySha256"] == baseline_hash
    if not baseline_receipt_verified:
        raise ValueError("Stage-47 baseline receipt does not match its bounds file")
    radius = protocol["slice_rule"]["baseline_radius"]
    folds = []
    for source_fold, baseline_fold in zip(source["folds"], baseline["folds"]):
        if source_fold["fold"] != baseline_fold["fold"]:
            raise ValueError("Frozen fold order changed")
        parameters = source_fold["native_parameters"]
        covariance = source_fold["training_jacobian"]["parameter_covariance_matrix"]
        conditional_mp = _conditional_matrix(covariance)
        conditional = [[float(conditional_mp[row, column]) for column in range(7)] for row in range(7)]
        candidates = period_candidates(parameters, covariance, radius)
        baseline_envelopes = {float(envelope["x"]): envelope for envelope in baseline_fold["envelopes"]}
        baseline_points = {float(point["x"]): point for point in baseline_fold["points"]}
        envelopes = []
        containment_violations = 0
        independent_violations = 0
        feasibility_failures = 0
        center_mismatches = 0
        baseline_matches = 0
        for x in sorted(baseline_envelopes):
            independent = baseline_envelopes[x]
            slice_result = slice_envelope(parameters, covariance, radius, x, conditional_mp)
            center_prediction = baseline_points[x]["native_prediction"]
            if not math.isclose(slice_result["center_prediction"], center_prediction, rel_tol=1.0e-12, abs_tol=1.0e-12):
                center_mismatches += 1
            independent_minimum = independent["prediction_minimum"]
            independent_maximum = independent["prediction_maximum"]
            independent_width = independent["envelope_width"]
            if independent_minimum > slice_result["prediction_minimum"] or independent_maximum < slice_result["prediction_maximum"]:
                containment_violations += 1
            ratio = slice_result["envelope_width"] / independent_width
            reduction = independent_width - slice_result["envelope_width"]
            evaluations = []
            for candidate in candidates:
                prediction_mp = fourier_value(candidate["exact_parameters"], x)
                prediction = float(prediction_mp)
                native_prediction = float(native_model(float(x), *[candidate["parameters"][name] for name in PARAMETER_NAMES]))
                if not math.isclose(prediction, native_prediction, rel_tol=1.0e-12, abs_tol=1.0e-12):
                    raise ValueError("Candidate prediction differs from the original native model")
                below = prediction < slice_result["prediction_minimum"]
                above = prediction > slice_result["prediction_maximum"]
                outside = below or above
                exceedance = max(slice_result["prediction_minimum"] - prediction, prediction - slice_result["prediction_maximum"], 0.0)
                inside_independent = independent_minimum <= prediction <= independent_maximum
                if not candidate["feasible"]:
                    feasibility_failures += 1
                if not inside_independent:
                    independent_violations += 1
                evaluations.append({
                    "direction": candidate["direction"],
                    "x": float(x),
                    "prediction": prediction,
                    "ellipsoid_quadratic": candidate["ellipsoid_quadratic"],
                    "feasible": candidate["feasible"],
                    "outside_slice": outside,
                    "slice_exceedance": exceedance,
                    "inside_independent_baseline": inside_independent,
                })
            baseline_matches += 1
            envelopes.append({
                **slice_result,
                "independent_minimum": independent_minimum,
                "independent_maximum": independent_maximum,
                "independent_width": independent_width,
                "slice_to_independent_width_ratio": ratio,
                "width_reduction": reduction,
                "candidate_evaluations": evaluations,
            })
        if containment_violations or independent_violations or feasibility_failures or center_mismatches:
            raise ValueError(f"Conditional slice consistency failure: fold {source_fold['fold']}; containment={containment_violations}, independent={independent_violations}, feasibility={feasibility_failures}, centers={center_mismatches}")
        ratios = [envelope["slice_to_independent_width_ratio"] for envelope in envelopes]
        reductions = [envelope["width_reduction"] for envelope in envelopes]
        evaluations = [candidate for envelope in envelopes for candidate in envelope["candidate_evaluations"]]
        witnesses = [candidate for candidate in evaluations if candidate["outside_slice"]]
        largest = max(witnesses, key=lambda candidate: candidate["slice_exceedance"], default=None)
        if largest is not None:
            direction = next(item for item in candidates if item["direction"] == largest["direction"])
            largest = {**largest, "fold": source_fold["fold"], "parameters": direction["parameters"], "exact_parameters": direction["exact_parameters"]}
        folds.append({
            "fold": source_fold["fold"],
            "native_test_rmse": source_fold["test_metrics"]["rmse"],
            "conditional_covariance": conditional,
            "conditional_matrix_scope": "Schur complement for seven coefficients with b4 and b7 fixed; not marginal covariance or posterior covariance",
            "candidate_directions": candidates,
            "slice_envelopes": envelopes,
            "baseline_envelope_match_count": baseline_matches,
            "candidate_evaluation_count": len(evaluations),
            "slice_violation_evaluation_count": len(witnesses),
            "slice_violating_envelope_count": sum(any(candidate["outside_slice"] for candidate in envelope["candidate_evaluations"]) for envelope in envelopes),
            "full_independent_violation_count": independent_violations,
            "slice_containment_violation_count": containment_violations,
            "candidate_feasibility_failure_count": feasibility_failures,
            "center_prediction_mismatch_count": center_mismatches,
            "min_slice_to_independent_width_ratio": min(ratios),
            "median_slice_to_independent_width_ratio": median(ratios),
            "max_slice_to_independent_width_ratio": max(ratios),
            "max_width_reduction": max(reductions),
            "median_width_reduction": median(reductions),
            "max_slice_violation_exceedance": max((candidate["slice_exceedance"] for candidate in witnesses), default=0.0),
            "largest_violation_witness": largest,
        })

    envelopes = [envelope for fold in folds for envelope in fold["slice_envelopes"]]
    evaluations = [candidate for envelope in envelopes for candidate in envelope["candidate_evaluations"]]
    witnesses = [candidate for candidate in evaluations if candidate["outside_slice"]]
    largest = max((fold["largest_violation_witness"] for fold in folds if fold["largest_violation_witness"] is not None), key=lambda candidate: candidate["slice_exceedance"], default=None)
    ratios = [envelope["slice_to_independent_width_ratio"] for envelope in envelopes]
    reductions = [envelope["width_reduction"] for envelope in envelopes]
    totals = {
        "fold_count": len(folds),
        "held_out_point_count": len(envelopes),
        "slice_envelope_count": len(envelopes),
        "candidate_direction_count": sum(len(fold["candidate_directions"]) for fold in folds),
        "candidate_evaluation_count": len(evaluations),
        "slice_violation_evaluation_count": len(witnesses),
        "slice_violating_envelope_count": sum(any(candidate["outside_slice"] for candidate in envelope["candidate_evaluations"]) for envelope in envelopes),
        "slice_violating_direction_ids": sorted({f"enso:{fold['fold']}:{candidate['direction']}" for fold in folds for envelope in fold["slice_envelopes"] for candidate in envelope["candidate_evaluations"] if candidate["outside_slice"]}),
        "full_independent_violation_count": sum(fold["full_independent_violation_count"] for fold in folds),
        "slice_containment_violation_count": sum(fold["slice_containment_violation_count"] for fold in folds),
        "candidate_feasibility_failure_count": sum(fold["candidate_feasibility_failure_count"] for fold in folds),
        "center_prediction_mismatch_count": sum(fold["center_prediction_mismatch_count"] for fold in folds),
        "conditional_matrix_failure_count": 0,
        "min_slice_to_independent_width_ratio": min(ratios),
        "median_slice_to_independent_width_ratio": median(ratios),
        "max_slice_to_independent_width_ratio": max(ratios),
        "max_width_reduction": max(reductions),
        "median_width_reduction": median(reductions),
        "max_slice_violation_exceedance": max((candidate["slice_exceedance"] for candidate in witnesses), default=0.0),
        "largest_violation_witness": largest,
        "slice_global_validity": "falsified_by_feasible_candidate" if witnesses else "not_established",
        "refit_count": 0,
    }
    expected = protocol["expected_structure"]
    for key in ["fold_count", "held_out_point_count", "slice_envelope_count", "candidate_direction_count", "candidate_evaluation_count", "full_independent_violation_count", "refit_count"]:
        if totals[key] != expected[key]:
            raise ValueError(f"Frozen structural expectation failed: {key}")
    return {
        "status": "computed_enso_conditional_period_slice_bounds",
        "protocol_sha256": sha256(protocol_path),
        "metadata_amendment_sha256": sha256(AMENDMENT),
        "native_identifiability_sha256": sha256(ROOT / protocol["inputs"]["native_identifiability"]["file"]),
        "baseline_bounds_sha256": baseline_hash,
        "baseline_receipt_verified": baseline_receipt_verified,
        "baseline_envelope_match_count": sum(fold["baseline_envelope_match_count"] for fold in folds),
        "analysis_scope": {
            **protocol["analysis_scope"],
            "baseline_radius": radius,
            "high_precision_decimal_digits": 80,
            "outward_rounding": True,
            "outward_relative_margin": 1.0e-24,
            "exact_rational_certificate": False,
            "candidate_model_is_original_fourier": True,
            "fixed_period_or_taylor_substitution_for_candidates": False,
            "baseline_envelope_replaced": False,
            "probability_region": False,
            "new_period_mechanism": False,
        },
        "known_answer": source["known_answer"],
        "folds": folds,
        "totals": totals,
        "full_ellipsoid_joint_nonlinear_optimum": None,
        "decision": protocol["decision"],
        "limitations": [
            "Schur-complement support is jointly optimized over seven coefficients only on each fixed-period ellipsoid slice, not over the full nine-dimensional nonlinear model",
            "The conditional matrix is an ellipsoid-slice quadratic form, not marginal coefficient covariance or posterior conditional covariance",
            "The four period-perturbation directions are deterministic feasibility witnesses, not global optimizers",
            "Any candidate outside a slice bound falsifies direct export of that bound to the full ellipsoid; zero candidate violations would not prove safety",
            "The stage-47 independent coefficient envelopes remain the conservative full-ellipsoid baseline and are not replaced by the conditional slices",
            "Width tightening on a slice and full-region violation frequency are different quantities and cannot cancel each other",
            "High-precision outward-rounded numerical intervals are not exact rational-algebra certificates",
            "Positive periods do not prove unique or physical periods; center consistency and candidate containment are not external validation",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    expected = analyze()
    actual_ratios = [envelope.get("slice_to_independent_width_ratio") for fold in summary.get("folds", []) for envelope in fold.get("slice_envelopes", [])]
    expected_ratios = [envelope["slice_to_independent_width_ratio"] for fold in expected["folds"] for envelope in fold["slice_envelopes"]]
    if actual_ratios != expected_ratios:
        errors.append("Slice-to-independent width ratio mismatch")
    actual_witnesses = summary.get("totals", {}).get("slice_violation_evaluation_count")
    expected_witnesses = expected["totals"]["slice_violation_evaluation_count"]
    if actual_witnesses != expected_witnesses:
        errors.append("Candidate violation witness count mismatch")
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
    folds = summary["folds"]
    numbers = [fold["fold"] for fold in folds]
    colors = ["#316c9b", "#4f7b5b", "#876a32", "#6a4c93", "#b44b4b"]
    fig, axes = plt.subplots(2, 2, figsize=(16.0, 11.5), constrained_layout=True)
    for fold, color in zip(folds, colors):
        ratios = [envelope["slice_to_independent_width_ratio"] for envelope in fold["slice_envelopes"]]
        axes[0, 0].scatter([fold["fold"]] * len(ratios), ratios, s=15, alpha=0.65, color=color, label=f"fold {fold['fold']}")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks(numbers)
    axes[0, 0].set_xlabel("Frozen fold")
    axes[0, 0].set_ylabel("Slice width / independent width (log)")
    axes[0, 0].set_title("A. Conditional tightening on each fixed-period slice")
    axes[0, 0].grid(which="both", alpha=0.2)
    axes[0, 0].legend(frameon=False, fontsize=8)

    violations = [fold["slice_violation_evaluation_count"] for fold in folds]
    bars = axes[0, 1].bar(numbers, violations, color=colors, width=0.62)
    for bar, value in zip(bars, violations):
        axes[0, 1].text(bar.get_x() + bar.get_width() / 2, value + max(violations + [1]) * 0.02, str(value), ha="center", fontsize=9)
    axes[0, 1].set_ylim(0, max(violations + [1]) * 1.18)
    axes[0, 1].set_xticks(numbers)
    axes[0, 1].set_xlabel("Frozen fold")
    axes[0, 1].set_ylabel("Candidate evaluations outside slice")
    axes[0, 1].set_title("B. Feasible full-ellipsoid counterexamples")
    axes[0, 1].grid(axis="y", alpha=0.2)

    plotted = False
    for fold, color in zip(folds, colors):
        pairs = [(envelope["width_reduction"], max(candidate["slice_exceedance"] for candidate in envelope["candidate_evaluations"])) for envelope in fold["slice_envelopes"]]
        positive = [(reduction, exceedance) for reduction, exceedance in pairs if reduction > 0 and exceedance > 0]
        if positive:
            axes[1, 0].scatter([pair[0] for pair in positive], [pair[1] for pair in positive], s=16, alpha=0.65, color=color, label=f"fold {fold['fold']}")
            plotted = True
    if plotted:
        axes[1, 0].set_xscale("log")
        axes[1, 0].set_yscale("log")
        axes[1, 0].legend(frameon=False, fontsize=8)
    else:
        axes[1, 0].text(0.5, 0.5, "No positive candidate exceedance; not a safety proof", transform=axes[1, 0].transAxes, ha="center")
    axes[1, 0].set_xlabel("Slice width reduction (log)")
    axes[1, 0].set_ylabel("Maximum candidate exceedance (log)")
    axes[1, 0].set_title("C. Tightening and full-region export are different")
    axes[1, 0].grid(which="both", alpha=0.2)

    direction_order = [direction for direction, _, _ in DIRECTIONS]
    direction_counts = {direction: 0 for direction in direction_order}
    for envelope in [envelope for fold in folds for envelope in fold["slice_envelopes"]]:
        for candidate in envelope["candidate_evaluations"]:
            direction_counts[candidate["direction"]] += candidate["outside_slice"]
    bars = axes[1, 1].bar(direction_order, [direction_counts[direction] for direction in direction_order], color=["#316c9b", "#4f7b5b", "#876a32", "#b44b4b"], width=0.58)
    for bar, direction in zip(bars, direction_order):
        axes[1, 1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, str(direction_counts[direction]), ha="center", fontsize=9)
    axes[1, 1].set_ylim(0, max(list(direction_counts.values()) + [1]) * 1.2)
    axes[1, 1].set_ylabel("Outside-slice evaluations")
    axes[1, 1].set_title("D. All four frozen directions are retained")
    axes[1, 1].grid(axis="y", alpha=0.2)

    totals = summary["totals"]
    fig.suptitle(f"ENSO conditional period slices: {totals['candidate_evaluation_count']} candidate evaluations; {totals['slice_violation_evaluation_count']} outside slice", fontsize=15, y=1.045)
    fig.text(
        0.5, 1.012,
        "Schur-complement coefficient slices, not full nonlinear optima. Candidate directions are witnesses, not optimizers; baseline envelopes are not replaced.",
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
            errors.append("Missing conditional-period slice output")
        elif json.loads(OUT.read_text(encoding="utf-8")) != summary:
            errors.append("Stored conditional-period slice output is stale")
        if not FIGURE.exists() or not FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("Missing or invalid conditional-period slice figure")
    else:
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        render_figure(summary)
    if errors:
        raise ValueError(errors)
    print(json.dumps({
        "status": "checked" if args.check else "computed",
        "slice_envelopes": summary["totals"]["slice_envelope_count"],
        "candidate_evaluations": summary["totals"]["candidate_evaluation_count"],
        "slice_violations": summary["totals"]["slice_violation_evaluation_count"],
        "full_independent_violations": summary["totals"]["full_independent_violation_count"],
        "median_width_ratio": summary["totals"]["median_slice_to_independent_width_ratio"],
        "output": str(OUT.relative_to(ROOT)),
        "figure": str(FIGURE.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
