"""Verify exact CA II sequence identity between 3HS4 entity 1 and P00918."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "validation"
pdb = json.loads((OUT / "pdb-3hs4-ca2.json").read_text(encoding="utf-8"))
uniprot = json.loads((OUT / "uniprot-ca2.json").read_text(encoding="utf-8"))
assert pdb["pdb_id"] == "3HS4" and pdb["entity_id"] == 1
assert pdb["gene"] == uniprot["gene"] == "CA2"
assert pdb["taxon_id"] == uniprot["taxon_id"] == 9606
assert pdb["length"] == uniprot["length"] == 260
assert pdb["sequence"] == uniprot["sequence"]
assert pdb["mutation_count"] == pdb["insertion_count"] == pdb["deletion_count"] == 0
md5 = hashlib.md5(uniprot["sequence"].encode("ascii")).hexdigest().upper()
assert md5 == uniprot["sequence_md5_reported_by_uniprot"]
report = {
    "engine": "PDB–UniProt CA II sequence check",
    "version": "snapshot-2026-10-31",
    "pdb_id": pdb["pdb_id"],
    "pdb_entity": pdb["entity_id"],
    "pdb_chain": pdb["chain"],
    "uniprot_accession": uniprot["primary_accession"],
    "uniprot_id": uniprot["uniprotkb_id"],
    "sequence_length": pdb["length"],
    "exact_sequence_match": True,
    "pdb_mutation_count": pdb["mutation_count"],
    "pdb_insertion_count": pdb["insertion_count"],
    "pdb_deletion_count": pdb["deletion_count"],
    "sequence_md5_recomputed": md5,
    "status": "verified",
    "scope": "3HS4 entity 1 与 reviewed P00918 的 260 aa 序列逐字符一致；不是独立酶活或临床验证。",
}
(OUT / "ca2-sequence.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
