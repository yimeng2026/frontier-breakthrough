"""Reproducible molecular-property calculation; external values stay separate."""
import importlib.metadata
import json
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, rdMolDescriptors

OUT = Path(__file__).resolve().parents[1] / "validation"
OUT.mkdir(exist_ok=True)
smiles = "CC(=O)Nc1nnc(S(N)(=O)=O)s1"
mol = Chem.MolFromSmiles(smiles)
assert mol is not None
formula = rdMolDescriptors.CalcMolFormula(mol)
tpsa_no = float(rdMolDescriptors.CalcTPSA(mol))
tpsa_with_s_p = float(rdMolDescriptors.CalcTPSA(mol, includeSandP=True))
xlogp = float(Crippen.MolLogP(mol))
exact_mass = float(Descriptors.ExactMolWt(mol))
external = json.loads((OUT / "pubchem-acetazolamide.json").read_text(encoding="utf-8"))
assert external["CID"] == 1986
external_mol = Chem.MolFromSmiles(external["ConnectivitySMILES"])
assert external_mol is not None
assert Chem.MolToSmiles(mol) == Chem.MolToSmiles(external_mol)
assert formula == external["MolecularFormula"], formula
# PubChem 此字段为整数；按同一显示精度比较，不把舍入差异当成异常。
assert round(tpsa_with_s_p) == external["TPSA"], tpsa_with_s_p
# Crippen MolLogP 与 PubChem XLogP 是不同算法，保留差异，不设伪等价阈值。
assert abs(exact_mass - float(external["ExactMass"])) < 1e-6, exact_mass
report = {
    "engine": "RDKit",
    "version": importlib.metadata.version("rdkit"),
    "python": "D:/research-engines/rdkit-env/Scripts/python.exe",
    "input_smiles": smiles,
    "compound": "acetazolamide（乙酰唑胺）",
    "pubchem_cid": external["CID"],
    "canonical_structure_matches_pubchem": True,
    "formula": formula,
    "tpsa_default_NO_A2": tpsa_no,
    "tpsa_include_S_P_A2": tpsa_with_s_p,
    "pubchem_tpsa_A2": external["TPSA"],
    "rdkit_crippen_mollogp": xlogp,
    "pubchem_xlogp": external["XLogP"],
    "xlogp_algorithm_note": "Crippen MolLogP 与 PubChem XLogP 算法不同，数值差异不能直接判为数据错误。",
    "exact_mass_Da": exact_mass,
    "pubchem_exact_mass_Da": float(external["ExactMass"]),
    "status": "verified",
    "scope": "规范结构、分子式和精确质量与 PubChem 快照一致；TPSA 计入 S/P 后按整数口径一致；XLogP 算法差异单独保留。这不是实验验证，也不据此指认数据造假。",
}
(OUT / "rdkit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
