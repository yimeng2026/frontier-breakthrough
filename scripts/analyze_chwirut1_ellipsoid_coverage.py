"""Frozen external candidate-model coverage analysis for NIST Chwirut1."""

import json
from pathlib import Path

from external_coverage import render_external_figure, run_external_analysis, validate_summary

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/chwirut1-ellipsoid-coverage-protocol.json"
OUT = ROOT / "validation/chwirut1-ellipsoid-coverage.json"
FIGURE = ROOT / "papers/28_Chwirut1椭球覆盖/fig28_chwirut1_ellipsoid_coverage.png"


def apply_scope_limitations(summary, protocol):
    summary["limitations"][0] = protocol["candidate_rule"]["scope_limitation"]
    summary["analysis_scope"]["independent_model_family_test"] = False
    return summary


def analyze(protocol_path=PROTOCOL, runner=run_external_analysis):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    summary = runner(protocol_path, Path(__file__).resolve())
    return apply_scope_limitations(summary, protocol)


def main(analyze_func=None, render_func=render_external_figure):
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing Chwirut1 coverage outputs")
    analyze_func = analyze if analyze_func is None else analyze_func
    summary = analyze_func()
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_func(summary, FIGURE)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
