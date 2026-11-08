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
    drug = read("drug-target-structure.json")
    selectivity = read("ca-selectivity.json")
    stability = read("ca-document-stability.json")
    structuralControl = read("structural-control.json")
    chwirut = read("chwirut-holdout.json")
    z3identifiability = read("z3-identifiability.json")
    aspirin = read("aspirin-crosscheck.json")
    material = read("material-crosscheck.json")
    eckerle = read("eckerle4-two-tail.json")
    cvc5 = read("cvc5-crosscheck.json")
    hahn1 = read("hahn1-high-temperature.json")
    z3Hahn1 = read("z3-hahn1-denominator.json")
    cvc5Hahn1 = read("cvc5-hahn1-denominator.json")
    groupedStress = read("grouped-stress.json")
    identifiability = read("hahn1-fold1-identifiability.json")
    denominatorRoots = read("hahn1-frozen-denominator-roots.json")
    thurber = read("thurber-prospective-gate.json")
    kirby = read("kirby2-prospective-gate.json")
    crossDataset = json.loads((ROOT / "exports/rational-cross-dataset.json").read_text(encoding="utf-8"))
    exactRoots = read("rational-exact-interval-roots.json")
    parameterBox = read("rational-parameter-box-stability.json")
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
        {
            "id": "acetazolamide-chembl-pubchem-pdb", "domain": "chemistry", "title": "乙酰唑胺—CA II—实验结构链",
            "status": drug["status"], "evidenceClass": "cross_database_check",
            "sources": ["https://www.ebi.ac.uk/chembl/api/data", "https://pubchem.ncbi.nlm.nih.gov/rest/pug", "https://data.rcsb.org/rest/v1/core"],
            "metrics": {"chemblMolecule": drug["chembl_molecule"], "pubchemCid": drug["pubchem_cid"], "targetChemblId": drug["target_chembl_id"], "targetUniprot": drug["target_uniprot"], "targetPdbEntity": drug["target_pdb_entity"], "targetPdbChain": drug["target_pdb_chain"], "targetSequenceExactMatch": drug["target_sequence_exact_match"], "targetSequenceLength": drug["target_sequence_length"], "targetSequenceMd5": drug["target_sequence_md5"], "activityId": drug["activity_id"], "assayChemblId": drug["assay_chembl_id"], "kiNm": drug["ki_nM"], "pchemblExternal": drug["pchembl_external"], "pchemblRecomputed": drug["pchembl_recomputed"], "potentialDuplicate": drug["potential_duplicate"], "pdbId": drug["pdb_id"], "ligandCompId": drug["pdb_ligand_comp_id"], "resolutionA": drug["resolution_A"], "caIKiNm": selectivity["ca_i"]["ki_nM"], "caIiKiNm": selectivity["ca_ii"]["ki_nM"], "caIxKiNm": selectivity["ca_ix"]["ki_nM"], "caIiKiRatio": selectivity["ca_i_ii_ki_ratio"], "caIiPchemblDelta": selectivity["ca_ii_minus_ca_i_pchembl_delta"], "caIxRatioComputed": selectivity["ca_ix_ratio_computed"], "selectivityIndependence": selectivity["independence"], "ratioMin": stability["ratio_min"], "ratioMax": stability["ratio_max"], "maxMinFold": stability["max_min_fold"], "methodMatchedCount": stability["strict_method_matched_count"], "methodIncompleteCount": stability["method_incomplete_count"], "documentCount": stability["document_count"], "stabilityConclusion": stability["stability_conclusion"], "structuralControlPdbId": structuralControl["control"]["pdb_id"], "structuralControlExactWildtypeReplication": structuralControl["exact_wildtype_replication"], "structuralControlDifferenceEvents": structuralControl["alignment_difference_event_count"], "structuralControlLengthDiscrepancy": structuralControl["length_metadata_discrepancy"]},
            "scientificClaim": "乙酰唑胺的化合物标识、CA II 策划机制、P00918/3HS4 的 260 aa 精确序列、单一 Ki 测定和实验复合物可以逐层追溯；同方法 CA I/II 表观比值单独分析，跨文档固定常数不成立；2H4N 只作不同构建的结构对照。",
            "limitations": drug["scope"] + " " + selectivity["scope"] + " " + stability["scope"] + " " + structuralControl["scope"], "upstreamContribution": "提供 InChIKey、靶点全长序列、assay、配体实体、重复标记、方法一致定量对照、跨文档负结果和不同构建结构对照完整保留的药物—靶点—结构审计链。",
            "snapshotFiles": ["validation/drug-target-structure.json", "validation/structural-control.json", "validation/pdb-2h4n.json", "validation/ca-selectivity.json", "validation/chembl-ca-selectivity-panel.json", "validation/ca-document-stability.json", "validation/chembl-ca-document-pairs.json", "validation/ca2-sequence.json", "validation/chembl-acetazolamide.json", "validation/pdb-3hs4.json", "validation/pdb-3hs4-ca2.json", "validation/uniprot-ca2.json", "validation/pubchem-acetazolamide.json"],
        },
        {
            "id": "chwirut-high-distance-holdout", "domain": "physics", "title": "Chwirut 高距离真实数据留出",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/chwirut2.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Chwirut2.dat"],
            "metrics": {"trainCount": chwirut["split"]["train_count"], "holdoutCount": chwirut["split"]["holdout_count"], "trainRmse": chwirut["train_fit"]["metrics"]["train_rmse"], "holdoutRmse": chwirut["train_fit"]["metrics"]["holdout_rmse"], "linearHoldoutRmse": chwirut["baselines"]["linear"]["holdout_rmse"], "meanHoldoutRmse": chwirut["baselines"]["training_mean"]["holdout_rmse"], "limitedSupport": chwirut["decision"]["limited_support"], "nistReproduction": chwirut["full_fit_certification"]["matches_nist_within_frozen_tolerances"]},
            "scientificClaim": "三参数模型在预注册高距离切片获得有限支持；NIST 全数据认证复现与留出预测证据严格分开。",
            "limitations": " ".join(chwirut["limitations"]), "upstreamContribution": "提供原始数据哈希、冻结留出协议、双起点拟合、两项基线和54点独立复算。",
            "snapshotFiles": ["validation/chwirut-holdout-protocol.json", "validation/chwirut-holdout.json", "validation/chwirut-holdout-verification.json"],
        },
        {
            "id": "z3-identifiability-counterexamples", "domain": "math", "title": "Z3 定义域与参数可识别性反例",
            "status": z3identifiability["status"], "evidenceClass": "known_answer_reproduction",
            "sources": ["https://github.com/Z3Prover/z3"],
            "metrics": {"version": z3identifiability["version"], "checks": z3identifiability["checks"]},
            "scientificClaim": "显式正性域内分母恒正；无分母约束存在反例，x=0 单点不能唯一识别全部参数。",
            "limitations": " ".join(z3identifiability["limitations"]), "upstreamContribution": "提供可重放的有限域证明义务、显式反例和实验设计可识别性边界。",
            "snapshotFiles": ["validation/z3-identifiability.json"],
        },
        {
            "id": "aspirin-pubchem-chembl-rdkit", "domain": "chemistry", "title": "阿司匹林跨库身份与描述符口径审计",
            "status": aspirin["status"], "evidenceClass": "cross_database_check",
            "sources": ["https://pubchem.ncbi.nlm.nih.gov/rest/pug", "https://www.ebi.ac.uk/chembl/api/data", "https://github.com/rdkit/rdkit"],
            "metrics": {"pubchemCid": aspirin["pubchem_cid"], "chemblId": aspirin["chembl_id"], "canonicalStructureIdentical": aspirin["canonical_structure_identical"], "inchikeyIdentical": aspirin["inchikey_identical"], "formula": aspirin["rdkit"]["formula"], "exactMass": aspirin["rdkit"]["exact_mass"], "tpsa": aspirin["rdkit"]["tpsa"], "rdkitMolLogP": aspirin["rdkit"]["mol_logp"], "pubchemXLogP": aspirin["pubchem"]["XLogP"], "chemblALogP": aspirin["chembl_properties"]["alogp"], "rdkitHba": aspirin["rdkit"]["hba"], "chemblHba": aspirin["chembl_properties"]["hba"], "pubchemRotatable": aspirin["pubchem"]["RotatableBondCount"], "chemblRotatable": aspirin["chembl_properties"]["rtb"]},
            "scientificClaim": "阿司匹林在 PubChem、ChEMBL 与 RDKit 间结构身份一致；LogP、氢键和可旋转键定义差异不构成造假证据。",
            "limitations": " ".join(aspirin["limitations"]), "upstreamContribution": "提供 CID/CHEMBL/InChIKey 对照、结构归一、精确质量和多口径描述符审计。",
            "snapshotFiles": ["validation/pubchem-aspirin.json", "validation/chembl-aspirin.json", "validation/aspirin-crosscheck.json"],
        },
        {
            "id": "mp-oqmd-structure-crosscheck", "domain": "physics", "title": "MP／OQMD／PyMatGen 三组材料结构复核",
            "status": material["status"], "evidenceClass": "cross_database_check",
            "sources": ["https://api.materialsproject.org", "https://oqmd.org/", "https://github.com/materialsproject/pymatgen"],
            "metrics": {"structureIdentityConfirmed": material["structure_identity_confirmed"], "items": [{"formula": item["formula"], "mpId": item["mp"]["material_id"], "oqmdEntryId": item["oqmd"]["entry_id"], "optimadeId": item["oqmd_structure_id"], "bandGapMpEv": item["band_gap_mp_eV"], "bandGapOqmdEv": item["band_gap_oqmd_eV"], "densityLocal": item["local"]["density_g_cm3"], "densityMp": item["density_mp_g_cm3"], "spaceGroupLocal": item["local"]["space_group_symbol"]} for item in material["materials"]]},
            "scientificClaim": "Si、GaAs、SiO2 的跨库结构身份分别成立，但 DFT 带隙、密度和稳定性不因此被强制相等。",
            "limitations": " ".join(material["limitations"]), "upstreamContribution": "提供原生 entry_id 与 OPTIMADE ID 的显式映射、完整结构快照和独立密度/空间群重算。",
            "snapshotFiles": ["validation/material-crosscheck-protocol.json", "validation/material-crosscheck-protocol-amendment-01.json", "validation/material-crosscheck.json", "validation/materials-project-si-dft.json", "validation/materials-project-gaas-dft.json", "validation/materials-project-sio2-dft.json", "validation/oqmd-structure-si.json", "validation/oqmd-structure-gaas.json", "validation/oqmd-structure-sio2.json"],
        },
        {
            "id": "eckerle4-two-tail-extrapolation", "domain": "physics", "title": "Eckerle4 双尾真实数据外推",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/eckerle4.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Eckerle4.dat"],
            "metrics": {"middleCount": eckerle["split"]["middle_count"], "lowCount": eckerle["split"]["low_count"], "highCount": eckerle["split"]["high_count"], "middleRmse": eckerle["middle_fit"]["metrics"]["middle_rmse"], "lowRmse": eckerle["middle_fit"]["metrics"]["low_rmse"], "highRmse": eckerle["middle_fit"]["metrics"]["high_rmse"], "holdoutRmse": eckerle["middle_fit"]["metrics"]["holdout_rmse"], "linearHoldoutRmse": eckerle["baselines"]["linear"]["holdout_rmse"], "meanHoldoutRmse": eckerle["baselines"]["training_mean"]["holdout_rmse"], "limitedSupport": eckerle["decision"]["limited_support"], "nistReproduction": eckerle["full_fit_certification"]["matches_nist_within_frozen_tolerances"]},
            "scientificClaim": "三参数高斯在独立 Eckerle4 的预注册双尾任务获得有限支持；全数据认证复现与双尾外推严格分开。",
            "limitations": " ".join(eckerle["limitations"]), "upstreamContribution": "提供第二独立数据集、双尾协议、中央拟合、两项基线和35点独立复算。",
            "snapshotFiles": ["validation/eckerle4-two-tail-protocol.json", "validation/eckerle4-two-tail.json", "validation/eckerle4-two-tail-verification.json"],
        },
        {
            "id": "cvc5-z3-cross-solver", "domain": "math", "title": "cvc5／Z3 交叉求解器复核",
            "status": cvc5["status"], "evidenceClass": "known_answer_reproduction",
            "sources": ["https://github.com/cvc5/cvc5/releases/tag/cvc5-1.4.2", "https://github.com/Z3Prover/z3"],
            "metrics": {"version": cvc5["solver_version"], "allResultsMatchZ3": cvc5["all_results_match_z3"], "checks": [{"id": item["id"], "cvc5": item["cvc5"], "z3": item["z3"]} for item in cvc5["checks"]]},
            "scientificClaim": "cvc5 与 Z3 对分母正性、零分母反例和 x=0 参数非识别性给出相同结果，并生成精确有理数反例模型。",
            "limitations": " ".join(cvc5["limitations"]), "upstreamContribution": "提供双求解器 SMT-LIB、原始日志、官方二进制哈希和精确模型，降低单求解器依赖。",
            "snapshotFiles": ["validation/cvc5-crosscheck.json", "validation/cvc5-positive-denominator.smt2", "validation/cvc5-zero-denominator.smt2", "validation/cvc5-xzero-identifiability.smt2"],
        },
        {
            "id": "hahn1-rational-high-temperature", "domain": "physics", "title": "Hahn1 有理模型高温外推与分母边界",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Hahn1.dat", "https://github.com/Z3Prover/z3", "https://github.com/cvc5/cvc5/releases/tag/cvc5-1.4.2"],
            "metrics": {"trainCount": hahn1["split"]["train_count"], "holdoutCount": hahn1["split"]["holdout_count"], "trainRmse": hahn1["train_fit"]["metrics"]["train_rmse"], "holdoutRmse": hahn1["train_fit"]["metrics"]["holdout_rmse"], "cubicHoldoutRmse": hahn1["baselines"]["cubic_polynomial"]["holdout_rmse"], "linearHoldoutRmse": hahn1["baselines"]["linear"]["holdout_rmse"], "limitedSupport": hahn1["decision"]["limited_support"], "nistReproduction": hahn1["full_fit_certification"]["matches_nist_within_frozen_tolerances"], "denominatorDomain": cvc5Hahn1["domain"], "cvc5Result": cvc5Hahn1["result"], "z3Result": z3Hahn1["result"], "unboundedRootExists": z3Hahn1["unbounded_root_exists"], "unboundedModelX": z3Hahn1["unbounded_model_x"]},
            "scientificClaim": "七参数有理模型在预注册高温切片获得有限支持并优于三次多项式基线；分母在实验区间内无零根，但存在域外正根。",
            "limitations": " ".join(hahn1["limitations"]) + " " + z3Hahn1["limitations"], "upstreamContribution": "提供有理模型、强基线、236点预测复算和双求解器分母边界审计。",
            "snapshotFiles": ["validation/hahn1-high-temperature-protocol.json", "validation/hahn1-high-temperature.json", "validation/hahn1-high-temperature-verification.json", "validation/z3-hahn1-denominator.json", "validation/cvc5-hahn1-denominator.json", "validation/cvc5-hahn1-denominator.smt2"],
        },
        {
            "id": "grouped-contiguous-stress-diagnostics", "domain": "physics", "title": "跨数据集连续区间压力测试与失效定位",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/chwirut2.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/eckerle4.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml"],
            "metrics": {"overallRobustLimitedSupport": groupedStress["overall_robust_limited_support"], "datasets": [{"id": item["id"], "robustLimitedSupport": item["decision"]["robust_limited_support"], "medianRmse": item["median_model_rmse"], "worstFold": item["worst_fold"]} for item in groupedStress["datasets"]]},
            "scientificClaim": "Chwirut 和 Eckerle4 五折均不劣于基线；Hahn1 第 1 折显著失效，因此整体不能称为稳健支持。",
            "limitations": " ".join(groupedStress["limitations"]), "upstreamContribution": "提供15折连续区间压力诊断、全部失败区间、基线对照和防泄漏协议。",
            "snapshotFiles": ["validation/grouped-stress-protocol.json", "validation/grouped-stress.json"],
        },
        {
            "id": "hahn1-fold1-identifiability-and-poles", "domain": "physics", "title": "Hahn1 第 1 折局部可识别性与双极点诊断",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Hahn1.dat"],
            "metrics": {"fold1TrainingRmse": identifiability["folds"][0]["training_metrics"]["rmse"], "fold1TestRmse": identifiability["folds"][0]["test_metrics"]["rmse"], "fold1ScaledConditionNumber": identifiability["folds"][0]["training_jacobian"]["scaled_condition_number"], "allFoldNumericalRanks": [fold["training_jacobian"]["numerical_rank"] for fold in identifiability["folds"]], "fold1MaxParameterCorrelation": identifiability["folds"][0]["training_jacobian"]["max_absolute_off_diagonal_parameter_correlation"], "fold1MaxLocalPredictionSd": identifiability["folds"][0]["held_out_prediction_sensitivity"]["max_local_standard_deviation"], "fold1MinAbsDenominatorHeldOut": identifiability["folds"][0]["denominator"]["min_absolute_on_held_out_points"], "fold1HeldOutPoles": [{"rootX": root["root_x"], "numeratorAtRoot": root["numerator_at_root"], "denominatorDerivativeAtRoot": root["denominator_derivative_at_root"]} for root in denominatorRoots["folds"][0]["real_roots"] if root["within_held_out_closed_interval"]], "fold1FailureReversed": identifiability["decision"]["fold_1_failure_reversed"]},
            "scientificClaim": "五折均为数值满秩；第 1 折在约 45.526978 K 和 72.131671 K 有两个留出区数值单极点，近根位置出现巨大预测与残差，支持局部失效机制解释。",
            "limitations": " ".join(identifiability["limitations"] + denominatorRoots["limitations"]), "upstreamContribution": "提供逐折解析雅可比、局部敏感度、数值根及根处分子和导数，形成预测区极点排除与可识别性验收义务。",
            "snapshotFiles": ["validation/hahn1-fold1-identifiability-protocol.json", "validation/hahn1-fold1-identifiability.json", "validation/hahn1-frozen-denominator-roots-protocol.json", "validation/hahn1-frozen-denominator-roots.json"],
        },
        {
            "id": "thurber-dataset-prospective-gate", "domain": "physics", "title": "Thurber 预测区与可识别性数据集前瞻验收",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Thurber.dat", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/v-thurber.shtml"],
            "metrics": {"nistReproduction": thurber["full_fit_certification"]["matches_nist_within_frozen_tolerances"], "overallAllFoldsGatedSupport": thurber["decision"]["overall_all_folds_gated_support"], "folds": [{"fold": fold["fold"], "testRmse": fold["test_metrics"]["rmse"], "baselineRmse": fold["baseline_test_metrics"]["rmse"], "rootsInHeldOutInterval": fold["domain_audit"].get("real_roots_in_closed_interval"), "numericalRank": fold["identifiability"].get("numerical_rank"), "scaledConditionNumber": fold["identifiability"].get("scaled_condition_number"), "gatedLimitedSupport": fold["decision"]["gated_limited_support"]} for fold in thurber["folds"]]},
            "scientificClaim": "Thurber 全数据拟合通过 NIST 已知答案复核；第 2—5 折通过冻结验收，第 1 折在约 -3.019661 的留出区实根处失效，因此整体五折支持不成立。",
            "limitations": " ".join(thurber["limitations"]), "upstreamContribution": "提供新数据集冻结协议、全部五折预测区根检查、局部秩与协方差检查、三次基线和失败记录。",
            "snapshotFiles": ["validation/thurber-prospective-gate-protocol.json", "validation/thurber-prospective-gate.json"],
        },
        {
            "id": "kirby2-cross-degree-prospective-gate", "domain": "physics", "title": "Kirby2 二次有理模型跨次数前瞻验收",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Kirby2.dat", "https://www.itl.nist.gov/div898/strd/nls/data/LINKS/v-kirby2.shtml"],
            "metrics": {"nistReproduction": kirby["full_fit_certification"]["matches_nist_within_frozen_tolerances"], "overallAllFoldsGatedSupport": kirby["decision"]["overall_all_folds_gated_support"], "fold1TrainingRmse": kirby["folds"][0]["identifiability"]["training_metrics"]["rmse"], "fold1TestRmse": kirby["folds"][0]["test_metrics"]["rmse"], "fold1BaselineRmse": kirby["folds"][0]["baseline_test_metrics"]["rmse"], "folds": [{"fold": fold["fold"], "testRmse": fold["test_metrics"]["rmse"], "baselineRmse": fold["baseline_test_metrics"]["rmse"], "rootsInHeldOutInterval": fold["domain_audit"].get("real_roots_in_closed_interval"), "numericalRank": fold["identifiability"].get("numerical_rank"), "scaledConditionNumber": fold["identifiability"].get("scaled_condition_number"), "gatedLimitedSupport": fold["decision"]["gated_limited_support"]} for fold in kirby["folds"]]},
            "scientificClaim": "Kirby2 五折均无留出区实根、数值秩均为 5 且均优于二次基线，因此获得本协议下整体有限支持；第 1 折外推衰减和高条件数仍保留。",
            "limitations": " ".join(kirby["limitations"]), "upstreamContribution": "提供不同次数有理模型的阳性对照、全部五折根检查、局部数值诊断、二次基线和训练—留出衰减对照。",
            "snapshotFiles": ["validation/kirby2-prospective-gate-protocol.json", "validation/kirby2-prospective-gate.json"],
        },
        {
            "id": "rational-cross-dataset-synthesis", "domain": "math", "title": "有理模型统一内核与跨数据集综合",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml"],
            "metrics": crossDataset["totals"],
            "scientificClaim": "统一内核下 15 折中 13 折符合验收；Hahn1 和 Thurber 各有一个预测区失败折，Kirby2 五折均通过。计数不表示普适检出率。",
            "limitations": " ".join(crossDataset["limitations"]), "upstreamContribution": "提供统一雅可比、数值根、预测区和局部数值诊断接口，并区分事后重建与数据集前瞻证据。",
            "snapshotFiles": ["validation/rational-cross-dataset-protocol.json", "validation/hahn1-fold1-identifiability.json", "validation/hahn1-frozen-denominator-roots.json", "validation/thurber-prospective-gate.json", "validation/kirby2-prospective-gate.json"],
        },
        {
            "id": "rational-exact-interval-sturm-solvers", "domain": "math", "title": "精确 Sturm 区间根隔离与双求解器复核",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml", "https://github.com/Z3Prover/z3", "https://github.com/cvc5/cvc5/releases/tag/cvc5-1.4.2"],
            "metrics": exactRoots["totals"],
            "scientificClaim": "对十五折有理系数快照，13 个闭区间精确无根，Hahn1 第 1 折精确有 2 根，Thurber 第 1 折精确有 1 根；双求解器逐折一致。",
            "limitations": " ".join(exactRoots["limitations"]), "upstreamContribution": "提供精确 Sturm 隔离、十五份 SMT-LIB、三十份求解器日志及完整哈希，区分快照证明与物理参数精确性。",
            "snapshotFiles": ["validation/rational-exact-interval-protocol.json", "validation/rational-exact-interval-roots.json", "validation/exact-interval-smt/hahn1-fold-1.smt2", "validation/exact-interval-smt/thurber-fold-1.smt2", "validation/exact-interval-logs/hahn1-fold-1-z3.log", "validation/exact-interval-logs/thurber-fold-1-cvc5.log"],
        },
        {
            "id": "rational-parameter-box-stability", "domain": "math", "title": "连续参数盒无根稳定性证明",
            "status": "verified", "evidenceClass": "local_recomputation",
            "sources": ["https://www.itl.nist.gov/div898/strd/nls/data/hahn1.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/thurber.shtml", "https://www.itl.nist.gov/div898/strd/nls/data/kirby2.shtml"],
            "metrics": {"totals": parameterBox["totals"], "finiteRadiusBrackets": [{"dataset": case["dataset"], "fold": case["fold"], "lower": case["certified_radius_lower_bound_float"], "upper": case["uncertified_radius_upper_bound_float"]} for case in parameterBox["cases"] if not case["cap_hit"] and case["snapshot_safe"]]},
            "scientificClaim": "13 个无根快照均获得正的连续参数盒无根半径；11 折达到上限 4，Hahn1 第 5 折和 Thurber 第 2 折为有限半径括号。",
            "limitations": " ".join(parameterBox["limitations"]), "upstreamContribution": "提供连续参数区域的精确充分性证明和跨零分段协议，不把下界当作置信区或必要最大半径。",
            "snapshotFiles": ["validation/rational-parameter-box-protocol.json", "validation/rational-parameter-box-protocol-amendment-01.json", "validation/rational-parameter-box-stability.json"],
        },
    ]
    packet = {
        "schemaVersion": 1,
        "asOf": "2026-11-09",
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
