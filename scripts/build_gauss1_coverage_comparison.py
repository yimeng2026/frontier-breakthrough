"""Build the preserved three-dataset external coverage comparison."""

import json
from pathlib import Path

import build_external_coverage_comparison as base

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/external-coverage-gauss1-comparison-protocol.json"
OUT = ROOT / "exports/external-coverage-gauss1-comparison.json"


def analyze():
    summary = base.analyze(PROTOCOL)
    summary["comparison_wrapper_sha256"] = base.sha256(Path(__file__).resolve())
    return summary


def validate_summary(summary):
    return base.validate_summary(summary)


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
