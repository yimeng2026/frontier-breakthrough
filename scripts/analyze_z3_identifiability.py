"""Z3 domain and identifiability counterexamples for the Chwirut model."""

import importlib.metadata
import json
from pathlib import Path

from z3 import Real, Solver, sat, unsat

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/z3-identifiability.json"


def value(model, variable):
    return str(model.eval(variable, model_completion=True))


def main():
    b1, b2, b3, x = Real("b1"), Real("b2"), Real("b3"), Real("x")

    positive = Solver()
    positive.add(b2 > 0, b3 >= 0, x >= 0, b2 + b3 * x <= 0)
    positive_result = positive.check()
    assert positive_result == unsat

    invalid = Solver()
    invalid.add(b1 > 0, b2 == 1, b3 == -1, x == 1, b2 + b3 * x == 0)
    invalid_result = invalid.check()
    assert invalid_result == sat
    invalid_model = invalid.model()

    a1, a2, a3, y = Real("a1"), Real("a2"), Real("a3"), Real("y")
    degenerate = Solver()
    # At x=0 the Chwirut response y=1/b2 contains no information about b1 or b3.
    degenerate.add(
        x == 0, y == 1,
        b2 == 1, a2 == 1,
        b1 == 0.1, a1 == 0.2,
        b3 == 0.02, a3 == 0.03,
        y == 1 / b2, y == 1 / a2,
        b1 != a1, b3 != a3,
    )
    degenerate_result = degenerate.check()
    assert degenerate_result == sat
    degenerate_model = degenerate.model()

    checks = [
        {
            "id": "positive_denominator_by_contradiction",
            "claim": "If b2>0, b3>=0 and x>=0, then b2+b3*x>0",
            "result": str(positive_result),
            "interpretation": "The negated implication is unsatisfiable within this explicit domain",
        },
        {
            "id": "nonpositive_denominator_counterexample",
            "claim": "The model remains defined without denominator constraints",
            "result": str(invalid_result),
            "model": {"b1": value(invalid_model, b1), "b2": value(invalid_model, b2), "b3": value(invalid_model, b3), "x": value(invalid_model, x)},
            "interpretation": "A zero denominator is reachable without sign restrictions; the claim is falsified",
        },
        {
            "id": "x_zero_parameter_nonidentifiability",
            "claim": "An x=0 response alone uniquely identifies all three parameters",
            "result": str(degenerate_result),
            "model": {name: value(degenerate_model, variable) for name, variable in [("b1", b1), ("b2", b2), ("b3", b3), ("a1", a1), ("a2", a2), ("a3", a3), ("y", y)]},
            "interpretation": "Two distinct parameter triples produce the same x=0 response; identifiability depends on experimental design",
        },
    ]
    report = {
        "status": "verified",
        "engine": "Z3",
        "version": importlib.metadata.version("z3-solver"),
        "python": "D:/research-engines/z3-env/Scripts/python.exe",
        "checks": checks,
        "universal_identifiability_claimed": False,
        "limitations": [
            "These are finite-domain satisfiability checks and explicit counterexamples, not a general proof of the Chwirut model or of all nonlinear systems",
            "The x=0 calculation is algebraically simplified before using Z3; no nonlinear exponential solver is claimed",
            "Counterexamples falsify the stated universal claims only; they do not invalidate the NIST dataset or the fitted model within its valid domain",
        ],
    }
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        if previous != report:
            raise ValueError("Refusing to overwrite a different frozen Z3 result")
    else:
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
