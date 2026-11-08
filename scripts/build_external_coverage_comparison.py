"""Build a dataset-specific comparison of reusable external coverage outputs."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/external-coverage-framework-protocol.json"
OUT = ROOT / "exports/external-coverage-comparison.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze(protocol_path=PROTOCOL):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    status = protocol["status"]
    if not status.startswith("frozen_before_") or not status.endswith("external_coverage_comparison"):
        raise ValueError("External comparison protocol is not frozen")
    datasets = []
    hashes = {}
    for dataset_id, info in protocol["inputs"].items():
        path = ROOT / info["file"]
        digest = sha256(path)
        if digest != info["sha256"]:
            raise ValueError(f"Input hash changed: {path}")
        summary = json.loads(path.read_text(encoding="utf-8"))
        hashes[dataset_id] = digest
        datasets.append({
            "id": dataset_id,
            "status": summary["status"],
            "native_model": summary["analysis_scope"]["native_model"],
            "totals": summary["totals"],
            "folds": [{
                "fold": case["fold"],
                "model_rmse": case["test_metrics"]["rmse"],
                "baseline_rmse": case["baseline_test_metrics"]["rmse"],
                "continuous_safe": case["continuous_ellipsoid_safe"],
                "point_count": len(case["point_results"]),
                "ellipsoid_available_point_count": sum(point.get("ellipsoid_available", False) for point in case["point_results"]),
                "covered_point_count": sum(point.get("coverage_violation") == 0 for point in case["point_results"]),
            } for case in summary["folds"]],
        })
    point_count = sum(item["totals"]["point_count"] for item in datasets)
    ellipsoid_available = sum(item["totals"]["ellipsoid_available_point_count"] for item in datasets)
    label = protocol.get("descriptive_label", "Filip and MGH17")
    totals = {
        "dataset_count": len(datasets),
        "point_count": point_count,
        "ellipsoid_available_point_count": ellipsoid_available,
        "ellipsoid_unavailable_point_count": point_count - ellipsoid_available,
        "covered_point_count": sum(item["totals"]["covered_point_count"] for item in datasets),
        "coverage_violation_count": sum(item["totals"]["coverage_violation_count"] for item in datasets),
        "fold_count": sum(item["totals"]["fold_count"] for item in datasets),
        "continuous_safe_fold_count": sum(item["totals"]["continuous_safe_fold_count"] for item in datasets),
        "independent_box_continuous_safe_fold_count": sum(item["totals"]["independent_box_continuous_safe_fold_count"] for item in datasets),
        "optimizer_failure_count": sum(item["totals"]["optimizer_failure_count"] for item in datasets),
        "interpretation": f"Descriptive totals for {label} only; not a universal external success rate or probability coverage",
    }
    return {
        "status": "computed_external_coverage_comparison",
        "protocol_sha256": sha256(protocol_path),
        "input_sha256": hashes,
        "analysis_scope": {
            "reusable_driver": "scripts/external_coverage.py",
            "driver_sha256": sha256(ROOT / "scripts/external_coverage.py"),
            "candidate_models_not_native": True,
            "refit": False,
            "independent_physical_experiment": False,
        },
        "datasets": datasets,
        "totals": totals,
        "decision": {
            "universal_external_success_rate_claimed": False,
            "probability_calibration_claimed": False,
            "native_physical_model_claimed": False,
            "parameter_endogeneity_proved": False,
        },
        "limitations": protocol.get("limitations", [
            "Both candidates are approximation stress tests and not their native model classes",
            "The 115-point descriptive total is not a probability coverage estimate or universal success rate",
            "Different native models, bound widths and independent-box availability remain dataset-specific",
            "Continuous denominator safety and pointwise residual coverage do not guarantee useful prediction or physical endogeneity",
        ]),
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    datasets = summary.get("datasets", [])
    totals = summary.get("totals", {})
    if len(datasets) != totals.get("dataset_count"):
        errors.append("Dataset total mismatch")
    checks = {
        "point_count": "Point total mismatch",
        "ellipsoid_available_point_count": "Ellipsoid availability total mismatch",
        "covered_point_count": "Covered point total mismatch",
        "coverage_violation_count": "Coverage violation total mismatch",
        "fold_count": "Fold total mismatch",
        "continuous_safe_fold_count": "Continuous safe total mismatch",
        "independent_box_continuous_safe_fold_count": "Independent-box continuous safe total mismatch",
        "optimizer_failure_count": "Optimizer failure total mismatch",
    }
    for key, message in checks.items():
        if totals.get(key) != sum(item["totals"][key] for item in datasets):
            errors.append(message)
    if totals.get("ellipsoid_unavailable_point_count") != totals.get("point_count", 0) - totals.get("ellipsoid_available_point_count", 0):
        errors.append("Ellipsoid unavailable total mismatch")
    for key in ["universal_external_success_rate_claimed", "probability_calibration_claimed", "native_physical_model_claimed", "parameter_endogeneity_proved"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def main():
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite: {OUT}")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "totals": summary["totals"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
