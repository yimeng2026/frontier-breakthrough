#!/usr/bin/env python3
"""Build a stable cross-domain evidence packet for downstream tools and widgets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation"
OUTPUT = ROOT / "exports" / "frontier-evidence.json"


def read(name: str) -> dict:
    return json.loads((VALIDATION / name).read_text(encoding="utf-8"))


def build() -> dict:
    sindy = read("pysindy.json")
    z3 = read("z3.json")
    rdkit = read("rdkit.json")
    pymatgen = read("pymatgen.json")
    pdb = read("pdb-uniprot.json")
    items = [
        {
            "id": "pysindy-linear-system", "domain": "math", "title": "稀疏动力学已知答案复核",
            "status": sindy["status"], "evidenceClass": "known_answer_reproduction",
            "sources": ["https://github.com/dynamicslab/pysindy"],
            "metrics": {"version": sindy["version"], "maxAbsError": sindy["max_abs_error"], "coefficients": sindy["coefficients"]},
            "scientificClaim": "本机 PySINDy 能从合成轨迹近似恢复预设线性系数。",
            "limitations": sindy["scope"], "upstreamContribution": "提供固定特征库和显式误差边界的可重放基线。",
            "snapshotFiles": ["validation/pysindy.json"],
        },
        {
            "id": "z3-real-constraints", "domain": "math", "title": "实数约束已知答案复核",
            "status": z3["status"], "evidenceClass": "known_answer_reproduction",
            "sources": ["https://github.com/Z3Prover/z3"],
            "metrics": {"version": z3["version"], "checks": z3["checks"]},
            "scientificClaim": "两个预设实数约束均被 Z3 判定为不可满足。",
            "limitations": z3["scope"], "upstreamContribution": "为形式化前的反例搜索提供最小可执行样例。",
            "snapshotFiles": ["validation/z3.json"],
        },
        {
            "id": "acetazolamide-pubchem-rdkit", "domain": "chemistry", "title": "乙酰唑胺跨库属性审计",
            "status": rdkit["status"], "evidenceClass": "cross_database_check",
            "sources": ["https://pubchem.ncbi.nlm.nih.gov/rest/pug", "https://github.com/rdkit/rdkit"],
            "metrics": {"pubchemCid": rdkit["pubchem_cid"], "formula": rdkit["formula"], "tpsaDefault": rdkit["tpsa_default_NO_A2"], "tpsaIncludeSP": rdkit["tpsa_include_S_P_A2"], "pubchemTpsa": rdkit["pubchem_tpsa_A2"], "rdkitMolLogP": rdkit["rdkit_crippen_mollogp"], "pubchemXLogP": rdkit["pubchem_xlogp"]},
            "scientificClaim": "规范结构、分子式和精确质量一致；描述符差异必须连算法口径一起解释。",
            "limitations": rdkit["scope"], "upstreamContribution": "提供结构归一、S/P 口径、算法差异和精度的公开对照样例。",
            "snapshotFiles": ["validation/rdkit.json", "validation/pubchem-acetazolamide.json"],
        },
        {
            "id": "silicon-materials-project-pymatgen", "domain": "physics", "title": "硅结构派生量独立重算",
            "status": pymatgen["status"], "evidenceClass": "local_recomputation",
            "sources": ["https://api.materialsproject.org", "https://github.com/materialsproject/pymatgen"],
            "metrics": {"materialId": pymatgen["material_id"], "densityLocal": pymatgen["density_local_g_cm3"], "densityExternal": pymatgen["density_external_g_cm3"], "spaceGroup": pymatgen["space_group_local"], "spaceGroupNumber": pymatgen["space_group_number_local"], "externalBandGapEv": pymatgen["external_band_gap_eV"]},
            "scientificClaim": "从同一公开晶体结构本地重算的密度和空间群与 Materials Project 快照一致。",
            "limitations": pymatgen["scope"], "upstreamContribution": "提供规范 ID 迁移、结构快照与本地派生量核对的轻量复现包。",
            "snapshotFiles": ["validation/pymatgen.json", "validation/materials-project-si.json"],
        },
        {
            "id": "4hhb-hbb-uniprot", "domain": "biology", "title": "血红蛋白结构—序列跨库桥接",
            "status": pdb["status"], "evidenceClass": "cross_database_check",
            "sources": ["https://data.rcsb.org/rest/v1/core", "https://rest.uniprot.org"],
            "metrics": {"pdbId": pdb["pdb_id"], "pdbEntity": pdb["pdb_entity"], "chains": pdb["pdb_chains"], "resolutionA": pdb["resolution_A"], "uniprotAccession": pdb["uniprot_accession"], "uniprotLength": pdb["uniprot_length"], "pdbLength": pdb["pdb_length"], "sequenceMd5": pdb["sequence_md5_recomputed"]},
            "scientificClaim": "P68871 去除起始甲硫氨酸后与 4HHB entity 2 的 146 aa 序列逐字符一致。",
            "limitations": pdb["scope"], "upstreamContribution": "提供不依赖截断字段、由基因/物种检索到精确序列验证的跨库桥接。",
            "snapshotFiles": ["validation/pdb-uniprot.json", "validation/pdb-4hhb.json", "validation/uniprot-hbb.json"],
        },
    ]
    packet = {
        "schemaVersion": 1,
        "asOf": "2026-10-31",
        "project": "frontier-breakthrough",
        "scope": "跨项目本地复核与数据库对照；verified 仅指所述检查，不是新发现、独立实验或外部认证。",
        "items": items,
    }
    validate(packet)
    return packet


def validate(packet: dict) -> None:
    assert packet["schemaVersion"] == 1 and packet["project"] == "frontier-breakthrough"
    ids = [item["id"] for item in packet["items"]]
    assert len(ids) == len(set(ids))
    required = {"id", "domain", "title", "status", "evidenceClass", "sources", "metrics", "scientificClaim", "limitations", "upstreamContribution", "snapshotFiles"}
    for item in packet["items"]:
        assert required <= item.keys()
        assert item["status"] == "verified"
        assert item["sources"] and all(url.startswith("https://") for url in item["sources"])
        assert item["limitations"] and item["upstreamContribution"]
        for name in item["snapshotFiles"]:
            assert name.startswith("validation/") and (ROOT / name).is_file(), name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        assert OUTPUT.exists() and OUTPUT.read_text(encoding="utf-8") == text, "证据包不是最新"
        print("OK: evidence packet is current")
    else:
        OUTPUT.parent.mkdir(exist_ok=True)
        OUTPUT.write_text(text, encoding="utf-8")
        print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
