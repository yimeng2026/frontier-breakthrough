"""Compare two CA II–acetazolamide structures without faking replication."""
import difflib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "validation"
reference = json.loads((OUT / "pdb-3hs4-ca2.json").read_text(encoding="utf-8"))
control = json.loads((OUT / "pdb-2h4n.json").read_text(encoding="utf-8"))
complex_3hs4 = json.loads((OUT / "pdb-3hs4.json").read_text(encoding="utf-8"))
uniprot = json.loads((OUT / "uniprot-ca2.json").read_text(encoding="utf-8"))
assert reference["sequence"] == uniprot["sequence"]
assert control["pdb_id"] == "2H4N" and control["ligand_comp_id"] == "AZM"
assert complex_3hs4["ligand"]["comp_id"] == "AZM"
assert control["mutation_count"] == 1
assert len(uniprot["sequence"]) == len(control["sequence"]) == 260
opcodes = difflib.SequenceMatcher(None, uniprot["sequence"], control["sequence"], autojunk=False).get_opcodes()
expected_opcodes = [
    ("delete", 0, 1, 0, 0),
    ("equal", 1, 93, 0, 92),
    ("replace", 93, 94, 92, 93),
    ("equal", 94, 201, 93, 200),
    ("insert", 201, 201, 200, 201),
    ("equal", 201, 260, 201, 260),
]
assert opcodes == expected_opcodes, opcodes
assert control["metadata_sample_sequence_length"] == 259
assert control["sequence_string_length"] == 260
differences = [
    {"type": "terminal_deletion", "reference": "M at position 1", "control": "absent"},
    {"type": "substitution", "position": 94, "reference": "H", "control": "N"},
    {"type": "insertion", "after_reference_position": 200, "control": "P"},
]
report = {
    "engine": "CA II structural control analysis",
    "version": "snapshot-2026-10-31",
    "reference": {
        "pdb_id": "3HS4", "resolution_A": complex_3hs4["resolution_A"],
        "data_collection_date": "2006-11-10", "primary_citation_doi": complex_3hs4["primary_citation_doi"],
        "construct": "wild-type CA II / P00918",
    },
    "control": {
        "pdb_id": "2H4N", "resolution_A": control["resolution_A"],
        "data_collection_date": control["data_collection_date"], "primary_citation_doi": control["primary_citation_doi"],
        "construct": "标题为 H94N；实际序列还含起始缺失和中段插入",
    },
    "shared": "均为 X-RAY DIFFRACTION 的人 CA II—乙酰唑胺实验结构，配体均为 AZM",
    "comparison_type": "different_construct_structural_control",
    "exact_wildtype_replication": False,
    "control_initial_methionine_absent": True,
    "alignment_difference_event_count": len(differences),
    "sequence_differences": differences,
    "alignment_opcodes": opcodes,
    "metadata_sample_sequence_length": control["metadata_sample_sequence_length"],
    "sequence_string_length": control["sequence_string_length"],
    "length_metadata_discrepancy": True,
    "excluded_candidates": [
        {"pdb_id": "1CA2", "reason": "CA II 但不含乙酰唑胺配体"},
        {"pdb_id": "3UCJ", "reason": "Coccomyxa beta-carbonic anhydrase，不是人 CA II"},
        {"pdb_id": "2XTK", "reason": "真菌几丁质酶，不是人 CA II"},
    ],
    "status": "verified",
    "scope": "2H4N 与 3HS4 是不同构建的实验结构对照，不能当作同一野生型复合物的独立重复；序列字符串长度 260 与元数据 259 不一致，需进一步核对原始 mmCIF。未比较坐标或结合几何，也不据此证明 Ki 重复。",
}
(OUT / "structural-control.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
