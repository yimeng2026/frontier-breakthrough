"""Build the native illustrated ENSO full-ellipsoid Lipschitz report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第五十一阶段：ENSO 全椭球 Lipschitz 保守界与交集收紧"
SOURCE = ROOT / "docs/ENSO_FULL_ELLIPSOID_LIPSCHITZ_INTERSECTION_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生ENSO全椭球Lipschitz交集_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-enso-full-ellipsoid-lipschitz-word.json"
EXPECTED = {"math": 4, "images": 1, "tables": 5}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "enso_full_ellipsoid_lipschitz"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_enso_full_ellipsoid_lipschitz_markdown(source):
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
