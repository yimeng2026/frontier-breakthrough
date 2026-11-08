# Gauss1 Bound Mechanism Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only, post-hoc diagnostic that recomputes all 250 Gauss1 denominator lower bounds, reconciles the 190 stored bounds, preserves all 60 unavailable points, and produces a validated JSON audit and figure without refitting.

**Architecture:** A single new diagnostic script reads the frozen Gauss1 coverage output and verifies its protocol, raw-data and original-runner hashes. It reuses exact rational evaluation and covariance-support helpers, but does not modify the frozen external-coverage driver or any model parameters. Tests first require the missing diagnostic, then verify classification, numerical agreement, scope limits and real output files.

**Tech Stack:** Python 3.12, `fractions.Fraction` through existing exact-root helpers, NumPy/Matplotlib, `unittest`, JSON and PNG.

## Global Constraints

- Do not refit, retune, change folds, change radius, or alter `scripts/external_coverage.py`.
- Treat continuous non-certification as non-certification, never as proof of unsafety.
- Keep all 250 observations: 190 ellipsoid-available and 60 unavailable.
- Require exact agreement with all 190 stored available classifications and stored floating-point bounds within explicit numerical tolerances.
- Do not claim native-model validation, probability calibration, independent physical experimentation, or universal external validity.
- Execute inline in the current session; do not dispatch subagents.

---

### Task 1: Frozen Gauss1 denominator and bound-width diagnostic

**Files:**
- Create: `scripts/analyze_gauss1_bound_mechanism.py`
- Create: `tests/test_gauss1_bound_mechanism.py`
- Create after analysis: `validation/gauss1-bound-mechanism.json`
- Create after analysis: `papers/21_Gauss1界失效机制/fig21_gauss1_bound_mechanism.png`

**Interfaces:**
- Consumes: `validation/gauss1-ellipsoid-coverage.json`, its frozen protocol, raw data and original analysis wrapper; existing `exact_roots.as_fraction`, `exact_roots.evaluate`, and `ellipsoid_bounds.covariance_support_upper_bound`.
- Produces: `load_source() -> dict`, `inspect_point(fold: dict, point: dict) -> dict`, `analyze() -> dict`, `validate_summary(summary: dict) -> list[str]`, `render_figure(summary: dict) -> None`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_gauss1_bound_mechanism.py`:

```python
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/analyze_gauss1_bound_mechanism.py"


class Gauss1BoundMechanismTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing diagnostic: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("analyze_gauss1_bound_mechanism", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_all_points_are_classified_and_stored_bounds_agree(self):
        module = self.load_module()
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["point_count"], 250)
        self.assertEqual(totals["ellipsoid_available_point_count"], 190)
        self.assertEqual(totals["ellipsoid_unavailable_point_count"], 60)
        self.assertEqual(totals["classification_mismatch_count"], 0)
        self.assertEqual(totals["stored_bound_agreement_count"], 190)
        self.assertEqual(totals["stored_bound_mismatch_count"], 0)
        self.assertEqual(module.validate_summary(summary), [])
        folds = {case["fold"]: case for case in summary["folds"]}
        self.assertFalse(folds[2]["continuous_ellipsoid_safe"])
        self.assertEqual(folds[2]["ellipsoid_available_point_count"], 40)
        self.assertFalse(folds[5]["continuous_ellipsoid_safe"])
        self.assertEqual(folds[5]["ellipsoid_available_point_count"], 0)
        self.assertEqual(sum(folds[5]["unavailable_reason_counts"].values()), 50)

    def test_analysis_is_post_hoc_and_not_refit(self):
        module = self.load_module()
        summary = module.analyze()
        self.assertTrue(summary["analysis_scope"]["post_hoc"])
        self.assertFalse(summary["analysis_scope"]["refit"])
        self.assertFalse(summary["analysis_scope"]["retuned"])
        self.assertFalse(summary["decision"]["continuous_noncertification_called_unsafe"])
        self.assertFalse(summary["decision"]["probability_calibration_claimed"])
        self.assertFalse(summary["decision"]["native_physical_model_claimed"])

    def test_final_outputs_are_real_and_current(self):
        module = self.load_module()
        self.assertTrue(module.OUT.is_file(), module.OUT)
        self.assertTrue(module.FIGURE.is_file(), module.FIGURE)
        summary = module.analyze()
        self.assertEqual(module.validate_summary(summary), [])
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_gauss1_bound_mechanism -v`

Expected: three failures with `Missing diagnostic: .../scripts/analyze_gauss1_bound_mechanism.py`.

- [ ] **Step 3: Write minimal implementation**

Create `scripts/analyze_gauss1_bound_mechanism.py`:

```python
"""Read-only post-hoc diagnosis of frozen Gauss1 denominator bounds."""

import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

import numpy as np

from exact_roots import as_fraction, evaluate
from ellipsoid_bounds import covariance_support_upper_bound

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "validation/gauss1-ellipsoid-coverage.json"
PROTOCOL = ROOT / "validation/gauss1-ellipsoid-coverage-protocol.json"
RAW_DATA = ROOT / "data/Gauss1.dat"
ORIGINAL_RUNNER = ROOT / "scripts/analyze_gauss1_ellipsoid_coverage.py"
OUT = ROOT / "validation/gauss1-bound-mechanism.json"
FIGURE = ROOT / "papers/21_Gauss1界失效机制/fig21_gauss1_bound_mechanism.png"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_source():
    summary = json.loads(SOURCE.read_text(encoding="utf-8"))
    if summary["protocol_sha256"] != sha256(PROTOCOL):
        raise ValueError("Frozen Gauss1 protocol hash mismatch")
    if summary["data_sha256"] != sha256(RAW_DATA):
        raise ValueError("Frozen Gauss1 raw-data hash mismatch")
    if summary["analysis_runner_sha256"] != sha256(ORIGINAL_RUNNER):
        raise ValueError("Frozen Gauss1 analysis-runner hash mismatch")
    return summary


def inspect_point(fold, point):
    parameters = fold["model_parameters"]
    x = as_fraction(point["x"])
    numerator = evaluate([parameters[name] for name in ["b1", "b2", "b3", "b4"]], x)
    denominator = evaluate([1, parameters["b5"], parameters["b6"], parameters["b7"]], x)
    if denominator == 0:
        raise ValueError("Snapshot denominator is zero")
    support, variance = covariance_support_upper_bound(fold["denominator_covariance"], [x, x**2, x**3])
    radius = as_fraction(1)
    perturbation = radius * support
    denominator_lower = abs(denominator) - perturbation
    available = denominator_lower > 0
    shift = None
    residual = None
    if available:
        shift = abs(numerator) * perturbation / (abs(denominator) * denominator_lower)
        residual = abs(as_fraction(point["observed_y"]) - numerator / denominator) + shift
    return {
        "x": point["x"],
        "available": available,
        "denominator_lower": float(denominator_lower),
        "support": float(support),
        "support_variance": float(variance),
        "shift": float(shift) if shift is not None else None,
        "residual_bound": float(residual) if residual is not None else None,
    }


def extreme(points, key, mode):
    candidates = [point for point in points if point[key] is not None]
    if not candidates:
        return None
    chooser = min if mode == "min" else max
    point = chooser(candidates, key=lambda item: item[key])
    return {"x": point["x"], "value": point[key]}


def analyze():
    source = load_source()
    folds = []
    totals = {
        "point_count": 0,
        "ellipsoid_available_point_count": 0,
        "ellipsoid_unavailable_point_count": 0,
        "classification_mismatch_count": 0,
        "stored_bound_agreement_count": 0,
        "stored_bound_mismatch_count": 0,
    }
    for fold in source["folds"]:
        diagnostics = [inspect_point(fold, point) for point in fold["point_results"]]
        agreements = 0
        classification_mismatches = 0
        bound_mismatches = 0
        for point, diagnostic in zip(fold["point_results"], diagnostics):
            if point["ellipsoid_available"] != diagnostic["available"]:
                classification_mismatches += 1
            if not point["ellipsoid_available"]:
                continue
            comparisons = [
                (diagnostic["denominator_lower"], point["ellipsoid_denominator_lower_bound_float"]),
                (diagnostic["shift"], point["ellipsoid_prediction_shift_upper_bound_float"]),
                (diagnostic["residual_bound"], point["ellipsoid_absolute_residual_upper_bound_float"]),
            ]
            if all(math.isclose(actual, stored, rel_tol=1.0e-9, abs_tol=1.0e-8) for actual, stored in comparisons):
                agreements += 1
            else:
                bound_mismatches += 1
        available_count = sum(point["ellipsoid_available"] for point in fold["point_results"])
        unavailable_reasons = Counter(point["ellipsoid_unavailable_reason"] for point in fold["point_results"] if not point["ellipsoid_available"])
        case = {
            "fold": fold["fold"],
            "continuous_ellipsoid_safe": fold["continuous_ellipsoid_safe"],
            "snapshot_root_count": fold["continuous_certificate"]["snapshot_root_count"],
            "support_polynomial_root_count": fold["continuous_certificate"]["support_polynomial_root_count"],
            "model_rmse": fold["test_metrics"]["rmse"],
            "baseline_rmse": fold["baseline_test_metrics"]["rmse"],
            "point_count": len(fold["point_results"]),
            "ellipsoid_available_point_count": available_count,
            "ellipsoid_unavailable_point_count": len(fold["point_results"]) - available_count,
            "unavailable_reason_counts": dict(unavailable_reasons),
            "unavailable_x": [point["x"] for point in fold["point_results"] if not point["ellipsoid_available"]],
            "minimum_denominator_lower": extreme(diagnostics, "denominator_lower", "min"),
            "maximum_covariance_support": extreme(diagnostics, "support", "max"),
            "maximum_prediction_shift_upper_bound": extreme(diagnostics, "shift", "max"),
            "maximum_residual_upper_bound": extreme(diagnostics, "residual_bound", "max"),
            "median_residual_upper_bound": statistics.median(point["residual_bound"] for point in diagnostics if point["residual_bound"] is not None) if available_count else None,
            "classification_mismatch_count": classification_mismatches,
            "stored_bound_agreement_count": agreements,
            "stored_bound_mismatch_count": bound_mismatches,
        }
        folds.append(case)
        totals["point_count"] += case["point_count"]
        totals["ellipsoid_available_point_count"] += available_count
        totals["ellipsoid_unavailable_point_count"] += case["ellipsoid_unavailable_point_count"]
        totals["classification_mismatch_count"] += classification_mismatches
        totals["stored_bound_agreement_count"] += agreements
        totals["stored_bound_mismatch_count"] += bound_mismatches
    return {
        "status": "computed_gauss1_post_hoc_bound_mechanism",
        "source_sha256": sha256(SOURCE),
        "protocol_sha256": sha256(PROTOCOL),
        "diagnostic_runner_sha256": sha256(Path(__file__).resolve()),
        "analysis_scope": {"post_hoc": True, "refit": False, "retuned": False, "radius": 1, "observations": 250},
        "folds": folds,
        "totals": totals,
        "decision": {
            "continuous_noncertification_called_unsafe": False,
            "probability_calibration_claimed": False,
            "native_physical_model_claimed": False,
            "independent_physical_experiment_claimed": False,
        },
        "limitations": [
            "This is a post-hoc diagnostic of frozen outputs, not a new prospective test",
            "Continuous non-certification is not proof of unsafety",
            "Denominator diagnostics do not explain or justify the candidate physical mechanism",
            "Stored bounds use observed residuals and are not probability intervals",
        ],
    }


def validate_summary(summary):
    errors = []
    totals = summary["totals"]
    expected = {
        "point_count": 250,
        "ellipsoid_available_point_count": 190,
        "ellipsoid_unavailable_point_count": 60,
        "classification_mismatch_count": 0,
        "stored_bound_agreement_count": 190,
        "stored_bound_mismatch_count": 0,
    }
    for key, value in expected.items():
        if totals.get(key) != value:
            errors.append(f"Unexpected {key}: {totals.get(key)} != {value}")
    if len(summary["folds"]) != 5:
        errors.append("Expected five folds")
    for key in ["continuous_noncertification_called_unsafe", "probability_calibration_claimed", "native_physical_model_claimed", "independent_physical_experiment_claimed"]:
        if summary["decision"][key]:
            errors.append(f"Overclaim detected: {key}")
    return errors


def render_figure(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    folds = summary["folds"]
    indices = [case["fold"] for case in folds]
    minimum_lower = [case["minimum_denominator_lower"]["value"] for case in folds]
    maximum_support = [case["maximum_covariance_support"]["value"] for case in folds]
    medians = [case["median_residual_upper_bound"] if case["median_residual_upper_bound"] is not None else np.nan for case in folds]
    maxima = [case["maximum_residual_upper_bound"]["value"] if case["maximum_residual_upper_bound"] else np.nan for case in folds]
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), constrained_layout=True)
    axes[0].plot(indices, minimum_lower, "o-", color="#b44b4b", label="Minimum denominator lower bound")
    axes[0].plot(indices, maximum_support, "s--", color="#316c9b", label="Maximum covariance support")
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set_xticks(indices)
    axes[0].set_xlabel("Contiguous fold")
    axes[0].set_ylabel("Denominator-scale quantity")
    axes[0].set_title("Availability boundary; negative lower bounds are retained")
    axes[0].grid(alpha=0.2)
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].plot(indices, medians, "o-", color="#316c9b", label="Median residual upper bound")
    axes[1].plot(indices, maxima, "s--", color="#876a32", label="Maximum residual upper bound")
    axes[1].set_yscale("log")
    axes[1].set_xticks(indices)
    axes[1].set_xlabel("Contiguous fold")
    axes[1].set_ylabel("Available deterministic residual upper bound")
    axes[1].set_title("Bound availability is not bound usefulness")
    axes[1].grid(which="both", alpha=0.2)
    axes[1].legend(frameon=False, fontsize=8)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite Gauss1 mechanism outputs")
    summary = analyze()
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_figure(summary)
    print(json.dumps({"output": str(OUT), "figure": str(FIGURE), "totals": summary["totals"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the diagnostic**

Run: `python scripts/analyze_gauss1_bound_mechanism.py`

Expected: exit 0; totals report 250 points, 190 available, 60 unavailable, zero classification mismatches, 190 stored-bound agreements and zero stored-bound mismatches.

- [ ] **Step 5: Run focused and legacy tests**

Run: `python -m unittest tests.test_gauss1_bound_mechanism tests.test_gauss1_ellipsoid_coverage tests.test_gauss1_external_protocol -v`

Expected: seven tests pass with no failures or errors.

- [ ] **Step 6: Inspect figure and run the full suite**

Check PNG dimensions and read the generated figure. Then run: `python -m unittest discover -s tests -v`

Expected: all repository tests pass; the two panels retain negative denominator lower bounds and omit unavailable fold-five residual bounds rather than plotting them as zero.

- [ ] **Step 7: Commit the validated diagnostic**

```bash
git add scripts/analyze_gauss1_bound_mechanism.py tests/test_gauss1_bound_mechanism.py validation/gauss1-bound-mechanism.json papers/21_Gauss1界失效机制/fig21_gauss1_bound_mechanism.png docs/superpowers/plans/2026-11-09-gauss1-bound-mechanism.md
git commit -m "research: diagnose Gauss1 denominator bound failures"
```

Push only after the complete test suite and secret scan pass. A later report must use the computed JSON rather than guessing which mechanism dominates.


---

### Task 1 Amendment: Same-point residual-bound decomposition

The first green result showed that maximum shift and maximum residual bound can occur at different x positions. Add a same-point decomposition so the report cannot confuse candidate error with denominator-perturbation inflation.

- [ ] **Step 1: Add the failing same-point assertions**

Add to `test_all_points_are_classified_and_stored_bounds_agree`:

```python
        first_maximum = folds[1]["maximum_residual_upper_bound"]
        second_maximum = folds[2]["maximum_residual_upper_bound"]
        self.assertLess(first_maximum["shift_share"], 0.05)
        self.assertGreater(second_maximum["shift_share"], 0.95)
        self.assertAlmostEqual(first_maximum["actual_absolute_residual"] + first_maximum["prediction_shift"], first_maximum["value"], places=8)
        self.assertAlmostEqual(second_maximum["actual_absolute_residual"] + second_maximum["prediction_shift"], second_maximum["value"], places=8)
```

Run: `python -m unittest tests.test_gauss1_bound_mechanism.Gauss1BoundMechanismTests.test_all_points_are_classified_and_stored_bounds_agree -v`

Expected: FAIL with `KeyError: 'shift_share'`.

- [ ] **Step 2: Add the minimal actual-residual calculation**

In `inspect_point`, before the availability branch, add:

```python
    actual_residual = abs(as_fraction(point["observed_y"]) - numerator / denominator)
```

Change the available residual calculation to:

```python
        residual = actual_residual + shift
```

Add to the returned dictionary:

```python
        "actual_residual": float(actual_residual),
```

In `extreme`, replace the direct return with:

```python
    result = {"x": point["x"], "value": point[key]}
    if key == "residual_bound":
        result.update({
            "actual_absolute_residual": point["actual_residual"],
            "prediction_shift": point["shift"],
            "shift_share": point["shift"] / point[key],
        })
    return result
```

- [ ] **Step 3: Regenerate without overwriting the first output**

Preserve the first JSON and figure as `validation/gauss1-bound-mechanism-v1.json` and `papers/21_Gauss1界失效机制/fig21_gauss1_bound_mechanism-v1.png` using file copies, then run `python scripts/analyze_gauss1_bound_mechanism.py`.

Expected: the amended output validates, and fold-one/fold-two maxima satisfy the same-point identities and share gates. This amendment changes diagnostics only; it does not alter the frozen model or bounds.


### Task 1 Visual Verification Amendment

The first rendered figure made fold five dominate the linear axis and hid fold-two near-zero structure. Add a real rendering test before changing the scale.

- [ ] **Step 1: Add the failing rendering test**

```python
    def test_mechanism_figure_uses_symmetric_log_for_extreme_scales(self):
        module = self.load_module()
        import matplotlib.pyplot as plt
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            module.FIGURE = Path(directory) / "figure.png"
            module.render_figure(module.analyze())
            axis = plt.gcf().axes[0]
            self.assertEqual(axis.get_yscale(), "symlog")
            self.assertEqual(axis.yaxis.get_transform().linthresh, 1.0)
        plt.close("all")
```

Run: `python -m unittest tests.test_gauss1_bound_mechanism.Gauss1BoundMechanismTests.test_mechanism_figure_uses_symmetric_log_for_extreme_scales -v`

Expected: FAIL with `'linear' != 'symlog'`.

- [ ] **Step 2: Add the minimal scale change**

Immediately after `axes[0].axhline(0, color="black", linewidth=0.8)`, add:

```python
    axes[0].set_yscale("symlog", linthresh=1.0)
```

Run the focused test, regenerate the outputs while retaining the prior version, read the new figure, and run the full suite. Expected: negative lower bounds, zero, fold-two near-zero values and fold-five extreme values remain simultaneously visible.


## Execution Record

Inline execution completed without subagents. During red-green verification, the same-point test was changed to assert key presence before comparison, the share denominator was corrected from `point["value"]` to `point[key]`, and the scale assertion was corrected to the public `axis.yaxis.get_transform().linthresh` property. The initial and same-point-decomposition outputs are preserved as `v1` and `v2`; regeneration only removed generated originals after byte-for-byte backup verification. The final figure uses a symmetric-log denominator axis and was visually inspected. Final verification: 157 tests passed, catalog remained at 92 projects, evidence packet remained current at 26 chains, and the graph remained append-only at 93 nodes and 158 edges.
