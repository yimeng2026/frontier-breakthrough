"""Build a dataset-specific comparison of reusable external coverage outputs."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/external-coverage-framework-protocol.json"
OUT = ROOT / "exports/external-coverage-comparison.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_external_coverage_comparison":
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
    totals = {
        "dataset_count": len(datasets),
        "point_count": sum(item["totals"]["point_count"] for item in datasets),
        "covered_point_count": sum(item["totals"]["covered_point_count"] for item in datasets),
        "coverage_violation_count": sum(item["totals"]["coverage_violation_count"] for item in datasets),
        "continuous_safe_fold_count": sum(item["totals"]["continuous_safe_fold_count"] for item in datasets),
        "optimizer_failure_count": sum(item["totals"]["optimizer_failure_count"] for item in datasets),
        "interpretation": "Descriptive totals for Filip and MGH17 only; not a universal external success rate or probability coverage",
    }
    return {
        "status": "computed_external_coverage_comparison",
        "protocol_sha256": sha256(PROTOCOL),
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
        "limitations": [
            "Both candidates are approximation stress tests and not their native model classes",
            "The 115-point descriptive total is not a probability coverage estimate or universal success rate",
            "Different native models, bound widths and independent-box availability remain dataset-specific",
            "Continuous denominator safety and pointwise residual coverage do not guarantee useful prediction or physical endogeneity",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def validate_summary(summary):
    errors = []
    datasets = summary.get("datasets", [])
    totals = summary.get("totals", {})
    if len(datasets) != 2:
        errors.append("Expected two external datasets")
    if totals.get("point_count") != sum(item["totals"]["point_count"] for item in datasets):
        errors.append("Point total mismatch")
    if totals.get("covered_point_count") != sum(item["totals"]["covered_point_count"] for item in datasets):
        errors.append("Covered point total mismatch")
    if totals.get("continuous_safe_fold_count") != sum(item["totals"]["continuous_safe_fold_count"] for item in datasets):
        errors.append("Continuous safe total mismatch")
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
