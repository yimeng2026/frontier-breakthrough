"""Render exact interval results using the scientific Python environment."""

import json

from prove_rational_interval_roots import FIGURE, OUT, validate_summary


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    if FIGURE.exists():
        raise FileExistsError(f"Refusing to overwrite: {FIGURE}")
    summary = json.loads(OUT.read_text(encoding="utf-8"))
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    cases = summary["cases"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2), constrained_layout=True)
    labels = [f"{case['dataset'][0].upper()}{case['fold']}" for case in cases]
    counts = [case["exact"]["root_count"] for case in cases]
    axes[0].bar(range(len(cases)), counts, color=["#b44b4b" if count else "#487a52" for count in counts])
    axes[0].set_xticks(range(len(cases)), labels, rotation=90)
    axes[0].set_ylabel("Exact distinct real roots in closed interval")
    axes[0].set_title("Sturm root counts for all fifteen folds")
    axes[0].grid(axis="y", alpha=0.2)
    for axis, dataset in zip(axes[1:], ["hahn1", "thurber"]):
        case = next(item for item in cases if item["dataset"] == dataset and item["fold"] == 1)
        lower, upper = case["closed_interval"]
        grid = np.linspace(lower, upper, 1200)
        parameters = case["model_parameters"]
        denominator = np.ones_like(grid)
        for degree, name in enumerate(case["denominator_parameter_order"], 1):
            denominator += parameters[name] * grid ** degree
        axis.plot(grid, denominator, color="#20252b", lw=1.5)
        axis.axhline(0, color="#876a32", lw=1, ls="--")
        for index, interval in enumerate(case["exact"]["isolating_intervals"]):
            axis.axvspan(interval["lower_float"], interval["upper_float"], color="#b44b4b", alpha=0.25, label="Exact isolating interval" if index == 0 else None)
        axis.set_title(f"{dataset} fold 1 denominator and exact root intervals")
        axis.set_xlabel("Held-out x")
        axis.set_ylabel("Denominator D(x)")
        axis.grid(alpha=0.2)
        axis.legend(frameon=False, fontsize=8)
    totals = summary["totals"]
    fig.suptitle(f"Exact Sturm isolation; Z3/cvc5: {totals['z3_unsat_count']} unsat and {totals['z3_sat_count']} sat consistency checks", fontsize=13)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps({"figure": str(FIGURE), "cases": len(cases)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
