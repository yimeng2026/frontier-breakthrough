"""Certify covariance-ellipsoid denominator safety over entire held-out intervals."""

import hashlib
import json
from pathlib import Path

from ellipsoid_interval import certify_ellipsoid_interval

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/rational-ellipsoid-interval-protocol.json"
OUT = ROOT / "validation/rational-ellipsoid-interval-safety.json"
FIGURE = ROOT / "papers/17_椭球连续区间/fig17_ellipsoid_interval_safety.png"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_ellipsoid_interval_certification":
        raise ValueError("Ellipsoid interval protocol is not frozen")
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
    comparison = inputs["comparison"]
    cases = []
    for frozen in inputs["parameter_box"]["cases"]:
        dataset, fold = frozen["dataset"], frozen["fold"]
        other = next(item for item in comparison["cases"] if item["dataset"] == dataset and item["fold"] == fold)
        coefficients = frozen["denominator_coefficients"]
        covariance = other["denominator_covariance"]
        radius = frozen["certified_radius_lower_bound_float"]
        lower, upper = frozen["closed_interval"]
        if not frozen["snapshot_safe"]:
            certificate = {
                "snapshot_safe": False,
                "continuous_ellipsoid_safe": False,
                "snapshot_root_count": None,
                "support_polynomial_root_count": None,
                "reason": "Rooted snapshot has no root-free neighborhood",
            }
        else:
            certificate = certify_ellipsoid_interval(coefficients, covariance, radius, lower, upper)
        cases.append({
            "dataset": dataset,
            "fold": fold,
            "closed_interval": [lower, upper],
            "certified_radius_lower_bound_float": radius,
            "denominator_coefficients": coefficients,
            "denominator_covariance": covariance,
            **certificate,
            "interpretation": "Only a successful exact continuous certificate is called safe; non-certification is not called unsafe",
        })
    totals = {
        "fold_count": len(cases),
        "continuous_safe_fold_count": sum(case["continuous_ellipsoid_safe"] for case in cases),
        "not_certified_fold_count": sum(case["snapshot_safe"] and not case["continuous_ellipsoid_safe"] for case in cases),
        "rooted_snapshot_fold_count": sum(not case["snapshot_safe"] for case in cases),
        "interpretation": "Counts distinguish exact continuous safety, non-certification and rooted snapshots",
    }
    return {
        "status": "computed_exact_rational_ellipsoid_interval_safety",
        "protocol_sha256": sha256(PROTOCOL),
        "input_sha256": hashes,
        "cases": cases,
        "totals": totals,
        "decision": {
            "non_certification_called_unsafe": False,
            "confidence_or_probability_claimed": False,
            "pointwise_check_substituted_for_interval": False,
            "numerator_perturbation_included": False,
            "physical_measurement_model_claimed": False,
        },
        "limitations": [
            "A continuous certificate applies only to the specified covariance ellipsoid, radius and closed x interval",
            "Non-certification does not prove the ellipsoid is unsafe; it means the exact sufficient condition was not established",
            "Rooted snapshots do not receive a root-free neighborhood certificate",
            "Numerator perturbation and model-structure errors are outside this certificate",
            "No confidence, probability or physical measurement model is implied",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    cases = summary.get("cases", [])
    if len(cases) != 15:
        errors.append("Expected fifteen interval cases")
    for case in cases:
        if not case["snapshot_safe"]:
            if case["continuous_ellipsoid_safe"]:
                errors.append(f"Rooted snapshot marked safe: {case['dataset']} fold {case['fold']}")
            continue
        recomputed = certify_ellipsoid_interval(
            case["denominator_coefficients"], case["denominator_covariance"],
            case["certified_radius_lower_bound_float"], *case["closed_interval"],
        )
        if recomputed["continuous_ellipsoid_safe"] != case["continuous_ellipsoid_safe"]:
            errors.append(f"Continuous certificate mismatch: {case['dataset']} fold {case['fold']}")
        if case["continuous_ellipsoid_safe"] and case["support_polynomial_root_count"] != 0:
            errors.append(f"Safe case has support roots: {case['dataset']} fold {case['fold']}")
    totals = summary.get("totals", {})
    if totals.get("continuous_safe_fold_count") != sum(case["continuous_ellipsoid_safe"] for case in cases):
        errors.append("Continuous safe total mismatch")
    if totals.get("rooted_snapshot_fold_count") != sum(not case["snapshot_safe"] for case in cases):
        errors.append("Rooted snapshot total mismatch")
    for key in ["non_certification_called_unsafe", "confidence_or_probability_claimed", "pointwise_check_substituted_for_interval", "physical_measurement_model_claimed"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing ellipsoid interval certificate")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cases = summary["cases"]
    labels = [f"{case['dataset'][0].upper()}{case['fold']}" for case in cases]
    colors = ["#487a52" if case["continuous_ellipsoid_safe"] else "#b88a3a" if case["snapshot_safe"] else "#b44b4b" for case in cases]
    values = [1 if case["continuous_ellipsoid_safe"] else 0.5 if case["snapshot_safe"] else 0 for case in cases]
    fig, ax = plt.subplots(figsize=(13.5, 5.4), constrained_layout=True)
    ax.bar(range(len(cases)), values, color=colors)
    ax.set_xticks(range(len(cases)), labels, rotation=90)
    ax.set_yticks([0, 0.5, 1], ["Rooted snapshot", "Not certified", "Continuous safe"])
    ax.set_xlabel("Dataset fold")
    ax.set_title("Exact squared-support certificates over the entire held-out intervals")
    ax.grid(axis="y", alpha=0.2)
    ax.set_ylim(-0.12, 1.18)
    for index, case in enumerate(cases):
        if not case["continuous_ellipsoid_safe"]:
            label = "not certified" if case["snapshot_safe"] else "rooted"
            ax.text(index, values[index] + 0.04, label, ha="center", va="bottom", fontsize=7, rotation=90, color=colors[index])
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "totals": summary["totals"], "cases": [{"dataset": case["dataset"], "fold": case["fold"], "safe": case["continuous_ellipsoid_safe"], "support_roots": case["support_polynomial_root_count"]} for case in cases]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
