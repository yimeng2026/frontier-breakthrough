"""Assess CA I/II ratio stability without meta-analyzing incomparable assays."""
import json
import statistics
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "validation"
panel = json.loads((OUT / "chembl-ca-document-pairs.json").read_text(encoding="utf-8"))
pairs = panel["pairs"]
assert len(pairs) == 6
assert len({p["document_chembl_id"] for p in pairs}) == 6
for pair in pairs:
    pair["ki_ratio"] = pair["ca_i_ki_nM"] / pair["ca_ii_ki_nM"]
    assert pair["ca_i_ki_nM"] > 0 and pair["ca_ii_ki_nM"] > 0
matched = [p for p in pairs if p["method_status"] == "explicit_matched"]
incomplete = [p for p in pairs if p["method_status"] == "method_incomplete"]
assert len(matched) == 1 and len(incomplete) == 5
assert matched[0]["ca_i_method"] == matched[0]["ca_ii_method"] == "esterase assay method"
ratios = sorted(p["ki_ratio"] for p in pairs)
median = statistics.median(ratios)
report = {
    "engine": "Cross-document CA I/II sensitivity analysis",
    "version": "snapshot-2026-10-31",
    "document_count": len(pairs),
    "strict_method_matched_count": len(matched),
    "method_incomplete_count": len(incomplete),
    "pairs": pairs,
    "ratio_min": ratios[0],
    "ratio_max": ratios[-1],
    "max_min_fold": ratios[-1] / ratios[0],
    "exploratory_median_ratio_not_a_selectivity_estimate": median,
    "stability_conclusion": "not_supported_as_stable_point_estimate",
    "meta_analysis_performed": False,
    "status": "verified",
    "scope": "六组文档的表观 Ki 比值从 20.8333 到 75，极差倍数为 3.6；仅一组明确同酯酶方法，其余方法信息不足，不能据此合并成普适选择性常数。不同文档和重复标记也不保证实验独立。",
}
(OUT / "ca-document-stability.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in report.items() if k != "pairs"}, ensure_ascii=False))
