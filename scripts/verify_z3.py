"""Known-answer checks for Z3, including a negated implication."""
import importlib.metadata
import json
from pathlib import Path

from z3 import Real, Solver, sat, unsat

OUT = Path(__file__).resolve().parents[1] / "validation"
OUT.mkdir(exist_ok=True)
x = Real("x")
positive_implication = Solver()
positive_implication.add(x > 0, x + 1 <= 0)
implication_result = positive_implication.check()
assert implication_result == unsat
nonnegative_square = Solver()
nonnegative_square.add(x * x < 0)
square_result = nonnegative_square.check()
assert square_result == unsat
report = {
    "engine": "Z3",
    "version": importlib.metadata.version("z3-solver"),
    "python": "D:/research-engines/z3-env/Scripts/python.exe",
    "checks": {
        "negation_of_x_positive_implies_x_plus_1_positive": str(implication_result),
        "x_squared_less_than_zero": str(square_result),
    },
    "status": "verified",
    "scope": "验证两个实数约束的已知答案，不等同一般数学定理的自动证明。",
}
assert sat != unsat
(OUT / "z3.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
