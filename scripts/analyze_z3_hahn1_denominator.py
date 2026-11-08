"""Prove the certified Hahn1 denominator has no zero root for x >= 0 using Z3."""

import importlib.metadata
import json
from pathlib import Path

from z3 import Real, Solver, unsat

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/z3-hahn1-denominator.json"


def main():
    protocol = json.loads((ROOT / "validation/hahn1-high-temperature-protocol.json").read_text(encoding="utf-8"))
    parameters = protocol["full_fit_certification_rule"]["certified_parameters"]
    x = Real("x")
    denominator = 1 + parameters["b5"] * x + parameters["b6"] * x ** 2 + parameters["b7"] * x ** 3
    solver = Solver()
    solver.add(x >= 0, x <= 900, denominator == 0)
    result = solver.check()
    if result != unsat:
        raise ValueError(f"Expected unsat within 0<=x<=900, got {result}: {solver.model()}")
    unbounded = Solver()
    unbounded.add(x >= 0, denominator == 0)
    unbounded_result = unbounded.check()
    if str(unbounded_result) != "sat":
        raise ValueError("Expected an out-of-domain positive root")
    unbounded_x = str(unbounded.model().eval(x))
    report = {
        "status": "verified",
        "engine": "Z3",
        "version": importlib.metadata.version("z3-solver"),
        "python": "D:/research-engines/z3-env/Scripts/python.exe",
        "result": str(result),
        "denominator_positive_within_0_to_900": True,
        "domain": "0<=x<=900",
        "unbounded_root_exists": True,
        "unbounded_model_x": unbounded_x,
        "parameters": parameters,
        "limitations": "The certified denominator has no zero root within 0<=x<=900, but a positive root exists beyond the experimental range; no positivity claim is made for every parameter triple or all x>=0",
    }
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        if previous != report:
            raise ValueError("Refusing to overwrite a different Z3 denominator result")
    else:
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
