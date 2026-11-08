"""Validate the preserved ten-dataset extreme-value report and receipt."""

import json
from pathlib import Path

import validate_extreme_reporting as base

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "contracts/extreme-reporting.rules.json"
REPORT = ROOT / "exports/maximum-full-composition-audit-v2.json"
CHECK = ROOT / "validation/extreme-reporting-v2-check.json"


def validate_v2_report(summary, claim_level):
    return base.validate_report(summary, claim_level)


def build_check():
    summary = json.loads(REPORT.read_text(encoding="utf-8"))
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    errors = validate_v2_report(summary, rules["default_claim_level"])
    return {
        "status": "passed" if not errors else "failed",
        "claim_level": rules["default_claim_level"],
        "level_names": rules["level_names"],
        "report_file": str(REPORT.relative_to(ROOT)),
        "report_sha256": base.sha256(REPORT),
        "rules_file": str(RULES.relative_to(ROOT)),
        "rules_sha256": base.sha256(RULES),
        "dataset_count": summary["totals"]["dataset_count"],
        "error_count": len(errors),
        "errors": errors,
        "decision": summary["decision"],
        "validator_sha256": base.sha256(Path(__file__).resolve()),
        "base_validator_sha256": base.sha256(Path(base.__file__).resolve()),
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
            raise ValueError("Extreme reporting v2 check is stale")
        print(f"OK: ten-dataset extreme reporting contract passed ({current['claim_level']})")
        return
    if CHECK.exists():
        raise FileExistsError("Refusing to overwrite extreme reporting v2 check")
    CHECK.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: ten-dataset extreme reporting contract passed ({current['claim_level']}); wrote {CHECK}")


if __name__ == "__main__":
    main()
