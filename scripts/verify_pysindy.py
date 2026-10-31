"""Known-answer smoke test for the D-drive PySINDy installation."""
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pysindy as ps

OUT = Path(__file__).resolve().parents[1] / "validation"
OUT.mkdir(exist_ok=True)
t = np.linspace(0.0, 2.0, 401)
x = np.column_stack((np.exp(-2.0 * t), np.exp(t)))
linear_library = ps.PolynomialLibrary(
    degree=1, include_interaction=False, include_bias=False
)
model = ps.SINDy(
    feature_library=linear_library,
    optimizer=ps.STLSQ(threshold=0.05),
)
model.fit(x, t=t, feature_names=["x", "y"])
coefficients = model.coefficients().tolist()
expected = np.array([[-2.0, 0.0], [0.0, 1.0]])
error = float(np.max(np.abs(model.coefficients() - expected)))
# 数值微分不是精确导数；保留误差，不用“完全相等”掩盖近似。
assert error < 1e-4, {"coefficients": coefficients, "max_abs_error": error}
report = {
    "engine": "PySINDy",
    "version": importlib.metadata.version("pysindy"),
    "python": "D:/research-engines/pysindy-env/Scripts/python.exe",
    "input": "x'= -2x, y'=y; 401 points; t in [0,2]",
    "coefficients": coefficients,
    "max_abs_error": error,
    "status": "verified",
    "scope": "仅验证本机指定版本能恢复已知线性系统，不是新规律发现。",
}
(OUT / "pysindy.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
