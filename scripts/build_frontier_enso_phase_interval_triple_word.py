"""Build the native illustrated ENSO phase-interval triple-intersection report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第五十二阶段：ENSO 精确三角区间余项与三重交集"
SOURCE = ROOT / "docs/ENSO_PHASE_INTERVAL_TRIPLE_INTERSECTION_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生ENSO三角区间三重交集_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-enso-phase-interval-triple-word.json"
EXPECTED = {"math": 4, "images": 1, "tables": 5}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "enso_phase_interval_triple"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_enso_phase_interval_triple_markdown(source):
    saved = configure()
    try:
        return base.prepare_frontier_markdown(source)
    finally:
        restore(saved)


def main():
    saved = configure()
    try:
        base.main()
    finally:
        restore(saved)


if __name__ == "__main__":
    main()
