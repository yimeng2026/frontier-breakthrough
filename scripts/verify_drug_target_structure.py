"""Audit the acetazolamide → CA II → experimental complex evidence chain."""
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "validation"
chembl = json.loads((OUT / "chembl-acetazolamide.json").read_text(encoding="utf-8"))
pubchem = json.loads((OUT / "pubchem-acetazolamide.json").read_text(encoding="utf-8"))
pdb = json.loads((OUT / "pdb-3hs4.json").read_text(encoding="utf-8"))
rdkit = json.loads((OUT / "rdkit.json").read_text(encoding="utf-8"))
activity = chembl["activity"]
mechanism = chembl["mechanism"]
assay = chembl["assay"]
assert chembl["molecule"]["molecule_chembl_id"] == "CHEMBL20"
assert chembl["molecule"]["standard_inchi_key"] == pubchem["InChIKey"]
assert chembl["molecule"]["full_molformula"] == pubchem["MolecularFormula"] == "C4H6N4O3S2"
assert rdkit["canonical_structure_matches_pubchem"] is True
assert mechanism["target_chembl_id"] == chembl["target"]["target_chembl_id"] == "CHEMBL205"
assert mechanism["action_type"] == "INHIBITOR"
assert activity["target_chembl_id"] == assay["target_chembl_id"] == "CHEMBL205"
assert activity["assay_chembl_id"] == assay["assay_chembl_id"] == "CHEMBL657848"
assert activity["standard_type"] == "Ki" and activity["standard_units"] == "nM"
assert activity["standard_relation"] == "="
pchembl = -math.log10(float(activity["standard_value"]) * 1e-9)
assert abs(pchembl - float(activity["pchembl_value"])) < 0.005
assert "carbonic anhydrase ii" in pdb["title"].lower()
assert pdb["experimental_method"] == "X-RAY DIFFRACTION"
assert pdb["ligand"]["comp_id"] == "AZM"
assert "AZM" in pdb["nonpolymer_bound_components"]
assert activity["potential_duplicate"] == 1  # 保留审计警告，不能静默丢弃。
report = {
    "engine": "ChEMBL–PubChem–PDB evidence-chain check",
    "version": "snapshot-2026-10-31",
    "drug": "acetazolamide",
    "chembl_molecule": "CHEMBL20",
    "pubchem_cid": pubchem["CID"],
    "inchi_key": pubchem["InChIKey"],
    "target_chembl_id": "CHEMBL205",
    "target_name": chembl["target"]["pref_name"],
    "target_uniprot": chembl["target"]["component_accession"],
    "mechanism": mechanism["mechanism_of_action"],
    "activity_id": activity["activity_id"],
    "assay_chembl_id": activity["assay_chembl_id"],
    "assay_description": activity["assay_description"],
    "ki_nM": float(activity["standard_value"]),
    "pchembl_external": float(activity["pchembl_value"]),
    "pchembl_recomputed": pchembl,
    "assay_confidence_score": assay["confidence_score"],
    "potential_duplicate": activity["potential_duplicate"],
    "pdb_id": pdb["pdb_id"],
    "pdb_ligand_entity": pdb["ligand"]["entity_id"],
    "pdb_ligand_comp_id": pdb["ligand"]["comp_id"],
    "resolution_A": pdb["resolution_A"],
    "experimental_method": pdb["experimental_method"],
    "status": "verified",
    "scope": "化合物 InChIKey、靶点、单一活性记录和实验复合物的对应关系已核对；Ki=12 nM 只属于 assay CHEMBL657848。potential_duplicate=1 保留为审计警告，不据此直接判造假，也不外推临床效力。",
}
(OUT / "drug-target-structure.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
