"""Freeze MP/OQMD property and structure records for three preregistered material pairs."""

import ast
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MP_TOOL = Path("C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/materials_project/scripts/materials_project_tool.py")
OQMD_TOOL = Path("C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/oqmd/scripts/oqmd_tool.py")
PAIRS = {
    "si": {"formula": "Si", "mp_id": "mp-aaaaaaft", "oqmd_entry_id": 5714, "structure_id": "4062615"},
    "gaas": {"formula": "GaAs", "mp_id": "mp-aaaaadtm", "oqmd_entry_id": 7551, "structure_id": "4063731"},
    "sio2": {"formula": "SiO2", "mp_id": "mp-aaaaakjg", "oqmd_entry_id": 22612, "structure_id": "4083627"},
}


def call(tool, api_name, params):
    completed = subprocess.run(
        [sys.executable, tool, "call", "--api-name", api_name, "--params-json", json.dumps(params)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        encoding="utf-8", errors="replace", timeout=120, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stdout)
    outer = ast.literal_eval(completed.stdout)
    payload = json.loads(outer["text"])
    return payload, json.loads(payload["data_preview"])


def main():
    selected = set(sys.argv[1:]) or set(PAIRS)
    provenance_path = ROOT / "sources/material-crosscheck-provenance.json"
    previous = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else {"files": {}}
    provenance = {"retrieved_at_local": datetime.now().astimezone().isoformat(), "pairs": PAIRS, "files": previous["files"]}
    for key, pair in PAIRS.items():
        if key not in selected:
            continue
        mp_payload, mp_data = call(MP_TOOL, "materials_project_get", {"material_id": pair["mp_id"]})
        mp_record = mp_data["data"][0]
        if mp_record["material_id"] != pair["mp_id"]:
            raise ValueError(f"MP canonical ID changed for {key}: {mp_record['material_id']}")
        structure_payload, structure_data = call(OQMD_TOOL, "oqmd_get_structure", {"id": pair["structure_id"]})
        structure = structure_data["data"]["attributes"]
        if structure["_oqmd_entry_id"] != pair["oqmd_entry_id"]:
            raise ValueError(f"Native/OPTIMADE ID mapping changed for {key}")
        oqmd_record = {
            "name": structure["chemical_formula_reduced"],
            "entry_id": structure["_oqmd_entry_id"],
            "composition": structure["chemical_formula_reduced"],
            "spacegroup": structure["space_group_symbol_hermann_mauguin"],
            "band_gap": structure["_oqmd_band_gap"],
            "delta_e": structure["_oqmd_delta_e"],
            "stability": structure["_oqmd_stability"],
            "record_origin": "OQMD OPTIMADE structure attributes, not a repeated native-list query",
        }
        outputs = {
            ROOT / f"sources/materials-project-{key}-response.json": mp_payload,
            ROOT / f"sources/oqmd-{key}-response.json": structure_payload,
            ROOT / f"sources/oqmd-structure-{key}-response.json": structure_payload,
            ROOT / f"validation/materials-project-{key}-dft.json": mp_record,
            ROOT / f"validation/oqmd-{key}.json": oqmd_record,
            ROOT / f"validation/oqmd-structure-{key}.json": {"id": structure_data["data"]["id"], "attributes": structure},
        }
        for path, data in outputs.items():
            if path.exists():
                raise FileExistsError(f"Refusing to overwrite: {path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        provenance["files"][key] = {
            "materials_project_sha256": hashlib.sha256(json.dumps(mp_record, sort_keys=True).encode()).hexdigest(),
            "oqmd_sha256": hashlib.sha256(json.dumps(oqmd_record, sort_keys=True).encode()).hexdigest(),
            "structure_sha256": hashlib.sha256(json.dumps(structure, sort_keys=True).encode()).hexdigest(),
        }
        print(json.dumps({"pair": key, "mp": mp_record["material_id"], "oqmd_entry": oqmd_record["entry_id"], "structure": structure_data["data"]["id"]}))
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
