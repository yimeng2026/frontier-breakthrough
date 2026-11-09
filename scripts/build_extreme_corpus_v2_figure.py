"""Render the expanded extreme-corpus classification counts."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "validation/extreme-corpus-v2-audit.json"
FIGURE = ROOT / "papers/43_极值全集分级V2/fig43_extreme_corpus_v2.png"


def render_figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    statuses = ["companion_required", "descriptive_only", "complete"]
    labels = ["Companion", "Descriptive", "Complete"]
    colors = ["#316c9b", "#876a32", "#477a55"]
    previous = json.loads((ROOT / spec["previous_spec"]["file"]).read_text(encoding="utf-8"))
    old_counts = [sum(item["review_status"] == status for item in previous["documents"]) for status in statuses]
    new_counts = [sum(item["review_status"] == status for item in spec["documents"]) for status in statuses]
    added = spec["documents"][-7:]
    added_counts = [sum(item["review_status"] == status for item in added) for status in statuses]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0), constrained_layout=True)
    x = np.arange(3)
    width = 0.34
    axes[0].bar(x - width / 2, old_counts, width, label="Previous 16", color="#9aa4aa")
    axes[0].bar(x + width / 2, new_counts, width, label="Current 23", color="#316c9b")
    axes[0].set_xticks(x, labels)
    axes[0].set_ylabel("Documents")
    axes[0].set_title("Current 23: 12 companion / 7 descriptive / 4 complete")
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].grid(axis="y", alpha=0.2)
    for index, values in enumerate(zip(old_counts, new_counts)):
        old, new = values
        axes[0].text(index - width / 2, old + 0.2, str(old), ha="center", fontsize=9)
        axes[0].text(index + width / 2, new + 0.2, str(new), ha="center", fontsize=9)
    axes[1].bar(labels, added_counts, color=colors)
    axes[1].set_ylabel("New documents")
    axes[1].set_title("New 7 by review status")
    axes[1].grid(axis="y", alpha=0.2)
    for index, value in enumerate(added_counts):
        axes[1].text(index, value + 0.08, str(value), ha="center", fontsize=10)
    fig.suptitle("Expanded extreme-report corpus; historical documents preserved", fontsize=12)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)


def main():
    if FIGURE.exists():
        raise FileExistsError("Refusing to overwrite extreme corpus v2 figure")
    render_figure()
    print(FIGURE)


if __name__ == "__main__":
    main()
