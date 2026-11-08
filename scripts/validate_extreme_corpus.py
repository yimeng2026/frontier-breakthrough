"""Validate corpus-wide extreme-value classifications and preservation hashes."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "validation/extreme-corpus-audit.json"
CHECK = ROOT / "validation/extreme-corpus-check.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_corpus(corpus_text=None):
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    corpus_path = ROOT / spec["corpus_document"]
    if corpus_text is None:
        if not corpus_path.is_file():
            return [f"Missing corpus document: {spec['corpus_document']}"]
        corpus_text = corpus_path.read_text(encoding="utf-8")
    errors = []
    documents = spec["documents"]
    if len(documents) != spec["document_count"] or len(documents) != 16:
        errors.append("Expected exactly 16 reviewed documents")
    for item in documents:
        path = ROOT / item["file"]
        if not path.is_file():
            errors.append(f"Missing reviewed document: {item['file']}")
            continue
        if item["file"] not in corpus_text:
            errors.append(f"Corpus does not classify {item['file']}")
        if item["review_status"] == "companion_required":
            if sha256(path) != item["original_sha256"]:
                errors.append(f"Original document changed: {item['file']}")
            if item["claim_level"] not in {"distribution_summary", "mechanism_interpretation"}:
                errors.append(f"Invalid companion claim level: {item['file']}")
        if item["review_status"] not in corpus_text:
            errors.append(f"Corpus missing review status {item['review_status']} for {item['file']}")
    for companion in spec["required_companions"]:
        if companion not in corpus_text:
            errors.append(f"Corpus missing companion link: {companion}")
    if spec["required_preservation_text"] not in corpus_text:
        errors.append("Corpus does not preserve original Markdown and Word explicitly")
    return errors


def build_check():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    errors = validate_corpus()
    corpus_path = ROOT / spec["corpus_document"]
    return {
        "status": "passed" if not errors else "failed",
        "document_count": spec["document_count"],
        "companion_required_count": spec["companion_required_count"],
        "complete_count": sum(item["review_status"] == "complete" for item in spec["documents"]),
        "descriptive_only_count": sum(item["review_status"] == "descriptive_only" for item in spec["documents"]),
        "unchanged_original_count": sum(item["review_status"] == "companion_required" and sha256(ROOT / item["file"]) == item["original_sha256"] for item in spec["documents"]),
        "error_count": len(errors),
        "errors": errors,
        "corpus_document": spec["corpus_document"],
        "corpus_document_sha256": sha256(corpus_path),
        "spec_file": str(SPEC.relative_to(ROOT)),
        "spec_sha256": sha256(SPEC),
        "validator_sha256": sha256(Path(__file__).resolve()),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    current = build_check()
    if current["error_count"]:
        raise ValueError(current["errors"])
    if args.check:
        stored = json.loads(CHECK.read_text(encoding="utf-8"))
        if stored != current:
            raise ValueError("Extreme corpus check is stale")
        print("OK: extreme corpus classification and original preservation passed")
        return
    if CHECK.exists():
        raise FileExistsError("Refusing to overwrite extreme corpus check")
    CHECK.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: extreme corpus classification passed; wrote {CHECK}")


if __name__ == "__main__":
    main()
