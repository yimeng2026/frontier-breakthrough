"""Verify the PDB–UniProt bridge using gene/organism and exact sequence alignment."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "validation"
pdb = json.loads((OUT / "pdb-4hhb.json").read_text(encoding="utf-8"))
uniprot = json.loads((OUT / "uniprot-hbb.json").read_text(encoding="utf-8"))
assert pdb["gene"] == uniprot["gene"] == "HBB"
assert pdb["taxon_id"] == uniprot["taxon_id"] == 9606
assert len(pdb["sequence"]) == pdb["length"] == 146
assert len(uniprot["sequence"]) == uniprot["length"] == 147
assert uniprot["sequence"][0] == "M"
assert uniprot["sequence"][1:] == pdb["sequence"]
md5 = hashlib.md5(uniprot["sequence"].encode("ascii")).hexdigest().upper()
assert md5 == uniprot["sequence_md5_reported_by_uniprot"]
report = {
    "engine": "PDB–UniProt cross-database check",
    "version": "snapshot-2026-10-31",
    "pdb_id": pdb["pdb_id"],
    "pdb_entity": pdb["entity_id"],
    "pdb_chains": pdb["chains"],
    "experimental_method": pdb["experimental_method"],
    "resolution_A": pdb["resolution_A"],
    "uniprot_accession": uniprot["primary_accession"],
    "uniprot_id": uniprot["uniprotkb_id"],
    "uniprot_length": uniprot["length"],
    "pdb_length": pdb["length"],
    "relationship": "UniProt 去除起始 M 后与 PDB entity 2 的 146 aa 序列逐字符一致",
    "sequence_md5_recomputed": md5,
    "mapping_basis": "PDB 的 HBB/9606 → UniProt 条件检索 → 精确序列比对；未依赖截断的跨库引用字段",
    "status": "verified",
    "scope": "验证实验结构实体与 reviewed 序列记录的对应关系，不是蛋白功能、机制或临床结论。",
}
(OUT / "pdb-uniprot.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
