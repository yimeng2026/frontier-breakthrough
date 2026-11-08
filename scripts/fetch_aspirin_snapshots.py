"""Fetch and freeze PubChem and ChEMBL aspirin records through the installed plugins."""

import ast
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBCHEM_TOOL = Path("C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/pubchem/scripts/pubchem_tool.py")
CHEMBL_TOOL = Path("C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/chembl/scripts/chembl_tool.py")


def call(tool, api_name, params):
    completed = subprocess.run(
        [sys.executable, tool, "call", "--api-name", api_name, "--params-json", json.dumps(params)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        encoding="utf-8", errors="replace", timeout=90, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stdout)
    outer = ast.literal_eval(completed.stdout)
    payload = json.loads(outer["text"])
    if "error" in payload.get("is_success", "").lower():
        raise RuntimeError(payload)
    return payload, json.loads(payload["data_preview"])


def main():
    pubchem_payload, properties = call(PUBCHEM_TOOL, "pubchem_get_properties", {
        "by": "cids", "value": "2244",
        "properties": "MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,IUPACName,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,ExactMass,MonoisotopicMass,Charge,HeavyAtomCount,Complexity,Title",
    })
    chembl_payload, molecule = call(CHEMBL_TOOL, "chembl_get", {"resource": "molecule", "chembl_id": "CHEMBL25"})
    record = properties["PropertyTable"]["Properties"][0]
    outputs = {
        ROOT / "sources/pubchem-aspirin-response.json": pubchem_payload,
        ROOT / "sources/chembl-aspirin-response.json": chembl_payload,
        ROOT / "validation/pubchem-aspirin.json": record,
        ROOT / "validation/chembl-aspirin.json": molecule,
    }
    for path in outputs:
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite frozen snapshot: {path}")
    provenance = {
        "retrieved_at_local": datetime.now().astimezone().isoformat(),
        "pubchem_api": "pubchem_get_properties by=cids value=2244",
        "chembl_api": "chembl_get resource=molecule chembl_id=CHEMBL25",
        "pubchem_sha256": hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest(),
        "chembl_sha256": hashlib.sha256(json.dumps(molecule, sort_keys=True).encode()).hexdigest(),
    }
    outputs[ROOT / "sources/aspirin-snapshot-provenance.json"] = provenance
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"outputs": [str(path) for path in outputs], "CID": record["CID"], "chembl_id": molecule["molecule_chembl_id"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
