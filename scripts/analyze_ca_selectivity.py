"""Compute only method-matched CA I/II ratios; keep CA IX outside the pool."""
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "validation"
panel = json.loads((OUT / "chembl-ca-selectivity-panel.json").read_text(encoding="utf-8"))
activities = {item["target"]: item for item in panel["activities"]}
assert set(activities) == {"CA I", "CA II", "CA IX"}
assert panel["molecule_chembl_id"] == "CHEMBL20"
for item in activities.values():
    assert item["standard_type"] == "Ki"
    assert item["standard_relation"] == "="
    assert item["standard_units"] == "nM"
    assert item["potential_duplicate"] == 1
    assert item["target_organism"] == "Homo sapiens"
    recomputed = -math.log10(item["standard_value"] * 1e-9)
    assert abs(recomputed - item["pchembl_value"]) < 0.005

ca1, ca2, ca9 = activities["CA I"], activities["CA II"], activities["CA IX"]
assert ca1["assay_method"] == ca2["assay_method"] == "esterase assay method"
assert ca9["assay_method"] == "CO2 hydrase assay method"
assert ca9["assay_method"] != ca2["assay_method"]
assert ca1["assay_chembl_id"] != ca2["assay_chembl_id"]
ratio = ca1["standard_value"] / ca2["standard_value"]
pchembl_delta = -math.log10(ca2["standard_value"] * 1e-9) - (-math.log10(ca1["standard_value"] * 1e-9))
assert abs(math.log10(ratio) - pchembl_delta) < 1e-12
report = {
    "engine": "ChEMBL method-aware selectivity analysis",
    "version": "snapshot-2026-10-31",
    "molecule_chembl_id": "CHEMBL20",
    "document_chembl_id": panel["document_chembl_id"],
    "record_id": panel["record_id"],
    "independence": "同一文档、同一 record_id；三条记录不是独立重复实验",
    "ca_i": {"activity_id": ca1["activity_id"], "ki_nM": ca1["standard_value"], "pchembl": ca1["pchembl_value"], "assay_method": ca1["assay_method"], "potential_duplicate": 1},
    "ca_ii": {"activity_id": ca2["activity_id"], "ki_nM": ca2["standard_value"], "pchembl": ca2["pchembl_value"], "assay_method": ca2["assay_method"], "potential_duplicate": 1},
    "ca_ix": {"activity_id": ca9["activity_id"], "ki_nM": ca9["standard_value"], "pchembl": ca9["pchembl_value"], "assay_method": ca9["assay_method"], "potential_duplicate": 1},
    "matched_comparison": "CA I 与 CA II 均为 esterase assay；Ki 单位均为 nM",
    "ca_i_ii_ki_ratio": ratio,
    "ca_ii_minus_ca_i_pchembl_delta": pchembl_delta,
    "ca_ix_comparison": "方法为 CO2 hydrase assay，不与 esterase 结果合并计算选择性比或统一排名",
    "ca_ix_ratio_computed": False,
    "status": "verified",
    "scope": "CA I/II 的 250/12=20.8333 是同一文档、同一酯酶方法下的表观 Ki 比值，提示而非证明普遍选择性；无重复实验统计、置信区间或临床外推。CA IX 因方法不同仅单列。potential_duplicate=1 全部保留。",
}
(OUT / "ca-selectivity.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
