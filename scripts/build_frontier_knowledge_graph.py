"""Build a validated claim-evidence-counterexample-experiment graph from real outputs."""

import json
from pathlib import Path


def node(identifier, kind, title, status, sources):
    return {"id": identifier, "kind": kind, "title": title, "status": status, "sourceFiles": sources}


def edge(source, target, relation):
    return {"from": source, "to": target, "relation": relation}


def build_graph(root):
    root = Path(root)
    chwirut = json.loads((root / "validation/chwirut-holdout.json").read_text(encoding="utf-8"))
    z3 = json.loads((root / "validation/z3-identifiability.json").read_text(encoding="utf-8"))
    aspirin = json.loads((root / "validation/aspirin-crosscheck.json").read_text(encoding="utf-8"))
    material = json.loads((root / "validation/material-crosscheck.json").read_text(encoding="utf-8"))
    eckerle = json.loads((root / "validation/eckerle4-two-tail.json").read_text(encoding="utf-8"))
    cvc5 = json.loads((root / "validation/cvc5-crosscheck.json").read_text(encoding="utf-8"))
    hahn1 = json.loads((root / "validation/hahn1-high-temperature.json").read_text(encoding="utf-8"))
    z3Hahn1 = json.loads((root / "validation/z3-hahn1-denominator.json").read_text(encoding="utf-8"))
    cvc5Hahn1 = json.loads((root / "validation/cvc5-hahn1-denominator.json").read_text(encoding="utf-8"))
    groupedStress = json.loads((root / "validation/grouped-stress.json").read_text(encoding="utf-8"))
    identifiability = json.loads((root / "validation/hahn1-fold1-identifiability.json").read_text(encoding="utf-8"))
    denominatorRoots = json.loads((root / "validation/hahn1-frozen-denominator-roots.json").read_text(encoding="utf-8"))
    thurber = json.loads((root / "validation/thurber-prospective-gate.json").read_text(encoding="utf-8"))
    kirby = json.loads((root / "validation/kirby2-prospective-gate.json").read_text(encoding="utf-8"))
    if not chwirut["decision"]["limited_support"] or not aspirin["canonical_structure_identical"] or not material["structure_identity_confirmed"] or not eckerle["decision"]["limited_support"] or not cvc5["all_results_match_z3"] or not hahn1["decision"]["limited_support"] or cvc5Hahn1["result"] != "unsat" or z3Hahn1["result"] != "unsat" or groupedStress["overall_robust_limited_support"] or identifiability["decision"]["fold_1_failure_reversed"] or denominatorRoots["decision"]["fold_1_failure_reversed"] or denominatorRoots["folds"][0]["real_root_count_in_held_out_closed_interval"] != 2 or thurber["decision"]["overall_all_folds_gated_support"] or not thurber["full_fit_certification"]["matches_nist_within_frozen_tolerances"] or not kirby["decision"]["overall_all_folds_gated_support"] or not kirby["full_fit_certification"]["matches_nist_within_frozen_tolerances"]:
        raise ValueError("Expected evidence states are not present")

    nodes = [
        node("track-holdout", "project", "真实数据留出与外推边界", "active", ["validation/chwirut-holdout-protocol.json"]),
        node("track-formal", "project", "形式化定义域与可识别性反例", "active", ["validation/z3-identifiability.json"]),
        node("track-chemistry", "project", "化学与生物数据质量", "active", ["validation/aspirin-crosscheck.json"]),
        node("track-materials", "project", "物理与材料跨库复核", "active", ["validation/material-crosscheck.json"]),
        node("track-knowledge", "project", "主张—证据—反例—实验知识连接", "active", ["contracts/frontier-knowledge-graph.schema.json"]),
        node("claim-chwirut-extrapolation", "claim", "Chwirut 三参数模型只在本预注册高距离切片获得有限支持", "limited_support", ["validation/chwirut-holdout.json"]),
        node("claim-nist-reproduction", "claim", "全数据拟合复现 NIST 认证值只属于已知答案复核", "supported", ["validation/chwirut-holdout.json", "validation/chwirut-holdout-verification.json"]),
        node("claim-universal-identifiability", "claim", "任意少量点都能唯一识别全部模型参数", "falsified", ["validation/z3-identifiability.json"]),
        node("claim-positive-denominator", "claim", "显式正性定义域内 Chwirut 分母为正", "supported", ["validation/z3-identifiability.json"]),
        node("claim-aspirin-identity", "claim", "阿司匹林在 PubChem、ChEMBL 与 RDKit 间具有同一结构身份", "supported", ["validation/aspirin-crosscheck.json"]),
        node("claim-descriptor-fraud", "claim", "描述符或计数差异本身就是数据造假证据", "falsified", ["validation/aspirin-crosscheck.json"]),
        node("claim-material-identity", "claim", "Si、GaAs、SiO2 的三组跨库结构身份分别成立", "supported", ["validation/material-crosscheck.json"]),
        node("claim-universal-bandgap", "claim", "同一结构在不同 DFT 数据库中必须给出相同带隙", "falsified", ["validation/material-crosscheck.json"]),
        node("claim-knowledge-graph", "claim", "知识连接必须同时保留支持、反例、实验与限制", "supported", ["contracts/frontier-knowledge-graph.schema.json"]),
        node("evidence-chwirut", "evidence", "54 个 NIST 观测的逐点预测与独立指标复算", "supported", ["validation/chwirut-holdout.json", "validation/chwirut-holdout-verification.json"]),
        node("evidence-z3", "evidence", "Z3 定义域不可满足性与可识别性反例", "supported", ["validation/z3-identifiability.json"]),
        node("evidence-aspirin", "evidence", "阿司匹林身份与描述符口径快照", "supported", ["validation/pubchem-aspirin.json", "validation/chembl-aspirin.json", "validation/aspirin-crosscheck.json"]),
        node("evidence-material", "evidence", "三组材料的跨库 DFT 与本地结构重算", "supported", ["validation/material-crosscheck.json"]),
        node("counterexample-xzero", "counterexample", "x=0 时两个不同参数三元组产生相同响应", "supported", ["validation/z3-identifiability.json"]),
        node("counterexample-descriptor", "counterexample", "LogP、氢键和可旋转键的定义差异无需被解释为造假", "supported", ["validation/aspirin-crosscheck.json"]),
        node("counterexample-bandgap", "counterexample", "同结构的 MP 与 OQMD 带隙仍可不同", "supported", ["validation/material-crosscheck.json"]),
        node("experiment-chwirut-protocol", "experiment", "47 个训练观测与 7 个高距离留出观测", "supported", ["validation/chwirut-holdout-protocol.json"]),
        node("experiment-material-protocol", "experiment", "三组 MP／OQMD／PyMatGen 结构复核协议", "supported", ["validation/material-crosscheck-protocol.json", "validation/material-crosscheck-protocol-amendment-01.json"]),
        node("limitation-single-split", "limitation", "单次单数据集留出不能证明普适规律或参数完全内生", "active", ["validation/chwirut-holdout.json"]),
        node("limitation-public-records", "limitation", "公开记录与本地重算不等于独立湿实验或临床结论", "active", ["validation/aspirin-crosscheck.json"]),
        node("limitation-small-material-sample", "limitation", "三种材料不是全球 DFT 基准，也不证明某个实现普遍更准确", "active", ["validation/material-crosscheck.json"]),
        node("claim-eckerle4-two-tail", "claim", "Eckerle4 高斯模型只在预注册双尾切片获得有限支持", "limited_support", ["validation/eckerle4-two-tail.json"]),
        node("evidence-eckerle4", "evidence", "35 个 Eckerle4 观测的逐点预测与独立指标复算", "supported", ["validation/eckerle4-two-tail.json", "validation/eckerle4-two-tail-verification.json"]),
        node("experiment-eckerle4-protocol", "experiment", "27 个中央训练观测、低尾 3 点和高尾 5 点", "supported", ["validation/eckerle4-two-tail-protocol.json"]),
        node("claim-solver-agreement", "claim", "cvc5 与 Z3 对三项定义域和可识别性检查给出一致结果", "supported", ["validation/cvc5-crosscheck.json"]),
        node("evidence-cvc5", "evidence", "cvc5 1.4.2 的 SMT-LIB 日志与精确有理数反例模型", "supported", ["validation/cvc5-crosscheck.json"]),
        node("limitation-two-datasets", "limitation", "两个 NIST 数据集的有限支持仍不是跨领域普适规律", "active", ["validation/chwirut-holdout.json", "validation/eckerle4-two-tail.json"]),
        node("claim-hahn1-high-temperature", "claim", "Hahn1 七参数有理模型只在预注册高温切片获得有限支持", "limited_support", ["validation/hahn1-high-temperature.json"]),
        node("evidence-hahn1", "evidence", "236 个 Hahn1 观测的逐点预测与独立指标复算", "supported", ["validation/hahn1-high-temperature.json", "validation/hahn1-high-temperature-verification.json"]),
        node("experiment-hahn1-protocol", "experiment", "219 个训练观测与 17 个高温留出观测", "supported", ["validation/hahn1-high-temperature-protocol.json"]),
        node("limitation-three-datasets", "limitation", "三个 NIST 数据集的有限支持仍不是跨模型类别普适规律", "active", ["validation/chwirut-holdout.json", "validation/eckerle4-two-tail.json", "validation/hahn1-high-temperature.json"]),
        node("claim-hahn1-denominator", "claim", "认证 Hahn1 分母在 0<=x<=900 内无零根", "supported", ["validation/z3-hahn1-denominator.json", "validation/cvc5-hahn1-denominator.json"]),
        node("evidence-hahn1-denominator", "evidence", "Z3 与 cvc5 对 Hahn1 分母实验区间给出 unsat", "supported", ["validation/z3-hahn1-denominator.json", "validation/cvc5-hahn1-denominator.json", "validation/cvc5-hahn1-denominator.smt2"]),
        node("claim-unbounded-denominator-safety", "claim", "Hahn1 分母在所有非负温度都没有零根", "falsified", ["validation/z3-hahn1-denominator.json"]),
        node("counterexample-hahn1-outdomain-root", "counterexample", "Hahn1 分母在约 1931 K 的域外正根", "supported", ["validation/z3-hahn1-denominator.json"]),
        node("claim-universal-robustness", "claim", "三个模型在五组连续区间留出中均稳健且不劣于基线", "falsified", ["validation/grouped-stress.json"]),
        node("evidence-grouped-stress", "evidence", "三个数据集的 15 折连续区间留出结果与失败审计", "supported", ["validation/grouped-stress.json"]),
        node("experiment-grouped-stress-protocol", "experiment", "相同 x 不跨训练与测试的五组连续区间留出协议", "supported", ["validation/grouped-stress-protocol.json"]),
        node("limitation-grouped-stress", "limitation", "分母非零、参数可识别和跨区间预测稳健是不同问题", "active", ["validation/grouped-stress.json"]),
        node("claim-fold1-heldout-pole-free", "claim", "Hahn1 第 1 折冻结模型在低温留出闭区间内无实极点", "falsified", ["validation/hahn1-frozen-denominator-roots.json"]),
        node("evidence-hahn1-fold1-identifiability", "evidence", "五折局部雅可比、参数相关和留出预测敏感度诊断", "supported", ["validation/hahn1-fold1-identifiability.json"]),
        node("evidence-hahn1-frozen-denominator-roots", "evidence", "第 1 折约 45.526978 K 与 72.131671 K 的两个数值单极点", "supported", ["validation/hahn1-frozen-denominator-roots.json"]),
        node("limitation-post-hoc-mechanism", "limitation", "事后机制诊断与数值根定位不是预注册检验或精确代数证书", "active", ["validation/hahn1-fold1-identifiability.json", "validation/hahn1-frozen-denominator-roots.json"]),
        node("claim-thurber-all-folds-gated", "claim", "Thurber 五个连续区间折全部通过预测区、可识别性与基线验收", "falsified", ["validation/thurber-prospective-gate.json"]),
        node("evidence-thurber-prospective-gate", "evidence", "Thurber 四折通过、一折预测区实根与预测失败的全部记录", "supported", ["validation/thurber-prospective-gate.json"]),
        node("experiment-thurber-prospective-protocol", "experiment", "在任何 Thurber 拟合前冻结的五折验收协议", "supported", ["validation/thurber-prospective-gate-protocol.json"]),
        node("limitation-thurber-prospective", "limitation", "单个新数据集的数值前瞻检验不是独立物理实验或普适检出率证明", "active", ["validation/thurber-prospective-gate.json"]),
        node("claim-kirby2-all-folds-gated", "claim", "Kirby2 五个连续区间折全部通过预测区、可识别性与二次基线验收", "supported", ["validation/kirby2-prospective-gate.json"]),
        node("evidence-kirby2-prospective-gate", "evidence", "Kirby2 五折有限支持及第 1 折外推衰减、高条件数记录", "supported", ["validation/kirby2-prospective-gate.json"]),
        node("experiment-kirby2-prospective-protocol", "experiment", "在任何 Kirby2 拟合前冻结的五折跨次数验收协议", "supported", ["validation/kirby2-prospective-gate-protocol.json"]),
        node("limitation-kirby2-prospective", "limitation", "Kirby2 的整体有限支持不是全域无根、绝对精度或其他模型的保证", "active", ["validation/kirby2-prospective-gate.json"]),
    ]
    edges = []
    for track, claims in {
        "track-holdout": ["claim-chwirut-extrapolation", "claim-nist-reproduction", "evidence-chwirut", "experiment-chwirut-protocol", "limitation-single-split", "claim-eckerle4-two-tail", "evidence-eckerle4", "experiment-eckerle4-protocol", "limitation-two-datasets", "claim-hahn1-high-temperature", "evidence-hahn1", "experiment-hahn1-protocol", "limitation-three-datasets", "claim-universal-robustness", "evidence-grouped-stress", "experiment-grouped-stress-protocol", "limitation-grouped-stress", "claim-fold1-heldout-pole-free", "evidence-hahn1-fold1-identifiability", "evidence-hahn1-frozen-denominator-roots", "limitation-post-hoc-mechanism", "claim-thurber-all-folds-gated", "evidence-thurber-prospective-gate", "experiment-thurber-prospective-protocol", "limitation-thurber-prospective", "claim-kirby2-all-folds-gated", "evidence-kirby2-prospective-gate", "experiment-kirby2-prospective-protocol", "limitation-kirby2-prospective"],
        "track-formal": ["claim-universal-identifiability", "claim-positive-denominator", "evidence-z3", "counterexample-xzero", "claim-solver-agreement", "evidence-cvc5", "claim-hahn1-denominator", "evidence-hahn1-denominator", "claim-unbounded-denominator-safety", "counterexample-hahn1-outdomain-root"],
        "track-chemistry": ["claim-aspirin-identity", "claim-descriptor-fraud", "evidence-aspirin", "counterexample-descriptor", "limitation-public-records"],
        "track-materials": ["claim-material-identity", "claim-universal-bandgap", "evidence-material", "counterexample-bandgap", "experiment-material-protocol", "limitation-small-material-sample"],
        "track-knowledge": ["claim-knowledge-graph"],
    }.items():
        edges.extend(edge(track, target, "contains") for target in claims)
    edges += [
        edge("evidence-chwirut", "claim-chwirut-extrapolation", "supports"),
        edge("evidence-chwirut", "claim-nist-reproduction", "supports"),
        edge("experiment-chwirut-protocol", "claim-chwirut-extrapolation", "tests"),
        edge("limitation-single-split", "claim-chwirut-extrapolation", "limits"),
        edge("evidence-z3", "claim-positive-denominator", "supports"),
        edge("counterexample-xzero", "claim-universal-identifiability", "contradicts"),
        edge("evidence-aspirin", "claim-aspirin-identity", "supports"),
        edge("counterexample-descriptor", "claim-descriptor-fraud", "contradicts"),
        edge("limitation-public-records", "claim-aspirin-identity", "limits"),
        edge("evidence-material", "claim-material-identity", "supports"),
        edge("counterexample-bandgap", "claim-universal-bandgap", "contradicts"),
        edge("experiment-material-protocol", "claim-material-identity", "tests"),
        edge("limitation-small-material-sample", "claim-material-identity", "limits"),
        edge("evidence-eckerle4", "claim-eckerle4-two-tail", "supports"),
        edge("experiment-eckerle4-protocol", "claim-eckerle4-two-tail", "tests"),
        edge("limitation-two-datasets", "claim-eckerle4-two-tail", "limits"),
        edge("evidence-cvc5", "claim-solver-agreement", "supports"),
        edge("evidence-cvc5", "counterexample-xzero", "supports"),
        edge("evidence-hahn1", "claim-hahn1-high-temperature", "supports"),
        edge("experiment-hahn1-protocol", "claim-hahn1-high-temperature", "tests"),
        edge("limitation-three-datasets", "claim-hahn1-high-temperature", "limits"),
        edge("evidence-hahn1-denominator", "claim-hahn1-denominator", "supports"),
        edge("evidence-hahn1-denominator", "counterexample-hahn1-outdomain-root", "supports"),
        edge("counterexample-hahn1-outdomain-root", "claim-unbounded-denominator-safety", "contradicts"),
        edge("experiment-grouped-stress-protocol", "claim-universal-robustness", "tests"),
        edge("evidence-grouped-stress", "claim-universal-robustness", "contradicts"),
        edge("limitation-grouped-stress", "claim-universal-robustness", "limits"),
        edge("evidence-hahn1-frozen-denominator-roots", "claim-fold1-heldout-pole-free", "contradicts"),
        edge("evidence-hahn1-fold1-identifiability", "claim-universal-robustness", "contradicts"),
        edge("limitation-post-hoc-mechanism", "evidence-hahn1-fold1-identifiability", "limits"),
        edge("limitation-post-hoc-mechanism", "evidence-hahn1-frozen-denominator-roots", "limits"),
        edge("experiment-thurber-prospective-protocol", "claim-thurber-all-folds-gated", "tests"),
        edge("evidence-thurber-prospective-gate", "claim-thurber-all-folds-gated", "contradicts"),
        edge("limitation-thurber-prospective", "claim-thurber-all-folds-gated", "limits"),
        edge("experiment-kirby2-prospective-protocol", "claim-kirby2-all-folds-gated", "tests"),
        edge("evidence-kirby2-prospective-gate", "claim-kirby2-all-folds-gated", "supports"),
        edge("limitation-kirby2-prospective", "claim-kirby2-all-folds-gated", "limits"),
        edge("claim-knowledge-graph", "track-holdout", "recommends"),
        edge("claim-knowledge-graph", "track-formal", "recommends"),
        edge("claim-knowledge-graph", "track-chemistry", "recommends"),
        edge("claim-knowledge-graph", "track-materials", "recommends"),
    ]
    return {"schemaVersion": 1, "asOf": "2026-11-09", "project": "frontier-breakthrough", "nodes": nodes, "edges": edges}


def validate_graph(graph, root):
    errors = []
    allowed_kinds = {"project", "claim", "evidence", "counterexample", "experiment", "limitation"}
    allowed_status = {"active", "supported", "limited_support", "falsified", "unresolved"}
    allowed_relations = {"contains", "supports", "contradicts", "tests", "limits", "recommends"}
    if graph.get("schemaVersion") != 1 or graph.get("project") != "frontier-breakthrough":
        errors.append("Invalid graph header")
    identifiers = set()
    for node in graph.get("nodes", []):
        identifier = node.get("id")
        if identifier in identifiers:
            errors.append(f"Duplicate node id: {identifier}")
        identifiers.add(identifier)
        if node.get("kind") not in allowed_kinds or node.get("status") not in allowed_status:
            errors.append(f"Invalid node kind/status: {identifier}")
        for source in node.get("sourceFiles", []):
            if not (Path(root) / source).is_file():
                errors.append(f"Missing source file: {identifier}: {source}")
    for edge in graph.get("edges", []):
        if edge["from"] not in identifiers or edge["to"] not in identifiers:
            errors.append(f"Dangling edge: {edge}")
        if edge["relation"] not in allowed_relations:
            errors.append(f"Invalid relation: {edge}")
    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "exports/frontier-knowledge-graph.json"
    graph = build_graph(root)
    errors = validate_graph(graph, root)
    if errors:
        raise ValueError(errors)
    import sys
    if output.exists():
        previous = json.loads(output.read_text(encoding="utf-8"))
        if previous != graph:
            if "--extend" not in sys.argv:
                raise ValueError("Refusing to overwrite a different knowledge graph; use --extend only for append-only additions")
            previous_nodes = {node["id"]: node for node in previous["nodes"]}
            current_nodes = {node["id"]: node for node in graph["nodes"]}
            if any(current_nodes.get(identifier) != node for identifier, node in previous_nodes.items()):
                raise ValueError("Existing nodes may not be modified or deleted")
            previous_edges = {(edge["from"], edge["to"], edge["relation"]) for edge in previous["edges"]}
            current_edges = {(edge["from"], edge["to"], edge["relation"]) for edge in graph["edges"]}
            if not previous_edges.issubset(current_edges):
                raise ValueError("Existing edges may not be modified or deleted")
            output.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "nodes": len(graph["nodes"]), "edges": len(graph["edges"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
