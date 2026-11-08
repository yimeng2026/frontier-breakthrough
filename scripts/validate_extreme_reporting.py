"""Validate layered extreme-value reporting contracts and write an audit receipt."""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "contracts/extreme-reporting.rules.json"
REPORT = ROOT / "exports/maximum-full-composition-audit.json"
CHECK = ROOT / "validation/extreme-reporting-check.json"
LEVELS = ["maximum_only", "distribution_summary", "mechanism_interpretation"]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_fields(item, fields, label, errors):
    for field in fields:
        if field not in item:
            errors.append(f"{label}: missing {field}")


def validate_report(summary, claim_level):
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    errors = []
    if claim_level not in LEVELS:
        return [f"Unknown claim_level: {claim_level}"]
    scope = summary.get("analysis_scope", {})
    for key, expected in rules["required_analysis_scope"].items():
        if scope.get(key) is not expected:
            errors.append(f"analysis_scope.{key} must be {expected}")
    decision = summary.get("decision", {})
    for key in rules["prohibited_decision_flags"]:
        if decision.get(key) is not False:
            errors.append(f"decision.{key} must be false")
    if rules["limitation_required_fragment"] not in " ".join(summary.get("limitations", [])):
        errors.append("limitations must state that maximum points are not typical")
    datasets = summary.get("datasets", [])
    if not datasets:
        errors.append("datasets must not be empty")
        return errors
    if summary.get("totals", {}).get("dataset_count") != len(datasets):
        errors.append("totals.dataset_count does not match datasets length")
    if claim_level == "mechanism_interpretation":
        require_fields(summary.get("totals", {}), rules["required_counterexample_total_fields"], "totals", errors)
    required = list(rules["level_dataset_fields"]["maximum_only"])
    if claim_level in {"distribution_summary", "mechanism_interpretation"}:
        required += rules["level_dataset_fields"]["distribution_summary"]
    if claim_level == "mechanism_interpretation":
        required += rules["level_dataset_fields"]["mechanism_interpretation"]
    for item in datasets:
        label = item.get("id", "unknown_dataset")
        require_fields(item, required, label, errors)
        if not isinstance(item.get("available_point_count"), int) or item["available_point_count"] <= 0:
            errors.append(f"{label}: available_point_count must be a positive integer")
            continue
        maximum_share = item.get("maximum_shift_share")
        if not isinstance(maximum_share, (int, float)) or not 0 <= maximum_share <= 1:
            errors.append(f"{label}: maximum_shift_share must be in [0,1]")
        maximum_bound = item.get("maximum_residual_upper_bound")
        if not isinstance(maximum_bound, (int, float)) or maximum_bound <= 0:
            errors.append(f"{label}: maximum_residual_upper_bound must be positive")
        if claim_level == "maximum_only":
            continue
        majority = item.get("majority_dominant")
        maximum_dominant = item.get("maximum_dominant")
        if majority not in {"prediction_shift_dominant", "snapshot_residual_dominant", "tie_no_single_majority"}:
            errors.append(f"{label}: invalid majority_dominant")
        elif item.get("maximum_matches_majority") != (maximum_dominant == majority if majority != "tie_no_single_majority" else None):
            errors.append(f"{label}: maximum_matches_majority is inconsistent")
        median_share = item.get("median_shift_share")
        if not isinstance(median_share, (int, float)) or not 0 <= median_share <= 1:
            errors.append(f"{label}: median_shift_share must be in [0,1]")
        elif not math.isclose(item.get("maximum_share_minus_median", float("nan")), maximum_share - median_share, rel_tol=1.0e-12, abs_tol=1.0e-15):
            errors.append(f"{label}: maximum_share_minus_median mismatch")
        median_bound = item.get("median_residual_upper_bound")
        if not isinstance(median_bound, (int, float)) or median_bound <= 0:
            errors.append(f"{label}: median_residual_upper_bound must be positive")
        else:
            ratio = item.get("bound_max_to_median_ratio")
            if not isinstance(ratio, (int, float)) or ratio < 1:
                errors.append(f"{label}: bound_max_to_median_ratio must be at least 1")
            elif not math.isclose(ratio, maximum_bound / median_bound, rel_tol=1.0e-12):
                errors.append(f"{label}: bound_max_to_median_ratio mismatch")
        if claim_level == "mechanism_interpretation":
            count = item.get("share_less_than_or_equal_maximum_count")
            if not isinstance(count, int) or not 0 <= count <= item["available_point_count"]:
                errors.append(f"{label}: share_less_than_or_equal_maximum_count is invalid")
            else:
                expected = count / item["available_point_count"]
                if not math.isclose(item.get("maximum_share_descriptive_percentile", float("nan")), expected, rel_tol=1.0e-12):
                    errors.append(f"{label}: maximum_share_descriptive_percentile mismatch")
    return errors


def build_check():
    summary = json.loads(REPORT.read_text(encoding="utf-8"))
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    errors = validate_report(summary, rules["default_claim_level"])
    return {
        "status": "passed" if not errors else "failed",
        "claim_level": rules["default_claim_level"],
        "level_names": rules["level_names"],
        "report_file": str(REPORT.relative_to(ROOT)),
        "report_sha256": sha256(REPORT),
        "rules_file": str(RULES.relative_to(ROOT)),
        "rules_sha256": sha256(RULES),
        "dataset_count": summary["totals"]["dataset_count"],
        "error_count": len(errors),
        "errors": errors,
        "decision": summary["decision"],
        "validator_sha256": sha256(Path(__file__).resolve()),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    current = build_check()
    if current["error_count"]:
        raise ValueError(current["errors"])
    if args.check:
        stored = json.loads(CHECK.read_text(encoding="utf-8"))
        if stored != current:
            raise ValueError("Extreme reporting check is stale")
        print(f"OK: extreme reporting contract passed ({current['claim_level']})")
        return
    if CHECK.exists():
        raise FileExistsError("Refusing to overwrite extreme reporting check")
    CHECK.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: extreme reporting contract passed ({current['claim_level']}); wrote {CHECK}")


if __name__ == "__main__":
    main()
