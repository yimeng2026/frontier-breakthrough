"""Validate the preserved 23-document extreme-report corpus and receipt."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "validation/extreme-corpus-v2-audit.json"
CHECK = ROOT / "validation/extreme-corpus-v2-check.json"
ALLOWED_LEVELS = {"maximum_only", "distribution_summary", "mechanism_interpretation"}
ALLOWED_STATUSES = {"companion_required", "descriptive_only", "complete"}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def previous_integrity(spec):
    errors = []
    for key in ["previous_spec", "previous_check"]:
        info = spec[key]
        path = ROOT / info["file"]
        if not path.is_file() or sha256(path) != info["sha256"]:
            errors.append(f"Historical file changed: {info['file']}")
    previous_spec = json.loads((ROOT / spec["previous_spec"]["file"]).read_text(encoding="utf-8"))
    current_by_file = {item["file"]: item for item in spec["documents"]}
    for item in previous_spec["documents"]:
        if item["review_status"] != "companion_required":
            continue
        path = ROOT / item["file"]
        if not path.is_file() or sha256(path) != item["original_sha256"]:
            errors.append(f"Historical companion original changed: {item['file']}")
        if current_by_file.get(item["file"], {}).get("original_sha256") != item["original_sha256"]:
            errors.append(f"V2 historical hash changed: {item['file']}")
    return errors


def validate_corpus(corpus_text=None):
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["status"] != "frozen_extreme_corpus_v2_classification":
        return ["V2 corpus is not frozen"]
    corpus_path = ROOT / spec["corpus_document"]
    if corpus_text is None:
        corpus_text = corpus_path.read_text(encoding="utf-8") if corpus_path.is_file() else ""
    errors = previous_integrity(spec)
    documents = spec["documents"]
    identifiers = [item["file"] for item in documents]
    if len(documents) != spec["document_count"] or len(documents) != 23:
        errors.append("Expected exactly 23 reviewed documents")
    if len(set(identifiers)) != len(identifiers):
        errors.append("Duplicate reviewed document")
    for field, status, expected in [
        ("companion_required_count", "companion_required", 12),
        ("complete_count", "complete", 4),
        ("descriptive_only_count", "descriptive_only", 7),
    ]:
        actual = sum(item["review_status"] == status for item in documents)
        if actual != expected or spec[field] != expected:
            errors.append(f"Unexpected {field}: {actual}")
    for item in documents:
        path = ROOT / item["file"]
        if item["review_status"] not in ALLOWED_STATUSES or item["claim_level"] not in ALLOWED_LEVELS:
            errors.append(f"Invalid claim/review level: {item['file']}")
        if not path.is_file():
            errors.append(f"Missing reviewed document: {item['file']}")
            continue
        if item["file"] not in corpus_text:
            errors.append(f"Corpus does not classify {item['file']}")
        if item["review_status"] not in corpus_text:
            errors.append(f"Corpus missing review status {item['review_status']} for {item['file']}")
        if item["original_sha256"] is not None and sha256(path) != item["original_sha256"]:
            errors.append(f"Document hash changed: {item['file']}")
    for companion in spec["required_companions"]:
        if companion not in corpus_text:
            errors.append(f"Corpus missing companion link: {companion}")
    if spec["required_preservation_text"] not in corpus_text:
        errors.append("Corpus does not preserve original Markdown and old Word explicitly")
    if not spec["previous_files_preserved"]:
        errors.append("Historical preservation flag is false")
    return errors


def build_check():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    errors = validate_corpus()
    corpus_path = ROOT / spec["corpus_document"]
    return {
        "status": "passed" if not errors else "failed",
        "document_count": spec["document_count"],
        "companion_required_count": spec["companion_required_count"],
        "complete_count": spec["complete_count"],
        "descriptive_only_count": spec["descriptive_only_count"],
        "hash_matched_document_count": sum(
            item["original_sha256"] is not None and sha256(ROOT / item["file"]) == item["original_sha256"]
            for item in spec["documents"]
        ),
        "unchanged_original_count": sum(
            item["review_status"] == "companion_required" and sha256(ROOT / item["file"]) == item["original_sha256"]
            for item in json.loads((ROOT / spec["previous_spec"]["file"]).read_text(encoding="utf-8"))["documents"]
        ),
        "error_count": len(errors),
        "errors": errors,
        "corpus_document": spec["corpus_document"],
        "corpus_document_sha256": sha256(corpus_path),
        "spec_file": str(SPEC.relative_to(ROOT)),
        "spec_sha256": sha256(SPEC),
        "validator_sha256": sha256(Path(__file__).resolve()),
        "previous_spec_file": spec["previous_spec"]["file"],
        "previous_spec_sha256": sha256(ROOT / spec["previous_spec"]["file"]),
        "previous_check_file": spec["previous_check"]["file"],
        "previous_check_sha256": sha256(ROOT / spec["previous_check"]["file"]),
        "previous_files_preserved": not previous_integrity(spec),
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
            raise ValueError("Extreme corpus v2 check is stale")
        print("OK: 23-document extreme corpus classification and historical preservation passed")
        return
    if CHECK.exists():
        raise FileExistsError("Refusing to overwrite extreme corpus v2 check")
    CHECK.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: 23-document extreme corpus classification passed; wrote {CHECK}")


if __name__ == "__main__":
    main()
