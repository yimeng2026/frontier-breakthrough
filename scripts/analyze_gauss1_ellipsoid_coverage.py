"""Frozen external candidate-model coverage analysis for NIST Gauss1."""

import json
from pathlib import Path

from external_coverage import load_observations, render_external_figure, run_external_analysis, validate_summary

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/gauss1-ellipsoid-coverage-protocol.json"
OUT = ROOT / "validation/gauss1-ellipsoid-coverage.json"
FIGURE = ROOT / "papers/20_Gauss1椭球覆盖/fig20_gauss1_ellipsoid_coverage.png"


def load_gauss1_data(path, expected_sha256=None):
    return load_observations(path, 250, expected_sha256)


def analyze():
    return run_external_analysis(PROTOCOL, Path(__file__).resolve())


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing Gauss1 coverage outputs")
    summary = analyze()
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_external_figure(summary, FIGURE)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
