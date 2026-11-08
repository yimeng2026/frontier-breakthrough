"""Cross-database identity and descriptor audit for aspirin (CID 2244 / CHEMBL25)."""

import hashlib
import importlib.metadata
import json
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, rdMolDescriptors

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/aspirin-crosscheck.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    pubchem = json.loads((ROOT / "validation/pubchem-aspirin.json").read_text(encoding="utf-8"))
    chembl = json.loads((ROOT / "validation/chembl-aspirin.json").read_text(encoding="utf-8"))
    structures = chembl["molecule_structures"]
    properties = chembl["molecule_properties"]
    mol = Chem.MolFromSmiles(structures["canonical_smiles"])
    pubchem_mol = Chem.MolFromSmiles(pubchem["ConnectivitySMILES"])
    if mol is None or pubchem_mol is None:
        raise ValueError("RDKit could not parse a frozen aspirin structure")

    canonical_rdkit = Chem.MolToSmiles(mol)
    canonical_pubchem = Chem.MolToSmiles(pubchem_mol)
    inchikey = Chem.MolToInchiKey(mol)
    formula = rdMolDescriptors.CalcMolFormula(mol)
    exact_mass = float(Descriptors.ExactMolWt(mol))
    tpsa = float(rdMolDescriptors.CalcTPSA(mol))
    mol_logp = float(Crippen.MolLogP(mol))
    hba = int(rdMolDescriptors.CalcNumHBA(mol))
    hbd = int(rdMolDescriptors.CalcNumHBD(mol))
    rotatable_default = int(rdMolDescriptors.CalcNumRotatableBonds(mol))
    rotatable_strict = int(rdMolDescriptors.CalcNumRotatableBonds(mol, rdMolDescriptors.NumRotatableBondsOptions.Strict))
    heavy_atoms = int(mol.GetNumHeavyAtoms())

    canonical_structure_identical = canonical_rdkit == canonical_pubchem == structures["canonical_smiles"]
    inchikey_identical = inchikey == structures["standard_inchi_key"]
    if not canonical_structure_identical or not inchikey_identical:
        raise ValueError("Aspirin structural identity mismatch")
    if formula != pubchem["MolecularFormula"] or formula != properties["full_molformula"]:
        raise ValueError("Aspirin formula mismatch")
    if abs(exact_mass - float(pubchem["ExactMass"])) > 1.0e-6:
        raise ValueError("Aspirin exact-mass mismatch")
    if abs(tpsa - float(pubchem["TPSA"])) > 1.0e-6 or abs(tpsa - float(properties["psa"])) > 1.0e-6:
        raise ValueError("Aspirin TPSA mismatch")
    if heavy_atoms != pubchem["HeavyAtomCount"] or heavy_atoms != properties["heavy_atoms"]:
        raise ValueError("Aspirin heavy-atom-count mismatch")

    report = {
        "status": "verified",
        "engine": "RDKit",
        "version": importlib.metadata.version("rdkit"),
        "python": "D:/research-engines/rdkit-env/Scripts/python.exe",
        "pubchem_cid": pubchem["CID"],
        "chembl_id": chembl["molecule_chembl_id"],
        "canonical_structure_identical": canonical_structure_identical,
        "inchikey_identical": inchikey_identical,
        "rdkit": {
            "canonical_smiles": canonical_rdkit,
            "inchikey": inchikey,
            "formula": formula,
            "exact_mass": exact_mass,
            "tpsa": tpsa,
            "mol_logp": mol_logp,
            "hba": hba,
            "hbd": hbd,
            "rotatable_bonds_default": rotatable_default,
            "rotatable_bonds_strict": rotatable_strict,
            "heavy_atoms": heavy_atoms,
        },
        "pubchem": pubchem,
        "chembl_properties": properties,
        "identity_checks": {
            "formula_matches_both": True,
            "exact_mass_matches_pubchem": True,
            "tpsa_matches_both": True,
            "heavy_atoms_match_both": True,
            "molecular_weight_display_matches_both": str(pubchem["MolecularWeight"]) == str(properties["full_mwt"]),
        },
        "difference_interpretation": {
            "status": "consistent identity with algorithm differences; not fraud evidence",
            "fields_not_forced_equal": ["XLogP/ALogP/MolLogP", "hba", "rtb"],
            "xlogp_note": "PubChem XLogP, ChEMBL ALogP and RDKit Crippen MolLogP are different algorithms or conventions; differences are retained",
            "hba_note": "PubChem and ChEMBL hydrogen-bond acceptor counts use different definitions; do not silently harmonize them",
            "rtb_note": "Rotatable-bond counts depend on terminal and amide/ester conventions; default and strict RDKit counts are reported separately",
        },
        "independent_wet_experiment": False,
        "snapshot_sha256": {
            "pubchem": sha256(ROOT / "validation/pubchem-aspirin.json"),
            "chembl": sha256(ROOT / "validation/chembl-aspirin.json"),
        },
        "limitations": [
            "This is a public-record identity and algorithm audit, not a wet-lab experiment, bioactivity meta-analysis or clinical conclusion",
            "Identical identity and selected descriptors do not imply every database field uses the same algorithm",
            "No activity value is merged or inferred from the structural match",
            "Descriptor differences are not labeled as data fabrication; provenance, units and conventions must be examined first",
        ],
    }
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        if previous != report:
            raise ValueError("Refusing to overwrite a different aspirin audit")
    else:
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
