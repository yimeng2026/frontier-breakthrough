"""Build the native illustrated repository-integrity audit report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第三十七阶段：全仓库一致性审计"
SOURCE = ROOT / "docs/REPOSITORY_INTEGRITY_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生仓库完整性审计_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-repository-integrity-word.json"
EXPECTED = {"math": 1, "images": 1, "tables": 5}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "repository_integrity"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_repository_integrity_markdown(source):
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
