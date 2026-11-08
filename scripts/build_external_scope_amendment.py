"""Create documentary scope corrections while preserving frozen numerical results."""

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "validation/external-scope-limitations-amendment-01.json"
AUDIT = ROOT / "validation/external-scope-limitations-amendment-01-audit.json"
STALE_FILIP_TEXT = "The cubic/cubic candidate is only an approximation stress test and not the native Filip eleven-parameter model"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def build_corrected_documents():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["status"] != "frozen_external_scope_limitations_amendment":
        raise ValueError("External scope amendment is not frozen")
    documents = []
    for spec in manifest["corrections"]:
        source_path = ROOT / spec["source"]
        protocol_path = ROOT / spec["protocol"]
        if sha256(source_path) != spec["source_sha256"] or sha256(protocol_path) != spec["protocol_sha256"]:
            raise ValueError(f"Frozen source or protocol hash changed for {spec['id']}")
        original = json.loads(source_path.read_text(encoding="utf-8"))
        if original["limitations"][0] != STALE_FILIP_TEXT:
            raise ValueError(f"Unexpected original limitation for {spec['id']}")
        corrected = copy.deepcopy(original)
        corrected["limitations"][0] = spec["corrected_limitation"]
        corrected["scope_correction"] = {
            "amendment_id": manifest["amendment_id"],
            "manifest": str(MANIFEST.relative_to(ROOT)),
            "source_file": spec["source"],
            "source_sha256": spec["source_sha256"],
            "protocol_file": spec["protocol"],
            "protocol_sha256": spec["protocol_sha256"],
            "changed_json_pointer": "/limitations/0",
            "numeric_results_modified": False,
            "original_file_preserved": True,
            "amendment_runner_sha256": sha256(Path(__file__).resolve()),
        }
        if set(corrected) != set(original) | {"scope_correction"}:
            raise ValueError(f"Unexpected field additions for {spec['id']}")
        for key in original:
            if key != "limitations" and corrected[key] != original[key]:
                raise ValueError(f"Original field changed for {spec['id']}: {key}")
        if corrected["limitations"][1:] != original["limitations"][1:] or len(corrected["limitations"]) != len(original["limitations"]):
            raise ValueError(f"More than the first limitation changed for {spec['id']}")
        documents.append({
            "id": spec["id"],
            "source": spec["source"],
            "output": spec["output"],
            "protocol": spec["protocol"],
            "source_sha256": spec["source_sha256"],
            "protocol_sha256": spec["protocol_sha256"],
            "corrected": corrected,
        })
    if [item["id"] for item in documents] != ["mgh17", "gauss1", "misra1a"]:
        raise ValueError("Expected exactly MGH17, Gauss1 and Misra1a documentary corrections")
    return documents


def analyze():
    documents = build_corrected_documents()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    records = []
    for item in documents:
        records.append({
            "id": item["id"],
            "protocol": item["protocol"],
            "protocol_sha256": item["protocol_sha256"],
            "source": item["source"],
            "source_sha256": item["source_sha256"],
            "output": item["output"],
            "corrected_sha256": hashlib.sha256(canonical(item["corrected"])).hexdigest(),
            "changed_json_pointer": "/limitations/0",
            "all_other_original_fields_preserved": True,
        })
    return {
        "status": "computed_external_scope_limitations_amendment",
        "amendment_id": manifest["amendment_id"],
        "created_at_local": manifest["created_at_local"],
        "correction_count": len(records),
        "dataset_ids": [item["id"] for item in records],
        "changed_json_pointer": "/limitations/0",
        "numeric_results_modified": False,
        "original_files_preserved": True,
        "future_protocol_rule": manifest["future_protocol_rule"],
        "corrections": records,
        "amendment_runner_sha256": sha256(Path(__file__).resolve()),
    }


def main():
    documents = build_corrected_documents()
    if AUDIT.exists() or any((ROOT / item["output"]).exists() for item in documents):
        raise FileExistsError("Refusing to overwrite external scope amendment outputs")
    audit = analyze()
    for item in documents:
        (ROOT / item["output"]).write_bytes(canonical(item["corrected"]))
    AUDIT.write_bytes(canonical(audit))
    print(json.dumps({"audit": str(AUDIT), "correction_count": audit["correction_count"], "outputs": [item["output"] for item in documents]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
