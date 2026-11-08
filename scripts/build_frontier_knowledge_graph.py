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
    crossDataset = json.loads((root / "exports/rational-cross-dataset.json").read_text(encoding="utf-8"))
    exactRoots = json.loads((root / "validation/rational-exact-interval-roots.json").read_text(encoding="utf-8"))
    parameterBox = json.loads((root / "validation/rational-parameter-box-stability.json").read_text(encoding="utf-8"))
    predictionBounds = json.loads((root / "validation/rational-prediction-box-bounds.json").read_text(encoding="utf-8"))
    ellipsoidComparison = json.loads((root / "validation/rational-ellipsoid-box-comparison.json").read_text(encoding="utf-8"))
    ellipsoidInterval = json.loads((root / "validation/rational-ellipsoid-interval-safety.json").read_text(encoding="utf-8"))
    filipCoverage = json.loads((root / "validation/filip-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    mgh17Coverage = json.loads((root / "validation/mgh17-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    externalComparison = json.loads((root / "exports/external-coverage-comparison.json").read_text(encoding="utf-8"))
    gauss1Coverage = json.loads((root / "validation/gauss1-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    gauss1Comparison = json.loads((root / "exports/external-coverage-gauss1-comparison.json").read_text(encoding="utf-8"))
    gauss1Mechanism = json.loads((root / "validation/gauss1-bound-mechanism.json").read_text(encoding="utf-8"))
    externalDecomposition = json.loads((root / "exports/external-bound-decomposition.json").read_text(encoding="utf-8"))
    internalExternalDecomposition = json.loads((root / "exports/internal-external-bound-comparison.json").read_text(encoding="utf-8"))
    misra1aCoverage = json.loads((root / "validation/misra1a-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    chwirut1Coverage = json.loads((root / "validation/chwirut1-ellipsoid-coverage.json").read_text(encoding="utf-8"))
    chwirut1Protocol = json.loads((root / "validation/chwirut1-ellipsoid-coverage-protocol.json").read_text(encoding="utf-8"))
    externalV2Decomposition = json.loads((root / "exports/external-bound-decomposition-v2.json").read_text(encoding="utf-8"))
    combinedV2Decomposition = json.loads((root / "exports/internal-external-bound-comparison-v2.json").read_text(encoding="utf-8"))
    externalV3Decomposition = json.loads((root / "exports/external-bound-decomposition-v3.json").read_text(encoding="utf-8"))
    combinedV3Decomposition = json.loads((root / "exports/internal-external-bound-comparison-v3.json").read_text(encoding="utf-8"))
    externalScopeAmendment = json.loads((root / "validation/external-scope-limitations-amendment-01-audit.json").read_text(encoding="utf-8"))
    if externalScopeAmendment["correction_count"] != 3 or externalScopeAmendment["numeric_results_modified"] or not externalScopeAmendment["original_files_preserved"] or externalScopeAmendment["dataset_ids"] != ["mgh17", "gauss1", "misra1a"]:
        raise ValueError("Expected external scope amendment is not present")
    if externalV3Decomposition["totals"]["point_count"] != 593 or externalV3Decomposition["totals"]["ellipsoid_available_point_count"] != 392 or externalV3Decomposition["totals"]["ellipsoid_unavailable_point_count"] != 201 or externalV3Decomposition["totals"]["prediction_shift_dominant_point_count"] != 217 or externalV3Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 175 or len(externalV3Decomposition["datasets"]) != 5 or externalV3Decomposition["datasets"][-1]["id"] != "chwirut1" or externalV3Decomposition["datasets"][-1]["prediction_shift_dominant_point_count"] != 75 or externalV3Decomposition["datasets"][-1]["snapshot_residual_dominant_point_count"] != 8 or combinedV3Decomposition["totals"]["ellipsoid_available_point_count"] != 761 or combinedV3Decomposition["totals"]["prediction_shift_dominant_point_count"] != 561 or combinedV3Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 200 or len(combinedV3Decomposition["datasets"]) != 8 or combinedV3Decomposition["analysis_scope"]["chwirut1_independent_model_family_test"]:
        raise ValueError("Expected v3 scope expansion and related-data scope are not present")
    if chwirut1Coverage["totals"]["point_count"] != 214 or chwirut1Coverage["totals"]["ellipsoid_available_point_count"] != 83 or chwirut1Coverage["totals"]["coverage_violation_count"] != 0 or chwirut1Coverage["totals"]["continuous_safe_fold_count"] != 2 or chwirut1Coverage["folds"][3]["test_metrics"]["rmse"] != min(case["test_metrics"]["rmse"] for case in chwirut1Coverage["folds"]) or chwirut1Coverage["folds"][3]["test_metrics"]["rmse"] >= chwirut1Coverage["folds"][3]["baseline_test_metrics"]["rmse"] or any(point.get("ellipsoid_available", False) for point in chwirut1Coverage["folds"][3]["point_results"]) or chwirut1Coverage["analysis_scope"]["independent_model_family_test"] or not chwirut1Protocol["dataset_scope"]["related_prior_dataset"]["same_study"] or not chwirut1Protocol["dataset_scope"]["related_prior_dataset"]["same_native_model_family"]:
        raise ValueError("Expected Chwirut1 prediction-proof dissociation and related-data scope are not present")
    if not chwirut["decision"]["limited_support"] or not aspirin["canonical_structure_identical"] or not material["structure_identity_confirmed"] or not eckerle["decision"]["limited_support"] or not cvc5["all_results_match_z3"] or not hahn1["decision"]["limited_support"] or cvc5Hahn1["result"] != "unsat" or z3Hahn1["result"] != "unsat" or groupedStress["overall_robust_limited_support"] or identifiability["decision"]["fold_1_failure_reversed"] or denominatorRoots["decision"]["fold_1_failure_reversed"] or denominatorRoots["folds"][0]["real_root_count_in_held_out_closed_interval"] != 2 or thurber["decision"]["overall_all_folds_gated_support"] or not thurber["full_fit_certification"]["matches_nist_within_frozen_tolerances"] or not kirby["decision"]["overall_all_folds_gated_support"] or not kirby["full_fit_certification"]["matches_nist_within_frozen_tolerances"] or crossDataset["totals"]["gate_consistent_fold_count"] != 13 or crossDataset["totals"]["domain_failed_fold_count"] != 2 or exactRoots["totals"]["exact_root_count_total"] != 3 or exactRoots["totals"]["dual_solver_agreement_count"] != 15 or exactRoots["decision"]["unresolved_or_disagreement_present"] or parameterBox["totals"]["certified_region_safe_fold_count"] != 13 or parameterBox["totals"]["cap_hit_fold_count"] != 11 or predictionBounds["totals"]["bounded_fold_count"] != 13 or predictionBounds["totals"]["bounded_point_count"] != 369 or ellipsoidComparison["totals"]["comparison_point_count"] != 369 or ellipsoidComparison["totals"]["tighter_point_count"] != 369 or ellipsoidComparison["totals"]["unavailable_rooted_fold_count"] != 2 or ellipsoidInterval["totals"]["continuous_safe_fold_count"] != 13 or ellipsoidInterval["totals"]["not_certified_fold_count"] != 0 or ellipsoidInterval["totals"]["rooted_snapshot_fold_count"] != 2 or filipCoverage["totals"]["ellipsoid_available_point_count"] != 82 or filipCoverage["totals"]["covered_point_count"] != 82 or filipCoverage["totals"]["continuous_safe_fold_count"] != 5 or mgh17Coverage["totals"]["ellipsoid_available_point_count"] != 33 or mgh17Coverage["totals"]["covered_point_count"] != 33 or mgh17Coverage["totals"]["continuous_safe_fold_count"] != 5 or mgh17Coverage["totals"]["independent_box_continuous_safe_fold_count"] != 5 or mgh17Coverage["totals"]["tighter_point_count"] != 32 or externalComparison["totals"]["point_count"] != 115 or externalComparison["totals"]["covered_point_count"] != 115:
        raise ValueError("Expected evidence states are not present")
    if gauss1Coverage["totals"]["point_count"] != 250 or gauss1Coverage["totals"]["ellipsoid_available_point_count"] != 190 or gauss1Coverage["totals"]["continuous_safe_fold_count"] != 3 or gauss1Coverage["folds"][1]["test_metrics"]["rmse"] <= gauss1Coverage["folds"][1]["baseline_test_metrics"]["rmse"] or any(point.get("ellipsoid_available", False) for point in gauss1Coverage["folds"][4]["point_results"]) or gauss1Comparison["totals"]["point_count"] != 365 or gauss1Comparison["totals"]["ellipsoid_available_point_count"] != 305 or gauss1Comparison["totals"]["ellipsoid_unavailable_point_count"] != 60 or gauss1Comparison["totals"]["continuous_safe_fold_count"] != 13:
        raise ValueError("Expected Gauss1 counterexample states are not present")
    if gauss1Mechanism["analysis_scope"]["refit"] or gauss1Mechanism["analysis_scope"]["retuned"] or gauss1Mechanism["totals"]["stored_bound_agreement_count"] != 190 or gauss1Mechanism["totals"]["stored_bound_mismatch_count"] != 0 or gauss1Mechanism["folds"][0]["maximum_residual_upper_bound"]["shift_share"] >= 0.05 or gauss1Mechanism["folds"][1]["maximum_residual_upper_bound"]["shift_share"] <= 0.95 or gauss1Mechanism["folds"][4]["ellipsoid_available_point_count"] != 0:
        raise ValueError("Expected Gauss1 bound-mechanism states are not present")
    if externalDecomposition["totals"]["bound_identity_mismatch_count"] != 0 or externalDecomposition["totals"]["prediction_shift_dominant_point_count"] != 138 or externalDecomposition["totals"]["snapshot_residual_dominant_point_count"] != 167 or externalDecomposition["datasets"][0]["prediction_shift_dominant_point_count"] != 82 or externalDecomposition["datasets"][0]["median_shift_share"] <= 0.99 or externalDecomposition["datasets"][2]["snapshot_residual_dominant_point_count"] != 166 or externalDecomposition["datasets"][2]["median_shift_share"] >= 0.2 or externalDecomposition["gauss1_regression"]["mismatch_count"] != 0:
        raise ValueError("Expected external bound-composition heterogeneity is not present")
    if internalExternalDecomposition["totals"]["ellipsoid_available_point_count"] != 674 or internalExternalDecomposition["totals"]["prediction_shift_dominant_point_count"] != 482 or internalExternalDecomposition["totals"]["snapshot_residual_dominant_point_count"] != 192 or internalExternalDecomposition["totals"]["external_unavailable_point_count"] != 60 or internalExternalDecomposition["totals"]["internal_unavailable_rooted_fold_count"] != 2 or internalExternalDecomposition["totals"]["bound_identity_mismatch_count"] != 0 or len(internalExternalDecomposition["datasets"]) != 6 or internalExternalDecomposition["datasets"][0]["prediction_shift_dominant_point_count"] != 189 or internalExternalDecomposition["datasets"][-1]["snapshot_residual_dominant_point_count"] != 166:
        raise ValueError("Expected internal/external bound-comparison states are not present")
    if misra1aCoverage["totals"]["point_count"] != 14 or misra1aCoverage["totals"]["ellipsoid_available_point_count"] != 4 or misra1aCoverage["totals"]["continuous_safe_fold_count"] != 1 or misra1aCoverage["totals"]["independent_box_continuous_safe_fold_count"] != 0 or misra1aCoverage["totals"]["max_ellipsoid_absolute_residual_upper_bound_float"] <= 400 or misra1aCoverage["folds"][4]["test_metrics"]["rmse"] <= misra1aCoverage["folds"][4]["baseline_test_metrics"]["rmse"] or not all(point["ellipsoid_prediction_shift_upper_bound_float"] / point["ellipsoid_absolute_residual_upper_bound_float"] > 0.999 for case in misra1aCoverage["folds"] for point in case["point_results"] if point.get("ellipsoid_available", False)):
        raise ValueError("Expected Misra1a prediction-proof dissociation is not present")
    if externalV2Decomposition["totals"]["point_count"] != 379 or externalV2Decomposition["totals"]["ellipsoid_available_point_count"] != 309 or externalV2Decomposition["totals"]["ellipsoid_unavailable_point_count"] != 70 or externalV2Decomposition["totals"]["prediction_shift_dominant_point_count"] != 142 or externalV2Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 167 or combinedV2Decomposition["totals"]["ellipsoid_available_point_count"] != 678 or combinedV2Decomposition["totals"]["prediction_shift_dominant_point_count"] != 486 or combinedV2Decomposition["totals"]["snapshot_residual_dominant_point_count"] != 192 or len(combinedV2Decomposition["datasets"]) != 7 or combinedV2Decomposition["datasets"][-1]["ellipsoid_available_point_count"] != 4:
        raise ValueError("Expected v2 scope-expansion states are not present")

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
        node("claim-rational-gate-always-passes", "claim", "统一有理验收在所有数据集和所有折上都通过", "falsified", ["exports/rational-cross-dataset.json"]),
        node("evidence-rational-cross-dataset", "evidence", "统一内核下 13／15 折符合验收及两种证据等级", "supported", ["exports/rational-cross-dataset.json"]),
        node("experiment-rational-cross-dataset-protocol", "experiment", "跨数据集冻结输入哈希与标准化综合协议", "supported", ["validation/rational-cross-dataset-protocol.json"]),
        node("limitation-rational-cross-dataset", "limitation", "三个数据集十五折且含事后重建，不能估计普适检出率", "active", ["exports/rational-cross-dataset.json"]),
        node("claim-exact-snapshot-all-folds-root-free", "claim", "全部十五折有理系数快照在各自留出闭区间内均无实根", "falsified", ["validation/rational-exact-interval-roots.json"]),
        node("evidence-exact-sturm-intervals", "evidence", "精确 Sturm 隔离的 13 折无根、Hahn1 两根与 Thurber 一根", "supported", ["validation/rational-exact-interval-roots.json"]),
        node("experiment-exact-interval-protocol", "experiment", "十五折精确有理计数与双求解器复核协议", "supported", ["validation/rational-exact-interval-protocol.json"]),
        node("limitation-exact-snapshot-scope", "limitation", "精确结论只覆盖有理系数快照和指定闭区间，不是物理常数或全域证明", "active", ["validation/rational-exact-interval-roots.json"]),
        node("claim-no-positive-rootfree-box", "claim", "无根快照不存在正的连续无根参数盒", "falsified", ["validation/rational-parameter-box-stability.json"]),
        node("evidence-parameter-box-stability", "evidence", "13 折正区域半径、11 折封顶与 2 折有限半径括号", "supported", ["validation/rational-parameter-box-stability.json"]),
        node("experiment-parameter-box-protocol", "experiment", "连续参数盒精确充分性证明与跨零分段协议", "supported", ["validation/rational-parameter-box-protocol.json", "validation/rational-parameter-box-protocol-amendment-01.json"]),
        node("limitation-parameter-box-scope", "limitation", "参数盒半径是充分下界，不是置信区、必要最大值或预测精度保证", "active", ["validation/rational-parameter-box-stability.json"]),
        node("claim-rootfree-box-useful-prediction-bound", "claim", "无根参数盒自动提供有实际用途的预测误差界", "falsified", ["validation/rational-prediction-box-bounds.json"]),
        node("evidence-prediction-box-bounds", "evidence", "13 折 369 点精确保守上界与两处巨大分母下界驱动界", "supported", ["validation/rational-prediction-box-bounds.json"]),
        node("experiment-prediction-box-protocol", "experiment", "固定分子、认证半径和逐点精确预测界协议", "supported", ["validation/rational-prediction-box-protocol.json"]),
        node("limitation-prediction-box-bounds", "limitation", "巨大有限上界数学有效但可能无实际信息，且不覆盖分子、连续 x 或统计误差", "active", ["validation/rational-prediction-box-bounds.json"]),
        node("claim-ellipsoid-all-369-tighter", "claim", "同一半径下当前 369 个适用点的椭球上界全部小于独立盒", "supported", ["validation/rational-ellipsoid-box-comparison.json"]),
        node("evidence-ellipsoid-box-comparison", "evidence", "369 点全部收紧、中位比值 0.604836 与两个有根折不适用", "supported", ["validation/rational-ellipsoid-box-comparison.json"]),
        node("experiment-ellipsoid-box-protocol", "experiment", "完整协方差、同半径和精确支撑上界比较协议", "supported", ["validation/rational-ellipsoid-box-protocol.json"]),
        node("limitation-ellipsoid-box-scope", "limitation", "样本内全部收紧不等于永远更紧；盒与椭球是不同区域且不是置信区", "active", ["validation/rational-ellipsoid-box-comparison.json"]),
        node("claim-ellipsoid-continuous-gap", "claim", "指定椭球的连续留出区间存在未认证的支撑安全缺口", "falsified", ["validation/rational-ellipsoid-interval-safety.json"]),
        node("evidence-ellipsoid-continuous-interval", "evidence", "13 折连续平方支撑均为正、0 折未认证、2 折有根", "supported", ["validation/rational-ellipsoid-interval-safety.json"]),
        node("experiment-ellipsoid-interval-protocol", "experiment", "连续闭区间平方支撑精确证明协议", "supported", ["validation/rational-ellipsoid-interval-protocol.json"]),
        node("limitation-ellipsoid-continuous-scope", "limitation", "连续证明只覆盖指定椭球、半径和区间，不覆盖分子或其他区域", "active", ["validation/rational-ellipsoid-interval-safety.json"]),
        node("claim-filip-ellipsoid-covered", "claim", "Filip 候选模型的 82 个适用点均由椭球上界覆盖实际残差", "supported", ["validation/filip-ellipsoid-coverage.json"]),
        node("evidence-filip-ellipsoid-coverage", "evidence", "Filip 五折连续安全、82 点无越界与独立盒连续安全为 0", "supported", ["validation/filip-ellipsoid-coverage.json"]),
        node("experiment-filip-coverage-protocol", "experiment", "未参与区域设计的 Filip 固定半径五折压力测试协议", "supported", ["validation/filip-ellipsoid-coverage-protocol.json"]),
        node("limitation-filip-candidate-scope", "limitation", "Filip 候选不是原生 11 参数模型，覆盖检查不是概率校准或物理内生证明", "active", ["validation/filip-ellipsoid-coverage.json"]),
        node("claim-external-coverage-framework", "claim", "通用驱动可复现 Filip 并支持 MGH17 的逐点覆盖与连续安全", "supported", ["exports/external-coverage-comparison.json"]),
        node("evidence-external-coverage-framework", "evidence", "两个数据集 115 点无越界、10 折连续安全及 MGH17 32 点更紧", "supported", ["exports/external-coverage-comparison.json"]),
        node("experiment-external-coverage-framework", "experiment", "通用驱动回归与 MGH17 独立冻结协议", "supported", ["validation/mgh17-ellipsoid-coverage-protocol.json", "validation/external-coverage-framework-protocol.json"]),
        node("limitation-external-coverage-framework", "limitation", "通用驱动减少实现漂移但不增加科学独立性，115 点不是概率覆盖或普适成功率", "active", ["exports/external-coverage-comparison.json"]),
        node("claim-reusable-driver-guarantees-coverage", "claim", "复用同一外部覆盖驱动即可保证所有外部点可给界且所有折连续安全", "falsified", ["exports/external-coverage-gauss1-comparison.json"]),
        node("evidence-gauss1-external-coverage", "evidence", "Gauss1 共 250 点，190 点可给界、60 点不可用，连续椭球安全为 3／5 折", "supported", ["validation/gauss1-ellipsoid-coverage.json", "exports/external-coverage-gauss1-comparison.json"]),
        node("counterexample-gauss1-fold2-fold5", "counterexample", "Gauss1 第 2 折候选预测显著差于基线，第 5 折没有任何可用椭球界", "supported", ["validation/gauss1-ellipsoid-coverage.json"]),
        node("experiment-gauss1-coverage-protocol", "experiment", "先于任何 Gauss1 候选分析冻结并推送的五折固定半径协议", "supported", ["validation/gauss1-ellipsoid-coverage-protocol.json", "validation/external-coverage-gauss1-comparison-protocol.json"]),
        node("limitation-gauss1-generated-candidate-scope", "limitation", "Gauss1 是生成数据，候选不是原生八参数模型；适用点检查不是概率覆盖或独立物理实验", "active", ["validation/gauss1-ellipsoid-coverage.json", "exports/external-coverage-gauss1-comparison.json"]),
        node("claim-wide-bounds-parameter-uncertainty", "claim", "所有宽残差界都主要由参数扰动造成", "falsified", ["validation/gauss1-bound-mechanism.json"]),
        node("evidence-gauss1-bound-decomposition", "evidence", "190 点数值一致及最大残差界位置的实际残差—预测平移同点分解", "supported", ["validation/gauss1-bound-mechanism.json"]),
        node("counterexample-gauss1-fold1-wide-bound", "counterexample", "第 1 折 x=1 的残差上界为 330.728324，其中预测平移仅占 0.688%", "supported", ["validation/gauss1-bound-mechanism.json"]),
        node("experiment-gauss1-bound-mechanism", "experiment", "不重拟合、不调参的全 250 点只读事后分母与界组成诊断", "supported", ["validation/gauss1-bound-mechanism.json", "docs/superpowers/plans/2026-11-09-gauss1-bound-mechanism.md"]),
        node("limitation-gauss1-bound-mechanism-posthoc", "limitation", "同点事后分解不是前瞻检验、概率贡献或物理机制识别，连续未认证不等于不安全", "active", ["validation/gauss1-bound-mechanism.json"]),
        node("claim-uniform-external-bound-mechanism", "claim", "所有外部残差上界都由同一种项主导", "falsified", ["exports/external-bound-decomposition.json"]),
        node("evidence-external-bound-decomposition", "evidence", "305 点算术一致性及 Filip、MGH17、Gauss1 的全点主导项分布对照", "supported", ["exports/external-bound-decomposition.json"]),
        node("counterexample-filip-gauss1-composition", "counterexample", "Filip 82／82 点由平移主导，而 Gauss1 有 166／190 点由实际残差主导", "supported", ["exports/external-bound-decomposition.json"]),
        node("experiment-external-bound-decomposition-protocol", "experiment", "冻结输入、0.5 阈值、零界规则与四点 Gauss1 回归的只读分解协议", "supported", ["validation/external-bound-decomposition-protocol.json", "docs/superpowers/plans/2026-11-09-external-bound-decomposition.md"]),
        node("limitation-external-bound-decomposition-posthoc", "limitation", "事后算术占比不是概率、方差或物理因果贡献，三数据不形成普适排名", "active", ["exports/external-bound-decomposition.json"]),
        node("claim-combined-internal-external-success-rate", "claim", "内部与外部证据可直接合并为统一成功率", "falsified", ["exports/internal-external-bound-comparison.json"]),
        node("evidence-internal-external-bound-comparison", "evidence", "六组 674 点中 482 点平移主导、192 点实际残差主导及两类不适用边界", "supported", ["exports/internal-external-bound-comparison.json"]),
        node("counterexample-six-dataset-bound-composition", "counterexample", "六组最大界均由平移主导，但 Gauss1 与其他五组的全点分布显著不同", "supported", ["exports/internal-external-bound-comparison.json"]),
        node("experiment-internal-external-bound-protocol", "experiment", "冻结双输入、范围分离和六组分布的只读内外部对照协议", "supported", ["validation/internal-external-bound-comparison-protocol.json", "validation/internal-bound-decomposition-protocol.json"]),
        node("limitation-internal-external-scope", "limitation", "内部两个有根折与外部 60 个不可用点不可混同，674 点不是总体成功率", "active", ["exports/internal-external-bound-comparison.json"]),
        node("claim-small-rmse-useful-proof", "claim", "较小 RMSE 自动意味着连续证明和有用逐点界", "falsified", ["validation/misra1a-ellipsoid-coverage.json"]),
        node("evidence-misra1a-prediction-proof-dissociation", "evidence", "Misra1a 小 RMSE 与仅 4／14 点可给界、1／5 折连续安全和宽上界并存", "supported", ["validation/misra1a-ellipsoid-coverage.json"]),
        node("counterexample-misra1a-four-of-fourteen", "counterexample", "Misra1a 候选 RMSE 约 0.04—0.22，但仅 4 点可给界且平移占比均超过 99.9%", "supported", ["validation/misra1a-ellipsoid-coverage.json"]),
        node("experiment-misra1a-prospective-protocol", "experiment", "在任何 Misra1a 候选分析前冻结并推送的小样本五折协议", "supported", ["validation/misra1a-ellipsoid-coverage-protocol.json"]),
        node("limitation-misra1a-small-sample-scope", "limitation", "小样本候选不是原生两参数模型，4 点零越界不是概率覆盖或高信息量证明", "active", ["validation/misra1a-ellipsoid-coverage.json"]),
        node("claim-new-data-overwrite-history", "claim", "新增数据可以覆盖旧对照并合并历史范围", "falsified", ["exports/internal-external-bound-comparison-v2.json"]),
        node("evidence-bound-comparison-v2", "evidence", "四外部 379／309／70 与七组 678 点的新版本对照及 Misra1a 增量", "supported", ["exports/external-bound-decomposition-v2.json", "exports/internal-external-bound-comparison-v2.json"]),
        node("counterexample-misra1a-v2-increment", "counterexample", "Misra1a 增加 14 总点、4 可用点、10 不可用点和 4 平移主导点，实际残差主导数不变", "supported", ["validation/misra1a-ellipsoid-coverage.json", "exports/internal-external-bound-comparison-v2.json"]),
        node("experiment-bound-comparison-v2-protocol", "experiment", "保留历史文件并冻结四外部与七组输入哈希和范围差异的新版协议", "supported", ["validation/external-bound-decomposition-v2-protocol.json", "validation/internal-external-bound-comparison-v2-protocol.json"]),
        node("limitation-bound-comparison-v2-scope", "limitation", "新版范围合计不是成功率或证明能力改善，内部有根折与外部不可用点不可混同", "active", ["exports/internal-external-bound-comparison-v2.json"]),
    ]
    edges = []
    for track, claims in {
        "track-holdout": ["claim-chwirut-extrapolation", "claim-nist-reproduction", "evidence-chwirut", "experiment-chwirut-protocol", "limitation-single-split", "claim-eckerle4-two-tail", "evidence-eckerle4", "experiment-eckerle4-protocol", "limitation-two-datasets", "claim-hahn1-high-temperature", "evidence-hahn1", "experiment-hahn1-protocol", "limitation-three-datasets", "claim-universal-robustness", "evidence-grouped-stress", "experiment-grouped-stress-protocol", "limitation-grouped-stress", "claim-fold1-heldout-pole-free", "evidence-hahn1-fold1-identifiability", "evidence-hahn1-frozen-denominator-roots", "limitation-post-hoc-mechanism", "claim-thurber-all-folds-gated", "evidence-thurber-prospective-gate", "experiment-thurber-prospective-protocol", "limitation-thurber-prospective", "claim-kirby2-all-folds-gated", "evidence-kirby2-prospective-gate", "experiment-kirby2-prospective-protocol", "limitation-kirby2-prospective", "claim-rational-gate-always-passes", "evidence-rational-cross-dataset", "experiment-rational-cross-dataset-protocol", "limitation-rational-cross-dataset", "claim-filip-ellipsoid-covered", "evidence-filip-ellipsoid-coverage", "experiment-filip-coverage-protocol", "limitation-filip-candidate-scope", "claim-external-coverage-framework", "evidence-external-coverage-framework", "experiment-external-coverage-framework", "limitation-external-coverage-framework", "claim-reusable-driver-guarantees-coverage", "evidence-gauss1-external-coverage", "counterexample-gauss1-fold2-fold5", "experiment-gauss1-coverage-protocol", "limitation-gauss1-generated-candidate-scope", "claim-wide-bounds-parameter-uncertainty", "evidence-gauss1-bound-decomposition", "counterexample-gauss1-fold1-wide-bound", "experiment-gauss1-bound-mechanism", "limitation-gauss1-bound-mechanism-posthoc", "claim-uniform-external-bound-mechanism", "evidence-external-bound-decomposition", "counterexample-filip-gauss1-composition", "experiment-external-bound-decomposition-protocol", "limitation-external-bound-decomposition-posthoc", "claim-combined-internal-external-success-rate", "evidence-internal-external-bound-comparison", "counterexample-six-dataset-bound-composition", "experiment-internal-external-bound-protocol", "limitation-internal-external-scope", "claim-small-rmse-useful-proof", "evidence-misra1a-prediction-proof-dissociation", "counterexample-misra1a-four-of-fourteen", "experiment-misra1a-prospective-protocol", "limitation-misra1a-small-sample-scope", "claim-new-data-overwrite-history", "evidence-bound-comparison-v2", "counterexample-misra1a-v2-increment", "experiment-bound-comparison-v2-protocol", "limitation-bound-comparison-v2-scope"],
        "track-formal": ["claim-universal-identifiability", "claim-positive-denominator", "evidence-z3", "counterexample-xzero", "claim-solver-agreement", "evidence-cvc5", "claim-hahn1-denominator", "evidence-hahn1-denominator", "claim-unbounded-denominator-safety", "counterexample-hahn1-outdomain-root", "claim-exact-snapshot-all-folds-root-free", "evidence-exact-sturm-intervals", "experiment-exact-interval-protocol", "limitation-exact-snapshot-scope", "claim-no-positive-rootfree-box", "evidence-parameter-box-stability", "experiment-parameter-box-protocol", "limitation-parameter-box-scope", "claim-rootfree-box-useful-prediction-bound", "evidence-prediction-box-bounds", "experiment-prediction-box-protocol", "limitation-prediction-box-bounds", "claim-ellipsoid-all-369-tighter", "evidence-ellipsoid-box-comparison", "experiment-ellipsoid-box-protocol", "limitation-ellipsoid-box-scope", "claim-ellipsoid-continuous-gap", "evidence-ellipsoid-continuous-interval", "experiment-ellipsoid-interval-protocol", "limitation-ellipsoid-continuous-scope"],
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
        edge("experiment-rational-cross-dataset-protocol", "claim-rational-gate-always-passes", "tests"),
        edge("evidence-rational-cross-dataset", "claim-rational-gate-always-passes", "contradicts"),
        edge("limitation-rational-cross-dataset", "claim-rational-gate-always-passes", "limits"),
        edge("experiment-exact-interval-protocol", "claim-exact-snapshot-all-folds-root-free", "tests"),
        edge("evidence-exact-sturm-intervals", "claim-exact-snapshot-all-folds-root-free", "contradicts"),
        edge("limitation-exact-snapshot-scope", "claim-exact-snapshot-all-folds-root-free", "limits"),
        edge("experiment-parameter-box-protocol", "claim-no-positive-rootfree-box", "tests"),
        edge("evidence-parameter-box-stability", "claim-no-positive-rootfree-box", "contradicts"),
        edge("limitation-parameter-box-scope", "claim-no-positive-rootfree-box", "limits"),
        edge("experiment-prediction-box-protocol", "claim-rootfree-box-useful-prediction-bound", "tests"),
        edge("evidence-prediction-box-bounds", "claim-rootfree-box-useful-prediction-bound", "contradicts"),
        edge("limitation-prediction-box-bounds", "claim-rootfree-box-useful-prediction-bound", "limits"),
        edge("experiment-ellipsoid-box-protocol", "claim-ellipsoid-all-369-tighter", "tests"),
        edge("evidence-ellipsoid-box-comparison", "claim-ellipsoid-all-369-tighter", "supports"),
        edge("limitation-ellipsoid-box-scope", "claim-ellipsoid-all-369-tighter", "limits"),
        edge("experiment-ellipsoid-interval-protocol", "claim-ellipsoid-continuous-gap", "tests"),
        edge("evidence-ellipsoid-continuous-interval", "claim-ellipsoid-continuous-gap", "contradicts"),
        edge("limitation-ellipsoid-continuous-scope", "claim-ellipsoid-continuous-gap", "limits"),
        edge("experiment-filip-coverage-protocol", "claim-filip-ellipsoid-covered", "tests"),
        edge("evidence-filip-ellipsoid-coverage", "claim-filip-ellipsoid-covered", "supports"),
        edge("limitation-filip-candidate-scope", "claim-filip-ellipsoid-covered", "limits"),
        edge("experiment-external-coverage-framework", "claim-external-coverage-framework", "tests"),
        edge("evidence-external-coverage-framework", "claim-external-coverage-framework", "supports"),
        edge("limitation-external-coverage-framework", "claim-external-coverage-framework", "limits"),
        edge("experiment-gauss1-coverage-protocol", "claim-reusable-driver-guarantees-coverage", "tests"),
        edge("evidence-gauss1-external-coverage", "claim-reusable-driver-guarantees-coverage", "contradicts"),
        edge("counterexample-gauss1-fold2-fold5", "claim-reusable-driver-guarantees-coverage", "contradicts"),
        edge("evidence-gauss1-external-coverage", "counterexample-gauss1-fold2-fold5", "supports"),
        edge("limitation-gauss1-generated-candidate-scope", "claim-reusable-driver-guarantees-coverage", "limits"),
        edge("experiment-gauss1-bound-mechanism", "claim-wide-bounds-parameter-uncertainty", "tests"),
        edge("evidence-gauss1-bound-decomposition", "claim-wide-bounds-parameter-uncertainty", "contradicts"),
        edge("counterexample-gauss1-fold1-wide-bound", "claim-wide-bounds-parameter-uncertainty", "contradicts"),
        edge("evidence-gauss1-bound-decomposition", "counterexample-gauss1-fold1-wide-bound", "supports"),
        edge("evidence-gauss1-bound-decomposition", "counterexample-gauss1-fold2-fold5", "supports"),
        edge("limitation-gauss1-bound-mechanism-posthoc", "claim-wide-bounds-parameter-uncertainty", "limits"),
        edge("experiment-external-bound-decomposition-protocol", "claim-uniform-external-bound-mechanism", "tests"),
        edge("evidence-external-bound-decomposition", "claim-uniform-external-bound-mechanism", "contradicts"),
        edge("counterexample-filip-gauss1-composition", "claim-uniform-external-bound-mechanism", "contradicts"),
        edge("evidence-external-bound-decomposition", "counterexample-filip-gauss1-composition", "supports"),
        edge("evidence-external-bound-decomposition", "claim-wide-bounds-parameter-uncertainty", "contradicts"),
        edge("limitation-external-bound-decomposition-posthoc", "claim-uniform-external-bound-mechanism", "limits"),
        edge("experiment-internal-external-bound-protocol", "claim-combined-internal-external-success-rate", "tests"),
        edge("evidence-internal-external-bound-comparison", "claim-combined-internal-external-success-rate", "contradicts"),
        edge("counterexample-six-dataset-bound-composition", "claim-combined-internal-external-success-rate", "contradicts"),
        edge("evidence-internal-external-bound-comparison", "counterexample-six-dataset-bound-composition", "supports"),
        edge("counterexample-six-dataset-bound-composition", "claim-uniform-external-bound-mechanism", "contradicts"),
        edge("evidence-internal-external-bound-comparison", "counterexample-filip-gauss1-composition", "supports"),
        edge("limitation-internal-external-scope", "claim-combined-internal-external-success-rate", "limits"),
        edge("experiment-misra1a-prospective-protocol", "claim-small-rmse-useful-proof", "tests"),
        edge("evidence-misra1a-prediction-proof-dissociation", "claim-small-rmse-useful-proof", "contradicts"),
        edge("counterexample-misra1a-four-of-fourteen", "claim-small-rmse-useful-proof", "contradicts"),
        edge("evidence-misra1a-prediction-proof-dissociation", "counterexample-misra1a-four-of-fourteen", "supports"),
        edge("evidence-misra1a-prediction-proof-dissociation", "claim-wide-bounds-parameter-uncertainty", "supports"),
        edge("limitation-misra1a-small-sample-scope", "claim-small-rmse-useful-proof", "limits"),
        edge("experiment-bound-comparison-v2-protocol", "claim-new-data-overwrite-history", "tests"),
        edge("evidence-bound-comparison-v2", "claim-new-data-overwrite-history", "contradicts"),
        edge("counterexample-misra1a-v2-increment", "claim-new-data-overwrite-history", "contradicts"),
        edge("evidence-bound-comparison-v2", "counterexample-misra1a-v2-increment", "supports"),
        edge("evidence-bound-comparison-v2", "evidence-misra1a-prediction-proof-dissociation", "supports"),
        edge("limitation-bound-comparison-v2-scope", "claim-new-data-overwrite-history", "limits"),
        edge("claim-knowledge-graph", "track-holdout", "recommends"),
        edge("claim-knowledge-graph", "track-formal", "recommends"),
        edge("claim-knowledge-graph", "track-chemistry", "recommends"),
        edge("claim-knowledge-graph", "track-materials", "recommends"),
    ]
    nodes.append(node("experiment-bound-comparison-v2-protocol-amendment", "experiment", "修订七组协议的外部诊断哈希并保留原协议与全部数值范围", "supported", ["validation/internal-external-bound-comparison-v2-protocol-amendment-01.json"]))
    edges.extend([
        edge("track-holdout", "experiment-bound-comparison-v2-protocol-amendment", "contains"),
        edge("experiment-bound-comparison-v2-protocol-amendment", "claim-new-data-overwrite-history", "tests"),
    ])
    nodes.extend([
        node("claim-untouched-data-independent-model-family", "claim", "未触碰数据自动构成独立模型族或独立实验室复现", "falsified", ["validation/chwirut1-ellipsoid-coverage-protocol.json", "validation/chwirut1-ellipsoid-coverage.json"]),
        node("evidence-chwirut1-prediction-proof-dissociation", "evidence", "Chwirut1 共 214 点，83 点可给界、131 点不可用，2／5 折连续安全且三折优于基线", "supported", ["validation/chwirut1-ellipsoid-coverage.json"]),
        node("counterexample-chwirut1-fold4-no-bounds", "counterexample", "Chwirut1 第 4 折 RMSE 最低且优于基线，但 23 个留出点有 0 个可用界", "supported", ["validation/chwirut1-ellipsoid-coverage.json"]),
        node("experiment-chwirut1-prospective-protocol", "experiment", "在任何 Chwirut1 候选分析前冻结并推送的同族数据五折协议", "supported", ["validation/chwirut1-ellipsoid-coverage-protocol.json"]),
        node("limitation-chwirut1-related-dataset-scope", "limitation", "Chwirut1 未触碰但与 Chwirut2 同研究同模型族，适用点零越界不是概率覆盖或独立模型族验证", "active", ["validation/chwirut1-ellipsoid-coverage-protocol.json", "validation/chwirut1-ellipsoid-coverage.json"]),
    ])
    edges.extend([
        edge("track-holdout", "claim-untouched-data-independent-model-family", "contains"),
        edge("track-holdout", "evidence-chwirut1-prediction-proof-dissociation", "contains"),
        edge("track-holdout", "counterexample-chwirut1-fold4-no-bounds", "contains"),
        edge("track-holdout", "experiment-chwirut1-prospective-protocol", "contains"),
        edge("track-holdout", "limitation-chwirut1-related-dataset-scope", "contains"),
        edge("evidence-chwirut1-prediction-proof-dissociation", "claim-small-rmse-useful-proof", "contradicts"),
        edge("counterexample-chwirut1-fold4-no-bounds", "claim-small-rmse-useful-proof", "contradicts"),
        edge("evidence-chwirut1-prediction-proof-dissociation", "counterexample-chwirut1-fold4-no-bounds", "supports"),
        edge("experiment-chwirut1-prospective-protocol", "claim-small-rmse-useful-proof", "tests"),
        edge("limitation-chwirut1-related-dataset-scope", "evidence-chwirut1-prediction-proof-dissociation", "limits"),
        edge("evidence-chwirut1-prediction-proof-dissociation", "claim-untouched-data-independent-model-family", "contradicts"),
        edge("limitation-chwirut1-related-dataset-scope", "claim-untouched-data-independent-model-family", "limits"),
        edge("evidence-chwirut1-prediction-proof-dissociation", "claim-reusable-driver-guarantees-coverage", "contradicts"),
    ])
    nodes.extend([
        node("evidence-bound-comparison-v3", "evidence", "五外部 593／392／201 与八组 761 点的新版本对照及 Chwirut1 增量", "supported", ["exports/external-bound-decomposition-v3.json", "exports/internal-external-bound-comparison-v3.json"]),
        node("counterexample-chwirut1-v3-increment", "counterexample", "Chwirut1 增加 214 总点、83 可用点、131 不可用点、75 平移主导点和 8 实际残差主导点，不能覆盖历史范围", "supported", ["validation/chwirut1-ellipsoid-coverage.json", "exports/internal-external-bound-comparison-v3.json"]),
        node("experiment-bound-comparison-v3-protocol", "experiment", "保留历史版本并冻结五外部与八组输入哈希、同族范围的新版协议", "supported", ["validation/external-bound-decomposition-v3-protocol.json", "validation/internal-external-bound-comparison-v3-protocol.json"]),
        node("limitation-bound-comparison-v3-scope", "limitation", "八组范围合计不是成功率或独立模型族验证，内部有根折、外部不可用点和同族边界均不可抹去", "active", ["exports/internal-external-bound-comparison-v3.json", "validation/chwirut1-ellipsoid-coverage-protocol.json"]),
    ])
    edges.extend([
        edge("track-holdout", "evidence-bound-comparison-v3", "contains"),
        edge("track-holdout", "counterexample-chwirut1-v3-increment", "contains"),
        edge("track-holdout", "experiment-bound-comparison-v3-protocol", "contains"),
        edge("track-holdout", "limitation-bound-comparison-v3-scope", "contains"),
        edge("evidence-bound-comparison-v3", "claim-new-data-overwrite-history", "contradicts"),
        edge("counterexample-chwirut1-v3-increment", "claim-new-data-overwrite-history", "contradicts"),
        edge("evidence-bound-comparison-v3", "counterexample-chwirut1-v3-increment", "supports"),
        edge("experiment-bound-comparison-v3-protocol", "claim-new-data-overwrite-history", "tests"),
        edge("limitation-bound-comparison-v3-scope", "claim-new-data-overwrite-history", "limits"),
        edge("evidence-bound-comparison-v3", "evidence-chwirut1-prediction-proof-dissociation", "supports"),
        edge("limitation-bound-comparison-v3-scope", "claim-untouched-data-independent-model-family", "limits"),
    ])
    nodes.append(node("experiment-external-scope-limitations-amendment", "experiment", "保留原冻结文件并修订 MGH17、Gauss1、Misra1a 的模型族限制文本及来源哈希", "supported", ["validation/external-scope-limitations-amendment-01.json", "validation/external-scope-limitations-amendment-01-audit.json"]))
    edges.extend([
        edge("track-knowledge", "experiment-external-scope-limitations-amendment", "contains"),
        edge("experiment-external-scope-limitations-amendment", "claim-knowledge-graph", "tests"),
    ])
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
