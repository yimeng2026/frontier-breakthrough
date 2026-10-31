"""Audit document identity and method evidence without inventing missing protocols."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / "data" / "ca-document-methods-source.json").read_text(encoding="utf-8"))
stability = json.loads((ROOT / "validation" / "ca-document-stability.json").read_text(encoding="utf-8"))
pairs = {pair["document_chembl_id"]: pair for pair in stability["pairs"]}
documents = source["documents"]
assert len(documents) == len(pairs) == 6
assert {doc["documentChemblId"] for doc in documents} == set(pairs)

normalized = lambda value: value.lower().replace("https://doi.org/", "")
output_documents = []
for doc in documents:
    document_id = doc["documentChemblId"]
    pair = pairs[document_id]
    binding = doc["bindingDb"]
    assert doc["methodStatus"] == pair["method_status"]
    assert doc["fullTextStatus"] == "not_obtained"
    assert binding["curatedByChembl"] is True
    assert binding["independentExperiment"] is False
    assert doc["primaryEvidence"]["readingLevel"] in {"abstract_checked", "partial_text_checked"}
    assert doc["openAccessEvidence"]["reportedOpenAccess"] is False
    by_target = {record["target"]: record for record in binding["records"]}
    ca_i = by_target["Carbonic anhydrase 1"]
    ca_ii = by_target["Carbonic anhydrase 2"]
    assert ca_i["kiNM"] == pair["ca_i_ki_nM"]
    assert ca_ii["kiNM"] == pair["ca_ii_ki_nM"]
    for record in binding["records"]:
        assert record["assayDescription"]
    if pair["method_status"] == "explicit_matched":
        assert "esterase assay method" in ca_i["assayDescription"]
        assert "esterase assay method" in ca_ii["assayDescription"]
    output_documents.append({
        **doc,
        "chemblPair": {
            "caIActivityId": pair["ca_i_activity"],
            "caIIActivityId": pair["ca_ii_activity"],
            "caIKiNM": pair["ca_i_ki_nM"],
            "caIIKiNM": pair["ca_ii_ki_nM"],
            "caIMethod": pair["ca_i_method"],
            "caIIMethod": pair["ca_ii_method"],
            "caIDuplicateFlag": pair["ca_i_duplicate"],
            "caIIDuplicateFlag": pair["ca_ii_duplicate"],
            "apparentKiRatio": pair["ki_ratio"],
        },
        "activityEvidenceClass": "separate_database_view_same_curated_origin",
        "protocolVerified": False,
    })

matched = [doc for doc in output_documents if doc["methodStatus"] == "explicit_matched"]
incomplete = [doc for doc in output_documents if doc["methodStatus"] == "method_incomplete"]
assert len(matched) == stability["strict_method_matched_count"] == 1
assert len(incomplete) == stability["method_incomplete_count"] == 5
assert all(not doc["protocolVerified"] for doc in output_documents)
report = {
    "engine": "ChEMBL document and assay-method evidence audit",
    "version": "snapshot-2026-11-01",
    "status": "verified",
    "documentCount": 6,
    "strictMethodMatchedCount": len(matched),
    "methodIncompleteCount": len(incomplete),
    "publisherSnippetCheckedCount": sum(doc["primaryEvidence"]["readingLevel"] == "partial_text_checked" for doc in output_documents),
    "abstractCheckedCount": sum(doc["primaryEvidence"]["readingLevel"] == "abstract_checked" for doc in output_documents),
    "fullTextObtainedCount": 0,
    "completeProtocolObtainedCount": 0,
    "independentWetExperimentCount": 0,
    "documents": output_documents,
    "scope": "六组文档身份均已由 ChEMBL、DOI 与 PubMed／BindingDB 书目交叉确认；三组仅可读出版社正文片段，三组仅摘要，均未取得可复原乙酰唑胺 Ki 测定的完整协议。BindingDB 标注 Curated by ChEMBL，属于同源策划记录的另一入口，不是独立实验。明确同酯酶仍为 1/6，方法不足仍为 5/6。",
    "source": "data/ca-document-methods-source.json",
    "verification": "脚本逐文档断言 DOI 对应的 BindingDB 靶点与 Ki 同 ChEMBL 配对一致，并禁止将摘要／正文片段升级为完整协议。",
}
target = ROOT / "validation" / "ca-document-methods.json"
target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in report.items() if key != "documents"}, ensure_ascii=False, indent=2))
