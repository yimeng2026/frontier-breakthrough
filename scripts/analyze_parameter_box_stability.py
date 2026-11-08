"""Certify simultaneous denominator-coefficient boxes for fifteen frozen folds."""

import hashlib
import json
from pathlib import Path

from box_stability import certified_box_safe, certify_parameter_box_radius

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/rational-parameter-box-protocol.json"
OUT = ROOT / "validation/rational-parameter-box-stability.json"
FIGURE = ROOT / "papers/14_参数盒稳定性/fig14_parameter_box_stability.png"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_parameter_box_stability":
        raise ValueError("Parameter-box protocol is not frozen")
    inputs, hashes = {}, {}
    for key, info in protocol["inputs"].items():
        path = ROOT / info["file"]
        digest = sha256(path)
        if digest != info["sha256"]:
            raise ValueError(f"Input hash changed: {path}")
        inputs[key] = json.loads(path.read_text(encoding="utf-8"))
        hashes[key] = digest
    amendment_path = ROOT / "validation/rational-parameter-box-protocol-amendment-01.json"
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    if amendment["parent_sha256"] != sha256(PROTOCOL):
        raise ValueError("Parameter-box amendment parent hash mismatch")
    hashes["protocol_amendment_01"] = sha256(amendment_path)
    return protocol, inputs, hashes


def analyze():
    protocol, inputs, hashes = load_inputs()
    exact = inputs["exact_roots"]
    scale_maps = {
        "hahn1": {
            fold["fold"]: {item["name"]: item["local_standard_error"] for item in fold["training_jacobian"]["parameters"]}
            for fold in inputs["hahn1_identifiability"]["folds"]
        },
        "thurber": {fold["fold"]: fold["identifiability"]["local_standard_errors"] for fold in inputs["thurber"]["folds"]},
        "kirby2": {fold["fold"]: fold["identifiability"]["local_standard_errors"] for fold in inputs["kirby2"]["folds"]},
    }
    cases = []
    for source in exact["cases"]:
        dataset, fold = source["dataset"], source["fold"]
        parameters = source["model_parameters"]
        names = source["denominator_parameter_order"]
        coefficients = [1, *[parameters[name] for name in names]]
        scales = [scale_maps[dataset][fold][name] for name in names]
        if any(scale <= 0 for scale in scales):
            raise ValueError(f"Non-positive local scale: {dataset} fold {fold}")
        lower, upper = source["closed_interval"]
        result = certify_parameter_box_radius(
            coefficients, scales, lower, upper,
            cap=protocol["radius_search_rule"]["cap"],
            iterations=protocol["radius_search_rule"]["iterations"],
        )
        result.pop("certified_radius_lower_bound")
        result.pop("uncertified_radius_upper_bound", None)
        if "certified_radius_lower_bound_rational" not in result:
            result["certified_radius_lower_bound_rational"] = "0"
        cases.append({
            "dataset": dataset,
            "fold": fold,
            "closed_interval": [lower, upper],
            "denominator_coefficients": coefficients,
            "denominator_parameter_order": names,
            "local_standard_error_scales": scales,
            "snapshot_exact_root_count": source["exact"]["root_count"],
            **result,
            "proof_scope": "Every denominator coefficient in the certified scaled box is root-free over the closed x interval; no probability or physical-tolerance claim",
        })
    totals = {
        "fold_count": len(cases),
        "snapshot_safe_fold_count": sum(case["snapshot_safe"] for case in cases),
        "rooted_snapshot_fold_count": sum(not case["snapshot_safe"] for case in cases),
        "certified_region_safe_fold_count": sum(case["certified_region_safe"] for case in cases),
        "cap_hit_fold_count": sum(case["cap_hit"] for case in cases),
        "certified_positive_radius_fold_count": sum(case["certified_radius_lower_bound_float"] > 0 for case in cases),
        "interpretation": "Counts report exact sufficient certificates for these frozen folds, not necessary radii or confidence coverage",
    }
    return {
        "status": "computed_exact_rational_parameter_box_stability",
        "protocol_sha256": sha256(PROTOCOL),
        "input_sha256": hashes,
        "cases": cases,
        "totals": totals,
        "decision": {
            "probability_or_confidence_region_claimed": False,
            "uncertified_upper_bound_called_unsafe": False,
            "global_root_free_claimed": False,
            "necessary_maximum_radius_claimed": False,
            "physical_parameter_endogeneity_proved": False,
        },
        "limitations": [
            "The radius is a sufficient certificate for the stated coefficient box, not a necessary maximum or a statistical confidence region",
            "Local linearized standard errors are only scales; they do not create a probability distribution or independent physical uncertainty estimate",
            "The proof covers simultaneous coefficient perturbations inside the certified box and the specified closed x interval only",
            "The uncertified upper bracket is not called unsafe; cap-hit results may permit larger boxes",
            "Rooted snapshots cannot have a root-free neighborhood; this does not predict how their roots move",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    cases = summary.get("cases", [])
    if len(cases) != 15:
        errors.append("Expected fifteen parameter-box cases")
    for case in cases:
        coefficients = case["denominator_coefficients"]
        scales = case["local_standard_error_scales"]
        lower, upper = case["closed_interval"]
        if not case["snapshot_safe"]:
            if case["certified_region_safe"]:
                errors.append(f"Rooted snapshot marked region-safe: {case['dataset']} fold {case['fold']}")
            continue
        radius = case["certified_radius_lower_bound_float"]
        if not certified_box_safe(coefficients, scales, lower, upper, radius):
            errors.append(f"Invalid certified lower bound: {case['dataset']} fold {case['fold']}")
        upper_radius = case["uncertified_radius_upper_bound_float"]
        if upper_radius is not None and certified_box_safe(coefficients, scales, lower, upper, upper_radius):
            errors.append(f"Upper bracket unexpectedly certified: {case['dataset']} fold {case['fold']}")
    totals = summary.get("totals", {})
    if totals.get("snapshot_safe_fold_count") != sum(case["snapshot_safe"] for case in cases):
        errors.append("Snapshot-safe total mismatch")
    if totals.get("certified_region_safe_fold_count") != sum(case["certified_region_safe"] for case in cases):
        errors.append("Region-safe total mismatch")
    for key in ["probability_or_confidence_region_claimed", "uncertified_upper_bound_called_unsafe", "global_root_free_claimed", "necessary_maximum_radius_claimed"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing parameter-box outputs")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cases = summary["cases"]
    labels = [f"{case['dataset'][0].upper()}{case['fold']}" for case in cases]
    radii = [case["certified_radius_lower_bound_float"] for case in cases]
    display = [max(value, 1.0e-12) for value in radii]
    colors = ["#487a52" if case["certified_region_safe"] else "#b44b4b" for case in cases]
    fig, ax = plt.subplots(figsize=(13.5, 5.8), constrained_layout=True)
    ax.bar(range(len(cases)), display, color=colors)
    ax.set_yscale("log")
    ax.axhline(4, color="#876a32", ls="--", lw=1.2, label="Frozen search cap")
    ax.set_xticks(range(len(cases)), labels, rotation=90)
    ax.set_ylabel("Certified sufficient radius (local-SE scale, log)")
    ax.set_xlabel("Dataset fold")
    ax.set_title("Every bar is a whole-box root-free certificate; upper brackets are not called unsafe")
    ax.grid(axis="y", which="both", alpha=0.2)
    for index, case in enumerate(cases):
        if not case["snapshot_safe"]:
            ax.text(index, 1.0e-11, "rooted", ha="center", va="bottom", fontsize=7, color="#b44b4b", rotation=90)
        elif case["cap_hit"]:
            ax.text(index, 4.5, "cap", ha="center", va="bottom", fontsize=7, color="#487a52")
    ax.legend(frameon=False, fontsize=8)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps({
        "output": str(OUT),
        "figure": str(FIGURE),
        "totals": summary["totals"],
        "radii": [{"dataset": case["dataset"], "fold": case["fold"], "lower": case["certified_radius_lower_bound_float"], "upper": case["uncertified_radius_upper_bound_float"], "cap_hit": case["cap_hit"]} for case in cases],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
