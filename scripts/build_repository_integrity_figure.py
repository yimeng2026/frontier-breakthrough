"""Render deterministic repository-integrity audit counts."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "validation/repository-integrity-report.json"
FIGURE = ROOT / "papers/44_仓库完整性审计/fig44_repository_integrity.png"


def render_figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    groups = report["groups"]
    labels = ["README links", "Figure links", "DOCX manifests", "Evidence snapshots", "Graph nodes", "Graph edges", "Protocols", "Corpus documents"]
    values = [
        groups["readme_local_links"]["count"],
        groups["document_figure_links"]["count"],
        groups["word_manifests"]["count"],
        groups["evidence_snapshots"]["count"],
        groups["knowledge_graph"]["nodes"],
        groups["knowledge_graph"]["edges"],
        groups["protocol_inputs"]["count"],
        groups["corpus_v2"]["documents"],
    ]
    fig, axes = plt.subplots(1, 1, figsize=(12.5, 5.4), constrained_layout=True)
    positions = list(range(len(labels)))
    axes.bar(positions, values, color="#316c9b")
    axes.set_yscale("log")
    axes.set_xticks(positions, labels, rotation=20, ha="right")
    axes.set_ylabel("Checks or linked objects (log scale)")
    axes.set_title(f"8 audit groups; {report['error_count']} errors")
    axes.grid(axis="y", which="both", alpha=0.2)
    for index, value in enumerate(values):
        axes.text(index, value * 1.08, str(value), ha="center", fontsize=9)
    fig.suptitle(f"Repository integrity: {groups['dynamic_counts']['evidenceItems']} evidence items; historical files preserved", fontsize=12)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)


def main():
    if FIGURE.exists():
        raise FileExistsError("Refusing to overwrite repository integrity figure")
    render_figure()
    print(FIGURE)


if __name__ == "__main__":
    main()
