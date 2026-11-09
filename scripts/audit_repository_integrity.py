"""Audit deterministic repository links, manifests, graphs and protocol inputs."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "validation/repository-integrity-rules.json"
OUTPUT = ROOT / "validation/repository-integrity-report.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def chinese_number(value):
    digits = "零一二三四五六七八九"
    if value < 10:
        return digits[value]
    if value == 10:
        return "十"
    if value < 20:
        return "十" + digits[value % 10]
    if value < 100:
        return digits[value // 10] + "十" + (digits[value % 10] if value % 10 else "")
    raise ValueError("Only values below 100 are supported")


def audit_docx_manifest(path):
    errors = []
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    document = ROOT / "papers" / manifest.get("file", "")
    if manifest.get("status") != "passed":
        errors.append(f"Word manifest status is not passed: {path.name}")
    if not document.is_file():
        errors.append(f"Missing Word document: {document}")
        return errors
    if document.stat().st_size != manifest.get("bytes"):
        errors.append(f"Word byte count changed: {document.name}")
    if sha256(document) != manifest.get("sha256"):
        errors.append(f"Word SHA-256 changed: {document.name}")
    return errors


def protocol_input_errors(info, label):
    if not isinstance(info, dict) or "file" not in info or "sha256" not in info:
        return []
    path = ROOT / info["file"]
    if not path.is_file():
        return [f"Missing protocol input: {label}: {info['file']}"]
    if sha256(path) != info["sha256"]:
        return [f"Protocol input hash changed: {label}: {info['file']}"]
    return []


def audit(readme_text=None):
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    if rules["status"] != "frozen_repository_integrity_audit":
        raise ValueError("Repository integrity rules are not frozen")
    if readme_text is None:
        readme_text = (ROOT / rules["readme"]["file"]).read_text(encoding="utf-8")
    groups = {}
    links = [link for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme_text) if not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", link)]
    errors = [f"Broken README link: {link}" for link in links if not (ROOT / link.split("#", 1)[0]).exists()]
    groups["readme_local_links"] = {"count": len(links), "errors": errors}
    figure_links = []
    for document in sorted((ROOT / "docs").glob("*.md")):
        for line in document.read_text(encoding="utf-8").splitlines():
            if line.startswith("图："):
                figure_links.extend(re.findall(r"`([^`]+)`", line))
    errors = [f"Broken document figure link: {link}" for link in figure_links if not (ROOT / link).is_file()]
    groups["document_figure_links"] = {"count": len(figure_links), "errors": errors}
    manifests = sorted((ROOT / "validation").glob("*word.json"))
    errors = [error for manifest in manifests for error in audit_docx_manifest(manifest)]
    groups["word_manifests"] = {"count": len(manifests), "errors": errors}

    evidence = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
    snapshot_files = [snapshot for item in evidence["items"] for snapshot in item["snapshotFiles"]]
    errors = [f"Missing evidence snapshot: {snapshot}" for snapshot in snapshot_files if not (ROOT / snapshot).is_file()]
    groups["evidence_snapshots"] = {"count": len(snapshot_files), "errors": errors}
    graph = json.loads((ROOT / "exports/frontier-knowledge-graph.json").read_text(encoding="utf-8"))
    identifiers = [node["id"] for node in graph["nodes"]]
    errors = []
    if len(set(identifiers)) != len(identifiers):
        errors.append("Duplicate knowledge-graph node id")
    for node in graph["nodes"]:
        for source in node["sourceFiles"]:
            if not (ROOT / source).is_file():
                errors.append(f"Missing graph source: {node['id']}: {source}")
    for item in graph["edges"]:
        if item["from"] not in identifiers or item["to"] not in identifiers:
            errors.append(f"Dangling graph edge: {item}")
    groups["knowledge_graph"] = {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]), "errors": errors}

    protocol_errors = []
    records_checked = 0
    for protocol_file in rules["protocols"]:
        path = ROOT / protocol_file
        if not path.is_file():
            protocol_errors.append(f"Missing protocol input: {protocol_file}")
            continue
        protocol = json.loads(path.read_text(encoding="utf-8"))
        for key in ["input", "original_protocol", "previous_spec", "previous_check"]:
            if key in protocol:
                protocol_errors.extend(protocol_input_errors(protocol[key], f"{protocol_file}:{key}"))
                records_checked += 1
        for info in protocol.get("inputs", {}).values():
            protocol_errors.extend(protocol_input_errors(info, f"{protocol_file}:inputs"))
            records_checked += 1
    groups["protocol_inputs"] = {"count": len(rules["protocols"]), "recordsChecked": records_checked, "errors": protocol_errors}

    corpus = json.loads((ROOT / rules["corpus_v2"]["file"]).read_text(encoding="utf-8"))
    expected = rules["corpus_v2"]
    corpus_errors = []
    for field, status, expected_count in [
        ("documents", "documents", expected["documents"]),
        ("companion_required", "companion_required", expected["companion_required"]),
        ("descriptive_only", "descriptive_only", expected["descriptive_only"]),
        ("complete", "complete", expected["complete"]),
    ]:
        actual = len(corpus["documents"]) if field == "documents" else sum(item["review_status"] == status for item in corpus["documents"])
        if actual != expected_count:
            corpus_errors.append(f"Corpus count mismatch {field}: {actual} != {expected_count}")
    hash_matched = sum(item["original_sha256"] is not None and sha256(ROOT / item["file"]) == item["original_sha256"] for item in corpus["documents"])
    if hash_matched != expected["non_null_hashes"]:
        corpus_errors.append(f"Corpus hash match count changed: {hash_matched}")
    previous = json.loads((ROOT / corpus["previous_spec"]["file"]).read_text(encoding="utf-8"))
    unchanged = sum(item["review_status"] == "companion_required" and sha256(ROOT / item["file"]) == item["original_sha256"] for item in previous["documents"])
    if unchanged != expected["historical_originals"]:
        corpus_errors.append(f"Historical original count changed: {unchanged}")
    groups["corpus_v2"] = {"documents": len(corpus["documents"]), "hashMatchedDocuments": hash_matched, "unchangedOriginals": unchanged, "errors": corpus_errors}

    dynamic_errors = []
    evidence_label = chinese_number(len(evidence["items"]))
    graph_label = f"{len(graph['nodes'])} 个节点、{len(graph['edges'])} 条边"
    evidence_consistent = f"{evidence_label}项已执行检查" in readme_text
    graph_consistent = graph_label in readme_text
    if not evidence_consistent:
        dynamic_errors.append(f"README evidence count is stale; expected {evidence_label}")
    if not graph_consistent:
        dynamic_errors.append(f"README graph count is stale; expected {graph_label}")
    consistent = evidence_consistent and graph_consistent
    groups["dynamic_counts"] = {
        "evidenceItems": len(evidence["items"]),
        "graphNodes": len(graph["nodes"]),
        "graphEdges": len(graph["edges"]),
        "readme_consistent": consistent,
        "errors": dynamic_errors,
    }
    all_errors = []
    for name, group in groups.items():
        all_errors.extend(group["errors"])
    return {
        "status": "passed" if not all_errors else "failed",
        "error_count": len(all_errors),
        "errors": all_errors,
        "groups": groups,
        "decision": rules["decision"],
        "rules_sha256": sha256(RULES),
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = audit()
    if report["error_count"]:
        raise ValueError(report["errors"])
    if args.check:
        stored = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if stored != report:
            raise ValueError("Repository integrity report is stale")
        print("OK: repository integrity audit passed")
        return
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite repository integrity report")
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: repository integrity audit passed; wrote {OUTPUT}")


if __name__ == "__main__":
    main()
