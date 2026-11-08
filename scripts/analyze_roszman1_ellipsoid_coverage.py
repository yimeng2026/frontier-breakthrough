"""Frozen external candidate-model coverage analysis for NIST Roszman1."""

import json
from pathlib import Path

from external_coverage import render_external_figure, validate_summary
from external_coverage_scoped import run_scoped_external_analysis

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-ellipsoid-coverage-protocol.json"
OUT = ROOT / "validation/roszman1-ellipsoid-coverage.json"
FIGURE = ROOT / "papers/35_Roszman1椭球覆盖/fig35_roszman1_ellipsoid_coverage.png"


def analyze(protocol_path=PROTOCOL, runner=None):
    return run_scoped_external_analysis(protocol_path, Path(__file__).resolve(), runner=runner)


def main(analyze_func=None, render_func=render_external_figure):
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing Roszman1 coverage outputs")
    analyze_func = analyze if analyze_func is None else analyze_func
    summary = analyze_func()
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_func(summary, FIGURE)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
